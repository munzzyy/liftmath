import pytest

from liftmath.tiers import (
    MEN_TOTAL_KG,
    TIER_NAMES,
    WOMEN_TOTAL_KG,
    classify_tier,
    thresholds_at_bodyweight,
)


def test_tier_names_order():
    assert TIER_NAMES == ("beginner", "novice", "intermediate", "advanced", "elite")


# ---------------------------------------------------------------------------
# thresholds_at_bodyweight: exact brackets (no interpolation)
# ---------------------------------------------------------------------------


def test_thresholds_exact_bracket_men_100kg():
    th = thresholds_at_bodyweight(100, "male")
    assert (th.beginner, th.novice, th.intermediate, th.advanced, th.elite) == (320, 390, 472, 560, 652)
    assert th.clamped is None
    assert th.clamp_bracket_kg is None


def test_thresholds_exact_bracket_women_60kg():
    th = thresholds_at_bodyweight(60, "female")
    assert (th.beginner, th.novice, th.intermediate, th.advanced, th.elite) == (120, 162, 211, 268, 328)
    assert th.clamped is None


# ---------------------------------------------------------------------------
# thresholds_at_bodyweight: interpolation between brackets
# ---------------------------------------------------------------------------


def test_thresholds_interpolated_midpoint_men():
    # Midpoint of the 100kg and 105kg brackets -> exact average of the two rows.
    th = thresholds_at_bodyweight(102.5, "male")
    assert th.beginner == pytest.approx((320 + 336) / 2)
    assert th.novice == pytest.approx((390 + 408) / 2)
    assert th.intermediate == pytest.approx((472 + 491) / 2)
    assert th.advanced == pytest.approx((560 + 582) / 2)
    assert th.elite == pytest.approx((652 + 675) / 2)
    assert th.clamped is None


def test_thresholds_interpolated_fifth_of_bracket_men():
    # 101kg is 1/5 of the way from the 100kg bracket to the 105kg bracket.
    th = thresholds_at_bodyweight(101, "male")
    frac = 0.2
    assert th.intermediate == pytest.approx(472 + frac * (491 - 472))
    assert th.elite == pytest.approx(652 + frac * (675 - 652))


def test_thresholds_interpolated_women():
    # Midpoint of the 45kg and 50kg women's brackets.
    th = thresholds_at_bodyweight(47.5, "female")
    assert th.beginner == pytest.approx((93 + 103) / 2)
    assert th.elite == pytest.approx((283 + 299) / 2)


# ---------------------------------------------------------------------------
# thresholds_at_bodyweight: clamping at the table edges
# ---------------------------------------------------------------------------


def test_thresholds_clamp_below_min_men():
    th = thresholds_at_bodyweight(45, "male")
    assert (th.beginner, th.novice, th.intermediate, th.advanced, th.elite) == MEN_TOTAL_KG[50]
    assert th.clamped == "below_min"
    assert th.clamp_bracket_kg == 50


def test_thresholds_clamp_above_max_men():
    th = thresholds_at_bodyweight(200, "male")
    assert (th.beginner, th.novice, th.intermediate, th.advanced, th.elite) == MEN_TOTAL_KG[140]
    assert th.clamped == "above_max"
    assert th.clamp_bracket_kg == 140


def test_thresholds_clamp_below_min_women():
    th = thresholds_at_bodyweight(35, "female")
    assert (th.beginner, th.novice, th.intermediate, th.advanced, th.elite) == WOMEN_TOTAL_KG[40]
    assert th.clamped == "below_min"
    assert th.clamp_bracket_kg == 40


def test_thresholds_clamp_above_max_women():
    th = thresholds_at_bodyweight(130, "female")
    assert (th.beginner, th.novice, th.intermediate, th.advanced, th.elite) == WOMEN_TOTAL_KG[120]
    assert th.clamped == "above_max"
    assert th.clamp_bracket_kg == 120


def test_thresholds_exactly_at_edge_is_not_clamped():
    # Exactly ON the lightest/heaviest published bracket is real data, not a
    # clamp - clamped should stay None right at the boundary.
    assert thresholds_at_bodyweight(50, "male").clamped is None
    assert thresholds_at_bodyweight(140, "male").clamped is None
    assert thresholds_at_bodyweight(40, "female").clamped is None
    assert thresholds_at_bodyweight(120, "female").clamped is None


def test_thresholds_invalid_sex_raises():
    with pytest.raises(ValueError):
        thresholds_at_bodyweight(100, "other")


def test_thresholds_nonpositive_bodyweight_raises():
    with pytest.raises(ValueError):
        thresholds_at_bodyweight(0, "male")
    with pytest.raises(ValueError):
        thresholds_at_bodyweight(-10, "male")


