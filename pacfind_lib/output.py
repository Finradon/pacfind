import os
import sys
from typing import List

from pacfind_lib.models import Result


def use_color(force: bool | None) -> bool:
    if force is not None:
        return force
    if os.environ.get("NO_COLOR") is not None:
        return False
    return sys.stdout.isatty()


def c(text: str, code: str, enabled: bool) -> str:
    if not enabled:
        return text
    return f"\x1b[{code}m{text}\x1b[0m"


def pad_and_color(text: str, width: int, code: str, enabled: bool) -> str:
    padded = f"{text:<{width}}"
    return c(padded, code, enabled) if enabled else padded


def format_row(res: Result, color: bool) -> str:
    name = res.name
    status = "installed" if res.installed else "not installed"
    manager = res.manager or "-"
    source = res.source or "-"

    name_col = f"{name:<28}"
    status_col = pad_and_color(status, 14, "32" if res.installed else "31", color)
    manager_col = (
        pad_and_color(manager, 10, "36", color) if res.installed else f"{manager:<10}"
    )
    source_col = c(source, "90", color) if res.installed else source

    return f"{name_col} {status_col} {manager_col} {source_col}"


def format_table(results: List[Result], color: bool) -> str:
    header = f"{'NAME':<28} {'STATUS':<14} {'MANAGER':<10} {'SOURCE'}"
    rows = [format_row(r, color) for r in results]
    return f"{c(header, '1', color)}\n" + "\n".join(rows)
