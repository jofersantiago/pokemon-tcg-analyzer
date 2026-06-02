# Inject the project venv's site-packages so `python3 main.py` works without activation
import sys as _sys
from pathlib import Path as _Path
_venv_lib = _Path(__file__).parent / "venv" / "lib"
if _venv_lib.exists():
    for _p in _venv_lib.iterdir():
        _sp = _p / "site-packages"
        if _sp.exists() and str(_sp) not in _sys.path:
            _sys.path.insert(0, str(_sp))
del _sys, _Path, _venv_lib, _p, _sp

from pathlib import Path  # noqa: E402
from src.data_ingest import fetch_card_catalog, fetch_tournament_data  # noqa: E402
from src.models import Card, Deck  # noqa: E402
from src.matchup import expected_win_rate  # noqa: E402
from src.card_roles import (  # noqa: E402
    compute_card_features, classify_roles, fit_win_rate_regression,
    attribute_win_rate, deck_role_fractions,
)
from src.visualizations import (  # noqa: E402
    plot_matchup_heatmap, plot_wr_comparison, plot_role_attribution,
)
from src.web_collection import launch_collection_browser, _prepare_page_data  # noqa: E402

_COLLECTION_PATH = Path(__file__).parent / "my_collection.json"
_OUTPUTS_DIR = Path(__file__).parent / "outputs"


# ---------------------------------------------------------------------------
# Pipeline helpers
# ---------------------------------------------------------------------------

def _load_pipeline_data() -> tuple:
    """Load catalog + tournament data and build meta decks."""
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
        if not known_cards:
            continue
        meta_decks.append(Deck.from_dict({**arch, "cards": known_cards}, catalog))

    return catalog, archetypes, matchup_matrix, meta_decks


def _run_analysis(catalog, archetypes, matchup_matrix, meta_decks) -> tuple:
    """Run role regression + EWR computation.

    Returns (ewrs, attributions, predicted_wrs, role_map, regression).
    """
    all_cards = list(catalog.values())
    features = compute_card_features(all_cards, archetypes)
    role_map = classify_roles(features)
    regression = fit_win_rate_regression(archetypes, role_map, catalog)
    print(f"  Role regression R² = {regression.r_squared:.3f}\n")

    ewrs, attributions, predicted_wrs = [], [], {}
    for deck, _arch in zip(meta_decks, archetypes):
        ewrs.append(expected_win_rate(deck, archetypes, matchup_matrix, catalog))
        fracs = deck_role_fractions(deck, role_map)
        attributions.append(attribute_win_rate(deck, role_map, regression))
        predicted_wrs[deck.archetype_label] = regression.predict(fracs)

    return ewrs, attributions, predicted_wrs, role_map, regression


def _generate_charts(archetypes, matchup_matrix, predicted_wrs, attributions) -> None:
    """Write all three matplotlib charts to outputs/."""
    arch_attr = {a["id"]: attr for a, attr in zip(archetypes, attributions)}
    plot_matchup_heatmap(matchup_matrix)
    plot_wr_comparison(archetypes, predicted_wrs)
    plot_role_attribution(archetypes, arch_attr)
    print("  Charts saved to outputs/\n")


# ---------------------------------------------------------------------------
# Reload callback (wired into the browser's ⟳ REFRESH button)
# ---------------------------------------------------------------------------

def _make_reload_fn(catalog: dict) -> object:
    """Return a callable the browser server uses to hot-reload tournament data."""
    def reload() -> dict:
        from src.data_ingest import _TOURNAMENT_CACHE
        if _TOURNAMENT_CACHE.exists():
            _TOURNAMENT_CACHE.unlink()

        print("  [REFRESH] Re-fetching tournament data...")
        tournament = fetch_tournament_data()
        new_archetypes = tournament["archetypes"]
        new_matchup_matrix = tournament["matchup_matrix"]

        new_meta_decks = []
        for arch in new_archetypes:
            known_cards = [e for e in arch["cards"] if e["id"] in catalog]
            if not known_cards:
                continue
            new_meta_decks.append(Deck.from_dict({**arch, "cards": known_cards}, catalog))

        new_ewrs, new_attributions, new_predicted_wrs, new_role_map, new_regression = \
            _run_analysis(catalog, new_archetypes, new_matchup_matrix, new_meta_decks)
        _generate_charts(new_archetypes, new_matchup_matrix, new_predicted_wrs, new_attributions)

        # Load the latest saved collection so analysis reflects current state
        my_cards: dict = {}
        if _COLLECTION_PATH.exists():
            import json
            with open(_COLLECTION_PATH) as f:
                my_cards = json.load(f)

        page_data = _prepare_page_data(
            new_archetypes, catalog, my_cards,
            new_ewrs, new_attributions, new_meta_decks,
            matchup_matrix=new_matchup_matrix,
            role_map=new_role_map,
            regression=new_regression,
        )
        print("  [REFRESH] Done.\n")
        return page_data  # {decks, meta, analysis} sent as JSON to the browser

    return reload


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 55)
    print("  Pokémon TCG Pocket Meta-Analyzer")
    print("=" * 55)

    catalog, archetypes, matchup_matrix, meta_decks = _load_pipeline_data()
    ewrs, attributions, predicted_wrs, role_map, regression = _run_analysis(
        catalog, archetypes, matchup_matrix, meta_decks
    )

    print("Generating charts...")
    _generate_charts(archetypes, matchup_matrix, predicted_wrs, attributions)

    reload_fn = _make_reload_fn(catalog)

    launch_collection_browser(
        archetypes=archetypes,
        catalog=catalog,
        collection_path=_COLLECTION_PATH,
        ewrs=ewrs,
        attributions=attributions,
        meta_decks=meta_decks,
        outputs_dir=_OUTPUTS_DIR,
        reload_fn=reload_fn,
        matchup_matrix=matchup_matrix,
        role_map=role_map,
        regression=regression,
    )


if __name__ == "__main__":
    main()
