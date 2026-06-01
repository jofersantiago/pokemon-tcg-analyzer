from __future__ import annotations

from pathlib import Path

from src.models import Card, Collection
from src.card_roles import ROLES, deck_role_fractions, attribute_win_rate
from src.cli.state import AppState
from src.cli import collection_io
from src.cli.display import header, table, separator, pick, prompt

_COLLECTION_PATH = Path(__file__).parent.parent.parent / "my_collection.json"

# ── helpers ──────────────────────────────────────────────────────────────────


def _pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def _build_meta_rows(state: AppState) -> list:
    rows = []
    for i, (arch, ewr) in enumerate(zip(state.archetypes, state.ewrs), 1):
        rows.append([
            i,
            arch["name"],
            _pct(arch["meta_share"]),
            _pct(arch["win_rate"]),
            _pct(ewr),
        ])
    return rows


def _build_catalog_rows(state: AppState, query: str) -> list:
    cards = (
        collection_io.fuzzy_search(query, state.catalog)
        if query
        else list(state.catalog.values())
    )
    cards.sort(key=lambda c: c.id)
    return [[c.id, c.name, c.card_type, c.hp or "—", c.set_id] for c in cards]


def _build_analysis_output(
    state: AppState, your_idx: int, opp_idx: int
) -> dict:
    your_arch = state.archetypes[your_idx]
    opp_arch = state.archetypes[opp_idx]
    your_deck = state.meta_decks[your_idx]
    opp_deck = state.meta_decks[opp_idx]

    ewr = state.matchup_matrix.get(your_arch["id"], {}).get(opp_arch["id"], 0.5)

    your_fracs = deck_role_fractions(your_deck, state.role_map)
    opp_fracs = deck_role_fractions(opp_deck, state.role_map)

    dna_rows = []
    max_delta = 0.0
    big_swing_role = ""
    for role in ROLES:
        yf = your_fracs.get(role, 0.0)
        mf = opp_fracs.get(role, 0.0)
        delta = yf - mf
        dna_rows.append([
            role,
            f"{yf * 100:.0f}%",
            f"{mf * 100:.0f}%",
            f"{'+' if delta >= 0 else ''}{delta * 100:.0f}%",
        ])
        if abs(delta) > max_delta:
            max_delta = abs(delta)
            big_swing_role = role

    if big_swing_role and max_delta >= 0.05:
        your_f = your_fracs.get(big_swing_role, 0.0)
        opp_f = opp_fracs.get(big_swing_role, 0.0)
        direction = "more" if your_f > opp_f else "less"
        big_swing = (
            f"Your deck runs {abs(your_f - opp_f) * 100:.0f}% "
            f"{direction} {big_swing_role.replace('_', ' ')} than theirs."
        )
    else:
        big_swing = "Decks have similar role composition."

    owned_collection = collection_io.load_collection()
    collection = Collection(cards=owned_collection)
    attribution = attribute_win_rate(your_deck, state.role_map, state.regression)

    gap_rows = []
    for role in ROLES:
        role_cards = [c for c in your_deck.unique_cards()
                      if state.role_map.get(c.id) == role]
        if not role_cards:
            continue
        needed = sum(your_deck.card_counts()[c.id] for c in role_cards)
        have = sum(
            min(owned_collection.get(c.id, 0), your_deck.card_counts()[c.id])
            for c in role_cards
        )
        missing_count = needed - have
        owned_pct = f"{100 * have // needed}%" if needed > 0 else "—"
        contrib = attribution.get(role, 0.0)
        gap_rows.append([
            role,
            owned_pct,
            missing_count if missing_count > 0 else "—",
            f"{'+' if contrib >= 0 else ''}{contrib * 100:.1f}%",
        ])

    missing = collection.missing_cards(your_deck)
    missing_rows = [
        [c.name, c.id, state.role_map.get(c.id, "?"), f"×{n}"]
        for c, n in missing
    ]

    return {
        "ewr": ewr,
        "dna_rows": dna_rows,
        "big_swing": big_swing,
        "gap_rows": gap_rows,
        "missing_rows": missing_rows,
    }


# ── commands ─────────────────────────────────────────────────────────────────

