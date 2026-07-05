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


def test_no_subcommand_requires_one():
    with pytest.raises(SystemExit):
        main([])
