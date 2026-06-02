from __future__ import annotations

import csv
import json
import random
from pathlib import Path

from src.models import Card

COLLECTION_PATH = Path(__file__).parent.parent.parent / "my_collection.json"
CSV_PATH = Path(__file__).parent.parent.parent / "data" / "my_collection.csv"

_CSV_TEMPLATE = (
    "# Pokémon TCG Pocket Collection\n"
    "# card_id = set code + number, e.g. A1-001, A2b-036, P-A-001\n"
    "# count   = number of copies owned\n"
    "card_id,count\n"
)


def load_collection() -> dict[str, int]:
    if not COLLECTION_PATH.exists():
        return {}
    with open(COLLECTION_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_collection(cards: dict[str, int]) -> None:
    COLLECTION_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(COLLECTION_PATH, "w", encoding="utf-8") as f:
        json.dump(cards, f, indent=2)


def import_csv(catalog: dict[str, Card]) -> tuple[int, list[str]]:
    """Import CSV into my_collection.json.

    Returns (rows_imported, list_of_warning_strings).
    If the CSV file does not exist, creates a blank template and returns (0, ['template_created']).
    Duplicate card_id rows are summed. Unknown IDs produce a warning and are skipped.
    """
    if not CSV_PATH.exists():
        CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
        CSV_PATH.write_text(_CSV_TEMPLATE)
        return 0, ["template_created"]

    collection = load_collection()
    warnings: list[str] = []
    imported = 0

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        non_comment = (row for row in f if not row.lstrip().startswith("#"))
        reader = csv.DictReader(non_comment)
        for row in reader:
            card_id = (row.get("card_id") or "").strip()
            count_str = (row.get("count") or "").strip()
            if not card_id or not count_str:
                continue
            if card_id not in catalog:
                warnings.append(f"WARNING: {card_id} not found in catalog — skipped")
                continue
            try:
                count = int(count_str)
            except ValueError:
                warnings.append(f"WARNING: invalid count '{count_str}' for {card_id} — skipped")
                continue
            if count <= 0:
                warnings.append(f"WARNING: count for {card_id} is {count} — skipped")
                continue
            collection[card_id] = collection.get(card_id, 0) + count
            imported += 1

    save_collection(collection)
    return imported, warnings


def generate_random(catalog: dict[str, Card], target: int) -> dict[str, int]:
    """Generate a random collection of exactly `target` cards weighted by rarity.

    Saves result to my_collection.json (overwrites). Returns the new collection dict.
    """
    cards = list(catalog.values())

    def _weight(card: Card) -> int:
        r = card.rarity.lower()
        if "immersive" in r:
            return 2
        if "full art" in r or "rainbow" in r:
            return 5
        if "ex" in r:
            return 15
        for n in range(5, 0, -1):
            if str(n) in r:
                return max(5, 105 - n * 15)
        return 50

    weights = [_weight(c) for c in cards]
    collection: dict[str, int] = {}
    pulled = random.choices(cards, weights=weights, k=target)
    for card in pulled:
        collection[card.id] = collection.get(card.id, 0) + 1

    save_collection(collection)
    return collection


def fuzzy_search(query: str, catalog: dict[str, Card]) -> list[Card]:
    """Return all cards whose name contains `query` (case-insensitive)."""
    q = query.lower()
    return [c for c in catalog.values() if q in c.name.lower()]


def update_card_count(card_id: str, count: int) -> None:
    """Set the owned count for a single card. Removes the entry if count <= 0."""
    collection = load_collection()
    if count <= 0:
        collection.pop(card_id, None)
    else:
        collection[card_id] = count
    save_collection(collection)
