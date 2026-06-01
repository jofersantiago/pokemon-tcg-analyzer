from __future__ import annotations
from dataclasses import dataclass
from src.models import Card, Deck
from src.card_roles import RegressionResult


@dataclass
class AppState:
    catalog: dict[str, Card]
    archetypes: list[dict]
    matchup_matrix: dict[str, dict[str, float]]
    meta_decks: list[Deck]
    ewrs: list[float]
    attributions: list[dict]
    role_map: dict[str, str]
    regression: RegressionResult
