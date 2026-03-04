import json
import os
import shutil
import subprocess
from typing import Dict, List, Optional, Protocol, Set
from urllib.parse import urlparse

from pacfind_lib.models import Result


def cmd_exists(name: str) -> bool:
    return shutil.which(name) is not None


def run(cmd: List[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "LC_ALL": "C", "LANG": "C"},
    )


class Backend(Protocol):
    manager: str

    def is_available(self) -> bool: ...

    def list_installed(self) -> List[Result]: ...


def chunked(items: List[str], size: int) -> List[List[str]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def parse_pacman_qi_output(text: str) -> Dict[str, Optional[str]]:
    results: Dict[str, Optional[str]] = {}
    name: Optional[str] = None
    repo: Optional[str] = None

    def flush() -> None:
        nonlocal name, repo
        if name:
            results[name] = repo
        name = None
        repo = None

    for line in text.splitlines():
        if not line.strip():
            flush()
            continue
        if line.startswith("Name"):
            _, val = line.split(":", 1)
            name = val.strip()
            continue
        if line.startswith("Repository") or line.startswith("Installed From"):
            _, val = line.split(":", 1)
            repo = val.strip()
            continue

    flush()
    return results


def pacman_repo_map(pkgs: List[str], chunk_size: int = 200) -> Dict[str, Optional[str]]:
    if not pkgs:
        return {}
    repo_map: Dict[str, Optional[str]] = {}
    for chunk in chunked(pkgs, chunk_size):
        cp = run(["pacman", "-Qi", *chunk])
        if cp.returncode != 0:
            continue
        repo_map.update(parse_pacman_qi_output(cp.stdout))
    return repo_map


class PacmanBackend:
    manager = "pacman"

    def is_available(self) -> bool:
        return cmd_exists("pacman")

    def list_installed(self) -> List[Result]:
        cp = run(["pacman", "-Qq"])
        if cp.returncode != 0:
            return []
        installed = [line.strip() for line in cp.stdout.splitlines() if line.strip()]
        foreign = self._list_foreign()
        repo_map = pacman_repo_map([p for p in installed if p not in foreign])
        out: List[Result] = []
        for name in installed:
            if name in foreign:
                continue
            out.append(
                Result(
                    name=name,
                    installed=True,
                    manager="pacman",
                    source=repo_map.get(name),
                )
            )
        return out

    def _list_foreign(self) -> Set[str]:
        cmd = ["pacman", "-Qm"]
        if cmd_exists("paru"):
            cmd = ["paru", "-Qm"]
        cp = run(cmd)
        if cp.returncode != 0:
            return set()
        out: Set[str] = set()
        for line in cp.stdout.splitlines():
            if not line.strip():
                continue
            out.add(line.split()[0])
        return out


class ParuBackend:
    manager = "paru"

    def is_available(self) -> bool:
        return cmd_exists("pacman")

    def list_installed(self) -> List[Result]:
        cp = run(["pacman", "-Qm"])
        if cp.returncode != 0:
            return []
        manager_name = "paru" if cmd_exists("paru") else "pacman"
        source_name = "aur" if cmd_exists("paru") else "local"
        out: List[Result] = []
        for line in cp.stdout.splitlines():
            if not line.strip():
                continue
            name = line.split()[0]
            out.append(
                Result(
                    name=name,
                    installed=True,
                    manager=manager_name,
                    source=source_name,
                )
            )
        # Only entries identified as paru should be emitted by this backend.
        return [r for r in out if r.manager == "paru"]


class FlatpakBackend:
    manager = "flatpak"

    def is_available(self) -> bool:
        return cmd_exists("flatpak")

    def list_installed(self) -> List[Result]:
        cp = run(["flatpak", "list", "--columns=application,origin", "--format=json"])
        if cp.returncode == 0:
            try:
                data = json.loads(cp.stdout)
                out = []
                for row in data:
                    app_id = row.get("application")
                    origin = row.get("origin")
                    if app_id:
                        out.append(
                            Result(
                                name=app_id,
                                installed=True,
                                manager="flatpak",
                                source=origin,
                            )
                        )
                return out
            except json.JSONDecodeError:
                pass

        cp = run(["flatpak", "list", "--columns=application,origin"])
        if cp.returncode != 0:
            return []

        out = []
        for line in cp.stdout.splitlines():
            parts = [p for p in line.split("\t") if p]
            if len(parts) >= 2:
                app_id, origin = parts[0].strip(), parts[1].strip()
                out.append(
                    Result(
                        name=app_id,
                        installed=True,
                        manager="flatpak",
                        source=origin,
                    )
                )
        return out


class PipBackend:
    manager = "pip"

    def is_available(self) -> bool:
        return os.path.exists("/usr/bin/python3")

    def list_installed(self) -> List[Result]:
        cp = self._run_pip_json()
        if cp is None or cp.returncode != 0:
            return []
        try:
            data = json.loads(cp.stdout)
        except json.JSONDecodeError:
            return []

        out: List[Result] = []
        for row in data:
            name = row.get("name")
            if not name:
                continue
            out.append(
                Result(
                    name=name,
                    installed=True,
                    manager="pip",
                    # Global pip packages are typically sourced from PyPI.
                    source="pypi",
                )
            )
        return out

    def _run_pip_json(self) -> Optional[subprocess.CompletedProcess]:
        env = {**os.environ, "LC_ALL": "C", "LANG": "C"}
        env.pop("VIRTUAL_ENV", None)
        cp = subprocess.run(
            ["/usr/bin/python3", "-m", "pip", "list", "--format=json"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )
        return cp


class NpmBackend:
    manager = "npm"

    def is_available(self) -> bool:
        return cmd_exists("npm")

    def list_installed(self) -> List[Result]:
        cp = run(["npm", "list", "-g", "--depth=0", "--json"])
        if cp.returncode != 0:
            return []
        try:
            data = json.loads(cp.stdout)
        except json.JSONDecodeError:
            return []

        registry = self._npm_registry_source()
        deps = data.get("dependencies", {})
        if not isinstance(deps, dict):
            return []

        out: List[Result] = []
        for name in deps.keys():
            if not name:
                continue
            out.append(
                Result(
                    name=name,
                    installed=True,
                    manager="npm",
                    source=registry,
                )
            )
        return out

    def _npm_registry_source(self) -> str:
        cp = run(["npm", "config", "get", "registry"])
        if cp.returncode != 0:
            return "registry.npmjs.org"
        raw = cp.stdout.strip()
        if not raw:
            return "registry.npmjs.org"
        parsed = urlparse(raw)
        if parsed.netloc:
            return parsed.netloc.lower()
        return raw.lower().strip("/")


class CargoBackend:
    manager = "cargo"

    def is_available(self) -> bool:
        return cmd_exists("cargo")

    def list_installed(self) -> List[Result]:
        cp = run(["cargo", "install", "--list"])
        if cp.returncode != 0:
            return []

        out: List[Result] = []
        for line in cp.stdout.splitlines():
            if not line or line.startswith(" "):
                continue
            if not line.endswith(":"):
                continue
            pkg = line[:-1].strip()
            if not pkg:
                continue
            # Format is usually "<name> v<version>"
            name = pkg.split()[0]
            out.append(
                Result(
                    name=name,
                    installed=True,
                    manager="cargo",
                    source="crates.io",
                )
            )
        return out


def get_backends() -> List[Backend]:
    return [
        PacmanBackend(),
        ParuBackend(),
        FlatpakBackend(),
        PipBackend(),
        NpmBackend(),
        CargoBackend(),
    ]
