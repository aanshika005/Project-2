"""
Retrieval strategies behind `search_listings`.

Two ways to rank the same filtered listings:

    keyword    the original strategy: score = 2 per query word found in the
               title + 1 per word found only in the other text fields.
               Behaviour is unchanged from before this module existed.

    category   keyword score, but listings of the garment type the user asked
               for are ranked first. "corduroy jacket" puts jackets ahead of
               corduroy pants; "pants" also finds jeans and trousers, which
               share no word with it.

This module uses only the standard library on purpose: the retrieval eval
(`python eval_retrieval.py`) imports it directly, so it runs with no API key,
no network and no model.
"""

import re

from utils.data_loader import load_listings

STRATEGIES = ("keyword", "category")
DEFAULT_LIMIT = 10


# ── shared helpers (moved verbatim from tools.py) ────────────────────────────

_STOPWORDS = {
    "a", "an", "and", "the", "for", "with", "under", "over", "in", "of"
}


def _keywords(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9']+", (text or "").lower())
    return {w for w in words if w not in _STOPWORDS and len(w) > 1}


def _size_tokens(size: str) -> set[str]:
    cleaned = re.sub(r"\([^)]*\)", " ", size or "")  # drop parentheticals
    parts = [p.strip().upper() for p in cleaned.split("/")]
    return {p for p in parts if p}


def _size_matches(wanted: str, listing_size: str) -> bool:
    if not wanted:
        return True
    listing_tokens = _size_tokens(listing_size)
    if any(token.startswith("ONE SIZE") for token in listing_tokens):
        return True
    return bool(_size_tokens(wanted) & listing_tokens)


def _keyword_score(wanted: set[str], item: dict) -> int:
    """2 per query word in the title, 1 per query word found only elsewhere."""
    title_words = _keywords(item["title"])
    other_text = " ".join([
        item["description"],
        item["category"],
        " ".join(item["style_tags"]),
        " ".join(item["colors"]),
        item["brand"] or "",          # brand is often None
    ])
    other_words = _keywords(other_text)
    return 2 * len(wanted & title_words) + len(wanted & (other_words - title_words))


# ── the category strategy ────────────────────────────────────────────────────
#
# A garment-type family says: if the query contains one of `terms`, listings
# whose TITLE contains one of `title_words` are an exact type match, and
# listings in `category` are a weaker one. Title words are the head nouns that
# actually appear in data/listings.json ("Tee", "Trousers", "Bomber", ...).
# `category` is None where the data's category label is unreliable (the slip
# dress is filed under "bottoms").
#
# Direction matters: "pants" is the broad word, so it reaches jeans and
# trousers; "trousers" is narrower and does not reach jeans.

_FAMILIES = [
    # name,        query terms,                                         title words,                       category
    ("tee",        {"tee", "tees", "tshirt", "tshirts"},                {"tee"},                           "tops"),
    ("shirt",      {"shirt", "shirts", "buttonup", "buttondown",
                    "flannel", "polo", "henley", "blouse"},             {"shirt", "button", "henley"},     "tops"),
    ("sweatshirt", {"sweatshirt", "sweatshirts", "hoodie", "hoodies",
                    "crewneck", "pullover"},                            {"sweatshirt", "hoodie", "crewneck"}, "tops"),
    ("sweater",    {"sweater", "sweaters", "cardigan"},                 {"cardigan"},                      "tops"),
    ("top",        {"top", "tops"},                                     set(),                             "tops"),
    ("vest",       {"vest", "vests"},                                   {"vest"},                          None),
    ("jacket",     {"jacket", "jackets", "coat", "coats", "bomber",
                    "windbreaker", "shacket"},                          {"jacket", "bomber", "windbreaker", "shacket"}, "outerwear"),
    ("blazer",     {"blazer", "blazers"},                               {"blazer"},                        "outerwear"),
    ("outerwear",  {"outerwear"},                                       set(),                             "outerwear"),
    ("jeans",      {"jeans"},                                           {"jeans"},                         "bottoms"),
    ("trousers",   {"trousers", "slacks"},                              {"trousers", "pants"},             "bottoms"),
    ("pants",      {"pants"},                                           {"pants", "trousers", "jeans"},    "bottoms"),
    ("shorts",     {"shorts"},                                          {"shorts"},                        "bottoms"),
    ("dress",      {"dress", "dresses"},                                {"dress"},                         None),
    ("bottoms",    {"bottoms"},                                         set(),                             "bottoms"),
    ("sneakers",   {"sneakers", "sneaker", "trainers", "kicks"},        {"sneakers"},                      "shoes"),
    ("boots",      {"boots", "boot"},                                   {"boots"},                         "shoes"),
    ("shoes",      {"shoes", "shoe", "footwear"},                       set(),                             "shoes"),
    ("bag",        {"bag", "bags", "purse", "handbag", "crossbody",
                    "tote"},                                            {"bag"},                           "accessories"),
    ("hat",        {"hat", "hats", "cap", "beanie"},                    {"hat"},                           "accessories"),
    ("belt",       {"belt", "belts"},                                   {"belt"},                          "accessories"),
    ("accessories", {"accessory", "accessories"},                       set(),                             "accessories"),
]

# Spellings that tokenize badly ("t-shirt" -> "t", "shirt"). Applied to the
# query for type detection only; the keyword score still sees the original text.
_PHRASES = [
    (re.compile(r"\bt[\s-]?shirts?\b"), "tshirt"),
    (re.compile(r"\bbutton[\s-]?up\b"), "buttonup"),
    (re.compile(r"\bbutton[\s-]?down\b"), "buttondown"),
]


def detect_families(description: str) -> list[str]:
    """Names of the garment-type families a query mentions (may be empty)."""
    text = (description or "").lower()
    for pattern, replacement in _PHRASES:
        text = pattern.sub(replacement, text)
    words = set(re.findall(r"[a-z0-9']+", text))
    return [name for name, terms, _, _ in _FAMILIES if words & terms]


def _type_match(item: dict, families: list[str]) -> int:
    """2 = title names the garment type, 1 = same category only, 0 = neither."""
    title_words = _keywords(item["title"])
    best = 0
    for name, _, wanted_title_words, category in _FAMILIES:
        if name not in families:
            continue
        if title_words & wanted_title_words:
            return 2
        if category and item["category"] == category:
            best = 1
    return best


# ── ranking ──────────────────────────────────────────────────────────────────

def rank(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
    strategy: str = "keyword",
    limit: int = DEFAULT_LIMIT,
    listings: list[dict] | None = None,
) -> list[dict]:
    """
    Filter by price and size, then rank by `strategy`. Returns a list of
    {"item", "score", "type_match", "families"} dicts, best first, at most
    `limit` long, [] when nothing matches. `type_match` and `families` are
    only meaningful for the category strategy (0 and [] for keyword).
    """
    if strategy not in STRATEGIES:
        raise ValueError(
            f"Unknown search strategy {strategy!r}. Choose one of: {', '.join(STRATEGIES)}."
        )
    if listings is None:
        listings = load_listings()
    wanted = _keywords(description)
    families = detect_families(description) if strategy == "category" else []

    scored = []
    for item in listings:
        # 1. Hard filters: price and size
        if max_price is not None and item["price"] > max_price:
            continue
        if not _size_matches(size, item["size"]):
            continue

        score = _keyword_score(wanted, item)
        type_match = _type_match(item, families) if families else 0

        # 2. Keep anything with keyword overlap. Under the category strategy an
        #    exact garment-type match is also kept at score 0, so "pants" can
        #    reach jeans, which share no word with it. A query with no
        #    keywords at all still returns [].
        if score > 0 or (type_match == 2 and wanted):
            scored.append({"item": item, "score": score,
                           "type_match": type_match, "families": families})

    # 3. Best first. Keyword: score, then cheaper. Category: garment type
    #    first, then score, then cheaper.
    scored.sort(key=lambda r: (-r["type_match"], -r["score"], r["item"]["price"]))
    return scored[:limit]
