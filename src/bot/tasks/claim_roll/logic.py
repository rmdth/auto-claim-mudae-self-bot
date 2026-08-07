from time import time

from src.bot.shared.domain import ClaimMethod, RollMessage
from src.bot.tasks.claim_roll.domain import PrefContext
from src.bot.tasks.shared.domain import Preference


def time_till_next_claim(minute_reset: int, shift_hour: int) -> float:
    now = time() % 86400
    hour_adjust = now - 3600 - (3600 * shift_hour)
    minute_adjust = minute_reset * 60
    time_till = 10800 - (hour_adjust - minute_adjust) % 10800
    return time_till
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

    def test(seconds: float, shift_hour: int, minute_reset: int) -> bool:
        hour_adjust = seconds - 3600 - (3600 * shift_hour)
        minute_adjust = minute_reset * 60
        result = 10800 - (hour_adjust - minute_adjust) % 10800
        print(f"{seconds} -> {result} ({result <= 3600})")
        return result <= 3600

    assert test(24815.34, 0, 10)  # 06:53:35
    assert not test(38154.18, 0, 0)  # 10:35:54
    assert not test(75022.12, 0, 0)  # 20:50:22
    assert test(1245.50, 0, 0)  # 00:20:45
    assert test(43200.00, 0, 0)  # 12:00:00
    assert not test(61453.89, 0, 0)  # 17:04:13
    assert not test(85399.11, 0, 0)  # 23:43:19
    assert not test(15842.05, 0, 0)  # 04:24:02
    assert not test(31500.67, 0, 0)  # 08:45:00
    assert not test(52911.23, 0, 0)  # 14:41:51
    assert not test(6723.45, 0, 0)  # 01:52:03
    assert not test(79410.56, 0, 0)  # 22:03:30
    assert not test(49142.70, 0, 0)  # 13:39:02
    assert not test(71105.92, 0, 0)  # 19:45:05
    assert test(2100.01, 0, 0)  # 00:35:00
    assert not test(28745.33, 0, 0)  # 07:59:05
    assert not test(57602.44, 0, 0)  # 16:00:02
    assert not test(82140.00, 0, 0)  # 22:49:00
    assert test(11025.15, 0, 0)  # 03:03:45
    assert not test(46800, 0, 0)  # 13:00:00

    assert not test(24815.34, 1, 0)  # 06:53:35
    assert test(38154.18, 1, 0)  # 10:35:54
    assert not test(75022.12, 1, 0)  # 20:50:22
    assert not test(1245.50, 1, 0)  # 00:20:45
    assert not test(43200.00, 1, 0)  # 12:00:00
    assert not test(61453.89, 1, 0)  # 17:04:13
    assert not test(85399.11, 1, 0)  # 23:43:19
    assert test(15842.05, 1, 0)  # 04:24:02
    assert not test(31500.67, 1, 0)  # 08:45:00
    assert not test(52911.23, 1, 0)  # 14:41:51
    assert test(6723.45, 1, 0)  # 01:52:03
    assert test(79410.56, 1, 0)  # 22:03:30
    assert test(49142.70, 1, 0)  # 13:39:02
    assert test(71105.92, 1, 0)  # 19:45:05
    assert not test(2100.01, 1, 0)  # 00:35:00
    assert test(28745.33, 1, 0)  # 07:59:05
    assert test(57602.44, 1, 0)  # 16:00:02
    assert test(82140.00, 1, 0)  # 22:49:00
    assert not test(11025.15, 1, 0)  # 03:03:45
    assert test(46800, 1, 0)  # 13:00:00

    assert not test(24815.34, 2, 0)  # 06:53:35
    assert not test(38154.18, 2, 0)  # 10:35:54
    assert test(75022.12, 2, 0)  # 20:50:22
    assert not test(1245.50, 2, 0)  # 00:20:45
    assert not test(43200.00, 2, 0)  # 12:00:00
    assert test(61453.89, 2, 0)  # 17:04:13
    assert test(85399.11, 2, 0)  # 23:43:19
    assert not test(15842.05, 2, 0)  # 04:24:02
    assert test(31500.67, 2, 0)  # 08:45:00
    assert test(52911.23, 2, 0)  # 14:41:51
    assert not test(6723.45, 2, 0)  # 01:52:03
    assert not test(79410.56, 2, 0)  # 22:03:30
    assert not test(49142.70, 2, 0)  # 13:39:02
    assert not test(71105.92, 2, 0)  # 19:45:05

    assert not test(2100.01, 2, 0)  # 00:35:00
    assert not test(28745.33, 2, 0)  # 07:59:05
    assert not test(57602.44, 2, 0)  # 16:00:02
    assert not test(82140.00, 2, 0)  # 22:49:00

    assert not test(46800, 2, 0)  # 13:00:00
