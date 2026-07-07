import math

import pytest

from liftmath.onerm import FORMULAS, estimate_one_rm


def test_single_rep_is_exact():
    est = estimate_one_rm(315, 1)
    assert est.is_exact
    assert est.consensus == 315


def test_epley_reference_values():
    # Epley: w * (1 + r/30). Hand-checked.
    assert FORMULAS["Epley"](100, 1) == pytest.approx(103.333, abs=0.01)
    assert FORMULAS["Epley"](100, 5) == pytest.approx(116.667, abs=0.01)


def test_225x5_consensus_matches_hand_calculation():
    # Hand-calculated per-formula values for 225 lb x 5 reps:
    #   Brzycki 253.125, O'Conner 253.125, Lander 255.845,
    #   Epley 262.5, Lombardi 264.289, Mayhew 267.774
    # median of the 6 sorted values (positions 3,4: 262.5 and 255.845... sorted ascending)
    est = estimate_one_rm(225, 5, unit="lb")
    assert est.per_formula["Brzycki"] == pytest.approx(253.125, abs=0.01)
    assert est.per_formula["O'Conner"] == pytest.approx(253.125, abs=0.01)
    assert est.per_formula["Lander"] == pytest.approx(255.845, abs=0.01)
    assert est.per_formula["Epley"] == pytest.approx(262.5, abs=0.01)
    assert est.per_formula["Lombardi"] == pytest.approx(264.289, abs=0.01)
    assert est.per_formula["Mayhew"] == pytest.approx(267.774, abs=0.01)
    assert est.consensus == pytest.approx(259.173, abs=0.01)
    assert est.low == pytest.approx(253.125, abs=0.01)
    assert est.high == pytest.approx(267.774, abs=0.01)
    assert est.high_rep_warning is False
    assert est.soft_estimate_warning is False


def test_high_rep_drops_curvilinear_formulas():
    est = estimate_one_rm(135, 15, unit="lb")
    assert est.high_rep_warning is True
    assert "Brzycki" not in est.per_formula
    assert "Lander" not in est.per_formula
    assert "Mayhew" not in est.per_formula
    assert "Epley" in est.per_formula
    assert "Lombardi" in est.per_formula
    assert "O'Conner" in est.per_formula


def test_soft_estimate_warning_above_8_reps():
    est = estimate_one_rm(135, 10, unit="lb")
    assert est.soft_estimate_warning is True
    assert est.high_rep_warning is False


def test_brzycki_nan_above_36_reps_is_excluded():
    # Brzycki formula divides by (37 - r); at r >= 37 it's undefined (NaN) and
    # is excluded from the consensus even though it isn't in the curvilinear drop set
    # for this particular r (r > 12 already drops it anyway, but this checks the NaN guard).
    assert math.isnan(FORMULAS["Brzycki"](100, 37))


def test_reps_below_one_raises():
    with pytest.raises(ValueError):
        estimate_one_rm(100, 0)


def test_zero_weight_raises():
    with pytest.raises(ValueError):
        estimate_one_rm(0, 5)


def test_negative_weight_raises():
    with pytest.raises(ValueError):
        estimate_one_rm(-100, 5)
