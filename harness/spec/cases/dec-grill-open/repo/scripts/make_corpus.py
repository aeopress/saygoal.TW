"""Write the reference corpus the memory benchmark indexes: 40 text files of
about 1 MB each, generated from a fixed seed so every run measures the same
input. Does nothing if the corpus is already complete."""
import random
import sys
from pathlib import Path

FILES = 40
WORDS_PER_FILE = 170_000
VOCAB = [f"w{i:05d}" for i in range(20_000)]


def main(out):
    out = Path(out)
    if len(list(out.glob("*.txt"))) == FILES:
        return
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(42)
    for n in range(FILES):
        words = (rng.choice(VOCAB) for _ in range(WORDS_PER_FILE))
        (out / f"doc{n:03d}.txt").write_text(" ".join(words))


if __name__ == "__main__":
    main(sys.argv[1])