def cmd_meta(state: AppState) -> None:
    while True:
        header("META — TOP ARCHETYPES")
        rows = _build_meta_rows(state)
        table(rows, headers=["#", "Deck", "Share", "WIN", "E[WR]"])
        choice = pick([a["name"] for a in state.archetypes],
                      "Enter deck number for details")
        if choice < 0:
            return
        arch = state.archetypes[choice]
        header(f"DECK DETAIL — {arch['name']}")
        deck = state.meta_decks[choice]
        counts = deck.card_counts()
        card_rows = [
            [c.id, c.name, c.card_type, counts[c.id],
             state.role_map.get(c.id, "?")]
            for c in deck.unique_cards()
        ]
        table(card_rows, headers=["ID", "Name", "Type", "Count", "Role"])
        input("\nPress Enter to go back...")


def cmd_collection(state: AppState) -> None:
    SUB = ["Import from CSV", "Generate random collection",
           "Add / remove cards manually", "View current collection"]
    while True:
        header("COLLECTION")
        choice = pick(SUB)
        if choice < 0:
            return
        if choice == 0:
            _collection_import(state)
        elif choice == 1:
            _collection_random(state)
        elif choice == 2:
            _collection_manual(state)
        elif choice == 3:
            _collection_view(state)


def _collection_import(state: AppState) -> None:
    count, warnings = collection_io.import_csv(state.catalog)
    for w in warnings:
        if w == "template_created":
            print("\nNo collection file found. A template has been created at:")
            print(f"  {collection_io.CSV_PATH}")
            print("\nFormat:")
            print("  card_id,count")
            print("  A1-001,2")
            print("\nFind card IDs at:")
            print("  https://github.com/flibustier/pokemon-tcg-pocket-database")
            print("\nEdit the file, then run import again.")
        else:
            print(w)
    if count > 0:
        total = sum(collection_io.load_collection().values())
        print(f"\nImported {count} entries. Collection now has {total} total cards.")
    input("\nPress Enter to continue...")


def _collection_random(state: AppState) -> None:
    SIZES = [
        ("Small  — ~60 cards  (early player, ~12 packs)", 60),
        ("Medium — ~150 cards (active player, ~30 packs)", 150),
        ("Large  — ~300 cards (veteran, ~60 packs)", 300),
    ]
    header("GENERATE RANDOM COLLECTION")
    existing = collection_io.load_collection()
    if existing:
        confirm = input(
            f"You have {sum(existing.values())} cards already. "
            "Overwrite? [y/N]: "
        ).strip().lower()
        if confirm != "y":
            print("Cancelled.")
            input("\nPress Enter to continue...")
            return

    choice = pick([s[0] for s in SIZES], "Choose size")
    if choice < 0:
        return

    target = SIZES[choice][1]
    print(f"\nGenerating {target} cards...")
    result = collection_io.generate_random(state.catalog, target)

    unique = len(result)
    total = sum(result.values())
    print(f"\nAdded {total} cards across {unique} unique cards to your collection.")
    print("Collection saved to my_collection.json.\n")

    print("Sample of what you got:")
    sample = sorted(result.items(), key=lambda x: -x[1])[:8]
    for cid, cnt in sample:
        card = state.catalog.get(cid)
        name = card.name if card else cid
        print(f"  {name} ({cid})  ×{cnt}")
    input("\nPress Enter to continue...")


def _collection_manual(state: AppState) -> None:
    while True:
        header("ADD / REMOVE CARDS")
        query = prompt("Search card name (or 0 to go back)")
        if query == "0":
            return
        results = collection_io.fuzzy_search(query, state.catalog)
        if not results:
            print("  No cards found.")
            continue
        results = results[:10]
        choice = pick(
            [f"{c.name} ({c.id}) — {c.card_type}"
             + (f" / {c.hp}HP" if c.hp else "")
             for c in results],
            "Pick card"
        )
        if choice < 0:
            continue
        card = results[choice]
        current = collection_io.load_collection().get(card.id, 0)
        print(f"\n  Current count for {card.name}: {current}")
        new_count_str = prompt("New count")
        if not new_count_str.isdigit():
            print("  Invalid — must be a number.")
            continue
        collection_io.update_card_count(card.id, int(new_count_str))
        print(f"  Saved. {card.name}: {int(new_count_str)} copies.")


