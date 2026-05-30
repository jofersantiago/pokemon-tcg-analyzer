from __future__ import annotations
import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from pathlib import Path  # noqa: E402
from tabulate import tabulate  # noqa: E402
from src.models import Deck, Collection  # noqa: E402
from src.card_roles import ROLES  # noqa: E402

OUTPUT_DIR = Path(__file__).parent.parent / "outputs"
_ROLE_COLORS = {
    "win_condition": "#E63946", "engine": "#457B9D", "staple": "#2A9D8F",
    "tech": "#E9C46A", "garnet": "#AAAAAA",
}


def _save(fig: plt.Figure, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_matchup_heatmap(
    matchup_matrix: dict[str, dict[str, float]],
    output_path: Path | None = None,
) -> Path:
    labels = list(matchup_matrix.keys())
    matrix = np.array([[matchup_matrix[r].get(c, 0.5) for c in labels] for r in labels])
    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(matrix, vmin=0, vmax=1, cmap="RdYlGn")
    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_yticklabels(labels)
    plt.colorbar(im, ax=ax, label="Win Rate")
    ax.set_title("Archetype Matchup Matrix")
    return _save(fig, output_path or OUTPUT_DIR / "matchup_heatmap.png")


def plot_wr_comparison(
    archetypes: list[dict],
    predicted_wrs: dict[str, float],
    output_path: Path | None = None,
) -> Path:
    labels = [a["id"] for a in archetypes]
    x = np.arange(len(labels))
    width = 0.35
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(
        x - width / 2,
        [a["win_rate"] for a in archetypes],
        width,
        label="Observed",
        color="steelblue",
    )
    ax.bar(
        x + width / 2,
        [predicted_wrs.get(a["id"], 0.5) for a in archetypes],
        width,
        label="Predicted",
        color="tomato",
    )
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=30, ha="right")
    ax.set_ylabel("Win Rate")
    ax.set_title("Observed vs Predicted Win Rate by Archetype")
    ax.legend()
    return _save(fig, output_path or OUTPUT_DIR / "wr_comparison.png")


def plot_role_attribution(
    archetypes: list[dict],
    attribution_by_arch: dict[str, dict[str, float]],
    output_path: Path | None = None,
) -> Path:
    labels = [a["id"] for a in archetypes]
    fig, ax = plt.subplots(figsize=(10, 5))
    bottoms = np.zeros(len(labels))
    for role in ROLES:
        values = np.array(
            [max(attribution_by_arch.get(aid, {}).get(role, 0.0), 0.0) for aid in labels]
        )
        ax.bar(labels, values, bottom=bottoms, label=role, color=_ROLE_COLORS[role])
        bottoms += values
    ax.set_ylabel("Win Rate Contribution")
    ax.set_title("Win Rate Attribution by Card Role per Archetype")
    ax.legend(loc="upper right")
    plt.xticks(rotation=30, ha="right")
    return _save(fig, output_path or OUTPUT_DIR / "role_attribution.png")


def print_collection_summary(
    collection: Collection,
    meta_decks: list[Deck],
    expected_wrs: list[float],
    role_attributions: list[dict[str, float]],
) -> None:
    ranked = sorted(
        zip(meta_decks, expected_wrs, role_attributions),
        key=lambda t: collection.completion_percent(t[0]),
        reverse=True,
    )[:5]
    rows = []
    for deck, ewr, attr in ranked:
        missing = collection.missing_cards(deck)
        top_role = max(attr, key=lambda r: attr[r]) if attr else "N/A"
        missing_str = ", ".join(f"{c.name}×{n}" for c, n in missing[:3])
        if len(missing) > 3:
            missing_str += f" (+{len(missing) - 3} more)"
        rows.append([
            deck.archetype_label,
            f"{collection.completion_percent(deck)}%",
            f"{ewr:.1%}",
            top_role,
            missing_str or "Complete!",
        ])
    print(tabulate(
        rows,
        headers=["Deck", "Completion", "Expected WR", "Key Role", "Missing"],
        tablefmt="rounded_outline",
    ))
