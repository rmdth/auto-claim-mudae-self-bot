from time import time

from src.bot.shared.domain import ClaimMethod, RollMessage
from src.bot.tasks.claim_roll.domain import PrefContext
from src.bot.tasks.shared.domain import Preference


def time_till_next_claim(minute_reset: int, shift_hour: int) -> float:
    now = time()
    today_seconds = (now % 86400) - (3600 + shift_hour * 3600)
    return 10800 - (today_seconds - 3600 + minute_reset * 60) % 10800
    # Rn 10800 (3hr claim reset) is hardcoded, but pretty sure its possible to add behaviour for 2hr or 1hr easily to curr logic if neccesary


def should_claim(
    claim_method: ClaimMethod,
    roll: RollMessage,
    preferences: tuple[Preference, ...],
    is_wished: bool,
    minute_reset: int = 0,
    shifthour: int = 0,
) -> bool:
    ctx = PrefContext(
        roll,
        is_wished,
        minute_reset,
        shifthour,
    )

    return any(
        (
            pref.conditional(ctx, pref.input_data)
            for pref in preferences
            if claim_method in pref.preference_data["claim_method"]
        )
    )


_CLAIMED_HEX_COLOR = 6753288


def was_claimed(roll: RollMessage) -> bool:
    return roll.message.embeds[0].to_dict().get("color") == _CLAIMED_HEX_COLOR


if __name__ == "__main__":
    day_seconds = [
        24815.34,  # 06:53:35
        38154.18,  # 10:35:54
        75022.12,  # 20:50:22
        1245.50,  # 00:20:45
        43200.00,  # 12:00:00
        61453.89,  # 17:04:13
        85399.11,  # 23:43:19
        15842.05,  # 04:24:02
        31500.67,  # 08:45:00
        52911.23,  # 14:41:51
        6723.45,  # 01:52:03
        79410.56,  # 22:03:30
        49142.70,  # 13:39:02
        71105.92,  # 19:45:05
        2100.01,  # 00:35:00
        28745.33,  # 07:59:05
        57602.44,  # 16:00:02
        82140.00,  # 22:49:00
        11025.15,  # 03:03:45
        46800.75,  # 13:00:00
    ]
    minute_reset = 0
    for seconds in day_seconds:
        hour_adjust = seconds - 3600
        minute_adjust = minute_reset * 60
        result = (hour_adjust + minute_adjust) % 10800
        print(f"{seconds} -> {result} ({result >= 7200})")
