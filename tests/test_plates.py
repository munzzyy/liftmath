import pytest

from liftmath.plates import _parse_inventory_spec, load_plates, load_plates_from_inventory


def test_245lb_on_45lb_bar_default_plates():
    # per side = (245-45)/2 = 100 -> 2x45 + 1x10
    result = load_plates(245, unit="lb")
    assert result.bar == 45
    assert result.per_side == pytest.approx(100.0)
    assert result.plates == [(45, 2), (10, 1)]
    assert result.exact is True


def test_315lb_on_45lb_bar_default_plates():
    # per side = (315-45)/2 = 135 -> 3x45
    result = load_plates(315, unit="lb")
    assert result.plates == [(45, 3)]
    assert result.exact is True


def test_142_5kg_on_20kg_bar_default_plates():
    # per side = (142.5-20)/2 = 61.25 -> 2x25 + 1x10 + 1x1.25
    result = load_plates(142.5, unit="kg")
    assert result.per_side == pytest.approx(61.25)
    assert result.plates == [(25, 2), (10, 1), (1.25, 1)]
    assert result.exact is True


def test_target_below_bar_raises():
    with pytest.raises(ValueError):
        load_plates(30, unit="lb", bar=45)


def test_custom_bar_and_plates():
    result = load_plates(100, unit="kg", bar=15, plates=(20, 10, 5))
    # per side = (100-15)/2 = 42.5 -> 2x20 + 0x10... remainder 2.5 short (no 2.5 plate given)
    assert result.per_side == pytest.approx(42.5)
    assert result.exact is False
    assert result.shortfall == pytest.approx(2.5)


def test_unloadable_target_reports_closest_achievable():
    result = load_plates(100, unit="kg", bar=15, plates=(20, 10, 5))
    # closest below = target - 2*shortfall = 100 - 5 = 95
    assert result.achievable == pytest.approx(95.0)


def test_womens_preset_uses_15kg_bar():
    # per side = (67.5-15)/2 = 26.25 -> 1x20 + 1x5 + 1x1.25
    result = load_plates(67.5, unit="kg", preset="womens")
    assert result.bar == 15
    assert result.plates == [(20, 1), (5, 1), (1.25, 1)]
    assert result.exact is True


def test_metric_no_45_preset_uses_20kg_bar_and_no_25_plate_analog():
    result = load_plates(100, unit="kg", preset="metric-no-45")
    assert result.bar == 20
    # per side = 40 -> 2x20, since 25 isn't in this preset's plate set
    assert result.plates == [(20, 2)]


def test_explicit_bar_or_plates_override_preset():
    result = load_plates(70, unit="kg", preset="womens", bar=20)
    assert result.bar == 20


def test_preset_with_lb_unit_raises():
    with pytest.raises(ValueError):
        load_plates(245, unit="lb", preset="womens")


def test_unknown_preset_raises():
    with pytest.raises(ValueError):
        load_plates(100, unit="kg", preset="not-a-real-preset")


def test_explicit_empty_plates_means_no_plates_available():
    # An explicitly empty plates=() must NOT fall back to DEFAULT_PLATES via
    # Python truthiness - it means "I have no plates", so the full per-side
    # amount should come back as shortfall on an empty bar.
    result = load_plates(135, unit="lb", plates=())
    assert result.plates == []
    assert result.exact is False
    assert result.shortfall == pytest.approx(45.0)


def test_explicit_empty_plates_list_also_means_no_plates_available():
    result = load_plates(135, unit="lb", plates=[])
    assert result.plates == []
    assert result.shortfall == pytest.approx(45.0)


# --- custom finite plate inventory (load_plates_from_inventory) -----------------


def test_parse_inventory_spec():
    assert _parse_inventory_spec("45x4,25x1,10x2,5x2,2.5x1") == {
        45.0: 4, 25.0: 1, 10.0: 2, 5.0: 2, 2.5: 1,
    }


def test_parse_inventory_spec_merges_duplicate_sizes():
    assert _parse_inventory_spec("10x2,10x1") == {10.0: 3}


def test_parse_inventory_spec_rejects_bad_term():
    with pytest.raises(ValueError):
        _parse_inventory_spec("45-4")


def test_parse_inventory_spec_rejects_non_positive_size_or_count():
    with pytest.raises(ValueError):
        _parse_inventory_spec("0x2")
    with pytest.raises(ValueError):
        _parse_inventory_spec("45x0")


def test_parse_inventory_spec_rejects_empty():
    with pytest.raises(ValueError):
        _parse_inventory_spec("")


