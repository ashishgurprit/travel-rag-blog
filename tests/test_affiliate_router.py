# tests/test_affiliate_router.py
import pytest
from unittest.mock import patch

import backend.affiliate.router  # pre-load so patch() can resolve the target
from backend.affiliate.router import route_affiliate


def test_hotel_mention_routes_to_booking():
    """Text mentioning 'hotel' returns Booking.com link."""
    with patch("backend.affiliate.router.settings") as mock_settings:
        mock_settings.booking_affiliate_id = "TEST_BOOKING_ID"
        mock_settings.klook_affiliate_id = "TEST_KLOOK_ID"
        mock_settings.wise_affiliate_id = "TEST_WISE_ID"
        result = route_affiliate("I recommend staying at a hotel in Kyoto near the station.")

    assert result is not None
    assert result["program"] == "booking"
    assert "TEST_BOOKING_ID" in result["url"]
    assert result["cta"] == "Find accommodation on Booking.com →"


def test_tour_mention_routes_to_klook():
    """Text mentioning 'tour' returns Klook link."""
    with patch("backend.affiliate.router.settings") as mock_settings:
        mock_settings.booking_affiliate_id = "B"
        mock_settings.klook_affiliate_id = "K123"
        mock_settings.wise_affiliate_id = "W"
        result = route_affiliate("Book a cooking class tour in Bangkok for an authentic experience.")

    assert result is not None
    assert result["program"] == "klook"
    assert "K123" in result["url"]


def test_money_mention_routes_to_wise():
    """Text mentioning currency exchange returns Wise link."""
    with patch("backend.affiliate.router.settings") as mock_settings:
        mock_settings.booking_affiliate_id = "B"
        mock_settings.klook_affiliate_id = "K"
        mock_settings.wise_affiliate_id = "WISE_REF_123"
        result = route_affiliate("Use Wise to exchange currency before your trip to avoid high ATM fees.")

    assert result is not None
    assert result["program"] == "wise"
    assert "WISE_REF_123" in result["url"]


def test_no_keyword_match_returns_none():
    """Text with no affiliate keywords returns None."""
    with patch("backend.affiliate.router.settings"):
        result = route_affiliate("The weather in Tokyo in April is very pleasant with cherry blossoms.")

    assert result is None


def test_only_first_matching_rule_returned():
    """When text matches multiple rules, only first (priority) rule returned."""
    with patch("backend.affiliate.router.settings") as mock_settings:
        mock_settings.booking_affiliate_id = "BOOKING"
        mock_settings.klook_affiliate_id = "KLOOK"
        mock_settings.wise_affiliate_id = "WISE"
        result = route_affiliate("Book a hotel room and also join a tour activity in Kyoto.")

    assert result is not None
    assert result["program"] == "booking"  # first rule wins


def test_case_insensitive_matching():
    """Keyword matching is case-insensitive."""
    with patch("backend.affiliate.router.settings") as mock_settings:
        mock_settings.booking_affiliate_id = "BID"
        mock_settings.klook_affiliate_id = "KID"
        mock_settings.wise_affiliate_id = "WID"
        result = route_affiliate("Find a HOTEL in TOKYO.")

    assert result is not None
    assert result["program"] == "booking"


def test_url_contains_affiliate_id():
    """Returned URL contains the correct affiliate ID."""
    with patch("backend.affiliate.router.settings") as mock_settings:
        mock_settings.booking_affiliate_id = "MY_BOOKING_AFF"
        mock_settings.klook_affiliate_id = "K"
        mock_settings.wise_affiliate_id = "W"
        result = route_affiliate("Great accommodation options near Fushimi Inari.")

    assert "booking.com" in result["url"]
    assert "MY_BOOKING_AFF" in result["url"]
