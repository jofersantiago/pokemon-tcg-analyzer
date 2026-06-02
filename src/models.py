from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


_TYPE_MAP = {
    "pokemon": "Pokemon",
    "item": "Trainer",
    "supporter": "Trainer",
    "tool": "Trainer",
    "fossil": "Trainer",
    "energy": "Energy",
}


@dataclass
class Card:
    id: str
    name: str
    card_type: str  # "Pokemon", "Trainer", "Energy"
    hp: Optional[int] = None
    attacks: list[dict] = field(default_factory=list)
    abilities: list[dict] = field(default_factory=list)
    retreat: Optional[int] = None
    weakness: Optional[str] = None
    energy_type: Optional[str] = None
    set_id: str = ""
    rarity: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> Card:
        raw_type = data.get("type", "")
        card_type = _TYPE_MAP.get(raw_type.lower(), raw_type)
        return cls(
            id=data["id"],
            name=data["name"],
            card_type=card_type,
            hp=data.get("health", data.get("hp")),
            attacks=data.get("attacks", []),
            abilities=data.get("abilities", []),
            retreat=data.get("retreatCost", data.get("retreat")),
            weakness=data.get("weakness"),
            energy_type=data.get("element", data.get("energyType")),
            set_id=data.get("set", ""),
            rarity=data.get("rarity", ""),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id, "name": self.name, "type": self.card_type,
            "hp": self.hp, "attacks": self.attacks, "abilities": self.abilities,
            "retreat": self.retreat, "weakness": self.weakness,
            "energyType": self.energy_type, "set": self.set_id, "rarity": self.rarity,
        }

    @property
    def max_damage(self) -> int:
        return max((a.get("damage", 0) for a in self.attacks), default=0)

    @property
    def is_pokemon(self) -> bool:
        return self.card_type == "Pokemon"

    @property
    def is_trainer(self) -> bool:
        return self.card_type == "Trainer"

    @property
    def is_energy(self) -> bool:
        return self.card_type == "Energy"


@dataclass
class Deck:
    cards: list[Card]
    archetype_label: str = ""

    def __post_init__(self) -> None:
        if len(self.cards) > 20:
            raise ValueError(f"Deck has {len(self.cards)} cards; max is 20")

    def card_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for card in self.cards:
            counts[card.id] = counts.get(card.id, 0) + 1
        return counts

    def unique_cards(self) -> list[Card]:
        seen: set[str] = set()
        result = []
        for card in self.cards:
            if card.id not in seen:
                seen.add(card.id)
                result.append(card)
        return result

    @classmethod
    def from_dict(cls, data: dict, card_catalog: dict[str, Card]) -> Deck:
        cards = []
        for entry in data["cards"]:
            card = card_catalog.get(entry["id"])
            if card is None:
                continue  # skip cards from sets not yet in the catalog
            cards.extend([card] * entry["count"])
        return cls(cards=cards, archetype_label=data.get("archetype", data.get("id", "")))

    def to_dict(self) -> dict:
        return {
            "archetype": self.archetype_label,
            "cards": [{"id": cid, "count": n} for cid, n in self.card_counts().items()],
        }


@dataclass
class Collection:
    cards: dict[str, int]  # {card_id: count_owned}

    def completion_percent(self, deck: Deck) -> float:
        needed = deck.card_counts()
        total_needed = sum(needed.values())
        if total_needed == 0:
            return 100.0
        have = sum(min(self.cards.get(cid, 0), count) for cid, count in needed.items())
        return round(100.0 * have / total_needed, 1)

    def missing_cards(self, deck: Deck) -> list[tuple[Card, int]]:
        needed = deck.card_counts()
        card_map = {c.id: c for c in deck.unique_cards()}
        result = []
        for cid, count in needed.items():
            shortfall = count - self.cards.get(cid, 0)
            if shortfall > 0:
                result.append((card_map[cid], shortfall))
        return sorted(result, key=lambda x: x[0].name)

    @classmethod
    def from_dict(cls, data: dict) -> Collection:
        return cls(cards=dict(data))

    def to_dict(self) -> dict:
        return dict(self.cards)
