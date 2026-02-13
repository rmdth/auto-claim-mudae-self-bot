from typing import Callable

from src.core.models import KakeraUnit, Roll


def default(
    unit: KakeraUnit | Roll,
    min_kakera: int,
    is_roll_threshold: bool,
    available_claim: str,
) -> bool:
    """
    Unit wished is claimed whenever with whatever.
    Unit not wished is claimed only with claim
    Kakera is claimed whenever
    Roll is claimed if threshold and meets min kakera
    """
    if unit.wished:
        return True
    elif not available_claim == "claim":  # Means is a reset
        return False  # Is not wished and is a reset.
    elif isinstance(unit, KakeraUnit):
        return True
    elif min_kakera <= unit.kakera_value:
        return True
    return is_roll_threshold


def decide_mode(
    mode: str,
) -> Callable[[Roll | KakeraUnit, int, bool, str], bool]:
    match mode:
        case _:
            return default
