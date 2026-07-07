import pytest

from liftmath.sessionload import (
    FOSTER_2001_TABLE_5_MONOTONY,
    FOSTER_2001_TABLE_5_SESSION_LOADS,
    FOSTER_2001_TABLE_5_STRAIN,
    FOSTER_2001_TABLE_5_WEEKLY_LOAD,
    session_load,
    weekly_load,
)


def test_session_load_is_rpe_times_duration():
    assert session_load(5, 180) == 900
    assert session_load(7, 120) == 840


def test_session_load_rejects_out_of_range_rpe():
    with pytest.raises(ValueError):
        session_load(11, 60)
    with pytest.raises(ValueError):
        session_load(-1, 60)


def test_session_load_rejects_negative_duration():
    with pytest.raises(ValueError):
        session_load(5, -10)


def test_foster_2001_table_5_weekly_load_matches_printed_total():
    # Foster et al. (2001), Table 5's own worked example: weekly load = 3400,
    # exactly the sum of the paper's own PRINTED per-session loads (not
    # recomputed RPE*duration - see module docstring for the Sunday 940-vs-900
    # transcription quirk).
    result = weekly_load(list(FOSTER_2001_TABLE_5_SESSION_LOADS))
    assert result.weekly_load == FOSTER_2001_TABLE_5_WEEKLY_LOAD == 3400


def test_foster_2001_table_5_monotony_matches_printed_value_when_rounded():
    # The paper prints monotony = 1.26. That only reproduces when mean/SD are
    # taken over the 9 individual SESSION rows (not 7 pre-summed day buckets -
    # see module docstring for how this was resolved against the alternative).
    result = weekly_load(list(FOSTER_2001_TABLE_5_SESSION_LOADS))
    assert round(result.monotony, 2) == FOSTER_2001_TABLE_5_MONOTONY == 1.26


def test_foster_2001_table_5_strain_matches_printed_value_via_rounded_monotony():
    # The paper's printed strain (4284) is weekly_load * ROUNDED monotony
    # (3400 * 1.26 = 4284 exactly), not weekly_load * full-precision monotony
    # (which gives ~4299.69). This is the paper's own rounding cascade, not a
    # bug in this module - pinning both numbers so a future maintainer can
    # see the relationship instead of "fixing" one to match the other.
    result = weekly_load(list(FOSTER_2001_TABLE_5_SESSION_LOADS))
    assert FOSTER_2001_TABLE_5_WEEKLY_LOAD * round(result.monotony, 2) == FOSTER_2001_TABLE_5_STRAIN == 4284
    assert result.strain == pytest.approx(4299.69, abs=0.01)


def test_higher_monotony_for_more_uniform_loads():
    uniform_ish = weekly_load([300, 310, 290, 305, 295, 300, 300])
    varied = weekly_load([100, 500, 100, 500, 100, 500, 100])
    assert uniform_ish.monotony > varied.monotony


def test_weekly_load_rejects_empty_list():
    with pytest.raises(ValueError):
        weekly_load([])


def test_weekly_load_rejects_zero_variance():
    with pytest.raises(ValueError):
        weekly_load([300, 300, 300])


def test_weekly_load_rejects_all_zero():
    with pytest.raises(ValueError):
        weekly_load([0, 0, 0])
