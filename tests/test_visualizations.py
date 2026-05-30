from src.visualizations import (
    plot_matchup_heatmap, plot_wr_comparison, plot_role_attribution, print_collection_summary,
)
from src.models import Deck, Collection


def test_heatmap_creates_file(tmp_path):
    matrix = {"a": {"a": 0.5, "b": 0.6}, "b": {"a": 0.4, "b": 0.5}}
    path = plot_matchup_heatmap(matrix, output_path=tmp_path / "h.png")
    assert path.exists() and path.stat().st_size > 0


def test_wr_comparison_creates_file(tmp_path):
    archetypes = [{"id": "a", "win_rate": 0.55}, {"id": "b", "win_rate": 0.45}]
    path = plot_wr_comparison(archetypes, {"a": 0.53, "b": 0.47}, output_path=tmp_path / "w.png")
    assert path.exists()


def test_role_attribution_creates_file(tmp_path):
    archetypes = [{"id": "a", "win_rate": 0.55}]
    attr = {"a": {"win_condition": 0.2, "engine": 0.15, "staple": 0.1, "tech": 0.05, "garnet": 0.0}}
    path = plot_role_attribution(archetypes, attr, output_path=tmp_path / "r.png")
    assert path.exists()


def test_collection_summary_prints(sample_cards, capsys):
    deck = Deck(
        cards=sample_cards[:2] * 2 + [sample_cards[2]] * 2,
        archetype_label="test-deck",
    )
    print_collection_summary(
        collection=Collection(cards={sample_cards[0].id: 2}),
        meta_decks=[deck],
        expected_wrs=[0.52],
        role_attributions=[
            {"win_condition": 0.3, "engine": 0.2, "staple": 0.1, "tech": 0.1, "garnet": 0.0}
        ],
    )
    out = capsys.readouterr().out
    assert "test-deck" in out and "%" in out
