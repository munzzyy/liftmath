import pytest

from liftmath.tonnage import TonnageSet, session_tonnage


def test_basic_total_tonnage():
    sets = [TonnageSet(weight=225, reps=5), TonnageSet(weight=185, reps=8)]
    r = session_tonnage(sets)
    assert r.total_tonnage == pytest.approx(225 * 5 + 185 * 8)


def test_single_set():
    r = session_tonnage([TonnageSet(weight=100, reps=10)])
    assert r.total_tonnage == pytest.approx(1000)


def test_per_lift_split_when_tagged():
    sets = [
        TonnageSet(weight=225, reps=5, lift="bench"),
        TonnageSet(weight=315, reps=3, lift="squat"),
        TonnageSet(weight=245, reps=5, lift="bench"),
    ]
    r = session_tonnage(sets)
    assert r.per_lift == {"bench": 225 * 5 + 245 * 5, "squat": 315 * 3}


def test_per_lift_none_when_untagged():
    sets = [TonnageSet(weight=225, reps=5), TonnageSet(weight=185, reps=8)]
    r = session_tonnage(sets)
    assert r.per_lift is None


def test_per_lift_groups_untagged_sets_as_unlabeled():
    sets = [TonnageSet(weight=225, reps=5, lift="bench"), TonnageSet(weight=100, reps=5)]
    r = session_tonnage(sets)
    assert r.per_lift == {"bench": 225 * 5, "unlabeled": 100 * 5}


def test_average_intensity_reps_weighted():
    # 5 reps @ 75% + 8 reps @ 60% -> (5*75 + 8*60)/13.
    sets = [
        TonnageSet(weight=225, reps=5, pct_1rm=75),
        TonnageSet(weight=185, reps=8, pct_1rm=60),
    ]
    r = session_tonnage(sets)
    assert r.average_intensity_pct == pytest.approx((5 * 75 + 8 * 60) / 13)


def test_average_intensity_ignores_untagged_sets():
    sets = [
        TonnageSet(weight=225, reps=5, pct_1rm=75),
        TonnageSet(weight=45, reps=20),  # no pct_1rm - excluded from the average
    ]
    r = session_tonnage(sets)
    assert r.average_intensity_pct == pytest.approx(75.0)


def test_average_intensity_none_when_no_sets_tagged():
    sets = [TonnageSet(weight=225, reps=5), TonnageSet(weight=185, reps=8)]
    r = session_tonnage(sets)
    assert r.average_intensity_pct is None


def test_unit_is_carried_through():
    r = session_tonnage([TonnageSet(weight=100, reps=5)], unit="kg")
    assert r.unit == "kg"


def test_rejects_empty_sets():
    with pytest.raises(ValueError):
        session_tonnage([])


def test_rejects_nonpositive_weight():
    with pytest.raises(ValueError):
        session_tonnage([TonnageSet(weight=0, reps=5)])


def test_rejects_nonpositive_reps():
    with pytest.raises(ValueError):
        session_tonnage([TonnageSet(weight=100, reps=0)])
