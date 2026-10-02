from src.indexer import build_index, load_all


def test_index_maps_each_token_to_the_documents_containing_it():
    index = build_index([b"red blue", b"blue green", b"blue"])
    assert index[b"blue"] == [0, 1, 2]
    assert index[b"red"] == [0]
    assert index[b"green"] == [1]


def test_repeated_token_lists_the_document_each_time():
    assert build_index([b"a a b"])[b"a"] == [0, 0]


def test_load_all_reads_files_in_order(tmp_path):
    paths = []
    for name, text in [("x.txt", b"one"), ("y.txt", b"two")]:
        p = tmp_path / name
        p.write_bytes(text)
        paths.append(str(p))
    assert load_all(paths) == [b"one", b"two"]
