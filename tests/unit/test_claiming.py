import pytest
from src.claiming.domain.preferences import ClaimPreferences
from src.claiming.domain.types import KakeraUnit
from src.claiming.logic.modes import default_mode
from src.claiming.logic.rules import (
    is_wished_roll,
    meets_min_value,
)
from src.rolling.domain.roll import Roll


@pytest.fixture
def prefs() -> ClaimPreferences:
    return ClaimPreferences(
        min_kakera_value=100,
        wish_list=frozenset({"Raiden Mei", "Zero Two"}),
        wish_series=frozenset({"Naruto"}),
        wish_kakera=frozenset({"kakera"}),
    )


@pytest.fixture
def wished_roll() -> Roll:
    return Roll(
        id="1",
        name="Raiden Mei",
        series="Honkai",
        kakera_value=50,
        key_amount=0,
        wished=True,
    )


@pytest.fixture
def normal_roll() -> Roll:
    return Roll(
        id="2",
        name="Random",
        series="Other",
        kakera_value=150,
        key_amount=0,
        wished=False,
    )


@pytest.fixture
def low_roll() -> Roll:
    return Roll(
        id="3", name="Low", series="Other", kakera_value=50, key_amount=0, wished=False
    )


class TestClaimRules:
    def test_wished_roll_by_name(self, prefs):
        roll = Roll(
            id="1", name="Raiden Mei", series="Honkai", kakera_value=50, key_amount=0
        )
        assert is_wished_roll(roll, prefs) is True

    def test_wished_roll_by_series(self, prefs):
        roll = Roll(
            id="2", name="Naruto", series="Naruto", kakera_value=50, key_amount=0
        )
        assert is_wished_roll(roll, prefs) is True

    def test_not_wished_roll(self, prefs):
        roll = Roll(
            id="3", name="Random", series="Other", kakera_value=50, key_amount=0
        )
        assert is_wished_roll(roll, prefs) is False

    def test_meets_min_value(self, prefs, normal_roll):
        assert meets_min_value(normal_roll, prefs) is True

    def test_does_not_meet_min_value(self, prefs, low_roll):
        assert meets_min_value(low_roll, prefs) is False


class TestDefaultMode:
    def test_wished_always_claimed(self, wished_roll):
        assert default_mode(wished_roll, 100, False, "claim") is True

    def test_not_wished_without_claim_method(self, normal_roll):
        assert default_mode(normal_roll, 100, False, "rt") is False
        assert default_mode(normal_roll, 100, False, "") is False

    def test_kakera_always_claimed_if_can_afford(self):
        unit = KakeraUnit(claim_cost=36, color="kakera", wished=False)
        assert default_mode(unit, 100, False, "claim") is True

    def test_roll_meets_min_value(self, normal_roll):
        assert default_mode(normal_roll, 100, False, "claim") is True

    def test_roll_below_min_value(self, low_roll):
        assert default_mode(low_roll, 100, False, "claim") is False

    def test_roll_below_min_value_at_threshold(self, low_roll):
        assert default_mode(low_roll, 100, True, "claim") is True
        assert default_mode(low_roll, 100, False, "claim") is False
