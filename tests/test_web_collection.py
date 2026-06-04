import pytest
from src.models import Card
from src.web_collection import _prepare_page_data


def test_prepare_page_data_includes_missing_catalog_cards(sample_card_catalog):
    archetypes = [
        {
            "id": "test-arch",
            "name": "Test Deck",
            "meta_share": 0.1,
            "win_rate": 0.5,
            "cards": [
                {"id": "A1-001", "count": 2},
                {"id": "B3a-999", "count": 1},
            ],
        }
    ]

    page_data = _prepare_page_data(
        archetypes=archetypes,
        catalog=sample_card_catalog,
        my_cards={},
        ewrs=[0.5],
        attributions=[{}],
        meta_decks=[],
        custom_decks=None,
        matchup_matrix=None,
        role_map=None,
        regression=None,
    )

    assert len(page_data["decks"]) == 1
    cards = page_data["decks"][0]["cards"]
    assert cards[0]["id"] == "A1-001"
    assert cards[1]["id"] == "B3a-999"
    assert cards[1]["name"] == "B3a-999"
    assert cards[1]["type"] == "Pokemon"
    assert cards[1]["img"].endswith("B3a/B3a_999_EN.webp")


def test_prepare_page_data_derives_missing_names_from_archetype_title(sample_card_catalog):
    archetypes = [
        {
            "id": "test-arch",
            "name": "Mega Altaria ex Espeon",
            "meta_share": 0.1,
            "win_rate": 0.5,
            "cards": [
                {"id": "B1-102", "count": 2},
                {"id": "B1-184", "count": 2},
                {"id": "B3a-020", "count": 2},
            ],
        }
    ]

    catalog = dict(sample_card_catalog)
    catalog["B1-102"] = Card(id="B1-102", name="Mega Altaria ex", card_type="Pokemon")
    catalog["B1-184"] = Card(id="B1-184", name="Eevee", card_type="Pokemon")

    page_data = _prepare_page_data(
        archetypes=archetypes,
        catalog=catalog,
        my_cards={},
        ewrs=[0.5],
        attributions=[{}],
        meta_decks=[],
        custom_decks=None,
        matchup_matrix=None,
        role_map=None,
        regression=None,
    )

    cards = page_data["decks"][0]["cards"]
    assert cards[2]["id"] == "B3a-020"
    assert cards[2]["name"] == "Espeon"


def test_meta_hero_images_prefers_missing_card_urls(sample_card_catalog):
    archetypes = [
        {
            "id": "test-arch",
            "name": "Miraidon ex Magnezone",
            "meta_share": 0.1,
            "win_rate": 0.5,
            "cards": [
                {"id": "B1a-026", "count": 1},
                {"id": "A3-066", "count": 1},
                {"id": "B3a-019", "count": 1},
            ],
        }
    ]

    catalog = dict(sample_card_catalog)
    catalog["B1a-026"] = Card(id="B1a-026", name="Magnezone", card_type="Pokemon", hp=170)
    catalog["A3-066"] = Card(id="A3-066", name="Oricorio", card_type="Pokemon", hp=80)

    page_data = _prepare_page_data(
        archetypes=archetypes,
        catalog=catalog,
        my_cards={},
        ewrs=[0.5],
        attributions=[{}],
        meta_decks=[],
        custom_decks=None,
        matchup_matrix=None,
        role_map=None,
        regression=None,
    )

    hero_imgs = page_data["meta"][0]["hero_imgs"]
    assert hero_imgs[0].endswith("B3a/B3a_019_EN.webp")
    assert hero_imgs[1].endswith("B1a/B1a_026_EN.webp")
