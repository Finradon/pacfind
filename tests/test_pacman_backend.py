from pacfind_lib.backends.pacman import (
    PacmanBackend,
    pacman_repo_map,
    parse_pacman_qi_output,
)


class CompletedProcessStub:
    def __init__(self, stdout: str, returncode: int = 0) -> None:
        self.stdout = stdout
        self.returncode = returncode


def test_parse_pacman_qi_output_extracts_package_repositories() -> None:
    output = """Name            : grep
Version         : 3.11-1
Repository      : core

Name            : ripgrep
Version         : 14.1.1-1
Installed From  : extra
"""

    assert parse_pacman_qi_output(output) == {"grep": "core", "ripgrep": "extra"}


def test_pacman_repo_map_chunks_queries(monkeypatch) -> None:
    calls: list[list[str]] = []
    responses = iter(
        [
            CompletedProcessStub("Name : grep\nRepository : core\n"),
            CompletedProcessStub("Name : sed\nRepository : base\n"),
        ]
    )

    def fake_run(cmd: list[str]) -> CompletedProcessStub:
        calls.append(cmd)
        return next(responses)

    monkeypatch.setattr("pacfind_lib.backends.pacman.run", fake_run)

    repo_map = pacman_repo_map(["grep", "awk", "sed"], chunk_size=2)

    assert repo_map == {"grep": "core", "sed": "base"}
    assert calls == [["pacman", "-Qi", "grep", "awk"], ["pacman", "-Qi", "sed"]]


def test_list_installed_excludes_foreign_packages(monkeypatch) -> None:
    responses = iter(
        [
            CompletedProcessStub("grep\nripgrep\nyay-bin\n"),
            CompletedProcessStub("yay-bin 12.0.0-1\n"),
        ]
    )

    monkeypatch.setattr("pacfind_lib.backends.pacman.run", lambda _: next(responses))
    monkeypatch.setattr("pacfind_lib.backends.pacman.cmd_exists", lambda _: False)
    monkeypatch.setattr(
        "pacfind_lib.backends.pacman.pacman_repo_map",
        lambda _: {"grep": "core", "ripgrep": "extra"},
    )

    results = PacmanBackend().list_installed()

    assert [result.name for result in results] == ["grep", "ripgrep"]
    assert [result.source for result in results] == ["core", "extra"]
