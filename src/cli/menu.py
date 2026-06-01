from __future__ import annotations

from src.cli.state import AppState
from src.cli.display import header, pick
from src.cli import commands

_TABS = ["Meta", "Collection", "Catalog", "Analysis"]


def run_menu(state: AppState) -> None:
    """Loop the main 4-tab menu until the user exits."""
    while True:
        header("POKÉMON TCG POCKET — META ANALYZER")
        choice = pick(_TABS)
        if choice < 0:
            print("\nGoodbye!\n")
            return
        if choice == 0:
            commands.cmd_meta(state)
        elif choice == 1:
            commands.cmd_collection(state)
        elif choice == 2:
            commands.cmd_catalog(state)
        elif choice == 3:
            commands.cmd_analysis(state)
