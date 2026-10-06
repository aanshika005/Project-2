"""
The three FitFindr tools.

Each one is a standalone function you can call and test on its own, before any
of them are wired into the loop. Build and test them one at a time — three
untested tools joined by a loop is one problem that looks like six, because you
can't tell which layer is lying to you.

    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)             → str
    create_fit_card(outfit, new_item)              → str

All three are stubs right now. They run and they do nothing — that's the
starting position and it's deliberate.

⚠️ Before you write any of them, fill in the **Tool Inventory** section of your
README (Milestone 2). Four lines per tool: what it does, each input with its
type, exactly what it returns, and what it returns when it has nothing to give.
That last line is what your loop branches on. "Returns a list" earns nothing —
the description has to say what is *in* the list.
"""

import re

import config
from generate import generate
from utils.data_loader import load_listings


# ── Tool 1: search_listings ───────────────────────────────────────────────────
_STOPWORDS = {
    "a", "an", "and", "the", "for", "with", "under", "over", "in", "of"
}


def _keywords(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9']+", (text or "").lower())
    return {w for w in words if w not in _STOPWORDS and len(w) > 1}

def _size_tokens(size: str) -> set[str]:
    cleaned = re.sub(r"\([^)]*\)", " ", size or "") #drop parentheticals
    parts = [p.strip().upper() for p in cleaned.split("/")]
    return {p for p in parts if p}

def _size_matches(wanted: str, listing_size: str) -> bool:
    if not wanted:
        return True
    listing_tokens = _size_tokens(listing_size)
    if any(token.startswith("ONE SIZE") for token in listing_tokens):
        return True
    return bool(_size_tokens(wanted) & listing_tokens)

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the listings data for items matching a description, and optionally a
    size and a price ceiling.

    This is the tool that doesn't call the model, which makes it the easiest one
    to test and the one to move onto MCP in unit 4.

    Args:
        description: keywords describing what the user wants
                     (e.g. "vintage graphic tee").
        size:        a size string to filter by, or None to skip size filtering.
                     Match case-insensitively — "M" should match "S/M".

                     ⚠️ Read the sizes in the data before you reach for a plain
                     substring test. `"s" in "us 9"` is True, and so is
                     `"l" in "xl"`. A filter that returns shoes when someone
                     asked for a small top reads like a broken search, and it
                     will quietly cost you in unit 4 when you test criterion 1.
                     What counts as a size match is part of your spec — decide
                     it and write it into your Tool Inventory.
        max_price:   maximum price, inclusive, or None to skip price filtering.

    Returns:
        A list of matching listing dicts, best match first.
        **Returns an empty list when nothing matches — an empty list, not None,
        and not an exception.** Your loop branches on this.

    Each listing dict has these fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand (str or None), platform

    Note that `brand` is None for most listings. That is deliberate and
    realistic — thrift listings often have no brand. If something you write
    assumes a brand is always there, you will find out in unit 4.

    TODO:
        1. Load every listing with load_listings().
        2. Filter by max_price and by size, when each is provided.
        3. Score what's left by keyword overlap with `description`.
        4. Drop anything scoring zero.
        5. Sort by score, highest first, and return the listing dicts —
           at most config.SEARCH_RESULT_LIMIT of them.

    Test it from a terminal before you move on:
        python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
    """
    listings = load_listings()
    wanted = _keywords(description)

    scored = []
    for item in listings:
        # 1. Hard filters: price and size
        if max_price is not None and item["price"] > max_price:
            continue
        if not _size_matches(size, item["size"]):
            continue

        # 2. Score by keyword overlap. Title words count double.
        title_words = _keywords(item["title"])
        other_text = " ".join([
            item["description"],
            item["category"],
            " ".join(item["style_tags"]),
            " ".join(item["colors"]),
            item["brand"] or "",          # brand is often None
        ])
        other_words = _keywords(other_text)
        score = 2 * len(wanted & title_words) + len(wanted & (other_words - title_words))

        # 3. Drop anything with no overlap
        if score > 0:
            scored.append((score, item))

    # 4. Best first; cheaper wins a tie
    scored.sort(key=lambda pair: (-pair[0], pair[1]["price"]))
    return [item for _, item in scored[: config.SEARCH_RESULT_LIMIT]]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def _describe_item(item: dict) -> str:
    """One readable line about a listing, for the prompt."""
    parts = [
        item.get("title", "Unknown item"),
        f"category: {item.get('category', 'unknown')}",
        f"colors: {', '.join(item.get('colors') or []) or 'unknown'}",
        f"style: {', '.join(item.get('style_tags') or []) or 'unknown'}",
    ]
    if item.get("brand"):              # brand is often None
        parts.append(f"brand: {item['brand']}")
    return " | ".join(parts)


def _describe_wardrobe_piece(piece: dict) -> str:
    """One readable line about something the user owns."""
    text = f"{piece.get('name', 'unnamed piece')} ({piece.get('category', 'unknown')}"
    if piece.get("colors"):
        text += f"; {', '.join(piece['colors'])}"
    text += ")"
    if piece.get("notes"):             # notes can be None
        text += f" — {piece['notes']}"
    return text


def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest one or two outfits.

    This one calls the model, through `generate()`. You don't need to think
    about rate limits — the adapter handles pacing for you.

    Args:
        new_item: a listing dict — the item the user is considering.
        wardrobe: a wardrobe dict with an 'items' key holding a list of items.
                  **It may be empty.** Handle that.

    Returns:
        A non-empty string with outfit suggestions.
        With an empty wardrobe, return general styling advice rather than
        raising or returning "". Unit 4 has you trigger the empty wardrobe on
        purpose, so decide now what it should do.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If it is, ask the model for general styling ideas for this item.
        3. If it isn't, format the wardrobe items into the prompt and ask for
           specific combinations naming pieces the user already owns.
        4. Return the model's response.

    Test it from a terminal before you move on:
        python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
    """
    items = (wardrobe or {}).get("items") or []
    item_text = _describe_item(new_item)

    system = (
        "You are a friendly personal stylist for secondhand fashion. "
        "Be specific and practical. Plain text only, no markdown headings."
    )

    if not items:
        # Empty wardrobe: general advice instead of failing
        prompt = (
            f"Someone is thinking about buying this thrifted item:\n{item_text}\n\n"
            "They haven't told us what's in their wardrobe yet. Suggest 1-2 outfits "
            "built around this item, describing the kinds of pieces, colors and shoes "
            "that would go with it. Keep it under 120 words."
        )
    else:
        wardrobe_text = "\n".join(f"- {_describe_wardrobe_piece(p)}" for p in items)
        prompt = (
            f"Someone is thinking about buying this thrifted item:\n{item_text}\n\n"
            f"Here is what they already own:\n{wardrobe_text}\n\n"
            "Suggest 1-2 outfits that pair the new item with pieces from their "
            "wardrobe. Name the wardrobe pieces exactly as listed. Only use pieces "
            "from the list. Keep it under 120 words."
        )

    response = generate(prompt, system=system)
    if not response.strip():
        # The contract says never return "", so fall back to something useful
        return f"Try the {new_item.get('title', 'item')} with simple basics in neutral colors."
    return response


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Write a short caption someone would actually post about the find.

    This calls the model too.

    Args:
        outfit:   the outfit suggestion string from suggest_outfit().
        new_item: the listing dict for the item.

    Returns:
        A two-to-four sentence caption.
        If `outfit` is empty or whitespace, return a descriptive message rather
        than raising.

    The caption should read like a real post rather than a product description,
    mention the item and its price and platform once each, and be specific about
    the vibe.

    It should also come out **differently for different inputs**. If you run
    this three times on the same item and get three word-for-word identical
    strings, it's one of two things, and both are near the top of `config.py`:

        • CACHE_ENABLED — the adapter handed back an answer it already had
        • TEMPERATURE   — at 0.0 the model gives the same words every time

    TODO:
        1. Guard against an empty or whitespace-only `outfit`.
        2. Build a prompt with the item details and the outfit.
        3. Call generate() and return the response.

    Test it from a terminal before you move on:
        python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
    """
    if not outfit or not outfit.strip():
        return "Can't write a fit card: no outfit suggestion was provided."

    title = new_item.get("title", "this find")
    price = new_item.get("price")
    price_text = f"${price:.2f}".replace(".00", "") if isinstance(price, (int, float)) else "a thrift price"
    platform = new_item.get("platform", "a resale app")

    system = (
        "You write short, casual social media captions about thrift finds. "
        "Sound like a real person posting, not a product description. "
        "Plain text only."
    )
    prompt = (
        f"Write a 2-4 sentence caption about this thrift find.\n\n"
        f"Item: {_describe_item(new_item)}\n"
        f"Price: {price_text}\n"
        f"Platform: {platform}\n"
        f"How I'm styling it: {outfit.strip()}\n\n"
        f"Mention the item ({title}), the price ({price_text}) and the platform "
        f"({platform}) once each. Be specific about the vibe. "
        "At most 2 emoji and 3 hashtags."
    )

    response = generate(prompt, system=system)
    if not response.strip():
        return f"Thrifted the {title} for {price_text} on {platform}. Styling post coming soon."
    return response.strip()


# ── Tool 4 (stretch): compare_prices ─────────────────────────────────────────

def compare_prices(item: dict, listings: list[dict] | None = None) -> dict:
    """
    Compare one listing's price against every other listing in its category.

    Args:
        item:     a listing dict (the item the agent selected).
        listings: the listings to compare against. None loads all of them.

    Returns:
        A dict with:
            price            (float) the item's price
            category         (str)   the item's category
            compared_with    (int)   how many other listings were compared
            median           (float) median price of those listings
            cheaper_than_pct (int)   % of them that cost more than this item
            verdict          (str)   "good deal" / "about average" / "pricey"

        With fewer than 3 other listings in the category it returns
        compared_with 0, median None, cheaper_than_pct None and verdict
        "not enough similar listings". Same if the item has no numeric price.
        It never raises and never calls the model.
    """
    if listings is None:
        listings = load_listings()

    price = item.get("price")
    category = item.get("category", "unknown")
    not_enough = {"price": price, "category": category, "compared_with": 0,
                  "median": None, "cheaper_than_pct": None,
                  "verdict": "not enough similar listings"}
    if not isinstance(price, (int, float)):       # nothing to compare
        return not_enough
    price = float(price)

    others = [
        float(l["price"]) for l in listings
        if l.get("category") == category and l.get("id") != item.get("id")
    ]

    if len(others) < 3:
        return not_enough

    others.sort()
    mid = len(others) // 2
    median = others[mid] if len(others) % 2 else (others[mid - 1] + others[mid]) / 2
    cheaper_than_pct = round(100 * sum(p > price for p in others) / len(others))

    if price <= 0.85 * median:
        verdict = "good deal"
    elif price >= 1.15 * median:
        verdict = "pricey"
    else:
        verdict = "about average"

    return {"price": price, "category": category, "compared_with": len(others),
            "median": median, "cheaper_than_pct": cheaper_than_pct, "verdict": verdict}
