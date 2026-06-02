from __future__ import annotations
from tabulate import tabulate as _tabulate


def header(title: str) -> None:
    width = max(50, len(title) + 4)
    print(f"\n{'=' * width}")
    print(f"  {title}")
    print(f"{'=' * width}\n")


def separator() -> None:
    print("─" * 52)


def table(rows: list, headers: list[str]) -> None:
    print(_tabulate(rows, headers=headers, tablefmt="simple"))


def prompt(msg: str) -> str:
    return input(f"\n{msg}: ").strip()


def pick(options: list[str], label: str = "Choose") -> int:
    """Print numbered options and return 0-based index of selection.

    Returns -1 when the user picks [0] (Back / Exit).
    Loops until a valid choice is entered.
    """
    for i, opt in enumerate(options, 1):
        print(f"  [{i}] {opt}")
    print("  [0] Back")
    while True:
        raw = input(f"\n{label}: ").strip()
        if raw == "0":
            return -1
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return int(raw) - 1
        print(f"  Please enter 1–{len(options)} or 0 to go back.")
