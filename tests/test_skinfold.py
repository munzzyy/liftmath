import pytest

from liftmath.skinfold import (
    jackson_pollock_men_3site,
    jackson_pollock_men_7site,
    jackson_pollock_women_3site,
    jackson_pollock_women_7site,
    siri_bodyfat_pct,
)

# Reference values below are hand-computed with Python floats from the
# verbatim coefficients in the module docstring, independent of the
# implementation under test.


def test_siri_basic():
    # BD 1.07 -> 495/1.07 - 450 = 12.6168...
    assert siri_bodyfat_pct(1.07) == pytest.approx(495.0 / 1.07 - 450.0)


def test_siri_rejects_nonpositive_density():
    with pytest.raises(ValueError):
        siri_bodyfat_pct(0)
    with pytest.raises(ValueError):
        siri_bodyfat_pct(-1.0)


def test_men_3site_reference_value():
    # chest=10, triceps=12, subscapular=15, age=30 -> sum=37.
    r = jackson_pollock_men_3site(chest_mm=10, triceps_mm=12, subscapular_mm=15, age=30)
    assert r.sex == "male"
    assert r.method == "3-site"
    assert r.sum_mm == pytest.approx(37)
    assert r.body_density == pytest.approx(1.0641494999999999)
    assert r.bodyfat_pct == pytest.approx(15.160205403470172)
    assert r.sites_mm == {"chest_mm": 10, "triceps_mm": 12, "subscapular_mm": 15}


def test_men_3site_second_reference_value():
    # chest=20, triceps=15, subscapular=18, age=45 -> sum=53.
    r = jackson_pollock_men_3site(chest_mm=20, triceps_mm=15, subscapular_mm=18, age=45)
    assert r.sum_mm == pytest.approx(53)
    assert r.body_density == pytest.approx(1.0474094999999999)
    assert r.bodyfat_pct == pytest.approx(22.594529646714136)


def test_men_7site_reference_value():
    # chest=8, axilla=10, triceps=12, subscapular=14, abdominal=20,
    # suprailiac=15, thigh=18, age=25 -> sum=97.
    r = jackson_pollock_men_7site(
        chest_mm=8, axilla_mm=10, triceps_mm=12, subscapular_mm=14,
        abdominal_mm=20, suprailiac_mm=15, thigh_mm=18, age=25,
    )
    assert r.method == "7-site"
    assert r.sum_mm == pytest.approx(97)
    assert r.body_density == pytest.approx(1.0677744200000001)
    assert r.bodyfat_pct == pytest.approx(13.581062374579005)


def test_women_3site_reference_value():
    # triceps=15, thigh=20, suprailiac=12, age=28 -> sum=47.
    r = jackson_pollock_women_3site(triceps_mm=15, thigh_mm=20, suprailiac_mm=12, age=28)
    assert r.sex == "female"
    assert r.method == "3-site"
    assert r.sum_mm == pytest.approx(47)
    assert r.body_density == pytest.approx(1.0540089)
    assert r.bodyfat_pct == pytest.approx(19.635503077820374)


def test_women_3site_second_reference_value():
    # triceps=18, thigh=25, suprailiac=16, age=35 -> sum=59.
    r = jackson_pollock_women_3site(triceps_mm=18, thigh_mm=25, suprailiac_mm=16, age=35)
    assert r.sum_mm == pytest.approx(59)
    assert r.body_density == pytest.approx(1.0440452999999998)
    assert r.bodyfat_pct == pytest.approx(24.11735870081509)


def test_women_7site_reference_value():
    # chest=10, axilla=12, triceps=14, subscapular=16, abdominal=22,
    # suprailiac=18, thigh=20, age=30 -> sum=112.
    r = jackson_pollock_women_7site(
        chest_mm=10, axilla_mm=12, triceps_mm=14, subscapular_mm=16,
        abdominal_mm=22, suprailiac_mm=18, thigh_mm=20, age=30,
    )
    assert r.sex == "female"
    assert r.method == "7-site"
    assert r.sum_mm == pytest.approx(112)
    assert r.body_density == pytest.approx(1.04756872)
    assert r.bodyfat_pct == pytest.approx(22.52269999050759)


def test_men_3site_sites_named_explicitly():
    # The men's-3-site site-combo ambiguity (see module docstring) means
    # every result must name its exact sites - never leave this implicit.
    r = jackson_pollock_men_3site(chest_mm=10, triceps_mm=12, subscapular_mm=15, age=30)
    assert set(r.sites_mm) == {"chest_mm", "triceps_mm", "subscapular_mm"}


@pytest.mark.parametrize("bad_kwargs", [
    {"chest_mm": 0, "triceps_mm": 12, "subscapular_mm": 15, "age": 30},
    {"chest_mm": 10, "triceps_mm": -1, "subscapular_mm": 15, "age": 30},
    {"chest_mm": 10, "triceps_mm": 12, "subscapular_mm": 15, "age": 0},
])
def test_men_3site_rejects_nonpositive_inputs(bad_kwargs):
    with pytest.raises(ValueError):
        jackson_pollock_men_3site(**bad_kwargs)


def test_women_3site_rejects_nonpositive_inputs():
    with pytest.raises(ValueError):
        jackson_pollock_women_3site(triceps_mm=0, thigh_mm=20, suprailiac_mm=12, age=28)
    with pytest.raises(ValueError):
        jackson_pollock_women_3site(triceps_mm=15, thigh_mm=20, suprailiac_mm=12, age=-1)
