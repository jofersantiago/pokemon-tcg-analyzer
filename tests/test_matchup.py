import pytest
from src.models import Deck
from src.matchup import deck_fingerprint, fingerprint_distance, match_archetype, expected_win_rate


@pytest.fixture
def deck_a(sample_card_catalog):
    return Deck.from_dict(
        {"id": "deck-a", "cards": [{"id": "A1-001", "count": 2}, {"id": "A1-225", "count": 2}]},
        sample_card_catalog,
    )


def test_fingerprint_sums_to_one(deck_a):
    assert abs(sum(deck_fingerprint(deck_a).values()) - 1.0) < 1e-9


def test_identical_distance_zero(deck_a):
    fp = deck_fingerprint(deck_a)
    assert fingerprint_distance(fp, fp) < 1e-9


def test_disjoint_distance_one():
    assert abs(fingerprint_distance({"A": 1.0}, {"B": 1.0}) - 1.0) < 1e-9


def test_match_archetype_returns_self(sample_card_catalog, deck_a):
    archetypes = [
        {"id": "deck-a", "cards": [{"id": "A1-001", "count": 2}, {"id": "A1-225", "count": 2}]},
        {"id": "deck-b", "cards": [{"id": "A1-002", "count": 2}, {"id": "A1-250", "count": 2}]},
    ]
    label, dist = match_archetype(deck_a, archetypes, sample_card_catalog)
    assert label == "deck-a" and dist < 1e-9


@pytest.fixture
def two_archetypes(sample_card_catalog):
    return [
        {"id": "deck-a", "meta_share": 0.60, "win_rate": 0.55,
         "cards": [{"id": "A1-001", "count": 2}, {"id": "A1-225", "count": 2}]},
        {"id": "deck-b", "meta_share": 0.40, "win_rate": 0.45,
         "cards": [{"id": "A1-002", "count": 2}, {"id": "A1-250", "count": 2}]},
    ]


@pytest.fixture
def two_matchup_matrix():
    return {
        "deck-a": {"deck-a": 0.50, "deck-b": 0.60},
        "deck-b": {"deck-a": 0.40, "deck-b": 0.50},
    }


def test_known_deck_ewr(sample_card_catalog, two_archetypes, two_matchup_matrix):
    # deck-a faces 60% deck-a (WR=0.50) + 40% deck-b (WR=0.60) → E[WR]=0.54
    deck_a = Deck.from_dict(two_archetypes[0], sample_card_catalog)
    wr = expected_win_rate(deck_a, two_archetypes, two_matchup_matrix, sample_card_catalog)
    assert abs(wr - 0.54) < 0.01


def test_ewr_bounded(sample_card_catalog, two_archetypes, two_matchup_matrix):
    for arch in two_archetypes:
        deck = Deck.from_dict(arch, sample_card_catalog)
        wr = expected_win_rate(deck, two_archetypes, two_matchup_matrix, sample_card_catalog)
        assert 0.0 <= wr <= 1.0


def test_ewr_field_invariance(sample_card_catalog, two_archetypes, two_matchup_matrix):
    doubled = [{**a, "meta_share": a["meta_share"] * 2} for a in two_archetypes]
    deck_a = Deck.from_dict(two_archetypes[0], sample_card_catalog)
    wr1 = expected_win_rate(deck_a, two_archetypes, two_matchup_matrix, sample_card_catalog)
    wr2 = expected_win_rate(deck_a, doubled, two_matchup_matrix, sample_card_catalog)
    assert abs(wr1 - wr2) < 0.001
