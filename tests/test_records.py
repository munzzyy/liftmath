import pytest

from liftmath.records import (
    format_seconds,
    parse_mark,
    percent_of_record,
    records_as_of,
    search_records,
    weight_class_for,
)

# --- weight_class_for ---

@pytest.mark.parametrize("bw,sex,expected", [
    (50, "male", "52"),
    (52, "male", "52"),        # exactly on a ceiling stays in that class
    (52.1, "male", "56"),
    (82.5, "male", "82.5"),
    (83, "male", "90"),
    (140, "male", "140"),
    (140.5, "male", "140+"),   # past the last ceiling -> superheavy
    (44, "female", "44"),
    (63, "female", "67.5"),
    (110, "female", "110"),
    (111, "female", "110+"),
])
def test_weight_class_boundaries(bw, sex, expected):
    assert weight_class_for(bw, sex) == expected


@pytest.mark.parametrize("bw,sex,expected", [
    (59, "male", "59"),
    (59.1, "male", "66"),
    (100, "male", "105"),
    (120, "male", "120"),
    (121, "male", "120+"),
    (47, "female", "47"),
    (84, "female", "84"),
    (85, "female", "84+"),
])
def test_weight_class_ipf_scheme(bw, sex, expected):
    assert weight_class_for(bw, sex, scheme="ipf") == expected


def test_weight_class_accepts_m_f_aliases():
    assert weight_class_for(80, "M") == weight_class_for(80, "male")
    assert weight_class_for(80, "F") == weight_class_for(80, "female")


def test_weight_class_rejects_bad_inputs():
    with pytest.raises(ValueError):
        weight_class_for(0, "male")
    with pytest.raises(ValueError):
        weight_class_for(80, "yes")
    with pytest.raises(ValueError):
        weight_class_for(80, "male", scheme="uspa")


# --- parse_mark / format_seconds ---

@pytest.mark.parametrize("text,expected", [
    ("9.58", 9.58),
    ("58.53s", 58.53),
    ("1:40.91", 100.91),
    ("3:26.00", 206.0),
    ("2:00:35", 7235.0),
    (" 12.4 ", 12.4),
])
def test_parse_mark(text, expected):
    assert parse_mark(text) == pytest.approx(expected)


@pytest.mark.parametrize("bad", ["", "a:b", "1:2:3:4", "-5", "4:-1"])
def test_parse_mark_rejects_junk(bad):
    with pytest.raises(ValueError):
        parse_mark(bad)


@pytest.mark.parametrize("seconds,expected", [
    (9.58, "9.58"),
    (59.994, "59.99"),
    (100.91, "1:40.91"),
    (206.0, "3:26.00"),
    (7235, "2:00:35"),
])
def test_format_seconds(seconds, expected):
    assert format_seconds(seconds) == expected


def test_parse_and_format_round_trip():
    for text in ("9.58", "1:40.91", "3:26.00", "2:00:35"):
        assert format_seconds(parse_mark(text)) == text


# --- search_records ---

def test_search_validates_sport_and_equipment():
    with pytest.raises(ValueError):
        search_records(sport="crossfit")
    with pytest.raises(ValueError):
        search_records(equipment="sleeves")


def test_search_bodyweight_needs_sex_and_excludes_weight_class():
    with pytest.raises(ValueError):
        search_records(bodyweight_kg=90)
    with pytest.raises(ValueError):
        search_records(sex="male", bodyweight_kg=90, weight_class="90")


def test_search_bodyweight_resolves_to_class():
    by_bw = search_records(sport="powerlifting", lift="deadlift", sex="male",
                           bodyweight_kg=95, equipment="raw")
    by_cls = search_records(sport="powerlifting", lift="deadlift", sex="male",
                            weight_class="100", equipment="raw")
    assert by_bw == by_cls
    assert by_bw  # the 100kg class exists in the data


def test_every_powerlifting_cell_is_sane():
    matches = search_records(sport="powerlifting")
    assert len(matches) > 500
    for r in matches:
        assert r.unit == "kg"
        assert r.value > 0
        assert r.athlete
        assert r.scope in ("all-time", "tested")
        assert r.equipment in ("raw", "wraps", "single-ply", "multi-ply")
        # Class rows carry their scheme; the open class is scheme-neutral.
        if r.weight_class is None:
            assert r.scheme is None
        else:
            assert r.scheme in ("traditional", "ipf")


