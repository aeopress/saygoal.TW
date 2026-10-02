"""The product catalog the search endpoint serves: 180,000 short listings,
generated deterministically so every run sees the same data."""
import random

WORDS = (
    "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu nu xi "
    "omicron pi rho sigma tau upsilon phi chi psi omega cable charger case "
    "adapter battery speaker headset monitor keyboard mouse stand lamp router "
    "drive hub dock webcam tripod mount bag sleeve filter"
).split()


def load_catalog(n=180000, seed=7):
    rng = random.Random(seed)
    return [
        " ".join(rng.choice(WORDS) for _ in range(rng.randint(8, 16)))
        for _ in range(n)
    ]


CATALOG = load_catalog()
