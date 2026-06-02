from __future__ import annotations

import numpy as np

from src.models import Card, Deck


def deck_fingerprint(deck: Deck) -> dict[str, float]:
    """Return a normalized card frequency vector: {card_id: count / total_cards}.

    Values sum to 1.0.
    """
    counts = deck.card_counts()
    total = sum(counts.values())
    if total == 0:
        return {}
    return {card_id: count / total for card_id, count in counts.items()}


def fingerprint_distance(fp1: dict[str, float], fp2: dict[str, float]) -> float:
    """Cosine distance between two fingerprint vectors: 1 - cosine_similarity.

    Returns 0.0 for identical fingerprints and 1.0 for completely disjoint ones.
    Handles zero-norm edge case by returning 1.0.
    """
    all_keys = list(set(fp1) | set(fp2))
    v1 = np.array([fp1.get(k, 0.0) for k in all_keys])
    v2 = np.array([fp2.get(k, 0.0) for k in all_keys])

    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)

    if norm1 == 0.0 or norm2 == 0.0:
        return 1.0

    cosine_similarity = np.dot(v1, v2) / (norm1 * norm2)
    return float(1.0 - cosine_similarity)


def match_archetype(
    deck: Deck,
    archetypes: list[dict],
    card_catalog: dict[str, Card],
) -> tuple[str, float]:
    """Find the closest archetype to the given deck.

    For each archetype dict (must have "id" and "cards" keys), builds a Deck via
    Deck.from_dict, computes its fingerprint, then computes the cosine distance to
    the input deck's fingerprint.

    Returns (archetype_id_with_minimum_distance, that_distance).
    """
    deck_fp = deck_fingerprint(deck)

    best_id = ""
    best_dist = float("inf")

    for arch in archetypes:
        arch_deck = Deck.from_dict(arch, card_catalog)
        arch_fp = deck_fingerprint(arch_deck)
        dist = fingerprint_distance(deck_fp, arch_fp)
        if dist < best_dist:
            best_dist = dist
            best_id = arch["id"]

    return best_id, best_dist


def expected_win_rate(
    deck: Deck,
    archetypes: list[dict],
    matchup_matrix: dict[str, dict[str, float]],
    card_catalog: dict[str, Card],
    off_meta_threshold: float = 0.35,
) -> float:
    """Estimate the expected win rate of a deck against the current meta field.

    If the deck closely matches a known archetype (distance <= off_meta_threshold)
    and that archetype has matchup data, its matchup row is used directly.
    Otherwise the deck is treated as off-meta and matchup win rates are interpolated
    by inverse-distance weighting across all archetypes.

    Returns a meta-share-weighted average win rate rounded to 4 decimal places.
    """
    matched_arch, distance = match_archetype(deck, archetypes, card_catalog)

    meta_shares = {a["id"]: a["meta_share"] for a in archetypes}
    total_share = sum(meta_shares.values())

    if distance <= off_meta_threshold and matched_arch in matchup_matrix:
        matchups = matchup_matrix[matched_arch]
    else:
        fps = {a["id"]: deck_fingerprint(Deck.from_dict(a, card_catalog)) for a in archetypes}
        our_fp = deck_fingerprint(deck)
        raw_w = {aid: 1.0 / (fingerprint_distance(our_fp, afp) + 1e-9) for aid, afp in fps.items()}
        total_w = sum(raw_w.values())
        weights = {k: v / total_w for k, v in raw_w.items()}
        matchups = {
            opp["id"]: sum(
                w * matchup_matrix.get(our_arch, {}).get(opp["id"], 0.5)
                for our_arch, w in weights.items()
            )
            for opp in archetypes
        }

    return round(
        sum(
            (meta_shares.get(opp_id, 0) / total_share) * matchups.get(opp_id, 0.5)
            for opp_id in meta_shares
        ),
        4,
    )
