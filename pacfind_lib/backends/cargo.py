from typing import List

from pacfind_lib.backends.common import cmd_exists, run
from pacfind_lib.models import Result


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
            out.append(
                Result(
                    name=pkg.split()[0],
                    installed=True,
                    manager=self.manager,
                    source="crates.io",
                )
            )
        return out
