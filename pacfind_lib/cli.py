import argparse
from typing import List, Sequence

from pacfind_lib.backends import Backend, get_backend_names, get_backends
from pacfind_lib.models import Result
from pacfind_lib.output import format_table, use_color


def build_parser(backend_names: Sequence[str]) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Find how a package is installed across supported package managers."
    )
    parser.add_argument(
        "name",
        nargs="?",
        help="Package/app name",
    )
    parser.add_argument(
        "-m",
        "--manager",
        choices=list(backend_names),
        help="Filter by manager and list installed entries for that manager",
    )
    parser.add_argument(
        "-s",
        "--source",
        help="Filter by source and list installed entries for that source",
    )
    return parser


def collect_results(backends: Sequence[Backend]) -> List[Result]:
    results: List[Result] = []
    for backend in backends:
        if not backend.is_available():
            continue
        results.extend(backend.list_installed())
    return results


def _not_found_name(name: str | None, manager: str | None, source: str | None) -> str:
    if name is not None:
        return name
    if manager is not None and source is not None:
        return f"{manager} packages from {source}"
    if manager is not None:
        return f"{manager} packages"
    return f"packages from {source}"


def main(argv: Sequence[str] | None = None, backends: Sequence[Backend] | None = None) -> int:
    available_backends = list(backends) if backends is not None else get_backends()
    parser = build_parser(get_backend_names(available_backends))
    args = parser.parse_args(list(argv) if argv is not None else None)

    name = args.name
    manager_filter = args.manager
    source_filter = args.source
    color = use_color(None)

    if name is None and manager_filter is None and source_filter is None:
        parser.error("either NAME, --manager/-m, or --source/-s must be provided")

    results = collect_results(available_backends)

    if name is not None:
        query = name.lower()
        results = [r for r in results if query in r.name.lower()]

    if manager_filter is not None:
        results = [r for r in results if r.manager == manager_filter]
    if source_filter is not None:
        source_query = source_filter.lower()
        results = [
            r
            for r in results
            if r.source is not None and r.source.lower() == source_query
        ]

    if results:
        if name is not None:
            query = name.lower()
            exact = [r for r in results if r.name.lower() == query]
            others = [r for r in results if r.name.lower() != query]
            others.sort(key=lambda r: r.name.lower())
            ordered = exact + others
        else:
            ordered = sorted(results, key=lambda r: r.name.lower())
        print(format_table(ordered, color))
        return 0

    print(
        format_table(
            [
                Result(
                    name=_not_found_name(name, manager_filter, source_filter),
                    installed=False,
                )
            ],
            color,
        )
    )
    return 1
