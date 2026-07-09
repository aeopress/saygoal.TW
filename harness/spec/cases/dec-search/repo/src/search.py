def search(query):
    # naive: re-tokenizes every request, no cache
    tokens = tokenize(query)
    return _scan(tokens)

def tokenize(q):
    return q.lower().split()

def _scan(tokens):
    return []
