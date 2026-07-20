from re import compile as re_compile

from src.bot.shared.domain import ClaimMethod, KakeraMessage
from src.bot.tasks.claim_kakera.domain import PrefContext
from src.bot.tasks.shared.domain import Preference

_KAKERA_PRIORITY: dict[str, int] = {
    "kakera": 1,
    "kakeraP": 2,
    "kakeraT": 3,
    "kakeraG": 4,
    "kakeraY": 5,
    "kakeraO": 7,
    "kakeraR": 8,
    "kakeraW": 9,
    "kakeraL": 10,
    "kakeraD": 10,
    "kakeraC": 12,
}

_KAKERA_DK_CONFIRMATION_PATTERN = re_compile(
    r"\*\*\+\d+\*\*<:kakera:469835869059153940>kakera"
)


def is_dk_confirmation(content: str) -> bool:
    return bool(_KAKERA_DK_CONFIRMATION_PATTERN.findall(content))


def get_kakera_claim_cost(
    base_cost: int, color: str, key_amount: int, on_owned_char: bool
) -> int:
    cost = base_cost
    if color == "kakeraP":  # There are new colors to consider
        cost = 0
    elif key_amount > 9 and on_owned_char:
        cost = cost // 2
    return cost


def should_claim(
    claim_method: ClaimMethod,
    kakera_message: KakeraMessage,
    preferences: tuple[Preference, ...],
    is_wished: bool,
) -> bool:
    ctx = PrefContext(
        kakera_message,
        is_wished,
    )
    return any(
        (
            pref.conditional(ctx, pref.input_data)
            for pref in preferences
            if claim_method in pref.preference_data["claim_method"]
        ),
    )
