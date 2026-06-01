import pytest
from pathlib import Path


def test_import_placeholder():
    from src.cli.state import AppState
    assert AppState is not None


def test_display_imports():
    from src.cli.display import header, table, pick, prompt, separator
    assert callable(header)
    assert callable(table)
    assert callable(pick)


import json
import tempfile
from pathlib import Path
from src.models import Card


def _make_catalog() -> dict[str, Card]:
    cards = [
        Card(id="A1-001", name="Pikachu", card_type="Pokemon",
             hp=60, rarity="1", set_id="A1"),
        Card(id="A1-002", name="Espeon", card_type="Pokemon",
             hp=90, rarity="3", set_id="A1"),
        Card(id="A1-003", name="Misty", card_type="Trainer",
             hp=None, rarity="2", set_id="A1"),
    ]
    return {c.id: c for c in cards}


def test_load_empty_collection(tmp_path, monkeypatch):
    from src.cli import collection_io
    monkeypatch.setattr(collection_io, "COLLECTION_PATH", tmp_path / "col.json")
    result = collection_io.load_collection()
    assert result == {}


def test_save_and_load_collection(tmp_path, monkeypatch):
    from src.cli import collection_io
    path = tmp_path / "col.json"
    monkeypatch.setattr(collection_io, "COLLECTION_PATH", path)
    collection_io.save_collection({"A1-001": 2, "A1-002": 1})
    loaded = collection_io.load_collection()
    assert loaded == {"A1-001": 2, "A1-002": 1}


def test_import_csv_creates_template_when_missing(tmp_path, monkeypatch):
    from src.cli import collection_io
    monkeypatch.setattr(collection_io, "COLLECTION_PATH", tmp_path / "col.json")
    monkeypatch.setattr(collection_io, "CSV_PATH", tmp_path / "my_collection.csv")
    count, warnings = collection_io.import_csv(_make_catalog())
    assert count == 0
    assert warnings == ["template_created"]
    assert (tmp_path / "my_collection.csv").exists()


def test_import_csv_valid_rows(tmp_path, monkeypatch):
    from src.cli import collection_io
    monkeypatch.setattr(collection_io, "COLLECTION_PATH", tmp_path / "col.json")
    csv_path = tmp_path / "my_collection.csv"
    monkeypatch.setattr(collection_io, "CSV_PATH", csv_path)
    csv_path.write_text("card_id,count\nA1-001,2\nA1-002,1\n")
    count, warnings = collection_io.import_csv(_make_catalog())
    assert count == 2
    assert warnings == []
    assert collection_io.load_collection() == {"A1-001": 2, "A1-002": 1}


def test_import_csv_unknown_id_warns(tmp_path, monkeypatch):
    from src.cli import collection_io
    monkeypatch.setattr(collection_io, "COLLECTION_PATH", tmp_path / "col.json")
    csv_path = tmp_path / "my_collection.csv"
    monkeypatch.setattr(collection_io, "CSV_PATH", csv_path)
    csv_path.write_text("card_id,count\nA1-001,1\nZZZ-999,1\n")
    count, warnings = collection_io.import_csv(_make_catalog())
    assert count == 1
    assert any("ZZZ-999" in w for w in warnings)


def test_import_csv_merges_duplicates(tmp_path, monkeypatch):
    from src.cli import collection_io
    monkeypatch.setattr(collection_io, "COLLECTION_PATH", tmp_path / "col.json")
    csv_path = tmp_path / "my_collection.csv"
    monkeypatch.setattr(collection_io, "CSV_PATH", csv_path)
    csv_path.write_text("card_id,count\nA1-001,2\nA1-001,1\n")
    count, _ = collection_io.import_csv(_make_catalog())
    assert count == 2
    assert collection_io.load_collection()["A1-001"] == 3


def test_generate_random_target_count(tmp_path, monkeypatch):
    from src.cli import collection_io
    monkeypatch.setattr(collection_io, "COLLECTION_PATH", tmp_path / "col.json")
    catalog = _make_catalog()
    result = collection_io.generate_random(catalog, target=10)
    assert sum(result.values()) == 10
    assert all(k in catalog for k in result)


def test_fuzzy_search_returns_matching_cards():
    from src.cli.collection_io import fuzzy_search
    catalog = _make_catalog()
    results = fuzzy_search("espe", catalog)
    assert len(results) == 1
    assert results[0].name == "Espeon"


def test_fuzzy_search_case_insensitive():
    from src.cli.collection_io import fuzzy_search
    catalog = _make_catalog()
    assert fuzzy_search("PIKACHU", catalog)[0].name == "Pikachu"


def test_update_card_count(tmp_path, monkeypatch):
    from src.cli import collection_io
    monkeypatch.setattr(collection_io, "COLLECTION_PATH", tmp_path / "col.json")
    collection_io.update_card_count("A1-001", 3)
    assert collection_io.load_collection()["A1-001"] == 3
    collection_io.update_card_count("A1-001", 0)
    assert "A1-001" not in collection_io.load_collection()
