import pytest

from liftmath.prilepin import (
    ZONES,
    classify_weekly_inol,
    classify_workout_inol,
    evaluate_scheme,
    inol_of_set,
    inol_total,
    zone_for_pct,
)

# ---------------------------------------------------------------------------
# Zone lookup
# ---------------------------------------------------------------------------


def test_zone_below_70():
    z = zone_for_pct(60)
    assert z.label == "<70%"
    assert (z.reps_per_set_low, z.reps_per_set_high) == (3, 6)
    assert (z.total_reps_low, z.total_reps_high) == (18, 30)
    assert z.optimal_total_reps == 24


def test_zone_69_is_below_70_band():
    assert zone_for_pct(69).label == "<70%"


def test_zone_70_79():
    z = zone_for_pct(75)
    assert z.label == "70-79%"
    assert (z.reps_per_set_low, z.reps_per_set_high) == (3, 6)
    assert (z.total_reps_low, z.total_reps_high) == (12, 24)
    assert z.optimal_total_reps == 18


def test_zone_boundary_70_is_in_70_79_band():
    assert zone_for_pct(70).label == "70-79%"


def test_zone_80_89():
    z = zone_for_pct(85)
    assert z.label == "80-89%"
    assert (z.reps_per_set_low, z.reps_per_set_high) == (2, 4)
    assert (z.total_reps_low, z.total_reps_high) == (10, 20)
    assert z.optimal_total_reps == 15


def test_zone_boundary_80_is_in_80_89_band():
    assert zone_for_pct(80).label == "80-89%"


def test_zone_boundary_89point9_is_in_80_89_band():
    # Half-open bins at 70/80/90 - see module docstring.
    assert zone_for_pct(89.9).label == "80-89%"


def test_zone_above_89():
    z = zone_for_pct(95)
    assert z.label == ">89%"
    assert (z.reps_per_set_low, z.reps_per_set_high) == (1, 2)
    assert (z.total_reps_low, z.total_reps_high) == (4, 10)
    assert z.optimal_total_reps == 7
    assert z.max_pct is None


def test_zone_boundary_90_is_above_89_band():
    assert zone_for_pct(90).label == ">89%"


def test_zone_rejects_nonpositive_pct():
    with pytest.raises(ValueError):
        zone_for_pct(0)
    with pytest.raises(ValueError):
        zone_for_pct(-5)


def test_zones_table_shape():
    assert len(ZONES) == 4
    assert [z.label for z in ZONES] == ["<70%", "70-79%", "80-89%", ">89%"]


# ---------------------------------------------------------------------------
# Scheme evaluation
# ---------------------------------------------------------------------------


def test_evaluate_scheme_optimal():
    # 5x3 @ 75% -> 15 total reps, zone 70-79% range is 12-24 -> optimal.
    e = evaluate_scheme(5, 3, 75)
    assert e.zone.label == "70-79%"
    assert e.total_reps == 15
    assert e.verdict == "optimal"
    assert e.reps_per_set_in_range is True
    assert e.reps_to_optimal == 18 - 15


def test_evaluate_scheme_under():
    # 2x2 @ 75% -> 4 total reps, below the 12-24 range.
    e = evaluate_scheme(2, 2, 75)
    assert e.total_reps == 4
    assert e.verdict == "under"


def test_evaluate_scheme_over():
    # 10x3 @ 75% -> 30 total reps, above the 12-24 range.
    e = evaluate_scheme(10, 3, 75)
    assert e.total_reps == 30
    assert e.verdict == "over"


def test_evaluate_scheme_exactly_at_low_boundary_is_optimal():
    # 4x3 @ 75% -> 12 total reps, exactly the zone's low bound.
    e = evaluate_scheme(4, 3, 75)
    assert e.total_reps == 12
    assert e.verdict == "optimal"


def test_evaluate_scheme_exactly_at_high_boundary_is_optimal():
    # 8x3 @ 75% -> 24 total reps, exactly the zone's high bound.
    e = evaluate_scheme(8, 3, 75)
    assert e.total_reps == 24
    assert e.verdict == "optimal"


