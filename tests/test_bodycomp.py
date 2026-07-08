import pytest

from liftmath.bodycomp import ffmi, navy_body_fat


def test_ffmi_no_height_adjustment_at_reference_height():
    # 90kg, 180cm, 12% BF -> lean mass 79.2kg -> FFMI 79.2/1.8^2 = 24.44.
    # Height is already 1.80m so normalized == raw.
    result = ffmi(90, 1.80, 12)
    assert result.lean_mass_kg == pytest.approx(79.2)
    assert result.ffmi == pytest.approx(24.44, abs=0.01)
    assert result.normalized_ffmi == pytest.approx(24.44, abs=0.01)
    assert result.above_natural_reference_ceiling is False


def test_ffmi_above_ceiling_flag():
    # 100kg, 175cm, 10% BF -> lean mass 90kg -> FFMI 29.39; normalized 29.70.
    result = ffmi(100, 1.75, 10)
    assert result.ffmi == pytest.approx(29.39, abs=0.01)
    assert result.normalized_ffmi == pytest.approx(29.70, abs=0.01)
    assert result.above_natural_reference_ceiling is True


def test_ffmi_third_reference_value():
    # 70kg, 165cm, 15% BF -> lean mass 59.5kg -> FFMI 21.85; normalized 22.80.
    result = ffmi(70, 1.65, 15)
    assert result.ffmi == pytest.approx(21.85, abs=0.01)
    assert result.normalized_ffmi == pytest.approx(22.80, abs=0.01)


def test_ffmi_rejects_nonpositive_inputs():
    with pytest.raises(ValueError):
        ffmi(0, 1.8, 12)
    with pytest.raises(ValueError):
        ffmi(90, 0, 12)


def test_ffmi_rejects_bodyfat_out_of_range():
    with pytest.raises(ValueError):
        ffmi(90, 1.8, 100)
    with pytest.raises(ValueError):
        ffmi(90, 1.8, -1)


def test_navy_bf_male_reference_value_one():
    # Height 70in, neck 15in, waist 34in -> ~17.5%.
    result = navy_body_fat("male", 70, 15, 34)
    assert result.bodyfat_pct == pytest.approx(17.5, abs=0.1)


def test_navy_bf_male_reference_value_two():
    # Height 72in, neck 16in, waist 40in -> ~25.4%.
    result = navy_body_fat("male", 72, 16, 40)
    assert result.bodyfat_pct == pytest.approx(25.4, abs=0.1)


def test_navy_bf_female_reference_value():
    # Height 65in, neck 13in, waist 30in, hip 38in -> ~28.5%.
    result = navy_body_fat("female", 65, 13, 30, 38)
    assert result.bodyfat_pct == pytest.approx(28.5, abs=0.1)


def test_navy_bf_female_requires_hip():
    with pytest.raises(ValueError):
        navy_body_fat("female", 65, 13, 30)


def test_navy_bf_male_waist_must_exceed_neck():
    with pytest.raises(ValueError):
        navy_body_fat("male", 70, 20, 15)


def test_navy_bf_invalid_sex_raises():
    with pytest.raises(ValueError):
        navy_body_fat("other", 70, 15, 34)


def test_navy_bf_error_band_is_documented():
    result = navy_body_fat("male", 70, 15, 34)
    assert result.error_band_pct == pytest.approx(3.5)


def test_navy_bf_flags_less_reliable_when_very_lean():
    # Height 72in, neck 16in, waist 30in lands well under 12% BF for a man.
    result = navy_body_fat("male", 72, 16, 30)
    assert result.bodyfat_pct < 12.0
    assert result.less_reliable_at_extremes is True


def test_navy_bf_flags_less_reliable_when_very_high():
    # Height 68in, neck 15in, waist 46in lands well over 25% BF for a man.
    result = navy_body_fat("male", 68, 15, 46)
    assert result.bodyfat_pct > 25.0
    assert result.less_reliable_at_extremes is True


def test_navy_bf_does_not_flag_middle_of_range():
    result = navy_body_fat("male", 70, 15, 34)
    assert 12.0 <= result.bodyfat_pct <= 25.0
    assert result.less_reliable_at_extremes is False
