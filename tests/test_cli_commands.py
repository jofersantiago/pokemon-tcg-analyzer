import pytest
from src.models import Card, Deck
from src.card_roles import RegressionResult
from src.cli.state import AppState


def _make_state() -> AppState:
    pikachu = Card(id="A1-001", name="Pikachu ex", card_type="Pokemon",
                   hp=120, rarity="ex", set_id="A1", attacks=[{"damage": 90}])
    misty = Card(id="A1-002", name="Misty", card_type="Trainer",
                 hp=None, rarity="2", set_id="A1")
    water = Card(id="A1-003", name="Water Energy", card_type="Energy",
                 hp=None, rarity="1", set_id="A1")
    catalog = {c.id: c for c in [pikachu, misty, water]}

    arch1 = {
        "id": "pikachu-ex",
        "name": "Pikachu ex",
        "meta_share": 0.20,
        "win_rate": 0.53,
        "cards": [{"id": "A1-001", "count": 2}, {"id": "A1-002", "count": 2},
                  {"id": "A1-003", "count": 2}],
    }
    arch2 = {
        "id": "misty-water",
        "name": "Misty Water",
        "meta_share": 0.10,
        "win_rate": 0.47,
        "cards": [{"id": "A1-002", "count": 2}, {"id": "A1-003", "count": 4}],
    }
    archetypes = [arch1, arch2]
    deck1 = Deck.from_dict(arch1, catalog)
    deck2 = Deck.from_dict(arch2, catalog)

    regression = RegressionResult(
        coef={"win_condition": 0.05, "engine": 0.03, "staple": 0.02,
              "tech": 0.01, "garnet": -0.01},
        intercept=0.45,
        r_squared=0.37,
    )
    role_map = {"A1-001": "win_condition", "A1-002": "engine", "A1-003": "staple"}

    return AppState(
        catalog=catalog,
        archetypes=archetypes,
        matchup_matrix={
            "pikachu-ex": {"pikachu-ex": 0.5, "misty-water": 0.55},
            "misty-water": {"pikachu-ex": 0.45, "misty-water": 0.5},
        },
        meta_decks=[deck1, deck2],
        ewrs=[0.512, 0.488],
        attributions=[
            {"win_condition": 0.023, "engine": 0.015, "staple": 0.01,
             "tech": 0.0, "garnet": 0.0},
            {"win_condition": 0.0, "engine": 0.02, "staple": 0.015,
             "tech": 0.0, "garnet": 0.0},
        ],
        role_map=role_map,
        regression=regression,
    )


def test_build_meta_rows():
    from src.cli.commands import _build_meta_rows
    state = _make_state()
    rows = _build_meta_rows(state)
    assert len(rows) == 2
    assert rows[0][1] == "Pikachu ex"
    assert rows[0][2] == "20.0%"


def test_build_catalog_rows_search():
    from src.cli.commands import _build_catalog_rows
    state = _make_state()
    rows = _build_catalog_rows(state, "pikachu")
    assert len(rows) == 1
    assert rows[0][1] == "Pikachu ex"


def test_build_catalog_rows_all():
    from src.cli.commands import _build_catalog_rows
    state = _make_state()
    rows = _build_catalog_rows(state, "")
    assert len(rows) == 3


def test_build_analysis_output():
    from src.cli.commands import _build_analysis_output
    state = _make_state()
    result = _build_analysis_output(state, your_idx=0, opp_idx=1)
    assert "win_condition" in result["dna_rows"][0]
    assert result["ewr"] == pytest.approx(0.55, abs=0.01)
    assert isinstance(result["big_swing"], str)
    assert len(result["gap_rows"]) > 0


def test_menu_imports():
    from src.cli.menu import run_menu
    assert callable(run_menu)
