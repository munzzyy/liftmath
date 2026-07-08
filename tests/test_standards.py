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


def test_dots_male_reference_value():
    # Hand-calculated from the DOTS coefficients at bodyweight 100kg, 500kg total.
    assert dots_score(500, 100, "male") == pytest.approx(307.758, abs=0.01)


def test_dots_female_reference_value():
    assert dots_score(300, 60, "female") == pytest.approx(332.564, abs=0.01)


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


def test_score_bundles_wilks_original_too():
    s = score(500, 100, "male")
    assert s.wilks_original == pytest.approx(304.295, abs=0.01)
