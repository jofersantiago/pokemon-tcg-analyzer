# Pokémon TCG Pocket — CLI Version Design Spec

**Date:** 2026-05-31
**Status:** Awaiting user approval

---

## Goal

Build a Python CLI version of the Pokémon TCG Pocket Meta-Analyzer that runs entirely in the terminal — no browser, no HTTP server. It must share all data (collection, decks) with the existing web app so changes in one are immediately visible in the other.

---

## Scope

- Lives **in the same repo** as the web app
- Entry point: `python3 main_cli.py`
- New folder: `src/cli/` for CLI-specific modules
- All analysis logic reused from existing `src/` modules (no duplication)
- Only `web_collection.py` has no CLI equivalent — everything else is shared

---

## Architecture

```
Final Project/
├── main.py                  (existing — web app, unchanged)
├── main_cli.py              (NEW — CLI entry point)
├── src/
│   ├── data_ingest.py       (shared, unchanged)
│   ├── models.py            (shared, unchanged)
│   ├── matchup.py           (shared, unchanged)
│   ├── card_roles.py        (shared, unchanged)
│   ├── visualizations.py    (shared, unchanged)
│   ├── web_collection.py    (existing — web only, unchanged)
│   └── cli/
│       ├── __init__.py
│       ├── menu.py          — interactive numbered menu loop
│       ├── collection_io.py — CSV import + random collection generator
│       ├── display.py       — tabulate-based formatted output helpers
│       └── commands.py      — thin wrappers calling existing src modules
└── data/
    ├── my_collection.json   (shared with web app — single source of truth)
    └── my_collection.csv    (user-provided import file — template generated on first run)
```

### Shared Data Contract

Both the CLI and web app read/write `my_collection.json` using the existing format:
```json
{ "A1-001": 2, "A1-036": 1, "A2b-004": 2 }
```

CSV is an **import format only** — it is converted to `my_collection.json` on import. It is never the live storage format.

---

## CLI Structure

### Entry point: `main_cli.py`

Two modes:

**1. Interactive menu** (no arguments):
```
python3 main_cli.py
```
Launches the numbered menu — guided, works for first-time users.

**2. Argparse subcommands** (direct use):
```
python3 main_cli.py meta
python3 main_cli.py collection import --file data/my_collection.csv
python3 main_cli.py collection random
python3 main_cli.py catalog --search "Espeon"
python3 main_cli.py analysis --deck "Mega Altaria ex Espeon"
```

When run with no arguments, `main_cli.py` falls back to the interactive menu.

---

## The 4 Tabs (mirroring the web app)

### [1] META

Displays all meta archetypes ranked by meta share, with win rate and E[WR].

```
=== META — TOP ARCHETYPES ===

 #   Deck                          Share    WIN     E[WR]
───  ────────────────────────────  ───────  ──────  ──────
 1   Mega Altaria ex Espeon        18.4%    53.2%   51.2%
 2   Hydreigon ex Mega Absol ex    11.6%    45.8%   46.5%
 3   Miraidon ex Magnezone         11.0%    45.3%   46.6%
...

Enter deck number for details, or [0] to go back: _
```

Selecting a deck number shows that archetype's full card list and matchup record.

---

### [2] COLLECTION

Sub-menu with 3 options:

```
=== COLLECTION ===

[1] Import from CSV
[2] Generate random collection
[3] Add / remove cards manually
[4] View current collection
[0] Back

Choose: _
```

#### [2.1] Import from CSV

On first run (no collection exists yet), print the template and save it:

```
No collection found. A template has been created at:
  data/my_collection.csv

Format:
  card_id,count
  A1-001,2
  A1-036,1

Find card IDs at:
  https://github.com/flibustier/pokemon-tcg-pocket-database

Edit the file, then run import again.
```

On subsequent runs (file exists):
- Parse CSV, validate card IDs against the catalog
- Warn (do not reject) on unknown IDs: `WARNING: A9-999 not found in catalog — skipped`
- Merge into `my_collection.json` (adds to existing counts, does not overwrite)
- Print summary: `Imported 47 entries. Collection now has 312 total cards.`

#### [2.2] Generate random collection

```
Generate random collection:

  [1] Small  — ~60 cards  (early player, ~12 packs)
  [2] Medium — ~150 cards (active player, ~30 packs)
  [3] Large  — ~300 cards (veteran, ~60 packs)

Choose size: _

Generating... done.

Added 150 cards across 89 unique cards to your collection.
Collection saved to my_collection.json.

Sample of what you got:
  Pikachu ex (A1-001)       ×2
  Charizard ex (A1-006)     ×1
  Misty (A1-153)            ×2
  ...
```

