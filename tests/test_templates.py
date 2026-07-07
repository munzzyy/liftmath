import pytest

from liftmath.templates import (
    T1_STAGES,
    T2_STAGES,
    T3_AMRAP_THRESHOLD,
    gzclp_next_session,
    nsuns_day,
    program_531,
    round_to_increment,
    training_max,
)

# --- round_to_increment -----------------------------------------------------


def test_round_down_default_behavior():
    assert round_to_increment(283.5, 5, direction="down") == 280.0


def test_round_up():
    assert round_to_increment(283.5, 5, direction="up") == 285.0


def test_round_nearest():
    assert round_to_increment(282.4, 5, direction="nearest") == 280.0
    assert round_to_increment(283.0, 5, direction="nearest") == 285.0


def test_round_exact_multiple_stays_put():
    assert round_to_increment(270.0, 5, direction="down") == 270.0


def test_round_kg_increment():
    assert round_to_increment(126.0, 2.5, direction="down") == 125.0


def test_round_rejects_non_positive_increment():
    with pytest.raises(ValueError):
        round_to_increment(100, 0)
    with pytest.raises(ValueError):
        round_to_increment(100, -5)


def test_round_rejects_unknown_direction():
    with pytest.raises(ValueError):
        round_to_increment(100, 5, direction="sideways")


# --- training_max -------------------------------------------------------------


def test_training_max_default_90_pct_lb():
    # 315 * 0.90 = 283.5 -> round down to nearest 5 -> 280
    tm = training_max(315, unit="lb")
    assert tm.training_max == pytest.approx(280.0)
    assert tm.pct == pytest.approx(0.90)
    assert tm.increment == pytest.approx(5.0)


def test_training_max_default_90_pct_kg():
    # 140 * 0.90 = 126 -> round down to nearest 2.5 -> 125
    tm = training_max(140, unit="kg")
    assert tm.training_max == pytest.approx(125.0)
    assert tm.increment == pytest.approx(2.5)


def test_training_max_custom_pct():
    # 315 * 0.85 = 267.75 -> round down to nearest 5 -> 265
    tm = training_max(315, pct=0.85, unit="lb")
    assert tm.training_max == pytest.approx(265.0)


def test_training_max_custom_increment():
    tm = training_max(315, increment=10, unit="lb")
    # 315*0.9 = 283.5 -> round down to nearest 10 -> 280
    assert tm.training_max == pytest.approx(280.0)


def test_training_max_exact_multiple_of_increment():
    # 300 * 0.90 = 270, already a multiple of 5
    tm = training_max(300, unit="lb")
    assert tm.training_max == pytest.approx(270.0)


def test_training_max_rejects_non_positive_one_rm():
    with pytest.raises(ValueError):
        training_max(0, unit="lb")
    with pytest.raises(ValueError):
        training_max(-100, unit="lb")


def test_training_max_rejects_pct_below_80():
    with pytest.raises(ValueError):
        training_max(315, pct=0.79)


def test_training_max_rejects_pct_above_100():
    with pytest.raises(ValueError):
        training_max(315, pct=1.01)


def test_training_max_accepts_pct_boundaries():
    training_max(315, pct=0.80)
    training_max(315, pct=1.00)


# --- program_531 ----------------------------------------------------------------


def test_531_week2_top_set_tm300_matches_brief_worked_example():
    # TM 300 lb, week 2 top (3rd) set: 90% x 300 = 270, already a multiple of 5.
    # Reps 3, AMRAP (the '+' set).
    week = program_531(300, 2)
    top = week.sets[-1]
    assert top.weight == pytest.approx(270.0)
    assert top.reps == 3
    assert top.amrap is True


def test_531_week1_percentages_and_reps():
    week = program_531(300, 1)
    pcts = [s.pct_tm for s in week.sets]
    reps = [s.reps for s in week.sets]
    amraps = [s.amrap for s in week.sets]
    assert pcts == pytest.approx([0.65, 0.75, 0.85])
    assert reps == [5, 5, 5]
    assert amraps == [False, False, True]
    weights = [s.weight for s in week.sets]
    # 300*.65=195, 300*.75=225, 300*.85=255 - all exact multiples of 5
    assert weights == pytest.approx([195.0, 225.0, 255.0])


def test_531_week2_percentages_and_reps():
    week = program_531(300, 2)
    assert [s.pct_tm for s in week.sets] == pytest.approx([0.70, 0.80, 0.90])
    assert [s.reps for s in week.sets] == [3, 3, 3]
    assert [s.amrap for s in week.sets] == [False, False, True]


def test_531_week3_percentages_and_reps():
    week = program_531(300, 3)
    assert [s.pct_tm for s in week.sets] == pytest.approx([0.75, 0.85, 0.95])
    assert [s.reps for s in week.sets] == [5, 3, 1]
    assert [s.amrap for s in week.sets] == [False, False, True]
    weights = [s.weight for s in week.sets]
    # 300*.75=225, 300*.85=255, 300*.95=285 - all exact multiples of 5
    assert weights == pytest.approx([225.0, 255.0, 285.0])


