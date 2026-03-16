import plistlib
import sys
from pathlib import Path
from typing import Iterable, List, Sequence

from pacfind_lib.models import Result


class MacOSApplicationsBackend:
    manager = "macos"

    def __init__(self, app_roots: Sequence[Path] | None = None) -> None:
        self.app_roots = (
            list(app_roots)
            if app_roots is not None
            else [
                Path("/Applications"),
                Path.home() / "Applications",
            ]
        )

    def is_available(self) -> bool:
        return sys.platform == "darwin"

    def list_installed(self) -> List[Result]:
        out: List[Result] = []
        for root in self.app_roots:
            if not root.is_dir():
                continue
            source = self._source_for_root(root)
            for app_path in self._iter_top_level_apps(root):
                out.append(
                    Result(
                        name=self._display_name(app_path),
                        installed=True,
                        manager=self.manager,
                        source=source,
                        detail=self._bundle_identifier(app_path),
                    )
                )
        return out

    def _iter_top_level_apps(self, root: Path) -> Iterable[Path]:
        for entry in sorted(root.iterdir(), key=lambda path: path.name.lower()):
            if entry.is_dir() and entry.suffix == ".app":
                yield entry

    def _source_for_root(self, root: Path) -> str:
        return (
            "user-applications"
            if root == Path.home() / "Applications"
            else "applications"
        )

    def _display_name(self, app_path: Path) -> str:
        info = self._read_info_plist(app_path)
        return (
            info.get("CFBundleDisplayName") or info.get("CFBundleName") or app_path.stem
        )

    def _bundle_identifier(self, app_path: Path) -> str | None:
        return self._read_info_plist(app_path).get("CFBundleIdentifier")

    def _read_info_plist(self, app_path: Path) -> dict:
        plist_path = app_path / "Contents" / "Info.plist"
        if not plist_path.is_file():
            return {}
        try:
            with plist_path.open("rb") as handle:
                data = plistlib.load(handle)
        except (OSError, plistlib.InvalidFileException):
            return {}
        return data if isinstance(data, dict) else {}
