import pytest

from liftmath.volume import LANDMARKS, band_for, describe_band, landmarks_for, resolve_muscle


def test_all_landmarks_have_mev_below_mrv():
    for muscle, (mv, mev, mav_lo, mav_hi, mrv) in LANDMARKS.items():
        assert mev < mrv, f"{muscle}: MEV must be < MRV"
        assert mv <= mev
        assert mev <= mav_lo
        assert mav_lo <= mav_hi
        assert mav_hi <= mrv


def test_alias_resolves_to_canonical_key():
    assert resolve_muscle("shoulders") == "sidedelts"
    assert resolve_muscle("lats") == "back"
    assert resolve_muscle("Legs") == "quads"


def test_unknown_muscle_raises_keyerror():
    with pytest.raises(KeyError):
        resolve_muscle("not-a-muscle")


def test_band_indirect_ok_for_zero_mev_muscle_at_zero_sets():
    # abs: MEV=0, so 0 direct sets is fine (grows from indirect work).
    assert band_for("abs", 0) == "indirect_ok"


def test_band_sub_mav_for_glutes_at_five_sets():
    # glutes: (MV=0, MEV=4, MAV=8-16, MRV=16). 5 sets is above MEV(4) but below MAV_lo(8).
    assert band_for("glutes", 5) == "sub_mav"


def test_band_productive_for_chest_at_fourteen_sets():
    # chest: (MV=8, MEV=10, MAV=12-20, MRV=22). 14 sets falls in the 12-20 productive range.
    assert band_for("chest", 14) == "productive"


def test_band_over_mrv_for_abs_at_thirty_sets():
    # abs: MRV=25. 30 sets exceeds it.
    assert band_for("abs", 30) == "over_mrv"


def test_band_below_maintenance():
    # chest: MV=8. 5 sets/wk is below maintenance.
    assert band_for("chest", 5) == "below_mv"


def test_band_high_near_mrv():
    # chest: MAV_hi=20, MRV=22. 21 sets is "high".
    assert band_for("chest", 21) == "high"


def test_describe_band_short_and_long_forms():
    assert describe_band("chest", 14) == "productive"
    assert "productive" in describe_band("chest", 14, long=True)


def test_landmarks_for_with_audit():
    # sidedelts: (MV=6, MEV=8, MAV=16-22, MRV=26). 14 sets is above MEV but below MAV_lo.
    info = landmarks_for("shoulders", sets=14)
    assert info.muscle == "sidedelts"
    assert info.mev == 8
    assert info.mrv == 26
    assert info.band == "sub_mav"
    assert info.verdict is not None


def test_landmarks_for_without_audit_leaves_sets_none():
    info = landmarks_for("chest")
    assert info.sets is None
    assert info.band is None
