# Pokémon TCG Pocket — Deck Meta-Analyzer & Collection Manager

A data-driven tool that helps Pokémon TCG Pocket players understand the competitive meta, evaluate their card collection, and make smarter decisions about which decks to build.

---

## What It Does

- **Fetches live tournament data** from the Limitless TCG API and the community card catalog from GitHub
- **Analyzes your collection** against every top meta deck — shows completion percentage and exactly which cards you're missing
- **Estimates expected win rate (E[WR])** for any deck against the current meta field using a matchup matrix and meta-share weighting
- **Classifies cards by role** (win condition, engine, staple, tech, garnet) and runs a regression to show which roles drive win rates
- **Generates charts**: matchup heatmap, observed vs. predicted win rates, role contribution breakdown
- **Launches a browser UI** where you can manage your collection, build custom decks, explore archetypes, and get deck vs. deck analysis

---

## Quickstart

### Mac / Linux
```bash
bash setup.sh
python3 main.py
```

### Windows
```bat
setup.bat
python main.py
```

The setup script creates a virtual environment and installs all dependencies. On first run, `main.py` downloads and caches the card catalog and tournament data automatically — no manual setup needed.

---

## Requirements

- Python 3.10+
- Internet connection on first run (data is cached locally after that)
- A Limitless TCG API key (required for deck list access — see [play.limitlesstcg.com/account/settings/api](https://play.limitlesstcg.com/account/settings/api))

Python dependencies (auto-installed by setup scripts):

| Package | Purpose |
|---|---|
| `requests` | API and data fetching |
| `numpy` | Numerical computation |
| `scikit-learn` | Role regression model |
| `matplotlib` | Chart generation |
| `tabulate` | Terminal summary table |
| `pytest` | Test suite |
| `flake8` | Code style enforcement |

---

## Project Structure

```
.
├── main.py                 # Entry point — runs pipeline then launches browser UI
├── src/
│   ├── data_ingest.py      # Fetch & cache card catalog + tournament data
│   ├── models.py           # Card, Deck, Collection dataclasses
│   ├── matchup.py          # Archetype fingerprinting + expected win rate
│   ├── card_roles.py       # Role classification + win rate regression
│   ├── visualizations.py   # Matplotlib charts + terminal table
│   └── web_collection.py   # Browser UI (HTTP server + full HTML/CSS/JS)
├── tests/
│   ├── conftest.py         # Shared fixtures
│   ├── test_models.py
│   ├── test_matchup.py
│   ├── test_card_roles.py
│   ├── test_data_ingest.py
│   └── test_visualizations.py
├── data/cache/             # Auto-generated — cached API responses (gitignored)
├── outputs/                # Auto-generated — PNG charts (gitignored)
├── requirements.txt
├── setup.sh                # Mac/Linux setup
└── setup.bat               # Windows setup
```

---

## How It Works

### Data Pipeline

```
Limitless TCG API  ──►  fetch_tournament_data()  ──►  data/cache/tournament.json
GitHub card DB     ──►  fetch_card_catalog()      ──►  data/cache/cards.json
                                │
                         main.py pipeline
                                │
              ┌─────────────────┼──────────────────┐
              ▼                 ▼                  ▼
      Expected Win Rate   Role Classification   Charts (PNG)
      matchup.py          card_roles.py         visualizations.py
                                │
                      Browser UI launched
                      web_collection.py
```

### Expected Win Rate Formula

For any deck, the expected win rate against the current meta is:

```
E[WR] = Σ  P(opponent plays deck d) × WR(our deck vs. d)
        d ∈ meta
```

Deck identity is matched to known archetypes using **cosine-distance fingerprinting** over the card list. Off-meta or custom decks fall back to a similarity-weighted average over the nearest known archetypes.

### Card Role Classification

Every card in tournament decklists is classified into one of five roles based on co-occurrence patterns and usage rates:

| Role | Description |
|---|---|
| `win_condition` | The primary attacker or combo piece the deck wins through |
| `engine` | Draw, search, or acceleration cards that keep the deck running |
| `staple` | High-usage utility cards present across many archetypes |
| `tech` | Situational cards targeting specific matchups |
| `garnet` | Low-count tech or filler cards rarely seen in multiple decks |

A linear regression then measures how each role's fraction in a deck predicts its observed tournament win rate — surfaced in the Analysis tab as **model contribution %** per role.

### Regression Model

```
Role regression R² = ~0.37
```

About 37% of win-rate variance across decks is explained by role composition alone. The remaining variance reflects specific card synergies, player skill, and tournament sample noise — the model intentionally stays interpretable rather than overfit.

---

## Browser UI — Tabs

| Tab | What You Can Do |
|---|---|
| **Meta** | Browse all top archetypes ranked by meta share and win rate |
| **Collection** | Track how many copies of each card you own |
| **Decks** | View completion % for every meta deck; see exactly which cards you're missing |
| **Analysis** | Select your deck and an opponent — see Role DNA divergence, win rate attribution, and Cards to Acquire |
| **Matchup** | Full head-to-head matchup matrix across all archetypes |
| **Catalog** | Browse all ~3,200 cards with search and filters |
| **New Deck** | Build and save custom decks from your collection |

Your collection and custom decks are saved locally as `my_collection.json` and `my_decks.json`.

---

## Running Tests

```bash
venv/bin/pytest tests/ -q
```

Run a single test file:
```bash
venv/bin/pytest tests/test_matchup.py -v
```

Run a single test:
```bash
venv/bin/pytest tests/test_matchup.py::test_known_deck_ewr -v
```

---

## Lint

```bash
flake8 src/ tests/ main.py --max-line-length=100
```

---

## Refreshing Tournament Data

The app caches tournament data on first run. To force a fresh pull from Limitless:

- Click the **Refresh** button in the browser UI, or
- Delete `data/cache/tournament.json` and re-run `python3 main.py`

---

## Submission Notes

When zipping for submission, exclude the following — they are large and auto-generated:

```bash
zip -r submission.zip . \
  -x "./venv/*" -x "./__pycache__/*" \
  -x "./src/__pycache__/*" -x "./tests/__pycache__/*" \
  -x "./data/cache/*" -x "./outputs/*" \
  -x "./.git/*" -x "./.pytest_cache/*"
```

To restore on a new machine:
```bash
bash setup.sh      # Mac/Linux
python3 main.py

setup.bat          # Windows
python main.py
```

---

## Data Sources

- **Card Catalog** — [flibustier/pokemon-tcg-pocket-database](https://github.com/flibustier/pokemon-tcg-pocket-database) on GitHub
- **Tournament Data** — [Limitless TCG API](https://docs.limitlesstcg.com/developer.html)
