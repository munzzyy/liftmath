import pytest

from liftmath.imports import e1rm_trend, parse_hevy_csv, parse_strong_csv, weekly_tonnage

# Fixture text below is trimmed from real, publicly posted exports (not invented
# schemas) - see the module docstring in imports.py for what was verified where.

# Real iOS/canonical Strong export: comma-delimited, no weight-unit column.
# (github.com/AlexandrosKyriakakis/StrongAppAnalytics/blob/main/Data/strong.csv)
STRONG_IOS = (
    "Date,Workout Name,Duration,Exercise Name,Set Order,Weight,Reps,Distance,Seconds,"
    "Notes,Workout Notes,RPE\n"
    '2020-12-30 18:51:52,"Evening Workout",2h 38m,"Snatch (Barbell)",1,40.0,3,0,0,"","",\n'
    '2020-12-30 18:51:52,"Evening Workout",2h 38m,"Snatch (Barbell)",2,50.0,2,0,0,,,\n'
    '2020-12-30 18:51:52,"Evening Workout",2h 38m,"Snatch (Barbell)",3,60.0,1,0,0,,,\n'
    '2020-12-30 18:51:52,"Evening Workout",2h 38m,"Clean (Barbell)",1,50.0,4,0,0,"",,\n'
)

# Real Android Strong export: semicolon-delimited, with per-row Weight/Distance
# Unit columns and "Workout Duration" instead of "Duration".
# (github.com/imacek/lifting-with-friends-old/blob/main/examples/android-strong.csv)
STRONG_ANDROID = (
    "Date;Workout Name;Exercise Name;Set Order;Weight;Weight Unit;Reps;RPE;Distance;"
    "Distance Unit;Seconds;Notes;Workout Notes;Workout Duration\n"
    '2022-02-16 17:40:08;"Kod Ivana 1st";"Overhead Press (Barbell)";1;45;lbs;2;;;;0;"";"note";58m\n'
    '2022-02-16 17:40:08;"Kod Ivana 1st";"Overhead Press (Barbell)";2;65;lbs;3;;;;0;;;58m\n'
)

# Real Hevy export (help.hevyapp.com's own tutorial sample, matching two
# independent open-source Hevy CSV parsers' expected column lists).
HEVY_CSV = (
    '"title","start_time","end_time","description","exercise_title","superset_id",'
    '"exercise_notes","set_index","set_type","weight_kg","reps","distance_km",'
    '"duration_seconds","rpe"\n'
    '"Morning workout","22 Dec 2025, 08:00","22 Dec 2025, 08:37","","Pull Up (Assisted)",,'
    '"",0,"normal",21,10,,0,8.5\n'
    '"Morning workout","22 Dec 2025, 08:00","22 Dec 2025, 08:37","","Leg Press (Machine)",,'
    '"",1,"normal",90,12,,0,7.5\n'
)


# --- Strong ---------------------------------------------------------------


def test_strong_ios_parses_by_column_name():
    sets = parse_strong_csv(STRONG_IOS, unit="lb")
    assert len(sets) == 4
    assert sets[0].date == "2020-12-30T18:51:52"
    assert sets[0].workout_name == "Evening Workout"
    assert sets[0].exercise == "Snatch (Barbell)"
    assert sets[0].set_order == 1
    assert sets[0].weight == 40.0
    assert sets[0].unit == "lb"
    assert sets[0].reps == 3
    assert sets[0].source == "strong"
    assert sets[0].set_type is None  # Strong has no warmup/working-set flag


def test_strong_set_order_resets_per_exercise():
    sets = parse_strong_csv(STRONG_IOS, unit="lb")
    # Snatch sets 1,2,3, then Clean resets to 1 - same convention Strong itself uses.
    assert [s.set_order for s in sets] == [1, 2, 3, 1]


def test_strong_ios_has_no_unit_column_so_weight_is_assumed_to_already_be_unit():
    sets_lb = parse_strong_csv(STRONG_IOS, unit="lb")
    sets_kg = parse_strong_csv(STRONG_IOS, unit="kg")
    # Same raw number both times - the iOS export gives no way to tell kg from
    # lb, so with no per-row unit column the value passes through unconverted.
    assert sets_lb[0].weight == sets_kg[0].weight == 40.0


