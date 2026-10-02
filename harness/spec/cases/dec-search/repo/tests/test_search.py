import json
import re

import pytest

from src.app import app
from src.corpus import CATALOG as FULL_CATALOG
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


def _full_scan(query, catalog):
    # Independent reference for the documented semantics, kept deliberately
    # slow and obvious: word match ignoring case, every term required,
    # rank by total occurrences, ties in catalog order.
    word = re.compile(r"[a-z0-9]+")
    terms = word.findall(query.lower())
    if not terms:
        return []
    hits = []
    for i, listing in enumerate(catalog):
        words = word.findall(listing.lower())
        counts = [words.count(t) for t in terms]
        if all(counts):
            hits.append((-sum(counts), i))
    return [i for _, i in sorted(hits)]


@pytest.mark.parametrize("query", ["cable", "Charger CASE", "omega omega", "lamp, stand!"])
def test_default_catalog_ranking_matches_a_full_scan(query):
    # Goes through the default catalog, the path GET /search uses.
    assert search(query) == _full_scan(query, FULL_CATALOG)


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