def test_531_week4_is_deload_no_amrap():
    week = program_531(300, 4)
    assert week.is_deload is True
    assert [s.pct_tm for s in week.sets] == pytest.approx([0.40, 0.50, 0.60])
    assert [s.reps for s in week.sets] == [5, 5, 5]
    assert all(not s.amrap for s in week.sets)


def test_531_weeks_1_to_3_are_not_deload():
    for w in (1, 2, 3):
        assert program_531(300, w).is_deload is False


def test_531_rounds_down_on_non_exact_percentages():
    # TM 285: week1 top .85*285=242.25 -> round down to nearest 5 -> 240
    week = program_531(285, 1)
    assert week.sets[-1].weight == pytest.approx(240.0)


def test_531_kg_increment():
    week = program_531(200, 2, increment=2.5)
    # 200*.90=180, already exact for 2.5 increment
    assert week.sets[-1].weight == pytest.approx(180.0)


def test_531_rejects_non_positive_tm():
    with pytest.raises(ValueError):
        program_531(0, 1)


def test_531_rejects_bad_week():
    with pytest.raises(ValueError):
        program_531(300, 0)
    with pytest.raises(ValueError):
        program_531(300, 5)


# --- GZCLP state machine --------------------------------------------------------


def test_gzclp_t1_made_lower_adds_10lb_stays_at_stage():
    r = gzclp_next_session("t1", "5x3", 300, True, lift_type="lower", unit="lb")
    assert r.next_stage == "5x3"
    assert r.next_weight == pytest.approx(310.0)
    assert r.needs_retest is False


def test_gzclp_t1_made_upper_adds_5lb():
    r = gzclp_next_session("t1", "5x3", 200, True, lift_type="upper", unit="lb")
    assert r.next_weight == pytest.approx(205.0)


def test_gzclp_t1_made_lower_kg_adds_5kg():
    r = gzclp_next_session("t1", "5x3", 100, True, lift_type="lower", unit="kg")
    assert r.next_weight == pytest.approx(105.0)


def test_gzclp_t1_made_upper_kg_adds_2_5kg():
    r = gzclp_next_session("t1", "5x3", 60, True, lift_type="upper", unit="kg")
    assert r.next_weight == pytest.approx(62.5)


def test_gzclp_t1_missed_5x3_advances_to_6x2_same_weight():
    r = gzclp_next_session("t1", "5x3", 300, False, lift_type="lower", unit="lb")
    assert r.next_stage == "6x2"
    assert r.next_weight == pytest.approx(300.0)
    assert r.needs_retest is False


def test_gzclp_t1_missed_6x2_advances_to_10x1_same_weight():
    r = gzclp_next_session("t1", "6x2", 300, False, lift_type="lower", unit="lb")
    assert r.next_stage == "10x1"
    assert r.next_weight == pytest.approx(300.0)


def test_gzclp_t1_missed_10x1_the_last_stage_needs_retest():
    r = gzclp_next_session("t1", "10x1", 300, False, lift_type="lower", unit="lb")
    assert r.needs_retest is True
    assert r.next_stage == "5x3"
    assert "retest" in r.note.lower()


def test_gzclp_t2_made_upper_adds_2_5lb():
    r = gzclp_next_session("t2", "3x10", 150, True, lift_type="upper", unit="lb")
    assert r.next_stage == "3x10"
    assert r.next_weight == pytest.approx(152.5)


def test_gzclp_t2_made_lower_adds_5lb():
    r = gzclp_next_session("t2", "3x10", 150, True, lift_type="lower", unit="lb")
    assert r.next_weight == pytest.approx(155.0)


def test_gzclp_t2_missed_3x10_advances_to_3x8():
    r = gzclp_next_session("t2", "3x10", 150, False, lift_type="lower", unit="lb")
    assert r.next_stage == "3x8"
    assert r.next_weight == pytest.approx(150.0)


def test_gzclp_t2_missed_3x8_advances_to_3x6():
    r = gzclp_next_session("t2", "3x8", 150, False, lift_type="lower", unit="lb")
    assert r.next_stage == "3x6"
    assert r.next_weight == pytest.approx(150.0)


def test_gzclp_t2_missed_3x6_the_last_stage_restarts_3x10_with_bump():
    # documented bump: +10lb (see T2_RESTART_BUMP)
    r = gzclp_next_session("t2", "3x6", 150, False, lift_type="lower", unit="lb")
    assert r.next_stage == "3x10"
    assert r.next_weight == pytest.approx(160.0)
    assert r.needs_retest is False


def test_gzclp_t2_missed_3x6_kg_bump_is_5kg():
    r = gzclp_next_session("t2", "3x6", 70, False, lift_type="lower", unit="kg")
    assert r.next_weight == pytest.approx(75.0)


def test_gzclp_t3_amrap_at_threshold_adds_increment():
    r = gzclp_next_session("t3", "", 50, True, lift_type="upper", unit="lb",
                            amrap_reps=T3_AMRAP_THRESHOLD)
    assert r.next_weight == pytest.approx(52.5)  # T2 upper lb increment = 2.5


