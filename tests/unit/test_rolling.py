import pytest
from src.rolling.domain.roll import Roll
from src.rolling.domain.types import RollingState
from src.rolling.logic import rules, transforms


@pytest.fixture
def fresh_state() -> RollingState:
    return RollingState(
        rolls_available=10,
        max_rolls=10,
        claim_cooldown_until=0.0,
        rt_cooldown_until=0.0,
    )


class TestRollingRules:
    def test_can_roll_when_rolls_available(self, fresh_state):
        assert rules.can_roll(fresh_state) is True

    def test_cannot_roll_when_empty(self, fresh_state):
        fresh_state.rolls_available = 0
        assert rules.can_roll(fresh_state) is False

    def test_can_claim_when_cooldown_expired(self, fresh_state):
        assert rules.can_claim(fresh_state, 100.0) is True

    def test_cannot_claim_when_cooldown_active(self, fresh_state):
        fresh_state.claim_cooldown_until = 200.0
        assert rules.can_claim(fresh_state, 100.0) is False

    def test_should_use_rt_when_ready(self, fresh_state):
        assert rules.should_use_rt(fresh_state, 100.0) is True

    def test_should_not_use_rt_when_cooldown(self, fresh_state):
        fresh_state.rt_cooldown_until = 200.0
        assert rules.should_use_rt(fresh_state, 100.0) is False

    def test_has_pending_when_empty(self, fresh_state):
        assert rules.has_pending(fresh_state) is False

    def test_has_pending_with_items(self, fresh_state):
        fresh_state.pending_claims.append(
            Roll(
                id="1",
                name="test",
                series="test_series",
                kakera_value=100,
                key_amount=0,
            )
        )
        assert rules.has_pending(fresh_state) is True


class TestRollingState:
    def test_consume_roll(self, fresh_state):
        fresh_state.consume_roll()
        assert fresh_state.rolls_available == 9

    def test_consume_roll_does_not_go_negative(self, fresh_state):
        fresh_state.rolls_available = 0
        fresh_state.consume_roll()
        assert fresh_state.rolls_available == 0

    def test_add_pending_sorts_by_priority(self, fresh_state):
        low_roll = Roll(id="1", name="low", series="s", kakera_value=50, key_amount=0)
        high_roll = Roll(
            id="2", name="high", series="s", kakera_value=200, key_amount=0
        )
        fresh_state.add_pending(low_roll)
        fresh_state.add_pending(high_roll)
        assert fresh_state.pending_claims[-1].kakera_value == 200
        assert fresh_state.pending_claims[0].kakera_value == 50

    def test_add_pending_wished_first(self, fresh_state):
        normal = Roll(id="1", name="a", series="s", kakera_value=200, key_amount=0)
        wished = Roll(
            id="2", name="b", series="s", kakera_value=100, key_amount=0, wished=True
        )
        fresh_state.add_pending(normal)
        fresh_state.add_pending(wished)
        assert fresh_state.pending_claims[-1].wished is True

    def test_reset_rolls(self, fresh_state):
        fresh_state.rolls_available = 3
        fresh_state.reset_rolls()
        assert fresh_state.rolls_available == 10

    def test_set_claim_cooldown(self, fresh_state):
        fresh_state.set_claim_cooldown(500.0)
        assert fresh_state.claim_cooldown_until == 500.0

    def test_pop_top_pending(self, fresh_state):
        roll = Roll(id="1", name="test", series="s", kakera_value=100, key_amount=0)
        fresh_state.add_pending(roll)
        popped = fresh_state.pop_top_pending()
        assert popped is roll
        assert len(fresh_state.pending_claims) == 0

    def test_pop_empty_pending(self, fresh_state):
        assert fresh_state.pop_top_pending() is None

    def test_clear_pending(self, fresh_state):
        fresh_state.pending_claims.append(
            Roll(id="1", name="test", series="s", kakera_value=100, key_amount=0)
        )
        fresh_state.clear_pending()
        assert fresh_state.pending_claims == []


class TestRollingTransforms:
    def test_filter_by_min_value(self, fresh_state):
        low = Roll(id="1", name="low", series="s", kakera_value=50, key_amount=0)
        high = Roll(id="2", name="high", series="s", kakera_value=200, key_amount=0)
        fresh_state.pending_claims = [low, high]
        result = transforms.filter_by_min_value(fresh_state, 100)
        assert len(result) == 1
        assert result[0].kakera_value == 200

    def test_sort_by_priority(self):
        rolls = [
            Roll(id="1", name="a", series="s", kakera_value=50, key_amount=0),
            Roll(id="2", name="b", series="s", kakera_value=200, key_amount=0),
            Roll(
                id="3",
                name="c",
                series="s",
                kakera_value=100,
                key_amount=0,
                wished=True,
            ),
        ]
        sorted_rolls = transforms.sort_by_priority(rolls)
        assert sorted_rolls[-1].wished is True
        assert sorted_rolls[0].kakera_value == 50
        assert sorted_rolls[-1].kakera_value == 100
