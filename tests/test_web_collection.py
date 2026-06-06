import pytest
from src.models import Card
from src.web_collection import _prepare_page_data, _card_image_url


# ── _card_image_url ───────────────────────────────────────────────────────────

def test_card_image_url_standard():
    url = _card_image_url("A1-036")
    assert "A1/A1_036_EN.webp" in url


def test_card_image_url_alphanumeric_set():
    url = _card_image_url("A2b-037")
    assert "A2b/A2b_037_EN.webp" in url


def test_card_image_url_promo_a_remapped():
    url = _card_image_url("PROMO-A-005")
    assert "P-A" in url
    assert "005" in url


def test_card_image_url_invalid_returns_empty():
    assert _card_image_url("BADID") == ""


# ── _prepare_page_data — decks ────────────────────────────────────────────────

def _base_call(archetypes, catalog, **kwargs):
    """Helper: call _prepare_page_data with sensible defaults."""
    defaults = dict(
        my_cards={},
        ewrs=[0.5] * len(archetypes),
        attributions=[{}] * len(archetypes),
        meta_decks=[],
        custom_decks=None,
        matchup_matrix=None,
        role_map=None,
        regression=None,
    )
    defaults.update(kwargs)
    return _prepare_page_data(archetypes=archetypes, catalog=catalog, **defaults)


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

    page_data = _base_call(archetypes, sample_card_catalog)

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

    page_data = _base_call(archetypes, catalog)

    cards = page_data["decks"][0]["cards"]
    assert cards[2]["id"] == "B3a-020"
    assert cards[2]["name"] == "Espeon"


def test_prepare_page_data_known_card_has_correct_fields(sample_card_catalog):
    archetypes = [{"id": "d1", "name": "Bulbasaur Deck", "meta_share": 0.2,
                   "win_rate": 0.55, "cards": [{"id": "A1-001", "count": 2}]}]
    page_data = _base_call(archetypes, sample_card_catalog)
    card = page_data["decks"][0]["cards"][0]
    assert card["name"] == "Bulbasaur"
    assert card["type"] == "Pokemon"
    assert card["need"] == 2
    assert card["have"] == 0
    assert "A1/A1_001_EN.webp" in card["img"]


def test_prepare_page_data_have_reflects_my_cards(sample_card_catalog):
    archetypes = [{"id": "d1", "name": "Deck", "meta_share": 0.1,
                   "win_rate": 0.5, "cards": [{"id": "A1-001", "count": 2}]}]
    page_data = _base_call(archetypes, sample_card_catalog, my_cards={"A1-001": 1})
    assert page_data["decks"][0]["cards"][0]["have"] == 1


def test_prepare_page_data_role_map_applied(sample_card_catalog):
    archetypes = [{"id": "d1", "name": "Deck", "meta_share": 0.1,
                   "win_rate": 0.5, "cards": [{"id": "A1-001", "count": 2}]}]
    page_data = _base_call(archetypes, sample_card_catalog,
                           role_map={"A1-001": "win_condition"})
    assert page_data["decks"][0]["cards"][0]["role"] == "win_condition"


def test_prepare_page_data_missing_role_defaults_to_garnet(sample_card_catalog):
    archetypes = [{"id": "d1", "name": "Deck", "meta_share": 0.1,
                   "win_rate": 0.5, "cards": [{"id": "A1-001", "count": 2}]}]
    page_data = _base_call(archetypes, sample_card_catalog, role_map={})
    assert page_data["decks"][0]["cards"][0]["role"] == "garnet"


def test_prepare_page_data_custom_deck_appended(sample_card_catalog):
    archetypes = [{"id": "d1", "name": "Meta Deck", "meta_share": 0.1,
                   "win_rate": 0.5, "cards": [{"id": "A1-001", "count": 2}]}]
    custom = [{"id": "my-deck", "name": "My Custom Deck",
               "cards": [{"id": "A1-002", "count": 1}]}]
    page_data = _base_call(archetypes, sample_card_catalog, custom_decks=custom)
    assert len(page_data["decks"]) == 2
    custom_entry = page_data["decks"][1]
    assert custom_entry["id"] == "my-deck"
    assert custom_entry["custom"] is True
    assert custom_entry["cards"][0]["name"] == "Ivysaur"


def test_prepare_page_data_no_custom_decks(sample_card_catalog):
    archetypes = [{"id": "d1", "name": "Deck", "meta_share": 0.1,
                   "win_rate": 0.5, "cards": [{"id": "A1-001", "count": 2}]}]
    page_data = _base_call(archetypes, sample_card_catalog)
    assert len(page_data["decks"]) == 1


