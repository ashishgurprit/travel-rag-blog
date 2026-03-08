# tests/test_destination_detector.py
import pytest


def test_detects_japan_from_tokyo():
    from backend.rag.destination_detector import detect_destination
    assert detect_destination("best ramen in Tokyo") == "japan"


def test_detects_japan_from_ramen():
    from backend.rag.destination_detector import detect_destination
    assert detect_destination("Where can I find authentic ramen?") == "japan"


def test_detects_italy_from_amalfi():
    from backend.rag.destination_detector import detect_destination
    assert detect_destination("Amalfi coast hotels in summer") == "italy"


def test_detects_turkey_from_cappadocia():
    from backend.rag.destination_detector import detect_destination
    assert detect_destination("Cappadocia hot air balloon sunrise") == "turkey"


def test_detects_south_korea_from_busan():
    from backend.rag.destination_detector import detect_destination
    assert detect_destination("Busan seafood market") == "south_korea"


def test_detects_thailand_from_bangkok():
    from backend.rag.destination_detector import detect_destination
    assert detect_destination("Floating markets Bangkok") == "thailand"


def test_returns_unknown_for_no_match():
    from backend.rag.destination_detector import detect_destination
    assert detect_destination("best beaches in Europe") == "unknown"


def test_case_insensitive():
    from backend.rag.destination_detector import detect_destination
    assert detect_destination("TOKYO ramen guide") == "japan"
    assert detect_destination("SEOUL street food") == "south_korea"


def test_detects_kpop_as_south_korea():
    from backend.rag.destination_detector import detect_destination
    assert detect_destination("k-pop concerts Seoul") == "south_korea"
