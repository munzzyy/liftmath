import pytest

from liftmath.convert import KG_PER_LB, convert_weight, kg_to_lbs, lbs_to_kg


def test_225lb_to_kg_matches_hand_calculation():
    # 225 * 0.45359237 = 102.05828325
    assert lbs_to_kg(225) == pytest.approx(102.05828325)


def test_100kg_to_lb_matches_hand_calculation():
    # 100 / 0.45359237 = 220.462262...
    assert kg_to_lbs(100) == pytest.approx(220.462262, abs=1e-4)


def test_round_trip_lb_to_kg_to_lb():
    original = 315.0
    assert kg_to_lbs(lbs_to_kg(original)) == pytest.approx(original)


def test_round_trip_kg_to_lb_to_kg():
    original = 140.0
    assert lbs_to_kg(kg_to_lbs(original)) == pytest.approx(original)


def test_zero_is_zero_both_ways():
    assert lbs_to_kg(0) == 0
    assert kg_to_lbs(0) == 0


def test_negative_lbs_rejected():
    with pytest.raises(ValueError):
        lbs_to_kg(-1)


def test_negative_kg_rejected():
    with pytest.raises(ValueError):
        kg_to_lbs(-0.01)


def test_round_to_applies_python_rounding():
    # 225 * 0.45359237 = 102.05828325 -> round to 2dp
    assert lbs_to_kg(225, round_to=2) == 102.06
    assert kg_to_lbs(100, round_to=1) == pytest.approx(220.5)


def test_round_to_none_returns_full_precision():
    assert lbs_to_kg(225, round_to=None) == pytest.approx(102.05828325)


def test_kg_per_lb_is_the_exact_international_avoirdupois_factor():
    assert KG_PER_LB == 0.45359237


# --- convert_weight ---


def test_convert_weight_lb_to_kg():
    result = convert_weight(225, unit="lb")
    assert result.value == 225
    assert result.unit == "lb"
    assert result.result_unit == "kg"
    assert result.result == pytest.approx(102.05828325)


def test_convert_weight_kg_to_lb():
    result = convert_weight(100, unit="kg")
    assert result.unit == "kg"
    assert result.result_unit == "lb"
    assert result.result == pytest.approx(220.462262, abs=1e-4)


def test_convert_weight_rejects_negative():
    with pytest.raises(ValueError):
        convert_weight(-10, unit="lb")


def test_convert_weight_rejects_bad_unit():
    with pytest.raises(ValueError):
        convert_weight(100, unit="stone")


def test_convert_weight_round_to():
    result = convert_weight(225, unit="lb", round_to=1)
    assert result.result == pytest.approx(102.1)