def test_inventory_exact_match_from_brief_example():
    # inventory 45x4,25x1,10x2,5x2,2.5x1 per side; bar 45; target 495
    # per side = (495-45)/2 = 225 = 45*4 + 25 + 10*2 (2x45x4=180, +25=205, +20=225)
    inv = _parse_inventory_spec("45x4,25x1,10x2,5x2,2.5x1")
    result = load_plates_from_inventory(495, inv, unit="lb", bar=45)
    assert result.per_side == pytest.approx(225.0)
    assert result.plates == [(45.0, 4), (25.0, 1), (10.0, 2)]
    assert result.exact is True
    assert result.shortfall == pytest.approx(0.0)


def test_inventory_uses_full_stock_when_needed_for_exact_match():
    # same inventory, target needing the 5s and the 2.5 too:
    # per side = (500-45)/2 = 227.5 = 180 + 25 + 20 + 2.5 (skip the 5s) - exact
    inv = _parse_inventory_spec("45x4,25x1,10x2,5x2,2.5x1")
    result = load_plates_from_inventory(500, inv, unit="lb", bar=45)
    assert result.per_side == pytest.approx(227.5)
    assert result.exact is True
    assert result.shortfall == pytest.approx(0.0)


def test_inventory_finite_counts_respected_not_infinite():
    # only 2x45 available per side - can't make 3x45=135, so 90 is the ceiling
    # target 45 + 2*100 = 245, per side = 100, but only 2x45=90 max reachable
    result = load_plates_from_inventory(245, {45: 2}, unit="lb", bar=45)
    assert result.per_side == pytest.approx(100.0)
    assert result.plates == [(45, 2)]
    assert result.exact is False
    assert result.shortfall == pytest.approx(10.0)
    assert result.achievable == pytest.approx(225.0)


def test_inventory_reports_nearest_above_and_below_when_unreachable():
    # inventory {45: 2, 25: 1} per side; achievable per-side combos: 0,25,45,70,90,115
    # target 190 -> per side 72.5, nearest achievable below=70 (185 total), above=115 (225 total)
    result = load_plates_from_inventory(190, {45: 2, 25: 1}, unit="lb", bar=45)
    assert result.per_side == pytest.approx(72.5)
    assert result.exact is False
    assert result.plates == [(45, 1), (25, 1)]
    assert result.shortfall == pytest.approx(2.5)
    assert result.nearest_below == pytest.approx(185.0)
    assert result.nearest_above == pytest.approx(225.0)


def test_inventory_exact_match_has_no_nearest_below():
    result = load_plates_from_inventory(495, _parse_inventory_spec("45x4,25x1,10x2,5x2,2.5x1"),
                                         unit="lb", bar=45)
    assert result.exact is True
    assert result.nearest_below is None


def test_inventory_greedy_would_be_wrong_here_but_exhaustive_search_finds_exact():
    # Counterexample to naive largest-first greedy (see plates.py docstring):
    # inventory {25: 1, 20: 2} per side, target-per-side 40. Greedy grabs the
    # single 25 first (best <= 40), leaving 15 remainder no plate fits - a
    # wrong "15 short" answer. The correct answer is 20+20=40, exact.
    result = load_plates_from_inventory(80 + 2 * 40, {25: 1, 20: 2}, unit="lb", bar=80)
    assert result.per_side == pytest.approx(40.0)
    assert result.plates == [(20, 2)]
    assert result.exact is True


def test_inventory_target_below_bar_raises():
    with pytest.raises(ValueError):
        load_plates_from_inventory(30, {45: 2}, unit="lb", bar=45)


def test_inventory_empty_raises():
    with pytest.raises(ValueError):
        load_plates_from_inventory(245, {}, unit="lb")


def test_inventory_rejects_non_positive_size_or_count():
    with pytest.raises(ValueError):
        load_plates_from_inventory(245, {0: 2}, unit="lb")
    with pytest.raises(ValueError):
        load_plates_from_inventory(245, {45: 0}, unit="lb")


def test_inventory_custom_bar_weight():
    # bar 20kg, inventory 20x2,10x1 per side -> target = 20 + 2*50 = 120
    result = load_plates_from_inventory(120, {20: 2, 10: 1}, unit="kg", bar=20)
    assert result.per_side == pytest.approx(50.0)
    assert result.plates == [(20, 2), (10, 1)]
    assert result.exact is True


def test_inventory_ties_prefer_fewer_total_plates():
    # inventory has 10x1 and 5x2 per side; target-per-side 10 reachable two ways
    # (1x10, or 2x5) with the same total - fewer-plates tiebreak picks the 10.
    result = load_plates_from_inventory(45 + 2 * 10, {10: 1, 5: 2}, unit="lb", bar=45)
    assert result.per_side == pytest.approx(10.0)
    assert result.plates == [(10, 1)]
    assert result.exact is True
