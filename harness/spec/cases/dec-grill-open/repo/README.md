# indexer

Builds an inverted index (token → list of document numbers) over a set of
text files and prints how many distinct tokens it found.

    python3 -m src.indexer data/corpus/*.txt

`scripts/mem.sh` generates the reference corpus under `data/corpus/` (40
files, about 45 MB) on first run and prints the peak RSS of one indexer run
over it as `peak_rss_mb=<N>`. `uv run pytest -q` runs the tests.
