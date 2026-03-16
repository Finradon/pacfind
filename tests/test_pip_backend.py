from pacfind_lib.backends.pip import PipBackend


class CompletedProcessStub:
    def __init__(self, stdout: str, returncode: int = 0) -> None:
        self.stdout = stdout
        self.returncode = returncode


def test_is_available_uses_python3_from_path(monkeypatch) -> None:
    calls: list[str] = []

    def fake_cmd_exists(name: str) -> bool:
        calls.append(name)
        return True

    monkeypatch.setattr("pacfind_lib.backends.pip.cmd_exists", fake_cmd_exists)

    assert PipBackend().is_available() is True
    assert calls == ["python3"]


def test_list_installed_reads_json_output(monkeypatch) -> None:
    monkeypatch.setattr(
        "pacfind_lib.backends.pip.run",
        lambda _: CompletedProcessStub('[{"name":"pip"},{"name":"setuptools"}]'),
    )

    results = PipBackend().list_installed()

    assert [result.name for result in results] == ["pip", "setuptools"]
    assert [result.source for result in results] == ["pypi", "pypi"]
