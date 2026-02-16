import random
from typing import Tuple, Optional

_rng = random.Random()

def set_seed(seed: Optional[int] = None) -> None:
    """Set the RNG seed for deterministic combat scenarios."""
    _rng.seed(seed)

def roll_2d10() -> Tuple[int, Tuple[int, int]]:
    d1 = _rng.randint(1, 10)
    d2 = _rng.randint(1, 10)
    return d1 + d2, (d1, d2)

def roll_1d2() -> int:
    return _rng.randint(1, 2)

def roll_1d3() -> int:
    return _rng.randint(1, 3)

def roll_1d4() -> int:
    return _rng.randint(1, 4)

def roll_1d6() -> int:
    return _rng.randint(1, 6)