def _collection_view(state: AppState) -> None:
    header("YOUR COLLECTION")
    col = collection_io.load_collection()
    if not col:
        print("  Your collection is empty.")
        print("  Use 'Import from CSV' or 'Generate random collection' to add cards.")
        input("\nPress Enter to continue...")
        return
    rows = sorted(col.items(), key=lambda x: x[0])
    display_rows = [
        [cid, state.catalog[cid].name if cid in state.catalog else "—", cnt]
        for cid, cnt in rows
    ]
    table(display_rows, headers=["Card ID", "Name", "Count"])
    print(f"\nTotal: {sum(col.values())} cards across {len(col)} unique cards.")
    input("\nPress Enter to continue...")


def cmd_catalog(state: AppState, search: str = "") -> None:
    while True:
        header("CATALOG")
        if not search:
            search = prompt("Search (name / type / set) or Enter to list all")
        rows = _build_catalog_rows(state, search)
        if not rows:
            print(f"  No results for '{search}'.")
            search = ""
            continue
        print(f"\nResults for '{search}':" if search else "\nAll cards:")
        table(rows[:30], headers=["ID", "Name", "Type", "HP", "Set"])
        if len(rows) > 30:
            print(f"  ... and {len(rows) - 30} more. Refine your search.")

        card_id = prompt("Enter Card ID for details, or 0 to go back")
        if card_id == "0":
            search = ""
            return
        card = state.catalog.get(card_id.upper()) or state.catalog.get(card_id)
        if not card:
            print(f"  Card ID '{card_id}' not found.")
            continue
        _catalog_detail(card, state)
        search = ""


def _catalog_detail(card: Card, state: AppState) -> None:
    header(f"{card.name} ({card.id})")
    print(f"Type:      {card.card_type}")
    if card.hp:
        print(f"HP:        {card.hp}")
    if card.weakness:
        print(f"Weakness:  {card.weakness} ×2")
    if card.retreat is not None:
        print(f"Retreat:   {card.retreat}")
    if card.energy_type:
        print(f"Energy:    {card.energy_type}")
    print(f"Set:       {card.set_id}  |  Rarity: {card.rarity}")
    if card.abilities:
        print("\nAbilities:")
        for ab in card.abilities:
            print(f"  {ab.get('name', '?')} — {ab.get('text', '')}")
    if card.attacks:
        print("\nAttacks:")
        for atk in card.attacks:
            dmg = atk.get("damage", "—")
            cost = atk.get("cost", [])
            cost_str = "[" + "][".join(cost) + "]" if cost else ""
            print(f"  {atk.get('name', '?')}  {cost_str}  {dmg}")
            if atk.get("text"):
                print(f"    {atk['text']}")
    owned = collection_io.load_collection().get(card.id, 0)
    print(f"\nYou own: {owned} {'copy' if owned == 1 else 'copies'}")
    input("\nPress Enter to go back...")


def cmd_analysis(state: AppState, your_name: str = "") -> None:
    header("ANALYSIS")
    arch_names = [a["name"] for a in state.archetypes]

    if your_name:
        your_idx = next(
            (i for i, a in enumerate(state.archetypes)
             if your_name.lower() in a["name"].lower()),
            None,
        )
        if your_idx is None:
            print(f"  Deck '{your_name}' not found. Please pick from the list.")
            your_name = ""
    if not your_name:
        print("Select YOUR deck:\n")
        your_idx = pick(arch_names, "Your deck")
        if your_idx < 0:
            return

    print("\nSelect OPPONENT deck:\n")
    opp_idx = pick(arch_names, "Opponent deck")
    if opp_idx < 0:
        return

    data = _build_analysis_output(state, your_idx, opp_idx)

    separator()
    print(f"YOUR DECK: {state.archetypes[your_idx]['name']}")
    print(f"OPP DECK:  {state.archetypes[opp_idx]['name']}")
    separator()

    print("\nWIN RATE / 勝率")
    print(f"  {data['ewr'] * 100:.1f}%   "
          f"(R² = {state.regression.r_squared:.3f} · MODEL FIT)\n")

    print("ROLE DNA — COMPOSITION DIVERGENCE")
    table(data["dna_rows"], headers=["Role", "YOUR", "META", "Δ"])
    print(f"\nTHE BIG SWING: {data['big_swing']}\n")

    print("CLOSE THE GAP — HOW TO WIN THIS MATCHUP")
    table(data["gap_rows"], headers=["Role", "Owned", "Missing", "Contrib"])

    if data["missing_rows"]:
        print(f"\nCARDS TO ACQUIRE ({len(data['missing_rows'])}):")
        table(data["missing_rows"], headers=["Name", "ID", "Role", "Need"])

    input("\nPress Enter to go back...")
