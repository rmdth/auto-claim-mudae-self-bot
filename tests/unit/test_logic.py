from datetime import datetime, timedelta, timezone

from src.core import logic


def test_next_claim():
    assert (
        logic.next_claim(
            datetime(1970, 1, 1, 6, 32, 0, tzinfo=timezone(timedelta(hours=-6))), 32
        )
        == 3600.0
    )
    assert (
        logic.next_claim(datetime(1970, 1, 1, 6, 45, 0, tzinfo=timezone.utc), 45)
        == 3600.0
    )
    assert (
        logic.next_claim(
            datetime(1970, 1, 1, 9, 39, 34, tzinfo=timezone(timedelta(hours=-6))), 32, 0
        )
        >= 3600.0
    )
