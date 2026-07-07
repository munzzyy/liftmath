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
