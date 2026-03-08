"""Contextual affiliate link router.

Scans answer text for the first matching affiliate keyword and returns
a single affiliate link. Never returns more than one link.
"""

from backend.affiliate.rules import AFFILIATE_RULES
from backend.config import settings


def _build_url(program: str) -> str:
    if program == "booking":
        return f"https://www.booking.com/?aid={settings.booking_affiliate_id}"
    if program == "klook":
        return f"https://www.klook.com/?aff={settings.klook_affiliate_id}"
    if program == "wise":
        return f"https://wise.com/invite/{settings.wise_affiliate_id}"
    return ""


def route_affiliate(answer_text: str) -> dict | None:
    """Return the first matching affiliate program for the given answer text.

    Returns {program, url, cta} or None if no keywords matched.
    """
    lowered = answer_text.lower()
    for rule in AFFILIATE_RULES:
        for keyword in rule["keywords"]:
            if keyword in lowered:
                return {
                    "program": rule["program"],
                    "url": _build_url(rule["program"]),
                    "cta": rule["cta"],
                }
    return None
