import pytest

from liftmath.plates import load_plates


def test_245lb_on_45lb_bar_default_plates():
    # per side = (245-45)/2 = 100 -> 2x45 + 1x10
    result = load_plates(245, unit="lb")
    assert result.bar == 45
    assert result.per_side == pytest.approx(100.0)
    assert result.plates == [(45, 2), (10, 1)]
    assert result.exact is True


def test_315lb_on_45lb_bar_default_plates():
    # per side = (315-45)/2 = 135 -> 3x45
    result = load_plates(315, unit="lb")
    assert result.plates == [(45, 3)]
    assert result.exact is True


def test_142_5kg_on_20kg_bar_default_plates():
    # per side = (142.5-20)/2 = 61.25 -> 2x25 + 1x10 + 1x1.25
    result = load_plates(142.5, unit="kg")
    assert result.per_side == pytest.approx(61.25)
    assert result.plates == [(25, 2), (10, 1), (1.25, 1)]
    assert result.exact is True


def test_target_below_bar_raises():
    with pytest.raises(ValueError):
        load_plates(30, unit="lb", bar=45)


def test_custom_bar_and_plates():
    result = load_plates(100, unit="kg", bar=15, plates=(20, 10, 5))
    # per side = (100-15)/2 = 42.5 -> 2x20 + 0x10... remainder 2.5 short (no 2.5 plate given)
    assert result.per_side == pytest.approx(42.5)
    assert result.exact is False
    assert result.shortfall == pytest.approx(2.5)


def test_unloadable_target_reports_closest_achievable():
    result = load_plates(100, unit="kg", bar=15, plates=(20, 10, 5))
    # closest below = target - 2*shortfall = 100 - 5 = 95
    assert result.achievable == pytest.approx(95.0)


def test_womens_preset_uses_15kg_bar():
    # per side = (67.5-15)/2 = 26.25 -> 1x20 + 1x5 + 1x1.25
    result = load_plates(67.5, unit="kg", preset="womens")
    assert result.bar == 15
    assert result.plates == [(20, 1), (5, 1), (1.25, 1)]
    assert result.exact is True


def test_metric_no_45_preset_uses_20kg_bar_and_no_25_plate_analog():
    result = load_plates(100, unit="kg", preset="metric-no-45")
    assert result.bar == 20
    # per side = 40 -> 2x20, since 25 isn't in this preset's plate set
    assert result.plates == [(20, 2)]


def test_explicit_bar_or_plates_override_preset():
    result = load_plates(70, unit="kg", preset="womens", bar=20)
    assert result.bar == 20


def test_preset_with_lb_unit_raises():
    with pytest.raises(ValueError):
        load_plates(245, unit="lb", preset="womens")


def test_unknown_preset_raises():
    with pytest.raises(ValueError):
        load_plates(100, unit="kg", preset="not-a-real-preset")


def test_explicit_empty_plates_means_no_plates_available():
    # An explicitly empty plates=() must NOT fall back to DEFAULT_PLATES via
    # Python truthiness - it means "I have no plates", so the full per-side
    # amount should come back as shortfall on an empty bar.
    result = load_plates(135, unit="lb", plates=())
    assert result.plates == []
    assert result.exact is False
    assert result.shortfall == pytest.approx(45.0)


def test_explicit_empty_plates_list_also_means_no_plates_available():
    result = load_plates(135, unit="lb", plates=[])
    assert result.plates == []
    assert result.shortfall == pytest.approx(45.0)
