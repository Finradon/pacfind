from typing import List, Protocol, Sequence

from pacfind_lib.backends.brew import BrewBackend
from pacfind_lib.backends.cargo import CargoBackend
from pacfind_lib.backends.flatpak import FlatpakBackend
from pacfind_lib.backends.macos import MacOSApplicationsBackend
from pacfind_lib.backends.npm import NpmBackend
from pacfind_lib.backends.pacman import PacmanBackend
from pacfind_lib.backends.paru import ParuBackend
from pacfind_lib.backends.pip import PipBackend


class Backend(Protocol):
    manager: str

    def is_available(self) -> bool: ...

    def list_installed(self): ...


def get_backends() -> List[Backend]:
    return [
        MacOSApplicationsBackend(),
        BrewBackend(),
        PacmanBackend(),
        ParuBackend(),
        FlatpakBackend(),
        PipBackend(),
        NpmBackend(),
        CargoBackend(),
    ]


def get_backend_names(backends: Sequence[Backend] | None = None) -> List[str]:
    registered = list(backends) if backends is not None else get_backends()
    return [backend.manager for backend in registered]