def test_gzclp_t3_amrap_above_threshold_adds_increment():
    r = gzclp_next_session("t3", "", 50, True, lift_type="upper", unit="lb", amrap_reps=30)
    assert r.next_weight == pytest.approx(52.5)


def test_gzclp_t3_amrap_below_threshold_repeats_weight():
    r = gzclp_next_session("t3", "", 50, True, lift_type="upper", unit="lb", amrap_reps=24)
    assert r.next_weight == pytest.approx(50.0)


def test_gzclp_t3_requires_amrap_reps():
    with pytest.raises(ValueError):
        gzclp_next_session("t3", "", 50, True, lift_type="upper", unit="lb")


def test_gzclp_t3_rejects_negative_amrap_reps():
    with pytest.raises(ValueError):
        gzclp_next_session("t3", "", 50, True, lift_type="upper", unit="lb", amrap_reps=-1)


def test_gzclp_rejects_unknown_tier():
    with pytest.raises(ValueError):
        gzclp_next_session("t4", "5x3", 300, True, unit="lb")


def test_gzclp_rejects_unknown_stage_for_tier():
    with pytest.raises(ValueError):
        gzclp_next_session("t1", "3x10", 300, True, unit="lb")  # that's a T2 stage
    with pytest.raises(ValueError):
        gzclp_next_session("t2", "5x3", 300, True, unit="lb")  # that's a T1 stage


def test_gzclp_rejects_unknown_lift_type():
    with pytest.raises(ValueError):
        gzclp_next_session("t1", "5x3", 300, True, lift_type="sideways", unit="lb")


def test_gzclp_rejects_unknown_unit():
    with pytest.raises(ValueError):
        gzclp_next_session("t1", "5x3", 300, True, unit="stone")


def test_gzclp_rejects_non_positive_weight():
    with pytest.raises(ValueError):
        gzclp_next_session("t1", "5x3", 0, True, unit="lb")
    with pytest.raises(ValueError):
        gzclp_next_session("t1", "5x3", -50, True, unit="lb")


def test_gzclp_t1_and_t2_stage_orders_are_the_documented_ones():
    assert T1_STAGES == ("5x3", "6x2", "10x1")
    assert T2_STAGES == ("3x10", "3x8", "3x6")


# --- nsuns_day ------------------------------------------------------------------


def test_nsuns_bench_day1_scheme_a_percentages_reps_amrap():
    d = nsuns_day("bench_day1", 200)
    assert d.scheme == "A"
    pcts = [s.pct_tm for s in d.sets]
    reps = [s.reps for s in d.sets]
    amraps = [s.amrap for s in d.sets]
    assert pcts == pytest.approx([0.65, 0.75, 0.85, 0.85, 0.85, 0.80, 0.75, 0.70, 0.65])
    assert reps == [8, 6, 4, 4, 4, 5, 6, 7, 8]
    assert amraps == [False, False, False, False, False, False, False, False, True]
    assert len(d.sets) == 9


def test_nsuns_bench_day1_weights_tm200():
    d = nsuns_day("bench_day1", 200)
    weights = [s.weight for s in d.sets]
    # 200 * each pct, all exact multiples of 5 already
    assert weights == pytest.approx([130.0, 150.0, 170.0, 170.0, 170.0, 160.0, 150.0, 140.0, 130.0])


def test_nsuns_squat_day2_scheme_b_percentages_reps_amrap():
    d = nsuns_day("squat_day2", 300)
    assert d.scheme == "B"
    pcts = [s.pct_tm for s in d.sets]
    reps = [s.reps for s in d.sets]
    amraps = [s.amrap for s in d.sets]
    assert pcts == pytest.approx([0.75, 0.85, 0.95, 0.90, 0.85, 0.80, 0.75, 0.70, 0.65])
    assert reps == [5, 3, 1, 3, 3, 3, 3, 3, 3]
    # both the 95% set (set 3) and final 65% set (set 9) are AMRAP
    assert amraps == [False, False, True, False, False, False, False, False, True]
    assert len(d.sets) == 9


def test_nsuns_squat_day2_weights_tm300():
    d = nsuns_day("squat_day2", 300)
    weights = [s.weight for s in d.sets]
    assert weights == pytest.approx([225.0, 255.0, 285.0, 270.0, 255.0, 240.0, 225.0, 210.0, 195.0])


def test_nsuns_bench_day3_and_deadlift_day4_use_scheme_b_too():
    assert nsuns_day("bench_day3", 300).scheme == "B"
    assert nsuns_day("deadlift_day4", 300).scheme == "B"


def test_nsuns_rounds_down_on_non_exact_percentages():
    # TM 287: set1 .75*287=215.25 -> round down to nearest 5 -> 215
    d = nsuns_day("squat_day2", 287)
    assert d.sets[0].weight == pytest.approx(215.0)


def test_nsuns_rejects_unknown_day():
    with pytest.raises(ValueError):
        nsuns_day("overhead_day5", 200)


def test_nsuns_rejects_non_positive_tm():
    with pytest.raises(ValueError):
        nsuns_day("bench_day1", 0)