- Weighted by rarity: common > uncommon > rare > ex/full art
- Saves directly to `my_collection.json`
- Overwrites existing collection (asks for confirmation if one exists)

#### [2.3] Add / remove cards manually

Fuzzy name search:
```
Search card name: espe

Results:
  [1] Espeon (A1-133) — Psychic / Pokemon / 90HP
  [2] Espeon ex (A1a-037) — Psychic / Pokemon / 150HP

Pick card [1-2]: 1

Current count for Espeon: 0
New count: 2

Saved.
```

#### [2.4] View current collection

Paginated table of all owned cards sorted by set ID, with count column.

---

### [3] CATALOG

Browse and search all ~3,200 cards.

```
=== CATALOG ===

Search (name / type / set) or press Enter to list all: altaria

Results for "altaria":
  ID         Name              Type     HP    Set
  ─────────  ────────────────  ───────  ────  ────
  A2b-036    Altaria           Pokemon   80   A2b
  A2b-037    Mega Altaria ex   Pokemon  190   A2b
  ...

Enter card ID for full details, or [0] to go back: _
```

Full card detail view:
```
=== Mega Altaria ex (A2b-037) ===

Type:     Pokemon (Dragon)
HP:       190
Weakness: Metal ×2
Retreat:  2

Abilities:
  Mega Evolution Boost — When Mega Altaria ex becomes your Active Pokémon...

Attacks:
  Mega Harmony   [C][C][C]   120
    Does 20 more damage for each of your Benched Pokémon.

You own: 2 copies
```

---

### [4] ANALYSIS

Mirrors the web Analysis tab — Role DNA, Close the Gap, Cards to Acquire.

```
=== ANALYSIS ===

Select YOUR deck (pick a meta archetype):
  [1] Mega Altaria ex Espeon     18.4%
  [2] Hydreigon ex Mega Absol ex 11.6%
  ...

Select OPPONENT deck:
  [1] Mega Altaria ex Espeon     18.4%
  [2] Hydreigon ex Mega Absol ex 11.6%
  ...

───────────────────────────────────────────────
YOUR DECK: Mega Altaria ex Espeon
OPP DECK:  Miraidon ex Magnezone
───────────────────────────────────────────────

WIN RATE / 勝率
  50.0%   (R² = 0.372 · MODEL FIT)

ROLE DNA — COMPOSITION DIVERGENCE
  Role           YOUR    META     Δ
  ─────────────  ──────  ───────  ────
  win_condition  20%     20%       0%
  engine         45%     30%     +15%
  staple         30%     30%       0%
  tech           5%      20%     -15%

THE BIG SWING: Your deck runs 15% more engine than theirs.

CLOSE THE GAP — HOW TO WIN THIS MATCHUP
  Role           Owned   Missing  Contrib
  ─────────────  ──────  ───────  ───────
  win_condition  100%    0        +2.3%
  engine         100%    0        +4.8%
  staple          75%    1       +13.5%
  tech           100%    0        -3.4%

CARDS TO ACQUIRE (1):
  Iono (A1-189)   STAPLE   ×1
```

The user selects their deck by picking from meta archetypes or using cards in their `my_collection.json`.

---

## CSV Format (full spec)

```csv
# Pokémon TCG Pocket Collection
# card_id = set code + number, e.g. A1-001, A2b-036, P-A-001
# count   = number of copies owned
card_id,count
A1-001,2
A1-036,1
A2b-037,2
```

Rules:
- Lines starting with `#` are comments — ignored
- `card_id` must match the catalog format `{SET}-{NUM}` (e.g. `A1-001`)
- `count` must be a positive integer
- Duplicate `card_id` rows are summed
- Unknown IDs produce a warning, not an error

---

## Dependencies

No new runtime dependencies. The CLI uses only what is already in `requirements.txt`:
- `tabulate` — already installed, used for table output
- `requests`, `numpy`, `scikit-learn` — already installed, used by shared modules

Optional (not required): `readline` (built into Python on Mac/Linux) for arrow-key history in search prompts.

---

## Error Handling

| Situation | Behaviour |
|---|---|
| No internet on first run | Clear message: "Could not fetch data. Check your connection." |
| CSV has unknown card IDs | Warn per ID, continue importing valid rows |
| Empty collection when entering Analysis | Prompt to import or generate first |
| Catalog not yet cached | Auto-fetch and cache before showing results |

---

## Non-Goals

- No charts/PNG output (terminal only)
- No HTTP server
- No deck builder (New Deck tab not included — out of scope for CLI v1)
- No matchup matrix display (data is used internally by Analysis but not shown as a grid)
