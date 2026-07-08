import pytest

from liftmath.gainrate import (
    ARAGON_HELMS_MONTHLY_PCT_BW,
    LEVELS,
    MCDONALD_YEARLY_LB,
    gain_rate,
)


def test_levels_present():
    assert set(LEVELS) == {"beginner", "intermediate", "advanced"}


def test_aragon_helms_bands_pinned():
    assert ARAGON_HELMS_MONTHLY_PCT_BW["beginner"] == pytest.approx((1.0, 1.5))
    assert ARAGON_HELMS_MONTHLY_PCT_BW["intermediate"] == pytest.approx((0.5, 1.0))
    assert ARAGON_HELMS_MONTHLY_PCT_BW["advanced"] == pytest.approx((0.25, 0.5))


def test_mcdonald_yearly_bands_pinned_as_currently_published():
    # Current bodyrecomposition.com text (not the widely-circulated 20-25lb
    # year-1 variant - see module docstring).
    assert MCDONALD_YEARLY_LB[1] == pytest.approx((10.0, 12.0))
    assert MCDONALD_YEARLY_LB[2] == pytest.approx((5.0, 6.0))
    assert MCDONALD_YEARLY_LB[3] == pytest.approx((2.0, 3.0))


def test_gain_rate_beginner_lb():
    r = gain_rate(150, "beginner", unit="lb")
    assert r.monthly_low == pytest.approx(150 * 0.01)
    assert r.monthly_high == pytest.approx(150 * 0.015)
    assert r.yearly_low == pytest.approx(r.monthly_low * 12)
    assert r.yearly_high == pytest.approx(r.monthly_high * 12)


def test_gain_rate_intermediate_matches_bodyrecomposition_worked_example():
    # bodyrecomposition.com's own worked example: 170lb intermediate ->
    # 0.85-1.7 lb/month.
    r = gain_rate(170, "intermediate", unit="lb")
    assert r.monthly_low == pytest.approx(0.85)
    assert r.monthly_high == pytest.approx(1.7)


def test_gain_rate_advanced_close_to_bodyrecomposition_worked_example():
    # bodyrecomposition.com's own worked example rounds this coarsely to
    # "0.5-1 lb/month"; the precise 0.25-0.5% band arithmetic gives 0.45-0.9,
    # which is what this asserts (the exact figure, not their rounded display).
    r = gain_rate(180, "advanced", unit="lb")
    assert r.monthly_low == pytest.approx(0.45)
    assert r.monthly_high == pytest.approx(0.9)


def test_gain_rate_mcdonald_fields_lb():
    r = gain_rate(180, "intermediate", unit="lb")
    assert (r.mcdonald_year1_low, r.mcdonald_year1_high) == pytest.approx((10.0, 12.0))
    assert (r.mcdonald_year2_low, r.mcdonald_year2_high) == pytest.approx((5.0, 6.0))
    assert (r.mcdonald_year3_low, r.mcdonald_year3_high) == pytest.approx((2.0, 3.0))
    assert "minimal" in r.mcdonald_year4_plus_note


def test_gain_rate_mcdonald_fields_converted_to_kg():
    r = gain_rate(80, "intermediate", unit="kg")
    assert r.mcdonald_year1_low == pytest.approx(10.0 * 0.45359237)
    assert r.mcdonald_year1_high == pytest.approx(12.0 * 0.45359237)


def test_gain_rate_bw_pct_unaffected_by_unit_choice():
    # 1% of 180lb and 1% of 80kg are each internally consistent - the %BW
    # fields don't need unit conversion, they scale with whatever bodyweight
    # (and unit) the caller passed in.
    r_lb = gain_rate(180, "beginner", unit="lb")
    r_kg = gain_rate(80, "beginner", unit="kg")
    assert r_lb.monthly_low == pytest.approx(180 * 0.01)
    assert r_kg.monthly_low == pytest.approx(80 * 0.01)


def test_source_label_present_and_honest():
    r = gain_rate(180, "intermediate")
    assert "Aragon" in r.aragon_helms_source_label
    assert "Helms" in r.aragon_helms_source_label
    assert "not independently confirmed" in r.aragon_helms_source_label


def test_informational_note_present():
    r = gain_rate(180, "intermediate")
    assert "not medical" in r.informational_note.lower() or "training math" in r.informational_note.lower()


def test_rejects_nonpositive_bodyweight():
    with pytest.raises(ValueError):
        gain_rate(0, "intermediate")


def test_rejects_unknown_level():
    with pytest.raises(ValueError):
        gain_rate(180, "elite")


def test_rejects_unknown_unit():
    with pytest.raises(ValueError):
        gain_rate(180, "intermediate", unit="stone")
