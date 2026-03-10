"""Claude-powered trip planning chatbot for logistics queries.

Handles visa requirements, transport modes, costs/budget, entry/exit points,
itinerary planning, and currency/money transfer questions.

Uses:
- Redis for multi-turn session memory (24h TTL)
- Tavily for live data (current visa fees, transport prices, advisories)
- Claude claude-sonnet-4-6 for reasoning + structured logistics answers
- Affiliate injection for accommodation/activities/currency triggers

Session state stored in Redis as:
    trip_session:{session_id} -> JSON with destination, dates, passport,
                                  budget_tier, confirmed_cities, history[]
"""

from __future__ import annotations

import json
import logging
from typing import AsyncGenerator, Optional

import anthropic
import redis

from backend.affiliate.router import route_affiliate
from backend.config import settings
from backend.rag.web_search import search_web

logger = logging.getLogger(__name__)

_SESSION_TTL = 86400  # 24 hours
_SESSION_PREFIX = "trip_session:"
_MAX_HISTORY_TURNS = 10  # prevent context overflow

# Affiliate triggers specific to logistics context
_LOGISTICS_AFFILIATE_TRIGGERS = {
    "accommodation": ("hotel", "hostel", "stay", "accommodation", "airbnb"),
    "activities": ("tour", "activity", "klook", "attraction", "ticket"),
    "currency": ("currency", "money transfer", "wise", "exchange rate", "send money"),
    "transport": ("train", "shinkansen", "bus", "ferry", "flight", "transfer"),
}

_SYSTEM_PROMPT = """\
You are a practical trip planning assistant specialising in Japan, Thailand, Italy, \
Turkey, and South Korea.

You help travellers with logistics: visa requirements, entry/exit rules, transport \
between cities, estimated costs, itinerary timing, currency exchange, and travel insurance.

Guidelines:
- Be specific with numbers (costs, durations, distances) when sources provide them
- Cite sources inline as [Source N] when answering
- Acknowledge when information may be outdated (visa rules change) and suggest official sources
- Build on previous conversation context — don't ask for information the user already gave
- For itinerary questions, produce a day-by-day structure
- Suggest ONE relevant action at the end (booking, currency transfer, or official gov link)

Current session context:
{session_context}
"""

_NO_COVERAGE_MSG = (
    "I don't have logistics information for this destination yet. "
    "I can help with Japan, Thailand, Italy, Turkey, or South Korea."
)


class TripPlanner:
    """Multi-turn Claude logistics chatbot with Redis session memory.

    Usage::

        planner = TripPlanner()
        async for event in planner.plan("how do I get a Japan visa from Australia",
                                         session_id="user123"):
            print(event)
    """

    def __init__(self) -> None:
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self._redis: redis.Redis | None = None
        self._connect_redis()

    def _connect_redis(self) -> None:
        try:
            self._redis = redis.Redis.from_url(settings.redis_url, decode_responses=True)
            self._redis.ping()
        except Exception as e:
            logger.warning("Redis unavailable for trip planner sessions: %s", e)
            self._redis = None

    # ── Session management ──────────────────────────────────────────────────

    def _session_key(self, session_id: str) -> str:
        return f"{_SESSION_PREFIX}{session_id}"

    def load_session(self, session_id: str) -> dict:
        """Load session state from Redis, or return empty session."""
        if self._redis is None:
            return _empty_session()
        try:
            raw = self._redis.get(self._session_key(session_id))
            if raw:
                return json.loads(raw)
        except Exception as e:
            logger.warning("Failed to load trip session %s: %s", session_id, e)
        return _empty_session()

    def save_session(self, session_id: str, session: dict) -> None:
        """Persist session state to Redis with 24h TTL."""
        if self._redis is None:
            return
        try:
            # Trim history to prevent unbounded growth
            if len(session.get("history", [])) > _MAX_HISTORY_TURNS * 2:
                session["history"] = session["history"][-(_MAX_HISTORY_TURNS * 2):]
            self._redis.set(
                self._session_key(session_id),
                json.dumps(session),
                ex=_SESSION_TTL,
            )
        except Exception as e:
            logger.warning("Failed to save trip session %s: %s", session_id, e)

    def update_session_from_intent(self, session: dict, intent_result) -> None:
        """Seed session with entities extracted by the intent classifier."""
        if intent_result.destination and not session.get("destination"):
            session["destination"] = intent_result.destination
        if intent_result.travel_dates and not session.get("travel_dates"):
            session["travel_dates"] = intent_result.travel_dates
        if intent_result.passport and not session.get("passport"):
            session["passport"] = intent_result.passport
        if intent_result.budget_tier and not session.get("budget_tier"):
            session["budget_tier"] = intent_result.budget_tier
        if intent_result.cities:
            existing = set(session.get("confirmed_cities", []))
            session["confirmed_cities"] = list(existing | set(intent_result.cities))

    # ── Main planning pipeline ──────────────────────────────────────────────

    async def plan(
        self,
        query: str,
        session_id: str,
        intent_result=None,
    ) -> AsyncGenerator[dict, None]:
        """Stream a logistics answer as SSE-style event dicts.

        Event types: 'text' | 'sources' | 'disclosure' | 'affiliate'

        Args:
            query:         User's logistics question.
            session_id:    Session identifier (per user/conversation).
            intent_result: Optional IntentResult from classifier — seeds session.
        """
        session = self.load_session(session_id)

        # Seed session with any entities extracted by the classifier
        if intent_result is not None:
            self.update_session_from_intent(session, intent_result)

        # Fetch live logistics data from Tavily
        search_query = _enrich_query(query, session)
        web_chunks = search_web(search_query, max_results=5)

        # Build session context string for the system prompt
        session_context = _format_session_context(session)

        # Build conversation messages (history + current query)
        messages = _build_messages(session, query, web_chunks)

        system = _SYSTEM_PROMPT.format(session_context=session_context)

        # Stream Claude response
        full_text_parts: list[str] = []
        try:
            with self._client.messages.stream(
                model="claude-sonnet-4-6",
                max_tokens=1500,
                system=system,
                messages=messages,
            ) as stream:
                for token in stream.text_stream:
                    full_text_parts.append(token)
                    yield {"type": "text", "content": token}
        except Exception as e:
            logger.error("Trip planner Claude call failed: %s", e)
            yield {"type": "text", "content": "Sorry, I encountered an error. Please try again."}
            return

        full_text = "".join(full_text_parts)

        # Update session history
        session["history"].append({"role": "user", "content": query})
        session["history"].append({"role": "assistant", "content": full_text})
        self.save_session(session_id, session)

        # Emit sources
        if web_chunks:
            sources = [
                {
                    "title": c.get("title", ""),
                    "url": c.get("url", ""),
                    "source_type": "web",
                    "timestamp_seconds": 0,
                }
                for c in web_chunks
            ]
            yield {"type": "sources", "content": sources}

        # Affiliate injection
        affiliate = route_affiliate(full_text)
        if affiliate is None:
            affiliate = _logistics_affiliate(full_text)

        disclosure = (
            "This response may contain affiliate links. "
            "We may earn a commission at no cost to you."
        )

        if affiliate is not None:
            yield {"type": "affiliate", "content": affiliate}

        yield {"type": "disclosure", "content": disclosure}


