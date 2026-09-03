"""Toy indexer: loads every document into memory before indexing."""
import sys


def load_all(paths):
    return [open(p, "rb").read() for p in paths]


def build_index(docs):
    index = {}
    for i, d in enumerate(docs):
        for tok in d.split():
            index.setdefault(tok, []).append(i)
    return index


if __name__ == "__main__":
    docs = load_all(sys.argv[1:])
    print(len(build_index(docs)))
