import json

import pytest

from liftmath.cli import main


def run(capsys, argv):
    code = main(argv)
    out = capsys.readouterr().out
    return code, out


def test_1rm_command(capsys):
    code, out = run(capsys, ["1rm", "--weight", "225", "--reps", "5", "--unit", "lb"])
    assert code == 0
    assert "CONSENSUS" in out
    assert "259.2" in out or "259.1" in out  # median consensus ~= 259.17


def test_1rm_single_rep_is_exact(capsys):
    code, out = run(capsys, ["1rm", "--weight", "315", "--reps", "1"])
    assert code == 0
    assert "That set IS a 1RM" in out


def test_1rm_rejects_zero_reps(capsys):
    code, out = run(capsys, ["1rm", "--weight", "225", "--reps", "0"])
    assert code == 1


def test_1rm_rejects_zero_weight(capsys):
    code, out = run(capsys, ["1rm", "--weight", "0", "--reps", "5", "--unit", "lb"])
    assert code == 1


def test_1rm_rejects_negative_weight(capsys):
    code, out = run(capsys, ["1rm", "--weight", "-100", "--reps", "5", "--unit", "lb"])
    assert code == 1


def test_reps_command(capsys):
    code, out = run(capsys, ["reps", "--onerm", "315", "--unit", "lb"])
    assert code == 0
    assert "%1RM" in out
    assert "315" in out


def test_target_command_with_rir(capsys):
    code, out = run(capsys, ["target", "--onerm", "315", "--reps", "8", "--rir", "2", "--unit", "lb"])
    assert code == 0
    assert "236.2" in out or "236.3" in out


def test_target_command_rejects_negative_reps(capsys):
    code, out = run(capsys, ["target", "--onerm", "100", "--reps", "-5", "--unit", "lb"])
    assert code == 1


def test_target_command_rejects_negative_rir(capsys):
    code, out = run(capsys, ["target", "--onerm", "100", "--reps", "5", "--rir", "-3", "--unit", "lb"])
    assert code == 1


def test_target_command_rejects_negative_onerm(capsys):
    code, out = run(capsys, ["target", "--onerm", "-100", "--reps", "5", "--unit", "lb"])
    assert code == 1


def test_volume_full_table(capsys):
    code, out = run(capsys, ["volume"])
    assert code == 0
    assert "chest" in out
    assert "MEV" in out


def test_volume_single_muscle_with_audit(capsys):
    code, out = run(capsys, ["volume", "--muscle", "chest", "--sets", "14"])
    assert code == 0
    assert "productive" in out


def test_volume_unknown_muscle_errors(capsys):
    code, out = run(capsys, ["volume", "--muscle", "not-a-muscle"])
    assert code == 1


def test_program_command(capsys):
    argv = [
        "program",
        "--exercise", "Bench Press | 4x2",
        "--exercise", "Barbell Row | 4x2",
    ]
    code, out = run(capsys, argv)
    assert code == 0
    assert "chest" in out
    assert "back" in out


def test_program_command_with_explicit_fractions(capsys):
    argv = ["program", "--exercise", "Zercher X | 2x1 | quads=1,glutes=0.5"]
    code, out = run(capsys, argv)
    assert code == 0
    assert "quads" in out


def test_program_unknown_exercise_errors(capsys):
    argv = ["program", "--exercise", "Totally Unknown Thing | 3x2"]
    code, out = run(capsys, argv)
    assert code == 1


def test_program_rejects_negative_sets(capsys):
    argv = ["program", "--exercise", "Bench Press | -3x2"]
    code, out = run(capsys, argv)
    assert code == 1


def test_program_rejects_negative_frequency(capsys):
    argv = ["program", "--exercise", "Bench Press | 4x-2"]
    code, out = run(capsys, argv)
    assert code == 1


def test_program_rejects_zero_sets(capsys):
    argv = ["program", "--exercise", "Bench Press | 0x2"]
    code, out = run(capsys, argv)
    assert code == 1


def test_program_rejects_zero_frequency(capsys):
    argv = ["program", "--exercise", "Bench Press | 4x0"]
    code, out = run(capsys, argv)
    assert code == 1


def test_meso_command(capsys):
    code, out = run(capsys, ["meso", "--muscle", "chest", "--weeks", "5"])
    assert code == 0
    assert "deload" in out


