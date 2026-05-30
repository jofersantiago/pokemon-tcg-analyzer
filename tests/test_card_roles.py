import pytest
from src.models import Deck
from src.card_roles import (
    compute_card_features, classify_roles, ROLES,
    fit_win_rate_regression, attribute_win_rate, deck_role_fractions,
)


@pytest.fixture
def tournament_decks():
    return [
        {"id": "deck-a", "win_rate": 0.60,
         "cards": [
             {"id": "A1-001", "count": 2},
             {"id": "A1-225", "count": 2},
             {"id": "A1-250", "count": 4},
         ]},
        {"id": "deck-b", "win_rate": 0.50,
         "cards": [
             {"id": "A1-002", "count": 2},
             {"id": "A1-225", "count": 2},
             {"id": "A1-250", "count": 4},
         ]},
        {"id": "deck-c", "win_rate": 0.45,
         "cards": [
             {"id": "A1-001", "count": 2},
             {"id": "A1-225", "count": 2},
             {"id": "A1-250", "count": 4},
         ]},
    ]


def test_deck_share_calculation(sample_cards, tournament_decks):
    features = compute_card_features(sample_cards, tournament_decks)
    assert features["A1-225"]["deck_share"] == pytest.approx(1.0)
    assert features["A1-002"]["deck_share"] == pytest.approx(1 / 3, rel=0.01)


def test_classify_produces_valid_roles(sample_cards, tournament_decks):
    roles = classify_roles(compute_card_features(sample_cards, tournament_decks))
    assert all(r in ROLES for r in roles.values())


def test_high_share_trainer_is_engine(sample_cards, tournament_decks):
    roles = classify_roles(compute_card_features(sample_cards, tournament_decks))
    assert roles["A1-225"] == "engine"


def test_roles_cover_all_cards(sample_cards, tournament_decks):
    roles = classify_roles(compute_card_features(sample_cards, tournament_decks))
    for card in sample_cards:
        assert card.id in roles


def test_regression_r_squared_valid(sample_cards, sample_card_catalog, tournament_decks):
    features = compute_card_features(sample_cards, tournament_decks)
    role_map = classify_roles(features)
    result = fit_win_rate_regression(tournament_decks, role_map, sample_card_catalog)
    assert 0.0 <= result.r_squared <= 1.0


def test_attribution_plus_intercept_equals_prediction(
    sample_cards, sample_card_catalog, tournament_decks
):
    features = compute_card_features(sample_cards, tournament_decks)
    role_map = classify_roles(features)
    regression = fit_win_rate_regression(tournament_decks, role_map, sample_card_catalog)
    deck = Deck.from_dict(tournament_decks[0], sample_card_catalog)
    attr = attribute_win_rate(deck, role_map, regression)
    predicted = regression.predict(deck_role_fractions(deck, role_map))
    assert abs(sum(attr.values()) + regression.intercept - predicted) < 1e-6
