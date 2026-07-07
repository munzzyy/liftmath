import pytest

from liftmath.symmetry import OHP_IS_SINGLE_SOURCED, score_symmetry


def test_ratio_to_deadlift_and_total():
    # squat 315, bench 225, deadlift 405 -> total 945
    r = score_symmetry(315, 225, 405, "male")
    assert r.total == pytest.approx(945.0)
    assert r.lifts["squat"].ratio_to_deadlift == pytest.approx(315 / 405)
    assert r.lifts["squat"].ratio_to_total == pytest.approx(315 / 945)
    assert r.lifts["deadlift"].ratio_to_deadlift == pytest.approx(1.0)


def test_lagging_squat_and_bench_hand_calculated():
    # squat ratio 315/405 = 0.7778 vs expected 0.87 -> deviation -9.22 points
    # bench ratio 225/405 = 0.5556 vs expected 0.65 -> deviation -9.44 points
    r = score_symmetry(315, 225, 405, "male")
    assert r.lifts["squat"].deviation_pct == pytest.approx(-9.222, abs=0.01)
    assert r.lifts["squat"].verdict == "lagging ~9%"
    assert r.lifts["bench"].deviation_pct == pytest.approx(-9.444, abs=0.01)
    assert r.lifts["bench"].verdict == "lagging ~9%"
    assert r.lifts["deadlift"].verdict == "balanced"


def test_exact_expected_ratio_is_balanced_with_zero_deviation():
    # squat/deadlift = 0.87 exactly (348/400) matches EXPECTED_RATIOS["male"]["squat"]
    r = score_symmetry(348, 200, 400, "male")
    assert r.lifts["squat"].deviation_pct == pytest.approx(0.0, abs=1e-9)
    assert r.lifts["squat"].verdict == "balanced"


def test_ahead_verdict_for_unusually_high_ratio():
    r = score_symmetry(400, 250, 400, "male")
    assert r.lifts["squat"].deviation_pct == pytest.approx(13.0, abs=0.01)
    assert r.lifts["squat"].verdict == "ahead ~13%"


def test_just_under_5_points_is_balanced():
    # expected squat/dl = 0.87 for men; 367/400 = 0.9175 -> deviation +4.75 points -> balanced (<=5)
    r = score_symmetry(367, 200, 400, "male")
    assert r.lifts["squat"].deviation_pct == pytest.approx(4.75, abs=0.01)
    assert r.lifts["squat"].verdict == "balanced"


def test_just_past_5_points_is_not_balanced():
    # 369/400 = 0.9225 -> deviation +5.25 points -> past the +/-5 band
    r = score_symmetry(369, 200, 400, "male")
    assert r.lifts["squat"].deviation_pct == pytest.approx(5.25, abs=0.01)
    assert r.lifts["squat"].verdict != "balanced"


def test_female_ratios_use_female_expected_table():
    r = score_symmetry(200, 110, 240, "female")
    assert r.lifts["squat"].expected_ratio == pytest.approx(0.84)
    assert r.lifts["bench"].expected_ratio == pytest.approx(0.57)
    assert r.lifts["squat"].deviation_pct == pytest.approx(-0.667, abs=0.01)


def test_ohp_optional_and_absent_by_default():
    r = score_symmetry(315, 225, 405, "male")
    assert "ohp" not in r.lifts


def test_ohp_included_when_given():
    r = score_symmetry(315, 225, 405, "male", ohp=135)
    assert "ohp" in r.lifts
    assert r.lifts["ohp"].expected_ratio == pytest.approx(0.423)


def test_ohp_is_flagged_single_sourced():
    # See symmetry.py module docstring: Symmetric Strength publishes no OHP
    # ratio, so OHP's expected ratio comes from Strength Level alone.
    assert OHP_IS_SINGLE_SOURCED is True


def test_bodyweight_is_optional_and_carried_through():
    r = score_symmetry(315, 225, 405, "male", bodyweight=180)
    assert r.bodyweight == 180
    r2 = score_symmetry(315, 225, 405, "male")
    assert r2.bodyweight is None


def test_total_includes_ohp_when_given():
    r = score_symmetry(315, 225, 405, "male", ohp=135)
    assert r.total == pytest.approx(945.0 + 135.0)


def test_invalid_sex_raises():
    with pytest.raises(ValueError):
        score_symmetry(315, 225, 405, "unicorn")


def test_zero_or_negative_lift_raises():
    with pytest.raises(ValueError):
        score_symmetry(0, 225, 405, "male")
    with pytest.raises(ValueError):
        score_symmetry(315, -225, 405, "male")
    with pytest.raises(ValueError):
        score_symmetry(315, 225, 0, "male")


def test_zero_or_negative_ohp_raises():
    with pytest.raises(ValueError):
        score_symmetry(315, 225, 405, "male", ohp=0)


def test_zero_or_negative_bodyweight_raises():
    with pytest.raises(ValueError):
        score_symmetry(315, 225, 405, "male", bodyweight=-10)