def test_evaluate_scheme_flags_reps_per_set_out_of_range():
    # 2x8 @ 75% -> 16 total reps (optimal range), but 8 reps/set is outside
    # this zone's 3-6 rep/set prescription.
    e = evaluate_scheme(2, 8, 75)
    assert e.verdict == "optimal"
    assert e.reps_per_set_in_range is False


def test_evaluate_scheme_rejects_nonpositive_sets_or_reps():
    with pytest.raises(ValueError):
        evaluate_scheme(0, 3, 75)
    with pytest.raises(ValueError):
        evaluate_scheme(3, 0, 75)


# ---------------------------------------------------------------------------
# INOL: paper's own worked examples (pinned exactly, per the research brief)
# ---------------------------------------------------------------------------


def test_inol_of_set_basic():
    assert inol_of_set(6, 60) == pytest.approx(6 / 40)
    assert inol_of_set(3, 75) == pytest.approx(3 / 25)


def test_inol_of_set_rejects_bad_inputs():
    with pytest.raises(ValueError):
        inol_of_set(0, 75)
    with pytest.raises(ValueError):
        inol_of_set(5, 100)
    with pytest.raises(ValueError):
        inol_of_set(5, 0)


def test_worked_example_bench_2x6_60_5x3_75():
    # Hristov's own arithmetic: 0.3 + 0.6 = 0.9.
    result = inol_total([(2, 6, 60), (5, 3, 75)])
    assert result.groups[0].inol == pytest.approx(0.3)
    assert result.groups[1].inol == pytest.approx(0.6)
    assert result.total == pytest.approx(0.9)


def test_worked_example_6x4_at_72pct():
    result = inol_total([(6, 4, 72)])
    assert result.total == pytest.approx(24 / 28)
    assert round(result.total, 2) == 0.86


def test_worked_example_6x4_at_77pct():
    result = inol_total([(6, 4, 77)])
    assert result.total == pytest.approx(24 / 23)
    assert round(result.total, 2) == 1.04


def test_inol_total_rejects_empty_groups():
    with pytest.raises(ValueError):
        inol_total([])


# ---------------------------------------------------------------------------
# INOL bands - per-workout and weekly, every boundary pinned
# ---------------------------------------------------------------------------


def test_workout_band_under_0_4():
    assert classify_workout_inol(0.39) == "too few reps, not enough stimulus?"


def test_workout_band_boundary_0_4():
    assert classify_workout_inol(0.4) == "fresh, quite doable and optimal if you are not accumulating fatigue"


def test_workout_band_0_4_to_1():
    assert classify_workout_inol(0.7) == "fresh, quite doable and optimal if you are not accumulating fatigue"


def test_workout_band_boundary_1():
    assert classify_workout_inol(1.0) == "fresh, quite doable and optimal if you are not accumulating fatigue"


def test_workout_band_1_to_2():
    assert classify_workout_inol(1.5) == "tough, but good for loading phases"


def test_workout_band_boundary_2():
    assert classify_workout_inol(2.0) == "tough, but good for loading phases"


def test_workout_band_over_2():
    assert classify_workout_inol(2.01) == "brutal"


def test_weekly_band_under_2():
    assert classify_weekly_inol(1.9) == "easy, doable, good to do after more tiring weeks and prepeaking"


def test_weekly_band_boundary_2():
    assert classify_weekly_inol(2.0) == "tough but doable, good for loading phases between"


def test_weekly_band_2_to_3():
    assert classify_weekly_inol(2.5) == "tough but doable, good for loading phases between"


def test_weekly_band_boundary_3():
    assert classify_weekly_inol(3.0) == "tough but doable, good for loading phases between"


def test_weekly_band_3_to_4():
    assert classify_weekly_inol(3.5) == "brutal, lots of fatigue, good for a limited time and shock microcycles"


def test_weekly_band_boundary_4():
    assert classify_weekly_inol(4.0) == "brutal, lots of fatigue, good for a limited time and shock microcycles"


def test_weekly_band_over_4():
    assert classify_weekly_inol(4.01) == "Are you out of your mind?"


def test_inol_result_carries_both_bands():
    result = inol_total([(2, 6, 60), (5, 3, 75)])
    assert result.workout_band == "fresh, quite doable and optimal if you are not accumulating fatigue"
    assert result.weekly_band == "easy, doable, good to do after more tiring weeks and prepeaking"
