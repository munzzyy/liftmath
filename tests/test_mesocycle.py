import pytest

from liftmath.mesocycle import ramp_mesocycle


def test_chest_five_week_ramp_hits_mev_and_mrv():
    # chest: MEV=10, MRV=22. 5 weeks -> 4 accumulation weeks + 1 deload.
    meso = ramp_mesocycle("chest", weeks=5)
    assert meso.mev == 10
    assert meso.mrv == 22
    assert len(meso.weeks) == 5
    assert meso.weeks[0].sets == 10          # week 1 starts at MEV
    assert meso.weeks[3].sets == 22          # week 4 (last accumulation week) reaches MRV
    assert meso.weeks[3].is_deload is False
    assert meso.weeks[4].is_deload is True
    assert meso.weeks[4].sets == 5           # deload: round(10 * 0.5) == 5


def test_intermediate_weeks_interpolate_linearly():
    meso = ramp_mesocycle("chest", weeks=5)
    # accumulation weeks 1..4 span MEV(10) to MRV(22): 10, 14, 18, 22
    assert [w.sets for w in meso.weeks[:4]] == [10, 14, 18, 22]


def test_two_week_meso_is_mev_then_deload():
    meso = ramp_mesocycle("back", weeks=2)
    assert len(meso.weeks) == 2
    assert meso.weeks[0].sets == meso.mev
    assert meso.weeks[1].is_deload


def test_weeks_below_two_raises():
    with pytest.raises(ValueError):
        ramp_mesocycle("chest", weeks=1)


def test_unknown_muscle_raises_keyerror():
    with pytest.raises(KeyError):
        ramp_mesocycle("not-a-muscle", weeks=5)


def test_alias_resolves_before_ramping():
    meso = ramp_mesocycle("shoulders", weeks=3)
    assert meso.muscle == "sidedelts"
