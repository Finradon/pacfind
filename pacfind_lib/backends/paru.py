from typing import List

from pacfind_lib.backends.common import cmd_exists, run
from pacfind_lib.models import Result


class ParuBackend:
    manager = "paru"

    def is_available(self) -> bool:
        return cmd_exists("paru")

    def list_installed(self) -> List[Result]:
        cp = run(["paru", "-Qm"])
        if cp.returncode != 0:
            return []

        out: List[Result] = []
        for line in cp.stdout.splitlines():
            if not line.strip():
                continue
            name = line.split()[0]
            out.append(
                Result(
                    name=name,
                    installed=True,
                    manager=self.manager,
                    source="aur",
                )
            )
        return out
