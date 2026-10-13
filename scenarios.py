"""
The runs your test needs. ← UNIT 4, MILESTONE 3

Each of your five criteria needs something run against it. A criterion about
the empty-search branch needs an impossible query. One about the fit card needs
the same item run more than once. Working that out is Milestone 3's first step,
and this file is where you write it down.

`run_eval.py` runs everything here five times and writes the run log — five
because your criteria are written out of five.

Three scenarios are filled in to show the shape. Add or change whatever your
own criteria need — these are a starting point, not a fixed set.
"""

SCENARIOS = [
    # ── Criterion 1: a matching query completes all three tools ──
    {"name": "matching query completes", "query": "vintage graphic tee under $30",
     "wardrobe": "example", "criterion": 1},

    # ── Criterion 2: an impossible query stops before suggest_outfit ──
    {"name": "impossible query stops early", "query": "designer ballgown size XXS under $5",
     "wardrobe": "example", "criterion": 2},

    # ── Criterion 3: the item search found is the item every later tool receives ──
    # A normal query that doesn't trigger the pricey switch (see the revision
    # note under criterion 3 in criteria.md).
    {"name": "state: item flows through", "query": "90s windbreaker",
     "wardrobe": "example", "criterion": 3},

    # ── Criterion 4: fit cards across 5 DIFFERENT items ──
    # Try t is judged across the five t-th runs together.
    {"name": "fit card A: band tee", "query": "vintage band tee",
     "wardrobe": "example", "criterion": 4},
    {"name": "fit card B: track jacket", "query": "90s track jacket in size M",
     "wardrobe": "example", "criterion": 4},
    {"name": "fit card C: slip dress", "query": "silk slip dress",
     "wardrobe": "example", "criterion": 4},
    {"name": "fit card D: platform sneakers", "query": "platform sneakers size 8",
     "wardrobe": "example", "criterion": 4},
    {"name": "fit card E: denim jacket", "query": "denim jacket under $50",
     "wardrobe": "example", "criterion": 4},

    # ── Criterion 5: search never breaks its own filters (price and/or size) ──
    # Try t is judged across the five t-th runs together.
    {"name": "filters A: price only", "query": "graphic tee under $30",
     "wardrobe": "example", "criterion": 5},
    {"name": "filters B: size + price", "query": "top size S under $20",
     "wardrobe": "example", "criterion": 5},
    {"name": "filters C: price, outerwear", "query": "jacket under $45",
     "wardrobe": "example", "criterion": 5},
    {"name": "filters D: shoe size + price", "query": "sneakers size 9 under $50",
     "wardrobe": "example", "criterion": 5},
    {"name": "filters E: letter size + price", "query": "tee size L under $25",
     "wardrobe": "example", "criterion": 5},

    # ── Diagnostics (not one of the five) ──
    # A user with nothing saved. One of unit 4's three failure modes.
    {"name": "empty wardrobe", "query": "denim jacket under $50",
     "wardrobe": "empty", "criterion": None},
    # Known gap from unit 3: the Levi's are labelled "W30 L30", which a plain
    # "W30" doesn't match.
    {"name": "waist size W30 vs 'W30 L30'", "query": "jeans size W30",
     "wardrobe": "example", "criterion": None},
]

WARDROBES = ("example", "empty")


def validate() -> list[str]:
    """Complain about anything malformed, before a long run rather than during."""
    problems = []
    for i, scenario in enumerate(SCENARIOS, 1):
        if not scenario.get("query", "").strip():
            problems.append(f"scenario {i} has no query")
        if scenario.get("wardrobe") not in WARDROBES:
            problems.append(
                f"scenario {i} has wardrobe {scenario.get('wardrobe')!r} — "
                f"it should be one of {WARDROBES}"
            )
    return problems
