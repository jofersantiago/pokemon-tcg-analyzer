import pytest
from src.models import Card


@pytest.fixture
def sample_cards() -> list[Card]:
    return [
        Card(id="A1-001", name="Bulbasaur", card_type="Pokemon", hp=70,
             attacks=[{"name": "Vine Whip", "damage": 40}]),
        Card(id="A1-002", name="Ivysaur", card_type="Pokemon", hp=90,
             attacks=[{"name": "Razor Leaf", "damage": 70}]),
        Card(id="A1-225", name="Misty", card_type="Trainer"),
        Card(id="A1-250", name="Water Energy", card_type="Energy", energy_type="Water"),
    ]


@pytest.fixture
def sample_card_catalog(sample_cards) -> dict[str, Card]:
    return {c.id: c for c in sample_cards}
