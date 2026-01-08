import random
from typing import Tuple

def roll_2d10() -> Tuple[int, Tuple[int, int]]:
    d1 = random.randint(1, 10)
    d2 = random.randint(1, 10)
    return d1 + d2, (d1, d2)

def roll_1d2() -> int:
    return random.randint(1, 2)

def roll_1d3() -> int:
    return random.randint(1, 3)

def roll_1d4() -> int:
    return random.randint(1, 4)

def roll_1d6() -> int:
    return random.randint(1, 6)
