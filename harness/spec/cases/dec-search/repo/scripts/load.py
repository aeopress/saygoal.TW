"""Load driver for GET /search.

Replays a fixed mix of 200 production-shaped queries against the WSGI app
in-process, one request at a time, and reports latency percentiles. Running
in-process keeps socket overhead out of the numbers, so they measure the
handler. Exits non-zero if any request does not return 200.
"""
import random
import sys
import time
from urllib.parse import urlencode
from wsgiref.util import setup_testing_defaults

from src.app import app
from src.corpus import WORDS

REQUESTS = 200


def main():
    rng = random.Random(1)
    queries = [
        " ".join(rng.choice(WORDS) for _ in range(rng.randint(1, 2)))
        for _ in range(REQUESTS)
    ]
    times = []
    for q in queries:
        environ = {}
        setup_testing_defaults(environ)
        environ.update(REQUEST_METHOD="GET", PATH_INFO="/search",
                       QUERY_STRING=urlencode({"q": q}))
        status = []
        t0 = time.perf_counter()
        b"".join(app(environ, lambda s, headers: status.append(s)))
        times.append((time.perf_counter() - t0) * 1000)
        if not status[0].startswith("200"):
            sys.exit(f"GET /search?q={q!r} returned {status[0]}")
    times.sort()
    p95 = times[int(len(times) * 0.95) - 1]
    p99 = times[int(len(times) * 0.99) - 1]
    print(f"requests={len(times)}  p95={p95:.0f}ms  p99={p99:.0f}ms")


if __name__ == "__main__":
    main()