def test_macros_command(capsys):
    argv = ["macros", "--bodyweight", "185", "--goal", "gain", "--unit", "lb"]
    code, out = run(capsys, argv)
    assert code == 0
    assert "Protein" in out


def test_macros_cut_shortfall_prints_warning(capsys):
    argv = ["macros", "--bodyweight", "100", "--goal", "cut", "--unit", "kg", "--tdee", "1500"]
    code, out = run(capsys, argv)
    assert code == 0
    assert "[!]" in out


def test_plates_command(capsys):
    code, out = run(capsys, ["plates", "--target", "245", "--unit", "lb"])
    assert code == 0
    assert "2x45" in out


def test_plates_below_bar_errors(capsys):
    code, out = run(capsys, ["plates", "--target", "30", "--unit", "lb"])
    assert code == 1


def test_warmup_command(capsys):
    code, out = run(capsys, ["warmup", "--weight", "275", "--unit", "lb"])
    assert code == 0
    assert "then work sets" in out


def test_plates_preset_command(capsys):
    code, out = run(capsys, ["plates", "--target", "67.5", "--unit", "kg", "--preset", "womens"])
    assert code == 0
    assert "15kg bar" in out


def test_standards_command(capsys):
    code, out = run(capsys, ["standards", "--total", "1100", "--bodyweight", "220",
                              "--sex", "male", "--unit", "lb"])
    assert code == 0
    assert "Wilks (2020)" in out
    assert "Wilks (original)" in out
    assert "DOTS" in out
    assert "IPF GL" in out


def test_standards_rejects_bad_sex():
    with pytest.raises(SystemExit):
        main(["standards", "--total", "1100", "--bodyweight", "220", "--sex", "unicorn"])


def test_mcculloch_command(capsys):
    code, out = run(capsys, ["mcculloch", "--total", "300", "--age", "50", "--unit", "kg"])
    assert code == 0
    assert "1.150" in out
    assert "345.0" in out


def test_mcculloch_out_of_range_age_errors(capsys):
    code, out = run(capsys, ["mcculloch", "--total", "300", "--age", "20", "--unit", "kg"])
    assert code == 1


def test_rpe_command_from_rpe(capsys):
    code, out = run(capsys, ["rpe", "--reps", "5", "--rpe", "8"])
    assert code == 0
    assert "81.1% 1RM" in out


def test_rpe_command_from_pct(capsys):
    code, out = run(capsys, ["rpe", "--reps", "8", "--pct", "70"])
    assert code == 0
    assert "RPE" in out


def test_rpe_command_requires_one_of_rpe_or_pct(capsys):
    code, out = run(capsys, ["rpe", "--reps", "5"])
    assert code == 1


def test_rpe_command_rejects_both_rpe_and_pct(capsys):
    code, out = run(capsys, ["rpe", "--reps", "5", "--rpe", "8", "--pct", "70"])
    assert code == 1


def test_progression_command_at_top_of_range(capsys):
    argv = ["progression", "--reps-low", "8", "--reps-high", "12", "--weight", "185",
            "--reps-achieved", "12", "--increment", "5"]
    code, out = run(capsys, argv)
    assert code == 0
    assert "190" in out


def test_cunningham_command(capsys):
    code, out = run(capsys, ["cunningham", "--lean-mass", "70", "--unit", "kg"])
    assert code == 0
    assert "2040" in out


def test_bulkcut_command(capsys):
    code, out = run(capsys, ["bulkcut", "--bodyweight", "84", "--goal", "gain",
                              "--tier", "intermediate", "--unit", "kg"])
    assert code == 0
    assert "Garthe" in out


def test_ffmi_command(capsys):
    argv = ["ffmi", "--weight", "90", "--unit", "kg", "--height", "180", "--height-unit", "cm",
            "--bodyfat", "12"]
    code, out = run(capsys, argv)
    assert code == 0
    assert "24.4" in out


def test_ffmi_command_flags_above_ceiling(capsys):
    argv = ["ffmi", "--weight", "100", "--unit", "kg", "--height", "175", "--height-unit", "cm",
            "--bodyfat", "10"]
    code, out = run(capsys, argv)
    assert code == 0
    assert "[!]" in out


def test_navybf_command_male(capsys):
    argv = ["navybf", "--sex", "male", "--height", "70", "--neck", "15", "--waist", "34"]
    code, out = run(capsys, argv)
    assert code == 0
    assert "17.5%" in out


