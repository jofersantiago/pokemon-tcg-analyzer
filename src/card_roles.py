from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from sklearn.linear_model import LinearRegression
from src.models import Card, Deck

ROLES = ["win_condition", "engine", "staple", "tech", "garnet"]


def compute_card_features(cards: list[Card], tournament_decks: list[dict]) -> dict[str, dict]:
    total_decks = len(tournament_decks)
    usage: dict[str, list[int]] = {}
    for deck_data in tournament_decks:
        for entry in deck_data["cards"]:
            usage.setdefault(entry["id"], []).append(entry["count"])
    features: dict[str, dict] = {}
    for card in cards:
        counts = usage.get(card.id, [])
        features[card.id] = {
            "deck_share": len(counts) / total_decks if total_decks > 0 else 0.0,
            "avg_copies": sum(counts) / len(counts) if counts else 0.0,
            "max_damage": card.max_damage,
            "is_pokemon": card.is_pokemon,
            "is_trainer": card.is_trainer,
            "is_energy": card.is_energy,
            "hp": card.hp or 0,
        }
    return features


def classify_roles(card_features: dict[str, dict]) -> dict[str, str]:
    roles: dict[str, str] = {}
    for cid, f in card_features.items():
        share = f["deck_share"]
        if f["is_pokemon"] and f["max_damage"] >= 80 and share <= 0.45:
            roles[cid] = "win_condition"
        elif share >= 0.50:
            roles[cid] = "engine"
        elif share >= 0.20:
            roles[cid] = "staple"
        elif share >= 0.05:
            roles[cid] = "tech"
        else:
            roles[cid] = "garnet"
    return roles


def deck_role_fractions(deck: Deck, role_map: dict[str, str]) -> dict[str, float]:
    fracs = {role: 0.0 for role in ROLES}
    for card in deck.cards:
        fracs[role_map.get(card.id, "garnet")] += 1
    total = len(deck.cards)
    if total > 0:
        fracs = {r: v / total for r, v in fracs.items()}
    return fracs


@dataclass
class RegressionResult:
    coef: dict[str, float]
    intercept: float
    r_squared: float

    def predict(self, role_fracs: dict[str, float]) -> float:
        return self.intercept + sum(
            self.coef.get(r, 0.0) * role_fracs.get(r, 0.0) for r in ROLES
        )


def fit_win_rate_regression(
    archetypes: list[dict],
    role_map: dict[str, str],
    card_catalog: dict[str, Card],
) -> RegressionResult:
    X, y = [], []
    for arch in archetypes:
        deck = Deck.from_dict(arch, card_catalog)
        fracs = deck_role_fractions(deck, role_map)
        X.append([fracs[r] for r in ROLES])
        y.append(arch["win_rate"])
    model = LinearRegression().fit(np.array(X), np.array(y))
    return RegressionResult(
        coef={r: float(model.coef_[i]) for i, r in enumerate(ROLES)},
        intercept=float(model.intercept_),
        r_squared=float(model.score(np.array(X), np.array(y))),
    )


def attribute_win_rate(
    deck: Deck,
    role_map: dict[str, str],
    regression: RegressionResult,
) -> dict[str, float]:
    fracs = deck_role_fractions(deck, role_map)
    return {r: regression.coef.get(r, 0.0) * fracs.get(r, 0.0) for r in ROLES}
