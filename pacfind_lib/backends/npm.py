import json
from typing import List
from urllib.parse import urlparse

from pacfind_lib.backends.common import cmd_exists, run
from pacfind_lib.models import Result


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
                    manager=self.manager,
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