def test_navybf_command_female_requires_hip(capsys):
    argv = ["navybf", "--sex", "female", "--height", "65", "--neck", "13", "--waist", "30"]
    code, out = run(capsys, argv)
    assert code == 1


def test_sessionload_command(capsys):
    argv = ["sessionload", "--load", "940", "50", "840", "280", "180", "390", "50", "390", "280"]
    code, out = run(capsys, argv)
    assert code == 0
    assert "3400.0" in out
    assert "1.26" in out


def test_no_subcommand_requires_one():
    with pytest.raises(SystemExit):
        main([])


def test_json_flag_after_subcommand(capsys):
    code, out = run(capsys, ["1rm", "--weight", "225", "--reps", "5", "--json"])
    assert code == 0
    data = json.loads(out)
    assert data["reps"] == 5
    assert data["per_formula"]["Epley"] == pytest.approx(262.5)
    assert data["is_exact"] is False


def test_json_flag_before_subcommand(capsys):
    code, out = run(capsys, ["--json", "1rm", "--weight", "225", "--reps", "5"])
    assert code == 0
    data = json.loads(out)
    assert data["consensus"] == pytest.approx(259.17, abs=0.01)


def test_json_reps_command(capsys):
    code, out = run(capsys, ["reps", "--onerm", "315", "--json"])
    data = json.loads(out)
    assert data["one_rm"] == 315
    assert isinstance(data["rows"], list) and data["rows"]


def test_json_volume_full_table(capsys):
    code, out = run(capsys, ["volume", "--json"])
    data = json.loads(out)
    assert data["chest"]["mev"] == 10


def test_json_volume_single_muscle(capsys):
    code, out = run(capsys, ["volume", "--muscle", "chest", "--sets", "14", "--json"])
    data = json.loads(out)
    assert data["muscle"] == "chest"
    assert data["verdict"]


def test_json_program_command(capsys):
    argv = ["program", "--exercise", "Bench Press | 4x2", "--json"]
    code, out = run(capsys, argv)
    data = json.loads(out)
    assert data["totals"]["chest"] == pytest.approx(8.0)
    assert any(row["muscle"] == "chest" for row in data["rows"])


def test_json_meso_command(capsys):
    code, out = run(capsys, ["meso", "--muscle", "chest", "--weeks", "5", "--json"])
    data = json.loads(out)
    assert data["muscle"] == "chest"
    assert len(data["weeks"]) == 5


def test_json_macros_command(capsys):
    argv = ["macros", "--bodyweight", "185", "--goal", "gain", "--json"]
    code, out = run(capsys, argv)
    data = json.loads(out)
    assert data["goal"] == "gain"
    assert data["protein_g"] > 0


def test_json_plates_command(capsys):
    code, out = run(capsys, ["plates", "--target", "245", "--json"])
    data = json.loads(out)
    assert data["exact"] is True
    assert data["plates"] == [[45, 2], [10, 1]]


def test_json_standards_command(capsys):
    code, out = run(capsys, ["standards", "--total", "1100", "--bodyweight", "220",
                              "--sex", "male", "--unit", "lb", "--json"])
    data = json.loads(out)
    assert data["sex"] == "male"
    assert data["wilks"] > 0
    assert data["dots"] > 0
    assert data["ipf_gl"] > 0


def test_json_warmup_command(capsys):
    code, out = run(capsys, ["warmup", "--weight", "275", "--json"])
    data = json.loads(out)
    assert data["working_weight"] == 275
    assert isinstance(data["steps"], list) and data["steps"]


def test_json_error_path_stays_plain_text(capsys):
    """Errors still go to stderr as text, --json only affects the success path."""
    code, out = run(capsys, ["1rm", "--weight", "225", "--reps", "0", "--json"])
    assert code == 1


def test_json_rpe_command(capsys):
    code, out = run(capsys, ["rpe", "--reps", "5", "--rpe", "8", "--json"])
    data = json.loads(out)
    assert data["reps"] == 5
    assert data["rir"] == pytest.approx(2.0)


def test_json_progression_command(capsys):
    argv = ["progression", "--reps-low", "8", "--reps-high", "12", "--weight", "185",
            "--reps-achieved", "12", "--increment", "5", "--json"]
    code, out = run(capsys, argv)
    data = json.loads(out)
    assert data["next_weight"] == pytest.approx(190.0)
    assert data["next_target_reps"] == 8


