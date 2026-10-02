import json

from src.app import app
from src.search import search

CATALOG = [
    "Cable charger cable",        # 0
    "charger case",               # 1
    "cable CABLE cable adapter",  # 2
    "lamp stand",                 # 3
]


def test_case_insensitive():
    assert set(search("CABLE", CATALOG)) == {0, 2}


def test_every_term_must_match():
    assert search("cable charger", CATALOG) == [0]


def test_ranked_by_term_occurrences_then_catalog_order():
    assert search("cable", CATALOG) == [2, 0]
    assert search("charger", CATALOG) == [0, 1]


def test_empty_query_returns_nothing():
    assert search("", CATALOG) == []
    assert search("   ", CATALOG) == []


def _get(path, query=""):
    status = []
    body = b"".join(app(
        {"REQUEST_METHOD": "GET", "PATH_INFO": path, "QUERY_STRING": query},
        lambda s, headers: status.append(s),
    ))
    return status[0], body


def test_endpoint_returns_top_20_as_json():
    status, body = _get("/search", "q=cable")
    assert status.startswith("200")
    results = json.loads(body)["results"]
    assert 0 < len(results) <= 20
    assert all("cable" in r["text"] for r in results)


def test_unknown_path_is_404():
    status, _ = _get("/nope")
    assert status.startswith("404")