# ── _prepare_page_data — meta ─────────────────────────────────────────────────

def test_prepare_page_data_meta_share_is_percentage(sample_card_catalog):
    archetypes = [{"id": "d1", "name": "Deck", "meta_share": 0.18,
                   "win_rate": 0.53, "cards": [{"id": "A1-001", "count": 2}]}]
    page_data = _base_call(archetypes, sample_card_catalog, ewrs=[0.51])
    meta = page_data["meta"][0]
    assert meta["meta_share"] == 18.0
    assert meta["win_rate"] == 53.0
    assert meta["ewr"] == 51.0


def test_prepare_page_data_meta_sorted_by_share_descending(sample_card_catalog):
    archetypes = [
        {"id": "d1", "name": "Low Deck", "meta_share": 0.05, "win_rate": 0.5,
         "cards": [{"id": "A1-001", "count": 1}]},
        {"id": "d2", "name": "High Deck", "meta_share": 0.20, "win_rate": 0.5,
         "cards": [{"id": "A1-002", "count": 1}]},
    ]
    page_data = _base_call(archetypes, sample_card_catalog, ewrs=[0.5, 0.5])
    assert page_data["meta"][0]["id"] == "d2"
    assert page_data["meta"][1]["id"] == "d1"


def test_prepare_page_data_meta_has_hero_imgs(sample_card_catalog):
    archetypes = [{"id": "d1", "name": "Bulbasaur Deck", "meta_share": 0.1,
                   "win_rate": 0.5, "cards": [{"id": "A1-001", "count": 2}]}]
    page_data = _base_call(archetypes, sample_card_catalog)
    meta = page_data["meta"][0]
    assert "hero_imgs" in meta
    assert isinstance(meta["hero_imgs"], list)


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

    page_data = _base_call(archetypes, catalog)

    hero_imgs = page_data["meta"][0]["hero_imgs"]
    assert hero_imgs[0].endswith("B3a/B3a_019_EN.webp")
    assert hero_imgs[1].endswith("B1a/B1a_026_EN.webp")


def test_meta_hero_images_named_pokemon_preferred(sample_card_catalog):
    catalog = dict(sample_card_catalog)
    catalog["X1-001"] = Card(id="X1-001", name="Charizard ex", card_type="Pokemon", hp=200)
    catalog["X1-002"] = Card(id="X1-002", name="Pidgey", card_type="Pokemon", hp=50)
    archetypes = [{"id": "d1", "name": "Charizard ex Deck", "meta_share": 0.1,
                   "win_rate": 0.5,
                   "cards": [{"id": "X1-002", "count": 4}, {"id": "X1-001", "count": 2}]}]
    page_data = _base_call(archetypes, catalog)
    # Charizard ex matches the deck name — should appear in hero_imgs
    hero_imgs = page_data["meta"][0]["hero_imgs"]
    assert any("X1_001" in url for url in hero_imgs)


# ── _prepare_page_data — catalog ──────────────────────────────────────────────

def test_prepare_page_data_catalog_contains_all_cards(sample_card_catalog):
    page_data = _base_call([], sample_card_catalog)
    catalog = page_data["catalog"]
    assert len(catalog) == len(sample_card_catalog)


def test_prepare_page_data_catalog_sorted_by_id(sample_card_catalog):
    page_data = _base_call([], sample_card_catalog)
    ids = [c["id"] for c in page_data["catalog"]]
    assert ids == sorted(ids)


def test_prepare_page_data_catalog_card_fields(sample_card_catalog):
    page_data = _base_call([], sample_card_catalog)
    card = next(c for c in page_data["catalog"] if c["id"] == "A1-001")
    assert card["name"] == "Bulbasaur"
    assert card["type"] == "Pokemon"
    assert "img" in card


# ── _prepare_page_data — matchup ─────────────────────────────────────────────

def test_prepare_page_data_matchup_passed_through(sample_card_catalog):
    matrix = {"d1": {"d2": 0.6}, "d2": {"d1": 0.4}}
    page_data = _base_call([], sample_card_catalog, matchup_matrix=matrix)
    assert page_data["matchup"] == matrix


def test_prepare_page_data_matchup_defaults_to_empty(sample_card_catalog):
    page_data = _base_call([], sample_card_catalog)
    assert page_data["matchup"] == {}