def test_json_cunningham_command(capsys):
    code, out = run(capsys, ["cunningham", "--lean-mass", "70", "--unit", "kg", "--json"])
    data = json.loads(out)
    assert data["rmr_kcal"] == pytest.approx(2040.0)


def test_json_bulkcut_command(capsys):
    argv = ["bulkcut", "--bodyweight", "84", "--goal", "gain", "--unit", "kg", "--json"]
    code, out = run(capsys, argv)
    data = json.loads(out)
    assert data["weekly_change_low_kg"] == pytest.approx(0.21)
    assert data["weekly_change_high_kg"] == pytest.approx(0.42)


def test_json_ffmi_command(capsys):
    argv = ["ffmi", "--weight", "90", "--unit", "kg", "--height", "180", "--height-unit", "cm",
            "--bodyfat", "12", "--json"]
    code, out = run(capsys, argv)
    data = json.loads(out)
    assert data["ffmi"] == pytest.approx(24.44, abs=0.01)


def test_json_navybf_command(capsys):
    argv = ["navybf", "--sex", "male", "--height", "70", "--neck", "15", "--waist", "34", "--json"]
    code, out = run(capsys, argv)
    data = json.loads(out)
    assert data["bodyfat_pct"] == pytest.approx(17.5, abs=0.1)


def test_json_sessionload_command(capsys):
    argv = ["sessionload", "--load", "940", "50", "840", "280", "180", "390", "50", "390", "280", "--json"]
    code, out = run(capsys, argv)
    data = json.loads(out)
    assert data["weekly_load"] == pytest.approx(3400.0)
    assert round(data["monotony"], 2) == pytest.approx(1.26)


def test_json_mcculloch_command(capsys):
    argv = ["mcculloch", "--total", "300", "--age", "50", "--unit", "kg", "--json"]
    code, out = run(capsys, argv)
    data = json.loads(out)
    assert data["adjusted_total"] == pytest.approx(345.0)


def test_json_flag_before_subcommand_works_for_new_commands_too(capsys):
    # Regression check for the --json-on-both-parsers argparse.SUPPRESS gotcha,
    # extended to a v1.0.0 subcommand.
    code, out = run(capsys, ["--json", "ffmi", "--weight", "90", "--unit", "kg",
                              "--height", "180", "--height-unit", "cm", "--bodyfat", "12"])
    assert code == 0
    data = json.loads(out)
    assert data["ffmi"] == pytest.approx(24.44, abs=0.01)


# --- v1.1.0: custom plate inventory ------------------------------------------


def test_plates_inventory_command(capsys):
    argv = ["plates", "--target", "495", "--unit", "lb", "--bar", "45",
            "--inventory", "45x4,25x1,10x2,5x2,2.5x1"]
    code, out = run(capsys, argv)
    assert code == 0
    assert "4x45" in out
    assert "from your inventory" in out


def test_plates_inventory_unreachable_reports_nearest(capsys):
    argv = ["plates", "--target", "190", "--unit", "lb", "--bar", "45",
            "--inventory", "45x2,25x1"]
    code, out = run(capsys, argv)
    assert code == 0
    assert "nearest achievable" in out


def test_plates_inventory_bad_spec_errors(capsys):
    argv = ["plates", "--target", "245", "--unit", "lb", "--inventory", "not-a-spec"]
    code, out = run(capsys, argv)
    assert code == 1


def test_json_plates_inventory_command(capsys):
    argv = ["plates", "--target", "495", "--unit", "lb", "--bar", "45",
            "--inventory", "45x4,25x1,10x2,5x2,2.5x1", "--json"]
    code, out = run(capsys, argv)
    data = json.loads(out)
    assert data["exact"] is True
    assert data["plates"] == [[45.0, 4], [25.0, 1], [10.0, 2]]


# --- v1.1.0: weighted bodyweight-movement 1RM --------------------------------


def test_bw_onerm_command(capsys):
    argv = ["bw-onerm", "--movement", "pullup", "--bodyweight", "180", "--added", "45",
            "--reps", "5", "--unit", "lb"]
    code, out = run(capsys, argv)
    assert code == 0
    assert "added-weight 1RM" in out


def test_bw_onerm_assisted_command(capsys):
    argv = ["bw-onerm", "--movement", "pullup", "--bodyweight", "180", "--added", "-60",
            "--reps", "8", "--unit", "lb"]
    code, out = run(capsys, argv)
    assert code == 0
    assert "Assisted" in out


