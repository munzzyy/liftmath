import pytest

from liftmath.standards import (
    dots_score,
    ipf_gl_points,
    score,
    wilks_original_score,
    wilks_score,
)


def test_wilks_male_reference_value():
    # Hand-calculated from the 2020 Wilks coefficients: 600 / (a+bx+cx^2+dx^3+ex^4+fx^5)
    # at bodyweight 100kg, times a 500kg total.
    assert wilks_score(500, 100, "male") == pytest.approx(364.681, abs=0.01)


def test_wilks_female_reference_value():
    assert wilks_score(300, 60, "female") == pytest.approx(395.710, abs=0.01)


def test_wilks_male_clamps_bodyweight_above_fitted_domain():
    # Past the men's 200.95kg fitted domain the unclamped quintic's
    # denominator crosses zero and the score inverts sign; wilks2020.rs
    # clamps bodyweight to the boundary before evaluating instead, and so
    # do we. Verified bug report values: 250kg used to give 371.58, 300kg
    # used to go negative (-599.43) - both should now land on 306.09.
    boundary = wilks_score(500, 200.95, "male")
    assert boundary == pytest.approx(306.09, abs=0.01)
    assert wilks_score(500, 250, "male") == pytest.approx(boundary, abs=0.01)
    assert wilks_score(500, 300, "male") == pytest.approx(boundary, abs=0.01)


def test_wilks_female_clamps_bodyweight_above_fitted_domain():
    boundary = wilks_score(300, 150.95, "female")
    assert wilks_score(300, 220, "female") == pytest.approx(boundary, abs=0.01)
    assert wilks_score(300, 300, "female") == pytest.approx(boundary, abs=0.01)
    assert wilks_score(300, 300, "female") > 0


def test_wilks_clamps_bodyweight_below_fitted_domain():
    # Both sexes floor at 40kg - an implausibly light "bodyweight" shouldn't
    # get an inflated coefficient any more than an implausibly heavy one
    # should get an inverted one.
    assert wilks_score(200, 20, "male") == pytest.approx(wilks_score(200, 40, "male"), abs=0.01)
    assert wilks_score(150, 20, "female") == pytest.approx(wilks_score(150, 40, "female"), abs=0.01)


def test_wilks_original_male_matches_openpowerlifting_pinned_test():
    # OpenPowerlifting's own Rust unit test: M, 100kg BW, 1000kg total -> 608.589.
    assert wilks_original_score(1000, 100, "male") == pytest.approx(608.589, abs=0.01)


def test_wilks_original_female_matches_openpowerlifting_pinned_test():
    # OpenPowerlifting's own Rust unit test: F, 60kg BW, 500kg total -> 557.4434.
    assert wilks_original_score(500, 60, "female") == pytest.approx(557.4434, abs=0.01)


def test_wilks_original_and_2020_disagree_meaningfully():
    # Same input, different formula era - they should NOT collapse to the same value.
    original = wilks_original_score(500, 100, "male")
    revised = wilks_score(500, 100, "male")
    assert original != pytest.approx(revised, abs=1.0)


def test_wilks_original_clamps_bodyweight_above_fitted_domain():
    # Same failure mode as Wilks-2020, same fix: wilks.rs clamps to
    # [40, 201.9]kg (men) before evaluating its own quintic.
    boundary = wilks_original_score(500, 201.9, "male")
    assert wilks_original_score(500, 300, "male") == pytest.approx(boundary, abs=0.01)
    assert wilks_original_score(500, 300, "male") > 0


def test_wilks_original_female_clamps_bodyweight_below_fitted_domain():
    # The original formula's female floor is 26.51kg, not the 40kg used
    # everywhere else - worth its own test since it's the odd one out.
    boundary = wilks_original_score(300, 26.51, "female")
    assert wilks_original_score(300, 15, "female") == pytest.approx(boundary, abs=0.01)


