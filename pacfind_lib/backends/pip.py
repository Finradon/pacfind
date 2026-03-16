import json
from typing import List, Optional

from pacfind_lib.backends.common import cmd_exists, run
from pacfind_lib.models import Result


class PipBackend:
    manager = "pip"

    def is_available(self) -> bool:
        return cmd_exists("python3")

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
                    manager=self.manager,
                    source="pypi",
                )
            )
        return out

    def _run_pip_json(self) -> Optional[object]:
        return run(["python3", "-m", "pip", "list", "--format=json"])