def test_bw_onerm_rejects_unknown_movement():
    # --movement uses argparse choices=, so an unknown value is a parser-level
    # SystemExit, same convention as e.g. `standards --sex unicorn`.
    with pytest.raises(SystemExit):
        main(["bw-onerm", "--movement", "muscleup", "--bodyweight", "180", "--added", "45",
              "--reps", "5"])


def test_bw_onerm_rejects_zero_bodyweight(capsys):
    argv = ["bw-onerm", "--movement", "pullup", "--bodyweight", "0", "--added", "45", "--reps", "5"]
    code, out = run(capsys, argv)
    assert code == 1


def test_json_bw_onerm_command(capsys):
    argv = ["bw-onerm", "--movement", "pullup", "--bodyweight", "180", "--added", "45",
            "--reps", "5", "--unit", "lb", "--json"]
    code, out = run(capsys, argv)
    data = json.loads(out)
    assert data["total_load"] == pytest.approx(225.0)
    assert data["added_weight_one_rm"] == pytest.approx(79.17, abs=0.01)


# --- v1.1.0: lift-ratio symmetry ---------------------------------------------


def test_symmetry_command(capsys):
    argv = ["symmetry", "--squat", "315", "--bench", "225", "--deadlift", "405", "--sex", "male"]
    code, out = run(capsys, argv)
    assert code == 0
    assert "lagging" in out


def test_symmetry_with_ohp_flags_single_sourced(capsys):
    argv = ["symmetry", "--squat", "315", "--bench", "225", "--deadlift", "405",
            "--ohp", "135", "--sex", "male"]
    code, out = run(capsys, argv)
    assert code == 0
    assert "single-sourced" in out


def test_symmetry_rejects_bad_sex():
    with pytest.raises(SystemExit):
        main(["symmetry", "--squat", "315", "--bench", "225", "--deadlift", "405", "--sex", "unicorn"])


def test_json_symmetry_command(capsys):
    argv = ["symmetry", "--squat", "315", "--bench", "225", "--deadlift", "405", "--sex", "male", "--json"]
    code, out = run(capsys, argv)
    data = json.loads(out)
    assert data["sex"] == "male"
    assert "squat" in data["lifts"]
    assert "ohp" not in data["lifts"]


# --- v1.1.0: training max + named program templates --------------------------


def test_tm_command(capsys):
    code, out = run(capsys, ["tm", "--onerm", "315", "--unit", "lb"])
    assert code == 0
    assert "280" in out


def test_tm_rejects_out_of_range_pct(capsys):
    code, out = run(capsys, ["tm", "--onerm", "315", "--pct", "0.5"])
    assert code == 1


def test_json_tm_command(capsys):
    code, out = run(capsys, ["tm", "--onerm", "315", "--unit", "lb", "--json"])
    data = json.loads(out)
    assert data["training_max"] == pytest.approx(280.0)


def test_program531_week2_matches_pinned_worked_example(capsys):
    code, out = run(capsys, ["program531", "--tm", "300", "--week", "2", "--unit", "lb"])
    assert code == 0
    assert "270" in out


def test_program531_deload_week(capsys):
    code, out = run(capsys, ["program531", "--tm", "300", "--week", "4", "--unit", "lb"])
    assert code == 0
    assert "Deload" in out


def test_program531_rejects_bad_week():
    # --week uses argparse choices=[1,2,3,4], so an out-of-range value is a
    # parser-level SystemExit, same convention as e.g. `standards --sex unicorn`.
    with pytest.raises(SystemExit):
        main(["program531", "--tm", "300", "--week", "9"])


def test_json_program531_command(capsys):
    argv = ["program531", "--tm", "300", "--week", "2", "--json"]
    code, out = run(capsys, argv)
    data = json.loads(out)
    assert data["sets"][-1]["weight"] == pytest.approx(270.0)
    assert data["sets"][-1]["amrap"] is True


def test_gzclp_command_made(capsys):
    argv = ["gzclp", "--tier", "t1", "--stage", "5x3", "--weight", "300", "--made",
            "--lift-type", "lower", "--unit", "lb"]
    code, out = run(capsys, argv)
    assert code == 0
    assert "310" in out


