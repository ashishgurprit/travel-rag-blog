"""Affiliate program rules — keyword → program mapping in priority order."""

AFFILIATE_RULES: list[dict] = [
    {
        "keywords": [
            "hotel", "hostel", "ryokan", "guesthouse", "accommodation",
            "stay", "airbnb", "lodge",
        ],
        "program": "booking",
        "cta": "Find accommodation on Booking.com →",
    },
    {
        "keywords": [
            "tour", "activity", "activities", "experience", "ticket",
            "excursion", "day trip", "day-trip",
        ],
        "program": "klook",
        "cta": "Book tours on Klook →",
    },
    {
        "keywords": [
            "money", "currency", "exchange", "forex", "transfer",
            "send money", "bank", "atm", "cash",
        ],
        "program": "wise",
        "cta": "Transfer money with Wise →",
    },
]
