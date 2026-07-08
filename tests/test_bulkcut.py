import pytest

from liftmath.bulkcut import GARTHE_2013_FAST_BULK, GARTHE_2013_SLOW_BULK, rate_target


def test_intermediate_gain_target():
    # 84kg, intermediate (0.25-0.5%/wk) -> 0.21-0.42 kg/week.
    r = rate_target(84, "gain", "intermediate")
    assert r.weekly_change_low_kg == pytest.approx(0.21)
    assert r.weekly_change_high_kg == pytest.approx(0.42)


def test_novice_gain_target():
    # 70kg, novice (0.5-1%/wk) -> 0.35-0.70 kg/week.
    r = rate_target(70, "gain", "novice")
    assert r.weekly_change_low_kg == pytest.approx(0.35)
    assert r.weekly_change_high_kg == pytest.approx(0.70)


def test_advanced_gain_target():
    # 100kg, advanced (<=0.25%/wk) -> <=0.25 kg/week.
    r = rate_target(100, "gain", "advanced")
    assert r.weekly_change_low_kg == pytest.approx(0.0)
    assert r.weekly_change_high_kg == pytest.approx(0.25)


def test_default_tier_is_intermediate():
    r = rate_target(84, "gain")
    assert r.tier == "intermediate"


def test_garthe_partition_anchors_documented():
    # NCG (fast, ~0.38%/wk): +1.7kg lean / +1.1kg fat = 60.7/39.3, rounded to 61/39.
    # ALG (slow, ~0.16%/wk): +1.2kg lean / +0.2kg fat = 85.7/14.3, rounded to 85/15.
    assert GARTHE_2013_FAST_BULK["rate_pct_per_week"] == pytest.approx(0.38)
    assert GARTHE_2013_FAST_BULK["lean_fraction"] == pytest.approx(0.61)
    assert GARTHE_2013_FAST_BULK["fat_fraction"] == pytest.approx(0.39)
    assert GARTHE_2013_SLOW_BULK["rate_pct_per_week"] == pytest.approx(0.16)
    assert GARTHE_2013_SLOW_BULK["lean_fraction"] == pytest.approx(0.85)
    assert GARTHE_2013_SLOW_BULK["fat_fraction"] == pytest.approx(0.15)


def test_gain_note_cites_garthe():
    r = rate_target(84, "gain", "intermediate")
    assert "Garthe" in r.partition_note


def test_gain_note_is_directional_not_precise():
    r = rate_target(84, "gain", "intermediate")
    assert "directional" in r.partition_note.lower()


def test_cut_note_present():
    r = rate_target(84, "cut", "intermediate")
    assert r.partition_note
    assert "lean" in r.partition_note.lower()


def test_unknown_tier_raises():
    with pytest.raises(ValueError):
        rate_target(84, "gain", "elite")


def test_unknown_goal_raises():
    with pytest.raises(ValueError):
        rate_target(84, "recomp")


def test_nonpositive_bodyweight_raises():
    with pytest.raises(ValueError):
        rate_target(0, "gain")
