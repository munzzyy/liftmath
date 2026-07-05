import pytest

from liftmath.macros import macro_targets


def test_cut_flags_shortfall_when_protein_and_fat_floor_exceeds_target():
    # 100 kg bodyweight, cut: protein 2.4 g/kg = 240g (960 kcal), fat 0.6 g/kg = 60g (540 kcal).
    # Floor = 1500 kcal. Target = 1500 * 0.80 = 1200 kcal. Floor(1500) > target(1200) -> shortfall,
    # and the reported "actual" calories must equal the floor (1500), not the requested target.
    m = macro_targets(100, "cut", unit="kg", tdee=1500)
    assert m.protein_g == pytest.approx(240.0)
    assert m.fat_g == pytest.approx(60.0)
    assert m.carb_g == pytest.approx(0.0)
    assert m.target_kcal == pytest.approx(1200.0)
    assert m.actual_kcal == pytest.approx(1500.0)
    assert m.shortfall is True


def test_gain_sums_exactly_to_target_with_no_shortfall():
    # 84 kg bodyweight, gain: protein 1.6 g/kg = 134.4g, fat 0.9 g/kg = 75.6g, target = 3000*1.12.
    m = macro_targets(84, "gain", unit="kg", tdee=3000)
    assert m.protein_g == pytest.approx(134.4)
    assert m.fat_g == pytest.approx(75.6)
    assert m.target_kcal == pytest.approx(3360.0)
    assert m.actual_kcal == pytest.approx(m.target_kcal, abs=1)
    assert m.carb_g == pytest.approx(535.5, abs=0.1)
    assert m.shortfall is False


def test_calorie_identity_always_holds_macros_sum_to_actual():
    for goal in ("gain", "maintain", "recomp", "cut"):
        m = macro_targets(80, goal, unit="kg", tdee=2500)
        summed = m.protein_kcal + m.fat_kcal + m.carb_kcal
        assert summed == pytest.approx(m.actual_kcal, abs=0.5)


def test_lb_bodyweight_converts_to_kg():
    m = macro_targets(220.462, "maintain", unit="lb", tdee=2500)
    assert m.bodyweight_kg == pytest.approx(100.0, abs=0.01)


def test_tdee_estimated_when_not_supplied():
    m = macro_targets(84, "maintain", unit="kg", activity="moderate")
    assert m.tdee_is_estimate is True
    assert m.tdee == pytest.approx(84 * 34, abs=0.01)


def test_tdee_supplied_marks_not_estimate():
    m = macro_targets(84, "maintain", unit="kg", tdee=2800)
    assert m.tdee_is_estimate is False
    assert m.tdee == 2800


def test_per_meal_protein_heuristic():
    m = macro_targets(80, "maintain", unit="kg", tdee=2600)
    assert m.per_meal_protein_g == pytest.approx(32.0)


def test_unknown_goal_raises():
    with pytest.raises(ValueError):
        macro_targets(80, "shred", unit="kg", tdee=2500)


def test_unknown_activity_raises():
    with pytest.raises(ValueError):
        macro_targets(80, "maintain", unit="kg", activity="superhuman")


def test_nonpositive_bodyweight_raises():
    with pytest.raises(ValueError):
        macro_targets(0, "maintain", unit="kg", tdee=2500)