def test_scheme_filter_keeps_open_class():
    ipf = search_records(sport="powerlifting", lift="total", sex="male",
                         equipment="raw", scope="all-time", scheme="ipf")
    classes = {r.weight_class for r in ipf}
    assert None in classes            # the scheme-neutral open row comes along
    assert "83" in classes            # an IPF class
    assert "82.5" not in classes      # traditional classes filtered out


def test_tested_record_never_exceeds_all_time():
    # A drug-tested meet is also a sanctioned meet, so its record is a subset
    # maximum - it can equal the all-time mark but never exceed it.
    all_time = {(r.sex, r.equipment, r.scheme, r.weight_class, r.lift): r.value
                for r in search_records(sport="powerlifting", scope="all-time")}
    for r in search_records(sport="powerlifting", scope="tested"):
        key = (r.sex, r.equipment, r.scheme, r.weight_class, r.lift)
        assert key in all_time
        assert r.value <= all_time[key]


def test_open_record_dominates_every_class():
    for scope in ("all-time", "tested"):
        matches = search_records(sport="powerlifting", scope=scope)
        opens = {(r.sex, r.equipment, r.lift): r.value
                 for r in matches if r.weight_class is None}
        for r in matches:
            if r.weight_class is not None:
                assert r.value <= opens[(r.sex, r.equipment, r.lift)]


def test_curated_sports_present_with_citations():
    for sport in ("strongman", "grip"):
        matches = search_records(sport=sport)
        assert matches, f"no {sport} records bundled"
        for r in matches:
            assert r.source and r.source.startswith("http")
            assert r.scope in ("official", "unofficial")
            assert r.confidence in ("high", "medium")
            assert r.unit in ("kg", "m", "s")


def test_known_curated_marks():
    # Pinned to the curated dataset on purpose: these only change when
    # tools/data/curated_records.json is deliberately edited.
    strongman_dl = search_records(sport="strongman", lift="deadlift", sex="male",
                                  weight_class="open")
    assert [r.value for r in strongman_dl] == [510]
    rt = search_records(sport="grip", lift="rolling-thunder", sex="male")
    assert [r.value for r in rt] == [130.5]


def test_sort_order_is_stable_and_class_ranked():
    matches = search_records(sport="powerlifting", lift="deadlift", sex="male",
                             equipment="raw", scope="all-time", scheme="traditional")
    classes = [r.weight_class for r in matches]
    # numeric ascending, then superheavy, then open (None)
    assert classes[-1] is None
    assert classes[-2] == "140+"
    numeric = [float(c) for c in classes[:-2]]
    assert numeric == sorted(numeric)


# --- percent_of_record ---

def test_percent_of_record_math():
    record = search_records(sport="grip", lift="rolling-thunder", sex="male")[0]
    assert percent_of_record(130.5, record) == pytest.approx(100.0)
    assert percent_of_record(65.25, record) == pytest.approx(50.0)


def test_percent_of_record_is_direction_and_unit_aware():
    # Meter-based records compare like any higher-is-better mark now.
    keg = search_records(sport="strongman", lift="keg-toss")[0]
    assert keg.unit == "m"
    assert percent_of_record(keg.value / 2, keg) == pytest.approx(50.0)
    record = search_records(sport="grip", lift="rolling-thunder", sex="male")[0]
    with pytest.raises(ValueError):
        percent_of_record(0, record)


# --- track & field ---

def test_track_levels_present_and_direction_consistent():
    for level in ("world", "college", "high-school"):
        matches = search_records(sport="track", level=level)
        assert matches, f"no {level} track records bundled"
        for r in matches:
            assert r.unit in ("s", "m", "pts")
            # Within track, seconds means a race (faster = better); meters
            # and points grow the usual way.
            assert (r.direction == "lower") == (r.unit == "s")
            assert r.source and r.source.startswith("http")
            assert r.level == level
            if r.unit == "s":
                assert r.display  # times carry their conventional rendering


def test_track_time_compare_inverts():
    hundred = search_records(sport="track", lift="100m", sex="male", level="world")[0]
    assert hundred.direction == "lower"
    # Twice the record time = half of record pace.
    assert percent_of_record(hundred.value * 2, hundred) == pytest.approx(50.0)
    # Equalling the record = 100%.
    assert percent_of_record(hundred.value, hundred) == pytest.approx(100.0)


def test_level_filter_rejects_junk():
    with pytest.raises(ValueError):
        search_records(sport="track", level="pro")


# --- dataset metadata ---

def test_as_of_is_a_date():
    as_of = records_as_of()
    assert len(as_of) == 10 and as_of[4] == "-" and as_of[7] == "-"