# ---------------------------------------------------------------------------
# classify_tier: the six buckets, at an exact bracket (men, 100kg: 320/390/472/560/652)
# ---------------------------------------------------------------------------


def test_classify_below_beginner():
    r = classify_tier(300, 100, "male")
    assert r.tier == "below_beginner"
    assert r.next_tier == "beginner"
    assert r.total_to_next_kg == pytest.approx(20)
    assert r.pct_into_tier is None


def test_classify_exactly_at_beginner_floor():
    r = classify_tier(320, 100, "male")
    assert r.tier == "beginner"
    assert r.next_tier == "novice"
    assert r.total_to_next_kg == pytest.approx(70)
    assert r.pct_into_tier == pytest.approx(0.0)


def test_classify_partway_through_beginner():
    r = classify_tier(389, 100, "male")
    assert r.tier == "beginner"
    assert r.pct_into_tier == pytest.approx(100 * 69 / 70)


def test_classify_exactly_at_intermediate_floor():
    r = classify_tier(472, 100, "male")
    assert r.tier == "intermediate"
    assert r.next_tier == "advanced"
    assert r.total_to_next_kg == pytest.approx(88)
    assert r.pct_into_tier == pytest.approx(0.0)


def test_classify_partway_through_advanced():
    r = classify_tier(600, 100, "male")
    assert r.tier == "advanced"
    assert r.next_tier == "elite"
    assert r.total_to_next_kg == pytest.approx(52)
    assert r.pct_into_tier == pytest.approx(100 * 40 / 92)


def test_classify_exactly_at_elite_floor():
    r = classify_tier(652, 100, "male")
    assert r.tier == "elite"
    assert r.next_tier is None
    assert r.total_to_next_kg is None
    assert r.pct_into_tier is None


def test_classify_above_elite_is_still_elite():
    r = classify_tier(900, 100, "male")
    assert r.tier == "elite"
    assert r.next_tier is None
    assert r.total_to_next_kg is None
    assert r.pct_into_tier is None


def test_classify_female_reference_point():
    # Women's 60kg bracket: 120/162/211/268/328 (novice floor exactly).
    r = classify_tier(162, 60, "female")
    assert r.tier == "novice"
    assert r.next_tier == "intermediate"
    assert r.total_to_next_kg == pytest.approx(211 - 162)
    assert r.pct_into_tier == pytest.approx(0.0)


def test_classify_carries_thresholds_through():
    r = classify_tier(500, 100, "male")
    assert r.thresholds.bodyweight_kg == 100
    assert r.thresholds.sex == "male"
    assert r.thresholds.intermediate == 472


def test_classify_uses_clamped_thresholds_for_light_bodyweight():
    r = classify_tier(150, 45, "male")
    assert r.thresholds.clamped == "below_min"
    assert r.thresholds.clamp_bracket_kg == 50
    # Same classification as if bodyweight were exactly 50kg.
    assert r.tier == classify_tier(150, 50, "male").tier


def test_classify_invalid_sex_raises():
    with pytest.raises(ValueError):
        classify_tier(500, 100, "other")


def test_classify_nonpositive_bodyweight_raises():
    with pytest.raises(ValueError):
        classify_tier(500, 0, "male")


def test_classify_nonpositive_total_raises():
    with pytest.raises(ValueError):
        classify_tier(0, 100, "male")
    with pytest.raises(ValueError):
        classify_tier(-50, 100, "male")


# ---------------------------------------------------------------------------
# Table sanity: every row strictly increasing, every table sorted, matching
# bracket keys across both sexes' 5kg spacing (guards against a transcription
# typo breaking either monotonicity or the interpolation's bracket math).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("table", [MEN_TOTAL_KG, WOMEN_TOTAL_KG])
def test_every_row_strictly_increasing(table):
    for bw, row in table.items():
        assert list(row) == sorted(row), f"row at {bw}kg is not strictly increasing: {row}"
        assert len(set(row)) == len(row), f"row at {bw}kg has duplicate thresholds: {row}"


@pytest.mark.parametrize("table", [MEN_TOTAL_KG, WOMEN_TOTAL_KG])
def test_brackets_are_evenly_spaced_5kg(table):
    brackets = sorted(table)
    diffs = {b2 - b1 for b1, b2 in zip(brackets, brackets[1:])}
    assert diffs == {5}


@pytest.mark.parametrize("table", [MEN_TOTAL_KG, WOMEN_TOTAL_KG])
def test_every_column_monotonically_increasing_with_bodyweight(table):
    brackets = sorted(table)
    for col in range(5):
        values = [table[b][col] for b in brackets]
        assert values == sorted(values), f"column {col} is not monotone increasing across bodyweight"
