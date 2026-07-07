import pytest

from liftmath.bodyweight import MOVEMENTS, weighted_bodyweight_one_rm


def test_pullup_total_load_is_bodyweight_plus_added():
    # bw 180 x fraction 1.0 + added 45 = 225 total system load
    r = weighted_bodyweight_one_rm("pullup", 180, 45, 5, unit="lb")
    assert r.total_load == pytest.approx(225.0)
    assert r.bodyweight_fraction == pytest.approx(1.0)


def test_pullup_225lbx5_matches_hand_calculated_consensus():
    # Total load 225lb x 5 reps is the exact same input as test_onerm's
    # 225x5 case, so the consensus must match that hand-checked value (259.173).
    r = weighted_bodyweight_one_rm("pullup", 180, 45, 5, unit="lb")
    assert r.total_load_estimate.consensus == pytest.approx(259.173, abs=0.01)
    # equivalent added-weight 1RM = total consensus - bodyweight*fraction = 259.173 - 180
    assert r.added_weight_one_rm == pytest.approx(79.173, abs=0.01)


def test_added_weight_pct_bodyweight():
    r = weighted_bodyweight_one_rm("pullup", 180, 45, 5, unit="lb")
    # 79.173 / 180 * 100 ~= 43.985
    assert r.added_weight_pct_bodyweight == pytest.approx(43.98, abs=0.01)


def test_dip_uses_full_bodyweight_fraction_too():
    r = weighted_bodyweight_one_rm("dip", 200, 90, 3, unit="lb")
    assert r.total_load == pytest.approx(290.0)
    assert r.bodyweight_fraction == pytest.approx(1.0)


def test_chinup_single_rep_is_exact():
    # reps=1 -> the total load lifted for 1 rep IS the total 1RM (no estimation)
    r = weighted_bodyweight_one_rm("chinup", 75, 20, 1, unit="kg")
    assert r.total_load_estimate.is_exact
    assert r.total_load_estimate.consensus == pytest.approx(95.0)
    assert r.added_weight_one_rm == pytest.approx(20.0)


def test_assisted_pullup_negative_added_weight_is_supported():
    # -60lb assistance: total load 120, still > 0, computes normally
    r = weighted_bodyweight_one_rm("pullup", 180, -60, 8, unit="lb")
    assert r.total_load == pytest.approx(120.0)
    assert r.is_assisted is True
    assert r.added_weight_one_rm < 0  # equivalent added weight is negative (net assist at 1 rep)


def test_unassisted_positive_added_weight_is_not_assisted():
    r = weighted_bodyweight_one_rm("pullup", 180, 45, 5, unit="lb")
    assert r.is_assisted is False


def test_zero_added_weight_is_bodyweight_only_set():
    r = weighted_bodyweight_one_rm("pullup", 180, 0, 8, unit="lb")
    assert r.total_load == pytest.approx(180.0)
    assert r.is_assisted is False


def test_over_assisted_to_zero_or_below_raises():
    # -180 assistance exactly cancels a 180lb bodyweight -> total load 0, invalid
    with pytest.raises(ValueError):
        weighted_bodyweight_one_rm("pullup", 180, -180, 5, unit="lb")


def test_over_assisted_past_bodyweight_raises():
    with pytest.raises(ValueError):
        weighted_bodyweight_one_rm("pullup", 180, -200, 5, unit="lb")


def test_unknown_movement_raises_keyerror():
    with pytest.raises(KeyError):
        weighted_bodyweight_one_rm("muscleup", 180, 45, 5, unit="lb")


def test_zero_bodyweight_raises():
    with pytest.raises(ValueError):
        weighted_bodyweight_one_rm("pullup", 0, 45, 5, unit="lb")


def test_negative_bodyweight_raises():
    with pytest.raises(ValueError):
        weighted_bodyweight_one_rm("pullup", -180, 45, 5, unit="lb")


def test_reps_below_one_raises():
    with pytest.raises(ValueError):
        weighted_bodyweight_one_rm("pullup", 180, 45, 0, unit="lb")


def test_push_up_is_deliberately_not_supported():
    # See bodyweight.py's module docstring: no verified source ties Ebben
    # 2011's push-up ground-reaction-force measurement to a weighted-push-up
    # 1RM fraction specifically, so it's left out rather than guessed.
    assert "pushup" not in MOVEMENTS


def test_movements_only_has_verified_fractions():
    assert set(MOVEMENTS) == {"pullup", "chinup", "dip"}
    assert all(frac == 1.0 for frac in MOVEMENTS.values())