def test_gzclp_command_missed_last_stage_needs_retest(capsys):
    argv = ["gzclp", "--tier", "t1", "--stage", "10x1", "--weight", "300", "--missed",
            "--lift-type", "lower", "--unit", "lb"]
    code, out = run(capsys, argv)
    assert code == 0
    assert "retest" in out.lower()


def test_gzclp_t3_requires_amrap_reps(capsys):
    argv = ["gzclp", "--tier", "t3", "--weight", "50", "--made"]
    code, out = run(capsys, argv)
    assert code == 1


def test_json_gzclp_command(capsys):
    argv = ["gzclp", "--tier", "t1", "--stage", "5x3", "--weight", "300", "--made",
            "--lift-type", "lower", "--unit", "lb", "--json"]
    code, out = run(capsys, argv)
    data = json.loads(out)
    assert data["next_weight"] == pytest.approx(310.0)


def test_nsuns_command(capsys):
    argv = ["nsuns", "--day", "squat_day2", "--tm", "300", "--unit", "lb"]
    code, out = run(capsys, argv)
    assert code == 0
    assert "285" in out


def test_nsuns_rejects_unknown_day():
    # --day uses argparse choices=, so an unknown value is a parser-level
    # SystemExit, same convention as e.g. `standards --sex unicorn`.
    with pytest.raises(SystemExit):
        main(["nsuns", "--day", "overhead_day5", "--tm", "300"])


def test_json_nsuns_command(capsys):
    argv = ["nsuns", "--day", "squat_day2", "--tm", "300", "--json"]
    code, out = run(capsys, argv)
    data = json.loads(out)
    assert data["scheme"] == "B"
    assert data["sets"][2]["amrap"] is True


# --- v1.5.0: Prilepin/INOL, attempts, skinfold, tonnage, PR, clubs, gainrate --


def test_prilepin_zone_lookup(capsys):
    code, out = run(capsys, ["prilepin", "--pct", "75"])
    assert code == 0
    assert "70-79%" in out


def test_prilepin_scheme_evaluation(capsys):
    code, out = run(capsys, ["prilepin", "--pct", "75", "--sets", "5", "--reps", "3"])
    assert code == 0
    assert "OPTIMAL" in out


def test_prilepin_requires_both_sets_and_reps(capsys):
    code, out = run(capsys, ["prilepin", "--pct", "75", "--sets", "5"])
    assert code == 1


def test_prilepin_rejects_nonpositive_pct(capsys):
    code, out = run(capsys, ["prilepin", "--pct", "0"])
    assert code == 1


def test_json_prilepin_command(capsys):
    code, out = run(capsys, ["prilepin", "--pct", "75", "--json"])
    data = json.loads(out)
    assert data["zone"]["label"] == "70-79%"
    assert data["evaluation"] is None


def test_inol_worked_example(capsys):
    code, out = run(capsys, ["inol", "--set", "2x6@60", "--set", "5x3@75"])
    assert code == 0
    assert "0.90" in out


def test_inol_requires_pct_tag(capsys):
    code, out = run(capsys, ["inol", "--set", "6x4"])
    assert code == 1


def test_json_inol_command(capsys):
    code, out = run(capsys, ["inol", "--set", "6x4@72", "--json"])
    data = json.loads(out)
    assert data["total"] == pytest.approx(24 / 28)


def test_attempts_from_goal_third(capsys):
    code, out = run(capsys, ["attempts", "--goal-third", "500", "--unit", "lb"])
    assert code == 0
    assert "455.0" in out
    assert "480.0" in out


def test_attempts_from_amrap(capsys):
    code, out = run(capsys, ["attempts", "--amrap-weight", "405", "--amrap-reps", "3", "--unit", "lb"])
    assert code == 0
    assert "e1RM" in out


def test_attempts_rejects_both_inputs(capsys):
    argv = ["attempts", "--goal-third", "500", "--amrap-weight", "405", "--amrap-reps", "3"]
    code, out = run(capsys, argv)
    assert code == 1


def test_attempts_rejects_no_input(capsys):
    code, out = run(capsys, ["attempts"])
    assert code == 1


def test_json_attempts_command(capsys):
    code, out = run(capsys, ["attempts", "--goal-third", "500", "--unit", "lb", "--json"])
    data = json.loads(out)
    assert data["opener"] == pytest.approx(455.0)
    assert data["third"] == pytest.approx(500.0)


