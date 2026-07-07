import pytest

from liftmath.loads import load_chart, pct_to_reps, reps_to_pct, target_load


@pytest.mark.parametrize("pct,expected_reps", [
    (1.00, 1),
    (0.95, 2),
    (0.90, 3),
    (0.85, 5),
    (0.80, 8),
    (0.75, 10),
    (0.70, 13),
    (0.65, 16),
    (0.60, 20),
    (0.50, 30),
])
def test_pct_to_reps_reference_values(pct, expected_reps):
    assert pct_to_reps(pct) == expected_reps


def test_pct_to_reps_zero_raises_value_error_not_zero_division_error():
    with pytest.raises(ValueError):
        pct_to_reps(0.0)


def test_pct_to_reps_negative_raises_value_error():
    with pytest.raises(ValueError):
        pct_to_reps(-0.5)


def test_reps_to_pct_reference_values():
    assert reps_to_pct(8) == pytest.approx(0.789474, abs=1e-5)
    assert reps_to_pct(10) == pytest.approx(0.75, abs=1e-9)


def test_reps_pct_round_trip_is_consistent():
    assert pct_to_reps(reps_to_pct(10)) == 10


def test_load_chart_rows_use_1rm_scaling():
    chart = load_chart(315, unit="lb")
    row_90 = next(r for r in chart.rows if r.pct == 0.90)
    assert row_90.load == pytest.approx(283.5, abs=0.01)
    assert row_90.max_reps == 3


def test_target_load_without_rir():
    # reps_to_pct(8) == 0.789474 (Epley inverse: 1 / (1 + 8/30))
    result = target_load(315, 8)
    assert result.pct == pytest.approx(0.789474, abs=1e-5)
    assert result.load == pytest.approx(248.68, abs=0.01)
    assert result.rir_load is None


def test_target_load_with_rir():
    # 8 reps at 2 RIR means the effective max-rep target is 10.
    result = target_load(315, 8, rir=2)
    assert result.rir_max_reps == 10
    assert result.rir_pct == pytest.approx(0.75, abs=1e-9)
    assert result.rir_load == pytest.approx(236.25, abs=0.01)


def test_target_load_rejects_zero_one_rm():
    with pytest.raises(ValueError):
        target_load(0, 5)


def test_target_load_rejects_negative_one_rm():
    with pytest.raises(ValueError):
        target_load(-100, 5)


def test_target_load_rejects_reps_below_one():
    with pytest.raises(ValueError):
        target_load(315, 0)
    with pytest.raises(ValueError):
        target_load(315, -5)


def test_target_load_rejects_negative_rir():
    with pytest.raises(ValueError):
        target_load(315, 5, rir=-3)
