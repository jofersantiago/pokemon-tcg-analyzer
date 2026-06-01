# Inject the project venv's site-packages so `python3 main_cli.py` works without activation
import sys as _sys
from pathlib import Path as _Path
_venv_lib = _Path(__file__).parent / "venv" / "lib"
if _venv_lib.exists():
    for _p in _venv_lib.iterdir():
        _sp = _p / "site-packages"
        if _sp.exists() and str(_sp) not in _sys.path:
            _sys.path.insert(0, str(_sp))
del _sys, _Path, _venv_lib, _p, _sp

import argparse  # noqa: E402

from src.data_ingest import fetch_card_catalog, fetch_tournament_data  # noqa: E402
from src.models import Card, Deck  # noqa: E402
from src.matchup import expected_win_rate  # noqa: E402
from src.card_roles import (  # noqa: E402
    compute_card_features, classify_roles,
    fit_win_rate_regression, attribute_win_rate,
)
from src.cli.state import AppState  # noqa: E402
from src.cli.menu import run_menu  # noqa: E402
from src.cli import commands  # noqa: E402


def _load_state() -> AppState:
    print("Loading card catalog...")
    cards_raw = fetch_card_catalog()
    catalog = {d["id"]: Card.from_dict(d) for d in cards_raw}
    print(f"  {len(catalog)} cards loaded.")

    print("Fetching tournament data from Limitless TCG API...")
    tournament = fetch_tournament_data()
    archetypes = tournament["archetypes"]
    matchup_matrix = tournament["matchup_matrix"]
    print(f"  {len(archetypes)} archetypes loaded.")

    meta_decks = []
    for arch in archetypes:
        known_cards = [e for e in arch["cards"] if e["id"] in catalog]
        if known_cards:
            meta_decks.append(
                Deck.from_dict({**arch, "cards": known_cards}, catalog)
            )

    all_cards = list(catalog.values())
    features = compute_card_features(all_cards, archetypes)
    role_map = classify_roles(features)
    regression = fit_win_rate_regression(archetypes, role_map, catalog)
    print(f"  Role regression R² = {regression.r_squared:.3f}\n")

    ewrs = [
        expected_win_rate(d, archetypes, matchup_matrix, catalog)
        for d in meta_decks
    ]
    attributions = [
        attribute_win_rate(d, role_map, regression)
        for d in meta_decks
    ]

    return AppState(
        catalog=catalog,
        archetypes=archetypes,
        matchup_matrix=matchup_matrix,
        meta_decks=meta_decks,
        ewrs=ewrs,
        attributions=attributions,
        role_map=role_map,
        regression=regression,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Pokémon TCG Pocket Meta-Analyzer — CLI",
        epilog="Run with no arguments to launch the interactive menu.",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("meta", help="Browse top archetypes")

    col = sub.add_parser("collection", help="Manage your card collection")
    col_sub = col.add_subparsers(dest="subcommand")
    col_import = col_sub.add_parser("import", help="Import collection from CSV")
    col_import.add_argument("--file", default=None,
                            help="Path to CSV file (default: data/my_collection.csv)")
    col_sub.add_parser("random", help="Generate a random collection")
    col_sub.add_parser("view", help="View current collection")

    cat = sub.add_parser("catalog", help="Search the card catalog")
    cat.add_argument("--search", default="", metavar="QUERY",
                     help="Search term (name, type, or set)")

    an = sub.add_parser("analysis", help="Analyze a deck vs. the meta")
    an.add_argument("--deck", default="", metavar="NAME",
                    help="Archetype name to analyze (partial match)")

    return parser


def main() -> None:
    print("=" * 55)
    print("  Pokémon TCG Pocket Meta-Analyzer — CLI")
    print("=" * 55)

    parser = _build_parser()
    args = parser.parse_args()

    try:
        state = _load_state()
    except Exception as exc:
        print(f"\nError loading data: {exc}")
        print("Check your internet connection and try again.")
        return

    if args.command == "meta":
        commands.cmd_meta(state)
    elif args.command == "collection":
        sub = getattr(args, "subcommand", None)
        if sub == "import":
            commands._collection_import(state)
        elif sub == "random":
            commands._collection_random(state)
        elif sub == "view":
            commands._collection_view()
        else:
            commands.cmd_collection(state)
    elif args.command == "catalog":
        commands.cmd_catalog(state, search=args.search)
    elif args.command == "analysis":
        commands.cmd_analysis(state, your_name=args.deck)
    else:
        run_menu(state)


if __name__ == "__main__":
    main()
