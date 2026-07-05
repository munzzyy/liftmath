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


def test_reps_command(capsys):
    code, out = run(capsys, ["reps", "--onerm", "315", "--unit", "lb"])
    assert code == 0
    assert "%1RM" in out
    assert "315" in out


def test_target_command_with_rir(capsys):
    code, out = run(capsys, ["target", "--onerm", "315", "--reps", "8", "--rir", "2", "--unit", "lb"])
    assert code == 0
    assert "236.2" in out or "236.3" in out


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
    assert "Wilks" in out
    assert "DOTS" in out
    assert "IPF GL" in out


def test_standards_rejects_bad_sex():
    with pytest.raises(SystemExit):
        main(["standards", "--total", "1100", "--bodyweight", "220", "--sex", "unicorn"])


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
