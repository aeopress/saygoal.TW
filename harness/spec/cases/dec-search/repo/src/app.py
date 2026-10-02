"""HTTP entry point (WSGI). GET /search?q=<terms> returns the top 20 listings
as JSON: {"results": [{"id": <index>, "text": <listing>}, ...]}."""
import json
from urllib.parse import parse_qs

from src.corpus import CATALOG
from src.search import search


def app(environ, start_response):
    if environ.get("REQUEST_METHOD") != "GET" or environ.get("PATH_INFO") != "/search":
        start_response("404 Not Found", [("Content-Type", "application/json")])
        return [b'{"error": "not found"}']
    query = parse_qs(environ.get("QUERY_STRING", "")).get("q", [""])[0]
    ids = search(query)[:20]
    body = json.dumps({"results": [{"id": i, "text": CATALOG[i]} for i in ids]})
    start_response("200 OK", [("Content-Type", "application/json")])
    return [body.encode()]


if __name__ == "__main__":
    from wsgiref.simple_server import make_server

    make_server("127.0.0.1", 8000, app).serve_forever()
