import pytest
from src.models import Card, Deck, Collection


def test_card_from_dict_basic():
    card = Card.from_dict({"id": "A1-001", "name": "Bulbasaur", "type": "Pokemon", "hp": 70})
    assert card.id == "A1-001" and card.hp == 70 and card.card_type == "Pokemon"


def test_card_from_dict_missing_type_defaults_to_pokemon():
    card = Card.from_dict({"id": "A1-002", "name": "Ivysaur"})
    assert card.card_type == "Pokemon"


def test_card_max_damage():
    card = Card.from_dict({
        "id": "A1-001", "name": "Bulbasaur", "type": "Pokemon", "hp": 70,
        "attacks": [{"name": "Vine Whip", "damage": 40}],
    })
    assert card.max_damage == 40


def test_card_max_damage_no_attacks():
    card = Card(id="A1-225", name="Misty", card_type="Trainer")
    assert card.max_damage == 0


def test_card_type_properties():
    assert Card(id="x", name="x", card_type="Pokemon").is_pokemon
    assert Card(id="x", name="x", card_type="Trainer").is_trainer
    assert Card(id="x", name="x", card_type="Energy").is_energy


def test_card_round_trip():
    data = {"id": "A1-001", "name": "Bulbasaur", "type": "Pokemon", "hp": 70}
    restored = Card.from_dict(data).to_dict()
    assert restored["id"] == "A1-001" and restored["hp"] == 70


def test_deck_card_counts():
    b = Card(id="A1-001", name="Bulbasaur", card_type="Pokemon")
    m = Card(id="A1-225", name="Misty", card_type="Trainer")
    counts = Deck(cards=[b, b, m]).card_counts()
    assert counts["A1-001"] == 2 and counts["A1-225"] == 1


def test_deck_rejects_oversized():
    card = Card(id="A1-001", name="B", card_type="Pokemon")
    with pytest.raises(ValueError, match="max is 20"):
        Deck(cards=[card] * 21)


def test_deck_from_dict(sample_card_catalog):
    data = {
        "archetype": "test",
        "cards": [{"id": "A1-001", "count": 2}, {"id": "A1-225", "count": 1}],
    }
    deck = Deck.from_dict(data, sample_card_catalog)
    assert len(deck.cards) == 3 and deck.archetype_label == "test"


def test_deck_round_trip(sample_card_catalog):
    data = {"archetype": "rt", "cards": [{"id": "A1-001", "count": 2}]}
    restored = Deck.from_dict(data, sample_card_catalog).to_dict()
    assert restored["archetype"] == "rt"
    assert {e["id"]: e["count"] for e in restored["cards"]}["A1-001"] == 2


def test_completion_full():
    card = Card(id="A1-001", name="B", card_type="Pokemon")
    assert Collection(cards={"A1-001": 2}).completion_percent(Deck(cards=[card, card])) == 100.0


def test_completion_partial():
    card = Card(id="A1-001", name="B", card_type="Pokemon")
    assert Collection(cards={"A1-001": 1}).completion_percent(Deck(cards=[card, card])) == 50.0


def test_completion_empty():
    card = Card(id="A1-001", name="B", card_type="Pokemon")
    assert Collection(cards={}).completion_percent(Deck(cards=[card, card])) == 0.0


def test_missing_cards():
    b = Card(id="A1-001", name="Bulbasaur", card_type="Pokemon")
    m = Card(id="A1-225", name="Misty", card_type="Trainer")
    deck = Deck(cards=[b, b, m])
    missing = {c.id: n for c, n in Collection(cards={"A1-001": 1}).missing_cards(deck)}
    assert missing["A1-001"] == 1 and missing["A1-225"] == 1


def test_collection_round_trip():
    c = Collection(cards={"A1-001": 2, "A1-225": 1})
    assert Collection.from_dict(c.to_dict()).cards == c.cards
