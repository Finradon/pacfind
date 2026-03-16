from dataclasses import dataclass

from pacfind_lib.cli import build_parser, main
from pacfind_lib.models import Result


@dataclass
class FakeBackend:
    manager: str
    results: list[Result]
    available: bool = True

    def is_available(self) -> bool:
        return self.available

    def list_installed(self) -> list[Result]:
        return list(self.results)


def test_build_parser_uses_registered_backends_for_manager_choices() -> None:
    parser = build_parser(["pacman", "brew"])

    manager_action = next(
        action for action in parser._actions if action.dest == "manager"
    )

    assert manager_action.choices == ["pacman", "brew"]


def test_main_filters_and_prioritizes_exact_name_matches(capsys) -> None:
    backends = [
        FakeBackend(
            manager="pacman",
            results=[
                Result(name="ripgrep", installed=True, manager="pacman", source="core"),
                Result(name="grep", installed=True, manager="pacman", source="core"),
                Result(
                    name="grepper", installed=True, manager="pacman", source="extra"
                ),
            ],
        )
    ]

    exit_code = main(["grep"], backends=backends)
    output_lines = capsys.readouterr().out.strip().splitlines()

    assert exit_code == 0
    assert output_lines[1].split()[0] == "grep"
    assert output_lines[2].split()[0] == "grepper"


def test_main_returns_not_found_row_for_empty_result(capsys) -> None:
    exit_code = main(
        ["--manager", "brew"],
        backends=[FakeBackend(manager="brew", results=[], available=True)],
    )

    assert exit_code == 1
    assert "brew packages" in capsys.readouterr().out
