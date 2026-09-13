"""Reporting service aggregating billing and the catalog."""

from app.services.billing import subtotal


def cheap_items(items, limit=10):
    return [item for item in items if item.get("price", 0) <= limit]


def summary(items):
    total = subtotal(items)
    return {"count": len(items), "total": round(total, 2), "cheap": len(cheap_items(items))}


def biggest(items):
    if not items:
        return None
    return max(items, key=lambda item: item["price"])
