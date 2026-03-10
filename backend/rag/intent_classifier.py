"""Claude intent classifier — routes queries to RAG or Trip Planner.

A single fast Claude call classifies each query into:
  - RAG:       experiences, places, food, activities, culture, what-to-do
  - LOGISTICS: visa, transport, costs, entry/exit, itinerary planning
  - HYBRID:    needs both (e.g. "plan my 7-day Tokyo trip with budget")

Also extracts lightweight entities (destination, travel_dates, passport)
to seed the trip planner session without a second round trip.

Uses claude-haiku-4-5 for speed and cost efficiency — classification
only needs ~50 tokens output.
"""

import json
import re
from dataclasses import dataclass, field
from typing import Optional

import anthropic

from backend.config import settings

_CLASSIFIER_MODEL = "claude-haiku-4-5-20251001"
_MAX_TOKENS = 120

_CLASSIFY_PROMPT = """\
You are a travel query classifier. Classify the user's query and extract entities.

Categories:
- RAG: Questions about experiences, places, food, activities, sights, culture, \
nightlife, hidden gems, recommendations, reviews. ("What's the best ramen in Tokyo?")
- LOGISTICS: Questions about visa requirements, transport modes, costs/budget, \
entry/exit points, flight routing, travel insurance, currency, tipping, \
how to get somewhere, itinerary scheduling. ("How do I get from Tokyo to Kyoto?")
- HYBRID: Requires both experience content AND logistics. \
("Plan my 7-day Tokyo trip with budget breakdown")

Respond with ONLY valid JSON:
{{
  "intent": "RAG" | "LOGISTICS" | "HYBRID",
  "destination": "<destination or null>",
  "cities": ["<city>"],
  "travel_dates": "<dates or null>",
  "passport": "<nationality or null>",
  "budget_tier": "budget" | "mid" | "luxury" | null
}}

Query: {query}"""


@dataclass
class IntentResult:
    intent: str                          # "RAG" | "LOGISTICS" | "HYBRID"
    destination: Optional[str] = None
    cities: list[str] = field(default_factory=list)
    travel_dates: Optional[str] = None
    passport: Optional[str] = None
    budget_tier: Optional[str] = None

    @property
    def needs_rag(self) -> bool:
        return self.intent in ("RAG", "HYBRID")

    @property
    def needs_logistics(self) -> bool:
        return self.intent in ("LOGISTICS", "HYBRID")


class IntentClassifier:
    """Classifies travel queries using a fast Claude Haiku call.

    Usage::

        classifier = IntentClassifier()
        result = classifier.classify("best ramen in Tokyo")
        # IntentResult(intent='RAG', destination='japan', cities=['tokyo'])

        result = classifier.classify("how do I get a Japan visa from Australia")
        # IntentResult(intent='LOGISTICS', destination='japan', passport='AU')
    """

    def __init__(self) -> None:
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    def classify(self, query: str) -> IntentResult:
        """Classify a query. Falls back to RAG on any error."""
        try:
            prompt = _CLASSIFY_PROMPT.format(query=query.strip())
            message = self._client.messages.create(
                model=_CLASSIFIER_MODEL,
                max_tokens=_MAX_TOKENS,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = message.content[0].text.strip()
            return _parse_result(raw)
        except Exception as e:
            print(f"[intent_classifier] Classification failed: {e} — defaulting to RAG")
            return IntentResult(intent="RAG")


def _parse_result(raw: str) -> IntentResult:
    """Parse JSON response from Claude into IntentResult."""
    # Strip markdown code fences if present
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"\s*```$", "", raw, flags=re.MULTILINE)

    try:
        data = json.loads(raw.strip())
    except json.JSONDecodeError:
        return IntentResult(intent="RAG")

    intent = data.get("intent", "RAG")
    if intent not in ("RAG", "LOGISTICS", "HYBRID"):
        intent = "RAG"

    return IntentResult(
        intent=intent,
        destination=data.get("destination"),
        cities=data.get("cities") or [],
        travel_dates=data.get("travel_dates"),
        passport=data.get("passport"),
        budget_tier=data.get("budget_tier"),
    )
