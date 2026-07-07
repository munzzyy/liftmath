import pytest

from liftmath.progression import DEFAULT_INCREMENT_KG, DEFAULT_INCREMENT_LB, next_progression_step


def test_below_top_of_range_repeats_weight_and_adds_a_rep():
    # Range 8-12, 185lb x 11 reps, increment 5lb -> repeat 185, aim for 12.
    step = next_progression_step(8, 12, 185, 11, 5)
    assert step.at_top_of_range is False
    assert step.next_weight == 185
    assert step.next_target_reps == 12


def test_at_top_of_range_adds_load_and_resets():
    # Range 8-12, 185lb x 12 reps, increment 5lb -> increase to 190, reset to 8.
    step = next_progression_step(8, 12, 185, 12, 5)
    assert step.at_top_of_range is True
    assert step.next_weight == 190
    assert step.next_target_reps == 8


def test_lower_body_lift_larger_increment():
    # Range 5-8, 225lb x 8 reps, increment 10lb (lower-body) -> 235, reset to 5.
    step = next_progression_step(5, 8, 225, 8, 10)
    assert step.next_weight == 235
    assert step.next_target_reps == 5


def test_reps_achieved_beyond_top_still_resets_target_to_bottom():
    step = next_progression_step(8, 12, 185, 15, 5)
    assert step.at_top_of_range is True
    assert step.next_target_reps == 8


def test_default_increments_documented_not_fitted():
    assert DEFAULT_INCREMENT_KG["upper"] == 2.5
    assert DEFAULT_INCREMENT_KG["lower"] == 5.0
    assert DEFAULT_INCREMENT_LB["upper"] == 5.0
    assert DEFAULT_INCREMENT_LB["lower"] == 10.0


def test_invalid_range_raises():
    with pytest.raises(ValueError):
        next_progression_step(12, 8, 185, 10, 5)
    with pytest.raises(ValueError):
        next_progression_step(8, 8, 185, 10, 5)


def test_nonpositive_increment_raises():
    with pytest.raises(ValueError):
        next_progression_step(8, 12, 185, 10, 0)


def test_zero_reps_achieved_raises():
    with pytest.raises(ValueError):
        next_progression_step(8, 12, 185, 0, 5)
