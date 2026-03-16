from typing import Dict, List, Optional, Set

from pacfind_lib.backends.common import chunked, cmd_exists, run
from pacfind_lib.models import Result


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
        repo_map = pacman_repo_map([pkg for pkg in installed if pkg not in foreign])
        out: List[Result] = []
        for name in installed:
            if name in foreign:
                continue
            out.append(
                Result(
                    name=name,
                    installed=True,
                    manager=self.manager,
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