def test_dots_male_reference_value():
    # Hand-calculated from the DOTS coefficients at bodyweight 100kg, 500kg total.
    assert dots_score(500, 100, "male") == pytest.approx(307.758, abs=0.01)


def test_dots_female_reference_value():
    assert dots_score(300, 60, "female") == pytest.approx(332.564, abs=0.01)


def test_dots_male_clamps_bodyweight_above_fitted_domain():
    # Past the men's 210kg fitted domain the unclamped quartic's denominator
    # crosses zero too; dots.rs clamps the same way Wilks does.
    boundary = dots_score(500, 210, "male")
    assert dots_score(500, 260, "male") == pytest.approx(boundary, abs=0.01)
    assert dots_score(500, 300, "male") == pytest.approx(boundary, abs=0.01)


def test_dots_female_clamps_bodyweight_above_fitted_domain():
    boundary = dots_score(300, 150, "female")
    assert dots_score(300, 200, "female") == pytest.approx(boundary, abs=0.01)
    assert dots_score(300, 300, "female") == pytest.approx(boundary, abs=0.01)
    assert dots_score(300, 300, "female") > 0


def test_dots_clamps_bodyweight_below_fitted_domain():
    assert dots_score(200, 20, "male") == pytest.approx(dots_score(200, 40, "male"), abs=0.01)


def test_ipf_gl_matches_official_worked_example_equipped_men():
    # From the IPF's own "IPF GL Coefficients for Relative Scoring" document (May 2020):
    # Men's Equipped Powerlifting, bodyweight 92.04kg, total 1035.0kg -> 112.855365 points.
    # This module only ships classic (raw) coefficients, so this checks the formula and
    # rounding procedure against the IPF's own example, not the classic-only coefficient
    # table (which is checked separately below).
    a, b, c = 1236.25115, 1449.21864, 0.01644
    import math
    coefficient = round(100.0 / (a - b * math.exp(-c * 92.04)), 6)
    assert coefficient == pytest.approx(0.109039, abs=1e-6)
    assert round(coefficient * 1035.0, 6) == pytest.approx(112.855365, abs=1e-3)


def test_ipf_gl_classic_male_reasonable_range():
    # Classic powerlifting men's coefficients, elite-ish total at a mid bodyweight.
    # An 800kg total at 100kg bodyweight should land in the low-100s GL points range,
    # consistent with a strong (but not world-record) raw total.
    points = ipf_gl_points(800, 100, "male")
    assert 90 < points < 130


def test_ipf_gl_classic_female_reasonable_range():
    points = ipf_gl_points(500, 65, "female")
    assert 90 < points < 140


def test_score_bundles_all_three():
    s = score(500, 100, "male")
    assert s.total == 500
    assert s.bodyweight_kg == 100
    assert s.sex == "male"
    assert s.wilks == pytest.approx(364.681, abs=0.01)
    assert s.dots == pytest.approx(307.758, abs=0.01)
    assert s.ipf_gl > 0


def test_invalid_sex_raises():
    with pytest.raises(ValueError):
        score(500, 100, "other")


def test_nonpositive_bodyweight_raises():
    with pytest.raises(ValueError):
        score(500, 0, "male")
    with pytest.raises(ValueError):
        score(500, -5, "male")


def test_nonpositive_total_raises():
    # A negative total used to sail through and print negative Wilks/DOTS/IPF GL.
    with pytest.raises(ValueError):
        score(-100, 90, "male")
    with pytest.raises(ValueError):
        score(0, 90, "male")


def test_non_finite_total_or_bodyweight_raises():
    with pytest.raises(ValueError):
        score(float("nan"), 90, "male")
    with pytest.raises(ValueError):
        score(float("inf"), 90, "male")
    with pytest.raises(ValueError):
        score(500, float("nan"), "male")
    with pytest.raises(ValueError):
        score(500, float("inf"), "male")


def test_score_bundles_wilks_original_too():
    s = score(500, 100, "male")
    assert s.wilks_original == pytest.approx(304.295, abs=0.01)
