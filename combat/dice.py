import random
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator, Optional, Tuple

_fallback_rng = random.Random()
_active_rng: ContextVar[Optional[random.Random]] = ContextVar("avasim_active_rng", default=None)


def current_rng() -> random.Random:
    """Return the RNG scoped to the active run, or the legacy fallback RNG."""
    return _active_rng.get() or _fallback_rng


@contextmanager
def rng_scope(rng: random.Random) -> Iterator[random.Random]:
    """Use *rng* for all dice rolls in the current execution context."""
    token = _active_rng.set(rng)
    try:
        yield rng
    finally:
        _active_rng.reset(token)

def set_seed(seed: Optional[int] = None) -> None:
    """Seed the legacy fallback RNG used by direct engine calls and fixtures."""
    _fallback_rng.seed(seed)

def roll_2d10() -> Tuple[int, Tuple[int, int]]:
    rng = current_rng()
    d1 = rng.randint(1, 10)
    d2 = rng.randint(1, 10)
    return d1 + d2, (d1, d2)

def roll_1d2() -> int:
    return current_rng().randint(1, 2)

def roll_1d3() -> int:
    return current_rng().randint(1, 3)

def roll_1d4() -> int:
    return current_rng().randint(1, 4)

def roll_1d6() -> int:
    return current_rng().randint(1, 6)
