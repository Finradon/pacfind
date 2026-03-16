from pacfind_lib.backends.brew import BrewBackend


class CompletedProcessStub:
    def __init__(self, stdout: str, returncode: int = 0) -> None:
        self.stdout = stdout
        self.returncode = returncode


def test_is_available_uses_brew_from_path(monkeypatch) -> None:
    calls: list[str] = []

    def fake_cmd_exists(name: str) -> bool:
        calls.append(name)
        return True

    monkeypatch.setattr("pacfind_lib.backends.brew.cmd_exists", fake_cmd_exists)

    assert BrewBackend().is_available() is True
    assert calls == ["brew"]


def test_list_installed_returns_formulae_and_casks(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_run(cmd: list[str]) -> CompletedProcessStub:
        calls.append(cmd)
        if cmd == ["brew", "list", "--formula"]:
            return CompletedProcessStub("wget\nzoxide\n")
        if cmd == ["brew", "list", "--cask"]:
            return CompletedProcessStub("firefox\nvisual-studio-code\n")
        raise AssertionError(f"unexpected command: {cmd}")

    monkeypatch.setattr("pacfind_lib.backends.brew.run", fake_run)

    results = BrewBackend().list_installed()

    assert calls == [["brew", "list", "--formula"], ["brew", "list", "--cask"]]
    assert [(result.name, result.source) for result in results] == [
        ("wget", "formula"),
        ("zoxide", "formula"),
        ("firefox", "cask"),
        ("visual-studio-code", "cask"),
    ]


def test_list_installed_tolerates_missing_cask_output(monkeypatch) -> None:
    def fake_run(cmd: list[str]) -> CompletedProcessStub:
        if cmd == ["brew", "list", "--formula"]:
            return CompletedProcessStub("fd\n")
        if cmd == ["brew", "list", "--cask"]:
            return CompletedProcessStub("", returncode=1)
        raise AssertionError(f"unexpected command: {cmd}")

    monkeypatch.setattr("pacfind_lib.backends.brew.run", fake_run)

    results = BrewBackend().list_installed()

    assert [(result.name, result.source) for result in results] == [("fd", "formula")]
