import pytest

from liftmath.program import ExerciseSet, audit_program, resolve_fractions


def test_longest_match_prefers_specific_exercise_name():
    # "Bench Press" should resolve via "bench", not the generic "press" fallback,
    # but both map to chest so the practical check is the disambiguating cases below.
    assert "chest" in resolve_fractions("Bench Press")


def test_leg_extension_resolves_to_quads_not_generic_extension():
    assert resolve_fractions("Leg Extension") == {"quads": 1.0}


def test_leg_curl_resolves_to_hamstrings_not_biceps_curl():
    assert resolve_fractions("Leg Curl") == {"hamstrings": 1.0}


def test_explicit_fractions_override_name_lookup():
    fracs = resolve_fractions("Zercher Squat Variant X", {"quads": 1.0, "glutes": 0.5})
    assert fracs == {"quads": 1.0, "glutes": 0.5}


def test_unknown_exercise_without_fractions_raises():
    with pytest.raises(ValueError):
        audit_program([ExerciseSet(name="Totally Unknown Move", sets=3, frequency=2)])


def test_audit_program_sums_weekly_sets_across_exercises():
    exercises = [
        ExerciseSet(name="Bench Press", sets=4, frequency=2),   # chest 1.0, triceps 0.5, sidedelts 0.3
        ExerciseSet(name="Barbell Row", sets=4, frequency=2),   # back 1.0, biceps 0.5, reardelts 0.3
    ]
    audit = audit_program(exercises)
    # Bench: 4*2=8 weekly sets -> chest 8.0, triceps 4.0, sidedelts 2.4
    # Row:   4*2=8 weekly sets -> back 8.0, biceps 4.0, reardelts 2.4
    assert audit.totals["chest"] == pytest.approx(8.0)
    assert audit.totals["triceps"] == pytest.approx(4.0)
    assert audit.totals["sidedelts"] == pytest.approx(2.4)
    assert audit.totals["back"] == pytest.approx(8.0)
    assert audit.totals["biceps"] == pytest.approx(4.0)
    assert audit.totals["reardelts"] == pytest.approx(2.4)


def test_audit_program_flags_untrained_muscles():
    exercises = [ExerciseSet(name="Bench Press", sets=4, frequency=2)]
    audit = audit_program(exercises)
    assert "quads" in audit.untrained
    assert "hamstrings" in audit.untrained
    assert "chest" not in audit.untrained


def test_audit_program_rows_carry_verdicts():
    exercises = [ExerciseSet(name="Bench Press", sets=4, frequency=2)]
    audit = audit_program(exercises)
    chest_row = next(r for r in audit.rows if r.muscle == "chest")
    assert chest_row.weekly_sets == pytest.approx(8.0)
    assert chest_row.mev == 10
    assert chest_row.mrv == 22
    assert chest_row.verdict  # non-empty string


def test_cable_crossover_resolves_to_chest():
    assert resolve_fractions("Cable Crossover") == {"chest": 1.0}


def test_preacher_curl_resolves_to_biceps():
    assert resolve_fractions("Preacher Curl") == {"biceps": 1.0}


def test_concentration_curl_resolves_to_biceps():
    assert resolve_fractions("Concentration Curl") == {"biceps": 1.0}


def test_skull_crusher_resolves_to_triceps():
    assert resolve_fractions("Skull Crusher") == {"triceps": 1.0}


def test_tricep_kickback_resolves_to_triceps():
    assert resolve_fractions("Tricep Kickback") == {"triceps": 1.0}


def test_new_curl_variants_do_not_break_hammer_curl():
    # hammer curl also trains forearms; make sure the new "curl" keys
    # (preacher, concentration) don't shadow the more specific hammer-curl match
    assert resolve_fractions("Hammer Curl") == {"biceps": 1.0, "forearms": 0.4}


def test_machine_fly_resolves_to_chest_not_chin():
    # "chin" is a substring of "machine"; word-boundary matching must not let
    # it fire here, or this would wrongly resolve to back/biceps.
    assert resolve_fractions("Machine Fly") == {"chest": 1.0}


def test_machine_chest_press_resolves_to_chest_not_chin():
    assert resolve_fractions("Machine Chest Press") == {
        "chest": 1.0, "triceps": 0.5, "sidedelts": 0.3
    }


def test_pec_deck_machine_resolves_to_chest_not_chin():
    assert resolve_fractions("Pec Deck Machine") == {"chest": 1.0}


def test_bare_machine_with_no_other_keyword_is_unresolved():
    assert resolve_fractions("Seated Machine") == {}


def test_chin_up_still_resolves_to_back_and_biceps():
    # Word-boundary matching must still match "chin" as a whole word/phrase,
    # including across a hyphen or space, not just as an exact full string.
    assert resolve_fractions("Chin-up") == {"back": 1.0, "biceps": 0.6}
    assert resolve_fractions("Chin Up") == {"back": 1.0, "biceps": 0.6}


def test_pendlay_row_resolves_to_back():
    assert resolve_fractions("Pendlay Row") == {
        "back": 1.0,
        "biceps": 0.5,
        "reardelts": 0.3,
    }


def test_landmine_press_resolves_to_delts_chest_and_triceps():
    assert resolve_fractions("Landmine Press") == {
        "sidedelts": 1.0,
        "chest": 0.5,
        "triceps": 0.5,
    }


def test_meadows_row_resolves_to_back():
    assert resolve_fractions("Meadows Row") == {
        "back": 1.0,
        "biceps": 0.5,
        "reardelts": 0.3,
    }


def test_sissy_squat_resolves_to_quads_and_glutes():
    assert resolve_fractions("Sissy Squat") == {
        "quads": 1.0,
        "glutes": 0.2,
    }


def test_nordic_curl_resolves_to_hamstrings():
    assert resolve_fractions("Nordic Curl") == {
        "hamstrings": 1.0,
    }


def test_reverse_hyper_resolves_to_glutes_hamstrings_and_back():
    assert resolve_fractions("Reverse Hyper") == {
        "glutes": 1.0,
        "hamstrings": 0.5,
        "back": 0.3,
    }


def test_back_extension_resolves_to_back_glutes_and_hamstrings():
    assert resolve_fractions("Back Extension") == {
        "back": 1.0,
        "glutes": 0.5,
        "hamstrings": 0.3,
    }


def test_goblet_squat_resolves_to_quads_and_glutes():
    assert resolve_fractions("Goblet Squat") == {
        "quads": 1.0,
        "glutes": 0.6,
    }


def test_copenhagen_plank_resolves_to_abs():
    assert resolve_fractions("Copenhagen Plank") == {
        "abs": 1.0,
    }


def test_cuban_press_resolves_to_delts():
    assert resolve_fractions("Cuban Press") == {
        "reardelts": 0.8,
        "sidedelts": 0.5,
    }
