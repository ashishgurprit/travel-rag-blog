"""NLP destination detector using keyword matching.

Detects which of the 5 supported destinations a query refers to.
Returns 'unknown' if no destination can be determined.
"""

_DESTINATION_KEYWORDS: dict[str, list[str]] = {
    "japan": [
        "japan", "japanese", "tokyo", "kyoto", "osaka", "hiroshima", "fuji",
        "ramen", "sushi", "shinkansen", "jr pass", "jrpass", "nara", "hokkaido",
    ],
    "thailand": [
        "thailand", "thai", "bangkok", "phuket", "chiang mai", "chiangmai",
        "ko samui", "koh samui", "pad thai", "tuk tuk", "tuk-tuk", "pattaya",
    ],
    "italy": [
        "italy", "italian", "rome", "florence", "venice", "milan", "amalfi",
        "tuscany", "colosseum", "naples", "sicily", "cinque terre",
    ],
    "turkey": [
        "turkey", "turkish", "istanbul", "ankara", "cappadocia", "ephesus",
        "pamukkale", "bodrum", "antalya", "baklava", "kebab",
    ],
    "south_korea": [
        "korea", "korean", "seoul", "busan", "jeju", "k-pop", "kpop",
        "hanbok", "bibimbap", "incheon", "gwangju", "daegu",
    ],
}

_PRIORITY_ORDER = ["japan", "thailand", "italy", "turkey", "south_korea"]


def detect_destination(query: str) -> str:
    """Return the destination referenced in the query, or 'unknown'."""
    lowered = query.lower()
    for destination in _PRIORITY_ORDER:
        for keyword in _DESTINATION_KEYWORDS[destination]:
            if keyword in lowered:
                return destination
    return "unknown"
