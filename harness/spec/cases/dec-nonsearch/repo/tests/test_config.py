import pytest
from src.config import parse_config

def test_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        parse_config("does/not/exist.json")
