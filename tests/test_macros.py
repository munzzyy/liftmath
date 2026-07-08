import pytest

from liftmath.macros import cunningham_tdee, macro_targets


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


def test_cunningham_rmr_reference_value_one():
    # Lean mass 70kg -> RMR = 500 + 22*70 = 2040 kcal.
    result = cunningham_tdee(70)
    assert result.rmr_kcal == pytest.approx(2040.0)


def test_cunningham_rmr_reference_value_two():
    # Lean mass 60kg -> RMR = 500 + 22*60 = 1820 kcal.
    result = cunningham_tdee(60)
    assert result.rmr_kcal == pytest.approx(1820.0)


def test_cunningham_rmr_reference_value_three():
    # Lean mass 85kg -> RMR = 500 + 22*85 = 2370 kcal.
    result = cunningham_tdee(85)
    assert result.rmr_kcal == pytest.approx(2370.0)


def test_cunningham_tdee_applies_activity_multiplier():
    result = cunningham_tdee(70, activity="sedentary")
    assert result.tdee == pytest.approx(2040.0 * 1.2)


def test_cunningham_rejects_nonpositive_lean_mass():
    with pytest.raises(ValueError):
        cunningham_tdee(0)


def test_cunningham_rejects_unknown_activity():
    with pytest.raises(ValueError):
        cunningham_tdee(70, activity="superhuman")


def test_cunningham_accepts_bodyweight_and_bodyfat_instead_of_lean_mass():
    # 100kg bodyweight, 20% bodyfat -> lean 80kg -> RMR 500+22*80=2260, TDEE 2260*1.55=3503.
    result = cunningham_tdee(activity="moderate", bodyweight_kg=100, bodyfat_pct=20)
    assert result.lean_mass_kg == pytest.approx(80.0)
    assert result.rmr_kcal == pytest.approx(2260.0)
    assert result.tdee == pytest.approx(3503.0)


def test_cunningham_rejects_both_forms_at_once():
    with pytest.raises(ValueError):
        cunningham_tdee(70, bodyweight_kg=100, bodyfat_pct=20)


def test_cunningham_rejects_neither_form():
    with pytest.raises(ValueError):
        cunningham_tdee()


def test_cunningham_rejects_bodyfat_out_of_range():
    with pytest.raises(ValueError):
        cunningham_tdee(bodyweight_kg=100, bodyfat_pct=100)


def test_mifflin_male_reference_value():
    # 90kg, 180cm, age 30, male, moderate: RMR = 10*90+6.25*180-5*30+5 = 1880;
    # TDEE = 1880 * 1.55 = 2914.0.
    m = macro_targets(90, "maintain", unit="kg", age=30, height_m=1.80, sex="male")
    assert m.tdee_method == "mifflin"
    assert m.tdee == pytest.approx(2914.0)


def test_mifflin_female_reference_value():
    # 65kg, 165cm, age 25, female, sedentary: RMR = 10*65+6.25*165-5*25-161 = 1395.25;
    # TDEE = 1395.25 * 1.2 = 1674.3.
    m = macro_targets(65, "maintain", unit="kg", activity="sedentary", age=25, height_m=1.65, sex="female")
    assert m.tdee_method == "mifflin"
    assert m.tdee == pytest.approx(1674.3)


def test_bodyfat_routes_through_cunningham():
    # 100kg, 20% bodyfat, moderate -> same Cunningham math as the direct-cunningham test above.
    m = macro_targets(100, "gain", unit="kg", bodyfat_pct=20)
    assert m.tdee_method == "cunningham"
    assert m.tdee == pytest.approx(3503.0)


def test_bodyfat_takes_priority_over_mifflin_when_both_given():
    m = macro_targets(100, "maintain", unit="kg", age=30, height_m=1.80, sex="male", bodyfat_pct=20)
    assert m.tdee_method == "cunningham"


def test_quick_estimate_method_label_when_nothing_special_given():
    m = macro_targets(84, "maintain", unit="kg")
    assert m.tdee_method == "quick_estimate"


def test_supplied_method_label():
    m = macro_targets(84, "maintain", unit="kg", tdee=2800)
    assert m.tdee_method == "supplied"


def test_partial_mifflin_inputs_raise():
    with pytest.raises(ValueError):
        macro_targets(84, "maintain", unit="kg", age=30)
    with pytest.raises(ValueError):
        macro_targets(84, "maintain", unit="kg", height_m=1.8)
    with pytest.raises(ValueError):
        macro_targets(84, "maintain", unit="kg", age=30, height_m=1.8)  # no sex


def test_mifflin_invalid_sex_raises():
    with pytest.raises(ValueError):
        macro_targets(84, "maintain", unit="kg", age=30, height_m=1.8, sex="other")
