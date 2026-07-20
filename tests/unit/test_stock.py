import pytest
from src.stock.domain.types import Cooldown, KakeraStock
from src.stock.logic.rules import (
    can_afford_claim,
    can_use_dk,
    determine_kakera_method,
)


@pytest.fixture
def full_stock() -> KakeraStock:
    return KakeraStock(
        current_value=110,
        max_value=110,
        cost_per_claim=36,
    )


@pytest.fixture
def empty_stock() -> KakeraStock:
    return KakeraStock(
        current_value=0,
        max_value=110,
        cost_per_claim=36,
    )


class TestCooldown:
    def test_is_ready_when_zero(self):
        cd = Cooldown(ready_at=0.0)
        assert cd.is_ready(100.0) is True

    def test_is_ready_when_expired(self):
        cd = Cooldown(ready_at=50.0)
        assert cd.is_ready(100.0) is True

    def test_is_not_ready_when_active(self):
        cd = Cooldown(ready_at=150.0)
        assert cd.is_ready(100.0) is False

    def test_remaining_seconds(self):
        cd = Cooldown(ready_at=150.0)
        assert cd.remaining_seconds(100.0) == 50.0

    def test_remaining_seconds_when_expired(self):
        cd = Cooldown(ready_at=50.0)
        assert cd.remaining_seconds(100.0) == 0.0

    def test_set_cooldown(self):
        cd = Cooldown()
        cd.set_cooldown(60.0, 100.0)
        assert cd.ready_at == 160.0


class TestKakeraStock:
    def test_can_afford(self, full_stock):
        assert full_stock.can_afford(36) is True

    def test_cannot_afford(self, empty_stock):
        assert empty_stock.can_afford(36) is False

    def test_can_use_dk_when_ready(self, full_stock):
        assert full_stock.can_use_dk(100.0) is True

    def test_can_use_dk_when_cooldown(self, full_stock):
        full_stock.dk_cooldown.set_cooldown(86400, 100.0)
        assert full_stock.can_use_dk(200.0) is False

    def test_apply_cost(self, full_stock):
        full_stock.apply_cost(36)
        assert full_stock.current_value == 74

    def test_regen_caps_at_max(self, full_stock):
        full_stock.regen()
        assert full_stock.current_value == 110

    def test_regen_increases(self, empty_stock):
        empty_stock.regen()
        assert empty_stock.current_value == 1

    def test_reset(self, empty_stock):
        empty_stock.reset()
        assert empty_stock.current_value == 110


class TestStockRules:
    def test_can_afford_claim_true(self, full_stock):
        assert can_afford_claim(full_stock, 36) is True

    def test_can_afford_claim_false(self, empty_stock):
        assert can_afford_claim(empty_stock, 36) is False

    def test_can_use_dk_true(self, full_stock):
        assert can_use_dk(full_stock, 100.0) is True

    def test_determine_method_claim(self, full_stock):
        assert determine_kakera_method(full_stock, 36, 100.0) == "claim"

    def test_determine_method_dk(self, empty_stock):
        assert determine_kakera_method(empty_stock, 36, 100.0) == "dk"

    def test_determine_method_none(self, empty_stock):
        empty_stock.dk_cooldown.set_cooldown(86400, 100.0)
        assert determine_kakera_method(empty_stock, 36, 200.0) == ""
