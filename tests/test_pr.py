import pytest

from liftmath.onerm import estimate_one_rm
from liftmath.pr import check_pr


def test_pr_from_direct_previous_one_rm():
    r = check_pr(previous_one_rm=300, new_weight=275, new_reps=5)
    expected_new = estimate_one_rm(275, 5).consensus
    assert r.previous_estimate.consensus == pytest.approx(300)
    assert r.previous_estimate.is_exact
    assert r.new_estimate.consensus == pytest.approx(expected_new)
    assert r.is_pr == (expected_new > 300)


def test_pr_from_previous_weight_and_reps():
    r = check_pr(previous_weight=275, previous_reps=5, new_weight=285, new_reps=5)
    expected_prev = estimate_one_rm(275, 5).consensus
    expected_new = estimate_one_rm(285, 5).consensus
    assert r.previous_estimate.consensus == pytest.approx(expected_prev)
    assert r.new_estimate.consensus == pytest.approx(expected_new)
    assert r.is_pr is True
    assert r.improvement == pytest.approx(expected_new - expected_prev)


def test_not_a_pr_when_new_set_is_lighter_estimate():
    r = check_pr(previous_one_rm=400, new_weight=300, new_reps=5)
    assert r.is_pr is False
    assert r.improvement < 0


def test_improvement_pct_computed_from_previous_consensus():
    r = check_pr(previous_one_rm=200, new_weight=200, new_reps=1)
    assert r.improvement == pytest.approx(0.0)
    assert r.improvement_pct == pytest.approx(0.0)


def test_unit_carried_through():
    r = check_pr(previous_one_rm=140, new_weight=145, new_reps=1, unit="kg")
    assert r.unit == "kg"
    assert r.previous_estimate.unit == "kg"
    assert r.new_estimate.unit == "kg"


def test_rejects_both_previous_routes_at_once():
    with pytest.raises(ValueError):
        check_pr(previous_one_rm=300, previous_weight=275, previous_reps=5, new_weight=280, new_reps=1)


def test_rejects_no_previous_route():
    with pytest.raises(ValueError):
        check_pr(new_weight=280, new_reps=1)


def test_rejects_partial_previous_weight_reps():
    with pytest.raises(ValueError):
        check_pr(previous_weight=275, new_weight=280, new_reps=1)


def test_propagates_onerm_validation_errors():
    with pytest.raises(ValueError):
        check_pr(previous_one_rm=300, new_weight=0, new_reps=5)