# ── Helpers ─────────────────────────────────────────────────────────────────

def _empty_session() -> dict:
    return {
        "destination": None,
        "travel_dates": None,
        "passport": None,
        "budget_tier": None,
        "confirmed_cities": [],
        "history": [],
    }


def _enrich_query(query: str, session: dict) -> str:
    """Add destination/passport context to the Tavily search query."""
    parts = [query]
    if session.get("destination"):
        parts.append(session["destination"])
    if session.get("passport"):
        parts.append(f"for {session['passport']} passport holders")
    return " ".join(parts)


def _format_session_context(session: dict) -> str:
    """Convert session dict to a readable string for the system prompt."""
    lines = []
    if session.get("destination"):
        lines.append(f"Destination: {session['destination']}")
    if session.get("travel_dates"):
        lines.append(f"Travel dates: {session['travel_dates']}")
    if session.get("passport"):
        lines.append(f"Passport/nationality: {session['passport']}")
    if session.get("budget_tier"):
        lines.append(f"Budget tier: {session['budget_tier']}")
    if session.get("confirmed_cities"):
        lines.append(f"Confirmed cities: {', '.join(session['confirmed_cities'])}")
    if not lines:
        return "No session context yet."
    return "\n".join(lines)


def _build_messages(session: dict, query: str, web_chunks: list[dict]) -> list[dict]:
    """Build the messages list: history + current query with web context."""
    messages: list[dict] = []

    # Prior conversation turns (trimmed to last N)
    history = session.get("history", [])[-(_MAX_HISTORY_TURNS * 2):]
    messages.extend(history)

    # Current turn: inject web context into user message
    if web_chunks:
        context_parts = []
        for i, chunk in enumerate(web_chunks):
            title = chunk.get("title", "")
            url = chunk.get("url", "")
            context_parts.append(f"[Source {i+1}: {title} ({url})]\n{chunk['text']}")
        context = "\n\n".join(context_parts)
        content = f"Live information:\n{context}\n\nQuestion: {query}"
    else:
        content = query

    messages.append({"role": "user", "content": content})
    return messages


def _logistics_affiliate(text: str) -> dict | None:
    """Scan logistics response for affiliate triggers not in the main rules."""
    from backend.config import settings as _settings

    lowered = text.lower()

    # accommodation → booking.com
    if any(kw in lowered for kw in _LOGISTICS_AFFILIATE_TRIGGERS["accommodation"]):
        return {
            "program": "booking",
            "url": f"https://www.booking.com/?aid={_settings.booking_affiliate_id}",
            "cta": "Find hotels for your trip on Booking.com",
        }

    # activities → klook
    if any(kw in lowered for kw in _LOGISTICS_AFFILIATE_TRIGGERS["activities"]):
        return {
            "program": "klook",
            "url": f"https://www.klook.com/?aff={_settings.klook_affiliate_id}",
            "cta": "Book tours and activities on Klook",
        }

    # currency / money transfer → wise
    if any(kw in lowered for kw in _LOGISTICS_AFFILIATE_TRIGGERS["currency"]):
        return {
            "program": "wise",
            "url": f"https://wise.com/invite/{_settings.wise_affiliate_id}",
            "cta": "Transfer money abroad with Wise",
        }

    return None
