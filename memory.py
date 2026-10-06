"""
Style memory (stretch feature): the wardrobe is saved between runs.

    data/saved_wardrobe.json     same shape as every other wardrobe: {"items": [...]}

`python app.py ask '...' --keep` adds the item the agent found to the saved
wardrobe. Every later `ask` loads it automatically, so suggest_outfit can build
outfits around something kept in an earlier run.
"""

import json

import config

SAVED_PATH = config.DATA_DIR / "saved_wardrobe.json"


def load_saved_wardrobe() -> dict | None:
    """The saved wardrobe, or None if nothing has been saved yet (or the file is unreadable)."""
    try:
        with open(SAVED_PATH, encoding="utf-8") as f:
            wardrobe = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    if not isinstance(wardrobe, dict) or not isinstance(wardrobe.get("items"), list):
        return None
    return wardrobe


def save_wardrobe(wardrobe: dict) -> None:
    with open(SAVED_PATH, "w", encoding="utf-8") as f:
        json.dump({"items": wardrobe.get("items", [])}, f, indent=2, ensure_ascii=False)


def listing_to_piece(listing: dict) -> dict:
    """Turn a listing into a wardrobe item, in the wardrobe schema's shape."""
    return {
        "id": f"kept_{listing.get('id')}",
        "name": listing.get("title", "kept item"),
        "category": listing.get("category", "unknown"),
        "colors": listing.get("colors") or [],
        "style_tags": listing.get("style_tags") or [],
        "notes": f"Kept from an earlier FitFindr search ({listing.get('platform')}, ${listing.get('price')})",
    }


def keep_item(wardrobe: dict, listing: dict) -> tuple[dict, bool]:
    """
    Add a listing to the wardrobe and save it.

    Returns (wardrobe, added). added is False if the item was already kept,
    so running --keep twice on the same find doesn't duplicate it.
    """
    piece = listing_to_piece(listing)
    items = list(wardrobe.get("items") or [])
    if any(i.get("id") == piece["id"] for i in items):
        return {"items": items}, False
    items.append(piece)
    updated = {"items": items}
    save_wardrobe(updated)
    return updated, True


def clear_saved_wardrobe() -> bool:
    """Delete the saved wardrobe. Returns True if there was one."""
    if SAVED_PATH.exists():
        SAVED_PATH.unlink()
        return True
    return False
