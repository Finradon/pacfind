from typing import List

from pacfind_lib.backends.common import cmd_exists, run
from pacfind_lib.models import Result


class BrewBackend:
    manager = "brew"

    def is_available(self) -> bool:
        return cmd_exists("brew")

    def list_installed(self) -> List[Result]:
        return self._list_formulae() + self._list_casks()

    def _list_formulae(self) -> List[Result]:
        return self._list_entries(["brew", "list", "--formula"], source="formula")

    def _list_casks(self) -> List[Result]:
        return self._list_entries(["brew", "list", "--cask"], source="cask")

    def _list_entries(self, cmd: List[str], source: str) -> List[Result]:
        cp = run(cmd)
        if cp.returncode != 0:
            return []

        out: List[Result] = []
        for line in cp.stdout.splitlines():
            name = line.strip()
            if not name:
                continue
            out.append(
                Result(
                    name=name,
                    installed=True,
                    manager=self.manager,
                    source=source,
                )
            )
        return out
