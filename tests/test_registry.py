from pacfind_lib.backends import get_backend_names, get_backends


def test_registry_names_match_backend_managers() -> None:
    backends = get_backends()

    assert get_backend_names(backends) == [backend.manager for backend in backends]


def test_registry_has_unique_manager_names() -> None:
    names = get_backend_names()

    assert len(names) == len(set(names))
