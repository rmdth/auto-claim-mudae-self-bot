from enum import StrEnum
from typing import Any

from src.bot.shared.domain import ClaimMethod
from src.bot.tasks.claim_kakera.domain import PrefContext
from src.bot.tasks.shared.domain import Preference


class ClaimRollsPreferences(StrEnum):
    ONLY_WISHED_KAKERA = (
        "only_wished_kakera"  # the same thing with claim_roll preferences
    )
    USE_RESETS_ON_WISH_ONLY = "use_resets_on_wish_only"
    ALWAYS_CLAIM = "always_claim"


def is_wished(ctx: PrefContext, input_data: dict[str, Any]) -> bool:
    return ctx.wished


def always_claim(ctx: PrefContext, input_data: dict[str, Any]) -> bool:
    return True


claim_kakera_preferences = (
    Preference(
        ClaimRollsPreferences.ONLY_WISHED_KAKERA,
        is_wished,
        input_data={},
        preference_data={"claim_method": frozenset({ClaimMethod.CLAIM})},
    ),
    Preference(
        ClaimRollsPreferences.USE_RESETS_ON_WISH_ONLY,
        is_wished,
        input_data={},
        preference_data={"claim_method": frozenset({ClaimMethod.RESET})},
    ),
    Preference(
        ClaimRollsPreferences.ALWAYS_CLAIM,
        always_claim,
        input_data={},
        preference_data={
            "claim_method": frozenset({ClaimMethod.CLAIM, ClaimMethod.RESET})
        },
    ),
)
