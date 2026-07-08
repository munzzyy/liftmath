import pytest

from liftmath.attempts import (
    OPENER_PCT,
    OPENER_RANGE_PCT,
    SECOND_PCT,
    SECOND_RANGE_PCT,
    THIRD_PCT,
    attempt_selection,
)


def test_headline_percentages_are_travis_zourdos_bazyler():
    assert OPENER_PCT == pytest.approx(0.91)
    assert SECOND_PCT == pytest.approx(0.96)
    assert THIRD_PCT == pytest.approx(1.00)


def test_coach_consensus_range_percentages():
    assert OPENER_RANGE_PCT == pytest.approx((0.88, 0.93))
    assert SECOND_RANGE_PCT == pytest.approx((0.93, 0.97))


def test_attempt_selection_lb_clean_multiple_of_5():
    # 500lb goal third: 91% = 455 (already a multiple of 5), 96% = 480.
    r = attempt_selection(500, lift="squat", unit="lb")
    assert r.lift == "squat"
    assert r.opener == pytest.approx(455.0)
    assert r.second == pytest.approx(480.0)
    assert r.third == pytest.approx(500.0)
    assert r.increment == pytest.approx(5.0)


def test_attempt_selection_coach_range_lb():
    r = attempt_selection(500, unit="lb")
    assert r.opener_range_low == pytest.approx(440.0)  # 500*0.88
    assert r.opener_range_high == pytest.approx(465.0)  # 500*0.93
    assert r.second_range_low == pytest.approx(465.0)  # 500*0.93
    assert r.second_range_high == pytest.approx(485.0)  # 500*0.97


def test_attempt_selection_kg_default_increment():
    r = attempt_selection(200, unit="kg")
    assert r.increment == pytest.approx(2.5)
    # 200*0.91 = 182.0 -> nearest 2.5kg = 182.5.
    assert r.opener == pytest.approx(182.5)
    # 200*0.96 = 192.0 -> nearest 2.5kg = 192.5.
    assert r.second == pytest.approx(192.5)
    assert r.third == pytest.approx(200.0)


def test_attempt_selection_rounds_to_nearest_increment():
    # 222kg goal third: 91% = 202.02 -> nearest 2.5kg = 202.5.
    r = attempt_selection(222, unit="kg")
    assert r.opener == pytest.approx(202.5)


def test_attempt_selection_custom_increment():
    r = attempt_selection(500, unit="lb", increment=10.0)
    assert r.increment == pytest.approx(10.0)
    # 500*0.91 = 455 -> nearest 10 = 460 (round-half-to-even at .5 boundary
    # doesn't apply here: 45.5 rounds to 46 under Python's round-half-even
    # since 46 is even).
    assert r.opener % 10 == pytest.approx(0.0)


def test_default_lift_label():
    r = attempt_selection(500)
    assert r.lift == "lift"


def test_rejects_nonpositive_goal_third():
    with pytest.raises(ValueError):
        attempt_selection(0)
    with pytest.raises(ValueError):
        attempt_selection(-100)


def test_rejects_unknown_unit_without_explicit_increment():
    with pytest.raises(ValueError):
        attempt_selection(500, unit="stone")


def test_unknown_unit_allowed_with_explicit_increment():
    # unit is only used to pick a default increment - an explicit increment
    # bypasses that lookup entirely.
    r = attempt_selection(500, unit="stone", increment=5.0)
    assert r.increment == pytest.approx(5.0)
