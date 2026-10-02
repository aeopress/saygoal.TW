import json

import pytest
from src.config import parse_config

def test_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        parse_config("does/not/exist.json")

def test_valid_file_parses(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"debug": True, "port": 8080}))
    assert parse_config(str(path)) == {"debug": True, "port": 8080}
