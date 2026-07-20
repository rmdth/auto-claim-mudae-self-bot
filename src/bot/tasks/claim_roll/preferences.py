from enum import StrEnum
from typing import Any

from src.bot.shared.domain import ClaimMethod
from src.bot.tasks.claim_roll.domain import PrefContext
from src.bot.tasks.claim_roll.logic import time_till_next_claim
from src.bot.tasks.shared.domain import Preference
from src.ui import update_log_debug


class ClaimRollsPreferences(StrEnum):
    ONLY_WISHED_ROLL = "only_wished_roll"  # This one should be priotized and exclude the other ones, since the should claim functions and the other prefences work as Any. Since its supossed to be TUI maybe a map that relates between certain preferences to exclude them
    CLAIM_THRESHOLD = "claim_threshold"
    USE_RESETS_ON_WISH_ONLY = "use_resets_on_wish_only"
    AUTO_LAST_CLAIM = "auto_last_claim"


def is_wished(ctx: PrefContext, input_data: dict[str, Any]) -> bool:
    update_log_debug(f"is_wished: ctx.wished={ctx.wished}")
    return ctx.wished


def is_claim_threshold(ctx: PrefContext, input_data: dict[str, Any]) -> bool:
    out = ctx.r.kakera_value >= input_data["claim_threshold"]
    update_log_debug(
        f"is_claim_threshold: ctx.r.kakera_value={ctx.r.kakera_value} input_data={input_data} ctx.wished={ctx.wished} out={out}"
    )
    return out


def is_last_claim(ctx: PrefContext, input_data: dict[str, Any]) -> bool:
    time = time_till_next_claim(ctx.minute_reset, ctx.shifthour)
    out = time <= 3600
    update_log_debug(
        f"is_last_claim: ctx.minute_reset={ctx.minute_reset} ctx.shifthour={ctx.shifthour} out={time}"
    )
    return out


claim_roll_preferences = (
    Preference(
        ClaimRollsPreferences.USE_RESETS_ON_WISH_ONLY,
        is_wished,
        input_data={},
        preference_data={
            "claim_method": frozenset({ClaimMethod.CLAIM, ClaimMethod.RESET})
        },
    ),
    Preference(
        ClaimRollsPreferences.CLAIM_THRESHOLD,
        is_claim_threshold,
        input_data={"claim_threshold": 0},
        preference_data={"claim_method": frozenset({ClaimMethod.CLAIM})},
    ),
    Preference(
        ClaimRollsPreferences.AUTO_LAST_CLAIM,
        is_last_claim,
        input_data={},
        preference_data={"claim_method": frozenset({ClaimMethod.CLAIM})},
    ),
)
