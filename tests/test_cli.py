import json

import pytest

from liftmath.cli import main


def run(capsys, *argv):
    code = main(list(argv))
    out = capsys.readouterr()
    return code, out.out, out.err


# --- 1rm ---

def test_1rm_estimate(capsys):
    code, out, _ = run(capsys, "1rm", "--weight", "225", "--reps", "5")
    assert code == 0
    assert "CONSENSUS" in out
    assert "225lb x 5 reps" in out


def test_1rm_exact_at_one_rep(capsys):
    code, out, _ = run(capsys, "1rm", "--weight", "315", "--reps", "1")
    assert code == 0
    assert "IS a 1RM" in out


def test_1rm_json(capsys):
    code, out, _ = run(capsys, "1rm", "--weight", "100", "--reps", "5", "--unit", "kg", "--json")
    assert code == 0
    data = json.loads(out)
    assert data["reps"] == 5
    assert data["unit"] == "kg"
    assert "consensus" in data


def test_1rm_json_before_subcommand(capsys):
    code, out, _ = run(capsys, "--json", "1rm", "--weight", "100", "--reps", "3")
    assert code == 0
    json.loads(out)  # parses as JSON


def test_1rm_bad_reps_errors(capsys):
    code, _, err = run(capsys, "1rm", "--weight", "100", "--reps", "0")
    assert code == 1
    assert "error" in err


# --- plates ---

def test_plates_default(capsys):
    code, out, _ = run(capsys, "plates", "--target", "315")
    assert code == 0
    assert "3x45" in out
    assert "45lb bar" in out


def test_plates_inventory_inexact(capsys):
    code, out, _ = run(capsys, "plates", "--target", "405", "--inventory", "45x3,25x1,10x1")
    assert code == 0
    assert "can't make it exactly" in out
    assert "nearest achievable below" in out


def test_plates_preset_womens_kg(capsys):
    code, out, _ = run(capsys, "plates", "--target", "60", "--unit", "kg", "--preset", "womens")
    assert code == 0
    assert "15kg bar" in out


def test_plates_preset_with_lb_errors(capsys):
    code, _, err = run(capsys, "plates", "--target", "100", "--preset", "womens")
    assert code == 1
    assert "kg-only" in err


def test_plates_json(capsys):
    code, out, _ = run(capsys, "plates", "--target", "225", "--json")
    assert code == 0
    data = json.loads(out)
    assert data["bar"] == 45
    assert data["exact"] is True


def test_plates_below_bar_errors(capsys):
    code, _, err = run(capsys, "plates", "--target", "20")
    assert code == 1
    assert "below the bar" in err


# --- standards ---

def test_standards_text(capsys):
    code, out, _ = run(capsys, "standards", "--total", "1200", "--bodyweight", "200", "--sex", "male")
    assert code == 0
    assert "Wilks (2020)" in out
    assert "IPF GL points" in out


def test_standards_json_kg(capsys):
    code, out, _ = run(capsys, "standards", "--total", "500", "--bodyweight", "90",
                       "--sex", "male", "--unit", "kg", "--json")
    assert code == 0
    data = json.loads(out)
    assert data["bodyweight_kg"] == pytest.approx(90.0)
    assert data["wilks"] == pytest.approx(383.498, abs=1e-2)


def test_standards_lb_converts_to_kg(capsys):
    # 90kg ~ 198.4lb: the same lifter given in lb should match the kg score.
    _, out_kg, _ = run(capsys, "standards", "--total", "500", "--bodyweight", "90",
                       "--sex", "male", "--unit", "kg", "--json")
    _, out_lb, _ = run(capsys, "standards", "--total", "1102.31", "--bodyweight", "198.416",
                       "--sex", "male", "--unit", "lb", "--json")
    assert json.loads(out_kg)["wilks"] == pytest.approx(json.loads(out_lb)["wilks"], abs=1e-2)


def test_standards_bad_sex_errors(capsys):
    with pytest.raises(SystemExit):  # argparse choices rejects it before our handler
        run(capsys, "standards", "--total", "500", "--bodyweight", "90", "--sex", "other")


# --- convert ---

def test_convert_lb_to_kg(capsys):
    code, out, _ = run(capsys, "convert", "--weight", "225", "--unit", "lb")
    assert code == 0
    assert "225lb = 102.06kg" in out


def test_convert_kg_to_lb(capsys):
    code, out, _ = run(capsys, "convert", "--weight", "100", "--unit", "kg")
    assert code == 0
    assert "100kg = 220.46lb" in out


def test_convert_default_unit_is_lb(capsys):
    code, out, _ = run(capsys, "convert", "--weight", "45")
    assert code == 0
    assert "45lb" in out


def test_convert_json(capsys):
    code, out, _ = run(capsys, "convert", "--weight", "225", "--unit", "lb", "--json")
    assert code == 0
    data = json.loads(out)
    assert data["unit"] == "lb"
    assert data["result_unit"] == "kg"
    assert data["result"] == pytest.approx(102.05828325)


def test_convert_negative_weight_errors(capsys):
    code, _, err = run(capsys, "convert", "--weight", "-10", "--unit", "lb")
    assert code == 1
    assert "error" in err


def test_convert_bad_unit_errors(capsys):
    with pytest.raises(SystemExit):  # argparse choices rejects it before our handler
        run(capsys, "convert", "--weight", "100", "--unit", "stone")


# --- top level ---

def test_no_subcommand_errors(capsys):
    with pytest.raises(SystemExit):
        run(capsys, "--json")