def test_strong_android_semicolon_delimiter_is_auto_detected():
    sets = parse_strong_csv(STRONG_ANDROID, unit="lb")
    assert len(sets) == 2
    assert sets[0].exercise == "Overhead Press (Barbell)"
    assert sets[0].weight == 45  # already lb, requested unit is lb - no conversion


def test_strong_android_per_row_weight_unit_is_converted_to_requested_unit():
    sets = parse_strong_csv(STRONG_ANDROID, unit="kg")
    # 45 lbs -> kg via the exact avoirdupois factor.
    assert sets[0].weight == pytest.approx(45 * 0.45359237)


def test_strong_workout_notes_carried_through():
    sets = parse_strong_csv(STRONG_ANDROID, unit="lb")
    assert sets[0].workout_notes == "note"


def test_strong_missing_required_column_raises():
    with pytest.raises(ValueError):
        parse_strong_csv("Date,Workout Name\n2020-01-01 00:00:00,X\n", unit="lb")


def test_strong_empty_text_raises():
    with pytest.raises(ValueError):
        parse_strong_csv("", unit="lb")


def test_strong_bad_unit_raises():
    with pytest.raises(ValueError):
        parse_strong_csv(STRONG_IOS, unit="stone")


def test_strong_blank_optional_cells_become_none_not_empty_string():
    sets = parse_strong_csv(STRONG_IOS, unit="lb")
    assert sets[1].notes is None
    assert sets[1].rpe is None


def test_strong_one_unreadable_date_does_not_lose_the_other_rows():
    # A date-only cell (no time) used to raise and abort the whole import, so
    # three years of history were thrown away over one hand-edited row.
    mixed = (
        "Date,Workout Name,Duration,Exercise Name,Set Order,Weight,Reps,Distance,Seconds,"
        "Notes,Workout Notes,RPE\n"
        '2026-06-01 18:00:00,"Push",1h,"Bench Press (Barbell)",1,185,5,0,0,,,\n'
        '2026-06-03,"Push",1h,"Bench Press (Barbell)",1,190,5,0,0,,,\n'
    )
    errors = []
    sets = parse_strong_csv(mixed, unit="lb", date_errors=errors)
    assert len(sets) == 2
    assert sets[0].date == "2026-06-01T18:00:00"
    assert sets[1].date == ""
    assert sets[1].weight == 190  # the rest of the row survived
    assert errors == ["2026-06-03"]


def test_strong_undated_rows_stay_out_of_the_day_and_week_views():
    undated = (
        "Date,Workout Name,Duration,Exercise Name,Set Order,Weight,Reps,Distance,Seconds,"
        "Notes,Workout Notes,RPE\n"
        '03/06/2026,"Push",1h,"Bench Press (Barbell)",1,190,5,0,0,,,\n'
    )
    errors = []
    sets = parse_strong_csv(undated, unit="lb", date_errors=errors)
    assert len(sets) == 1
    assert errors == ["03/06/2026"]
    assert e1rm_trend(sets) == {}
    assert weekly_tonnage(sets) == {}


def test_strong_blank_date_is_not_reported_as_an_error():
    blank = (
        "Date,Workout Name,Duration,Exercise Name,Set Order,Weight,Reps,Distance,Seconds,"
        "Notes,Workout Notes,RPE\n"
        ',"Push",1h,"Bench Press (Barbell)",1,190,5,0,0,,,\n'
    )
    errors = []
    sets = parse_strong_csv(blank, unit="lb", date_errors=errors)
    assert sets[0].date == ""
    assert errors == []


def test_strong_wrong_file_still_raises():
    # Row tolerance is for rows. A file that isn't a Strong export at all is a
    # real user error and still fails loudly.
    with pytest.raises(ValueError):
        parse_strong_csv("Datum;Gewicht\n2026-06-01;100\n", unit="lb")


# --- Hevy -------------------------------------------------------------------


