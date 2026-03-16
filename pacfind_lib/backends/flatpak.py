import json
from typing import List

from pacfind_lib.backends.common import cmd_exists, run
from pacfind_lib.models import Result


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
                                manager=self.manager,
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
            parts = [part for part in line.split("\t") if part]
            if len(parts) >= 2:
                app_id, origin = parts[0].strip(), parts[1].strip()
                out.append(
                    Result(
                        name=app_id,
                        installed=True,
                        manager=self.manager,
                        source=origin,
                    )
                )
        return out
