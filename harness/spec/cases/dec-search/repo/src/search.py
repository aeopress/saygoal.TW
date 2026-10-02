"""Catalog search behind GET /search.

search(query) returns catalog indexes, best match first. Matching is
case-insensitive, every query term must occur in the listing (AND), listings
rank by how many times the terms occur in total, and ties keep catalog order.
"""
import re

from src.corpus import CATALOG


def tokenize(text):
    # words only: punctuation and symbols never match a query term
    return re.findall(r"[a-z0-9]+", text.lower())


def search(query, catalog=CATALOG):
    terms = tokenize(query)
    if not terms:
        return []
    scored = []
    for i, listing in enumerate(catalog):
        # naive: re-tokenizes every listing on every request, no index, no cache
        tokens = tokenize(listing)
        counts = [tokens.count(t) for t in terms]
        if all(counts):
            scored.append((-sum(counts), i))
    scored.sort()
    return [i for _, i in scored]