def test_hevy_parses_by_column_name():
    sets = parse_hevy_csv(HEVY_CSV, unit="kg")
    assert len(sets) == 2
    assert sets[0].date == "2025-12-22T08:00:00"
    assert sets[0].workout_name == "Morning workout"
    assert sets[0].exercise == "Pull Up (Assisted)"
    assert sets[0].weight == 21
    assert sets[0].unit == "kg"
    assert sets[0].reps == 10
    assert sets[0].rpe == 8.5
    assert sets[0].set_type == "normal"
    assert sets[0].source == "hevy"


def test_hevy_set_index_is_0_based_converted_to_1_based_set_order():
    sets = parse_hevy_csv(HEVY_CSV, unit="kg")
    assert [s.set_order for s in sets] == [1, 2]


def test_hevy_weight_kg_converts_to_lb_on_request():
    sets = parse_hevy_csv(HEVY_CSV, unit="lb")
    assert sets[0].weight == pytest.approx(21 / 0.45359237)


def test_hevy_default_unit_is_kg():
    sets = parse_hevy_csv(HEVY_CSV)
    assert sets[0].unit == "kg"
    assert sets[0].weight == 21


def test_hevy_missing_required_column_raises():
    with pytest.raises(ValueError):
        parse_hevy_csv("title,start_time\nX,2025-01-01\n")


def test_hevy_empty_text_raises():
    with pytest.raises(ValueError):
        parse_hevy_csv("")


def test_hevy_unreadable_start_time_keeps_the_row():
    odd = HEVY_CSV + (
        '"Morning workout","2025-12-23T08:00:00","22 Dec 2025, 08:37","","Squat (Barbell)",,'
        '"",0,"normal",100,5,,0,8\n'
    )
    errors = []
    sets = parse_hevy_csv(odd, unit="kg", date_errors=errors)
    assert len(sets) == 3
    assert sets[2].date == ""
    assert sets[2].exercise == "Squat (Barbell)"
    assert errors == ["2025-12-23T08:00:00"]


def test_hevy_bad_unit_raises():
    with pytest.raises(ValueError):
        parse_hevy_csv(HEVY_CSV, unit="stone")


# --- e1rm_trend / weekly_tonnage --------------------------------------------


def test_e1rm_trend_keeps_best_estimate_per_exercise_per_day():
    sets = parse_strong_csv(STRONG_IOS, unit="lb")
    trend = e1rm_trend(sets)
    assert set(trend) == {"Snatch (Barbell)", "Clean (Barbell)"}
    # 3 Snatch sets on the same day - only the best estimate survives.
    assert list(trend["Snatch (Barbell)"]) == ["2020-12-30"]
    assert trend["Snatch (Barbell)"]["2020-12-30"] > 0


def test_e1rm_trend_skips_sets_with_no_reps_or_weight():
    no_reps = (
        "Date,Workout Name,Duration,Exercise Name,Set Order,Weight,Reps,Distance,Seconds,"
        "Notes,Workout Notes,RPE\n"
        '2022-05-30 12:00:00,MURPH,46m,MURPH,1,0,0,0,2762,"result: 46:02","",\n'
    )
    sets = parse_strong_csv(no_reps, unit="lb")
    assert e1rm_trend(sets) == {}


def test_weekly_tonnage_sums_weight_times_reps():
    sets = parse_strong_csv(STRONG_IOS, unit="lb")
    tonnage = weekly_tonnage(sets)
    # 40*3 + 50*2 + 60*1 + 50*4 = 120+100+60+200 = 480
    assert list(tonnage.values()) == [480.0]


def test_weekly_tonnage_iso_week_crosses_year_boundary_correctly():
    # 2020-12-30 falls in ISO week 2020-W53, not a plain calendar-year split.
    sets = parse_strong_csv(STRONG_IOS, unit="lb")
    assert list(weekly_tonnage(sets)) == ["2020-W53"]


def test_weekly_tonnage_ignores_bodyweight_only_sets():
    bodyweight = (
        "Date,Workout Name,Duration,Exercise Name,Set Order,Weight,Reps,Distance,Seconds,"
        "Notes,Workout Notes,RPE\n"
        '2024-01-08 12:00:00,Bodyweight Day,20m,Pull Up,1,0,10,0,0,,,\n'
    )
    sets = parse_strong_csv(bodyweight, unit="lb")
    assert weekly_tonnage(sets) == {}
