from datetime import datetime, timedelta, timezone

from src.shared.domain.time import next_claim


def test_next_claim():
    assert (
        next_claim(
            datetime(1970, 1, 1, 6, 32, 0, tzinfo=timezone(timedelta(hours=-6))), 32
        )
        == 3600.0
    )
    assert next_claim(datetime(1970, 1, 1, 6, 45, 0, tzinfo=timezone.utc), 45) == 3600.0
    assert (
        next_claim(
            datetime(1970, 1, 1, 5, 39, 34, tzinfo=timezone(timedelta(hours=-6))), 32, 0
        )
        >= 3600.0
    )
    assert (
        next_claim(
            datetime(1970, 1, 1, 6, 39, 34, tzinfo=timezone(timedelta(hours=-6))), 32, 0
        )
        <= 3600.0
    )
