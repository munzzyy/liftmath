import pytest

from liftmath.rpe import (
    ZOURDOS_2016_ANCHORS,
    pct_1rm_from_reps_and_rir,
    pct_1rm_from_reps_and_rpe,
    rir_to_rpe,
    rpe_from_reps_and_pct,
    rpe_to_rir,
)


def test_rpe_rir_are_defined_as_complements():
    assert rpe_to_rir(10) == 0
    assert rpe_to_rir(7) == 3
    assert rir_to_rpe(0) == 10
    assert rir_to_rpe(3) == 7


def test_one_rep_at_rpe_10_is_exactly_100_percent():
    # The Zourdos (2016) definitional anchor: 1RM = 100% 1RM, RPE 10, 0 RIR.
    # Special-cased rather than run through Epley (which alone gives ~96.8%
    # for a 1-rep set), same as onerm.estimate_one_rm treats reps==1 as exact.
    est = pct_1rm_from_reps_and_rpe(1, 10)
    assert est.pct_1rm == 1.0
    assert est.rir == 0
    assert est.is_extrapolated is False


def test_one_rep_at_zero_rir_matches_rpe_10():
    est = pct_1rm_from_reps_and_rir(1, 0)
    assert est.pct_1rm == 1.0
    assert est.rpe == 10


def test_rpe_from_reps_and_pct_inverts_pct_1rm_from_reps_and_rpe():
    forward = pct_1rm_from_reps_and_rir(5, 2)
    back = rpe_from_reps_and_pct(5, forward.pct_1rm)
    assert back.rir == pytest.approx(2.0, abs=1e-6)
    assert back.rpe == pytest.approx(8.0, abs=1e-6)


def test_more_rir_means_lighter_load_for_the_same_reps():
    heavier = pct_1rm_from_reps_and_rir(5, 0)
    lighter = pct_1rm_from_reps_and_rir(5, 4)
    assert lighter.pct_1rm < heavier.pct_1rm


def test_zourdos_anchors_are_documented_not_hardcoded_as_exact_cells():
    # These are the ONLY 3 points Zourdos (2016) actually measured. Kept here
    # purely as a soft sanity check per the research spec - the derived
    # (Epley-based) model is allowed to diverge from them since the paper
    # itself reports means +/- SD, not a single ground truth, and the spec
    # explicitly says not to pin these as exact cells.
    assert ZOURDOS_2016_ANCHORS["1rm"]["pct_1rm"] == 1.00
    assert ZOURDOS_2016_ANCHORS["1rm"]["rir"] == 0
    assert ZOURDOS_2016_ANCHORS["single_at_90pct"]["pct_1rm"] == 0.90
    assert ZOURDOS_2016_ANCHORS["eight_at_70pct"]["pct_1rm"] == 0.70
    # Sanity check only: derived RIR at the 90% anchor should be single digits,
    # not wildly outside the reported ~0.5-1 RIR range (soft check, generous bound).
    derived = rpe_from_reps_and_pct(1, 0.90)
    assert 0 <= derived.rir <= 5


def test_reps_below_one_raises():
    with pytest.raises(ValueError):
        pct_1rm_from_reps_and_rpe(0, 8)
    with pytest.raises(ValueError):
        rpe_from_reps_and_pct(0, 0.8)


def test_rpe_out_of_range_raises():
    with pytest.raises(ValueError):
        pct_1rm_from_reps_and_rpe(5, 11)
    with pytest.raises(ValueError):
        pct_1rm_from_reps_and_rpe(5, -1)


def test_pct_1rm_out_of_range_raises():
    with pytest.raises(ValueError):
        rpe_from_reps_and_pct(5, 0)
    with pytest.raises(ValueError):
        rpe_from_reps_and_pct(5, 1.5)