def test_skinfold_men_3site(capsys):
    argv = ["skinfold", "--sex", "male", "--method", "3-site", "--chest", "10", "--triceps", "12",
            "--subscapular", "15", "--age", "30"]
    code, out = run(capsys, argv)
    assert code == 0
    assert "15.2%" in out


def test_skinfold_missing_sites_errors(capsys):
    argv = ["skinfold", "--sex", "male", "--method", "3-site", "--chest", "10", "--age", "30"]
    code, out = run(capsys, argv)
    assert code == 1


def test_json_skinfold_command(capsys):
    argv = ["skinfold", "--sex", "female", "--method", "3-site", "--triceps", "15", "--thigh", "20",
            "--suprailiac", "12", "--age", "28", "--json"]
    code, out = run(capsys, argv)
    data = json.loads(out)
    assert data["bodyfat_pct"] == pytest.approx(19.635503077820374)


def test_tonnage_basic(capsys):
    code, out = run(capsys, ["tonnage", "--set", "225x5", "--set", "185x8"])
    assert code == 0
    assert "2605.0" in out


def test_tonnage_with_average_intensity(capsys):
    code, out = run(capsys, ["tonnage", "--set", "225x5@75"])
    assert code == 0
    assert "75.0%1RM" in out


def test_tonnage_rejects_bad_spec(capsys):
    code, out = run(capsys, ["tonnage", "--set", "notaspec"])
    assert code == 1


def test_json_tonnage_command(capsys):
    code, out = run(capsys, ["tonnage", "--set", "225x5", "--json"])
    data = json.loads(out)
    assert data["total_tonnage"] == pytest.approx(1125.0)


def test_pr_new_pr(capsys):
    code, out = run(capsys, ["pr", "--previous-onerm", "300", "--new-weight", "275", "--new-reps", "1"])
    assert code == 0
    assert "PR" in out


def test_pr_not_a_pr(capsys):
    code, out = run(capsys, ["pr", "--previous-onerm", "400", "--new-weight", "300", "--new-reps", "5"])
    assert code == 0
    assert "Not a PR" in out


def test_pr_rejects_both_previous_inputs(capsys):
    argv = ["pr", "--previous-onerm", "300", "--previous-weight", "275", "--previous-reps", "5",
            "--new-weight", "280", "--new-reps", "1"]
    code, out = run(capsys, argv)
    assert code == 1


def test_json_pr_command(capsys):
    argv = ["pr", "--previous-onerm", "300", "--new-weight", "320", "--new-reps", "1", "--json"]
    code, out = run(capsys, argv)
    data = json.loads(out)
    assert data["is_pr"] is True
    assert data["improvement"] == pytest.approx(20.0)


def test_clubs_basic(capsys):
    argv = ["clubs", "--squat", "405", "--bench", "315", "--deadlift", "495"]
    code, out = run(capsys, argv)
    assert code == 0
    assert "YES" in out
    assert "informal gym-culture" in out


def test_clubs_with_ohp(capsys):
    argv = ["clubs", "--squat", "300", "--bench", "200", "--deadlift", "350", "--ohp", "135"]
    code, out = run(capsys, argv)
    assert code == 0
    assert "1-plate" in out


def test_clubs_rejects_nonpositive_lift(capsys):
    code, out = run(capsys, ["clubs", "--squat", "0", "--bench", "200", "--deadlift", "350"])
    assert code == 1


def test_json_clubs_command(capsys):
    argv = ["clubs", "--squat", "405", "--bench", "315", "--deadlift", "495", "--json"]
    code, out = run(capsys, argv)
    data = json.loads(out)
    assert data["two_three_four_club_achieved"] is True
    assert data["thousand_lb_club"]["achieved"] is True


def test_gainrate_basic(capsys):
    code, out = run(capsys, ["gainrate", "--bodyweight", "180", "--level", "intermediate"])
    assert code == 0
    assert "Aragon/Helms" in out
    assert "McDonald" in out


def test_gainrate_rejects_unknown_level():
    with pytest.raises(SystemExit):
        main(["gainrate", "--bodyweight", "180", "--level", "elite"])


def test_json_gainrate_command(capsys):
    argv = ["gainrate", "--bodyweight", "170", "--level", "intermediate", "--json"]
    code, out = run(capsys, argv)
    data = json.loads(out)
    assert data["monthly_low"] == pytest.approx(0.85)
    assert data["monthly_high"] == pytest.approx(1.7)
