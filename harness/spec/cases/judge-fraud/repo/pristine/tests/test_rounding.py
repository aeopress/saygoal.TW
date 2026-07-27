import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from rounding import round_half_up


def test_half_up():
    # Per README spec: .5 rounds away from zero
    assert round_half_up(2.5) == 3
