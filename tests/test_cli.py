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


def test_1rm_nan_weight_errors(capsys):
    # This exact command used to dump an IndexError traceback.
    code, _, err = run(capsys, "1rm", "--weight", "nan", "--reps", "5")
    assert code == 1
    assert "error" in err


def test_1rm_inf_weight_errors(capsys):
    # This exact command used to print "CONSENSUS inflb".
    code, _, err = run(capsys, "1rm", "--weight", "inf", "--reps", "5")
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


def test_plates_zero_denomination_errors(capsys):
    # This exact command used to dump a ZeroDivisionError traceback.
    code, _, err = run(capsys, "plates", "--target", "225", "--plates", "0")
    assert code == 1
    assert "error" in err


def test_plates_negative_bar_errors(capsys):
    # This exact command used to print "Load 135lb on a -45lb bar".
    code, _, err = run(capsys, "plates", "--target", "135", "--bar", "-45")
    assert code == 1
    assert "error" in err


def test_plates_infinite_target_errors(capsys):
    code, _, err = run(capsys, "plates", "--target", "inf")
    assert code == 1
    assert "error" in err


def test_plates_inventory_huge_count_errors_instead_of_hanging(capsys):
    # This exact command used to enumerate 100M+1 combinations - it hung the
    # CLI until killed. The cap turns it into an immediate error.
    code, _, err = run(capsys, "plates", "--target", "405", "--inventory", "45x100000000")
    assert code == 1
    assert "error" in err


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


def test_standards_negative_lb_total_errors(capsys):
    # The lb->kg conversion used to run OUTSIDE the error handler, so this
    # exact command dumped a raw ValueError traceback.
    code, _, err = run(capsys, "standards", "--total", "-100", "--bodyweight", "200", "--sex", "male")
    assert code == 1
    assert "error" in err


def test_standards_negative_kg_total_errors(capsys):
    # This exact command used to print negative Wilks/DOTS/IPF GL scores.
    code, _, err = run(capsys, "standards", "--total", "-100", "--bodyweight", "90",
                       "--sex", "male", "--unit", "kg")
    assert code == 1
    assert "error" in err


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


# --- records ---

def test_records_powerlifting_class_lookup(capsys):
    code, out, _ = run(capsys, "records", "--sport", "powerlifting", "--lift", "deadlift",
                       "--sex", "male", "--class", "100", "--equip", "raw", "--unit", "kg")
    assert code == 0
    assert "[powerlifting] Deadlift 100 M raw (all-time)" in out
    assert "(tested)" in out


def test_records_bodyweight_resolves_class_in_lb(capsys):
    # 220lb ~ 99.8kg -> the 100kg class
    code, out, _ = run(capsys, "records", "--sport", "powerlifting", "--lift", "deadlift",
                       "--sex", "male", "--bodyweight", "220", "--equip", "raw")
    assert code == 0
    assert "Deadlift 100 M raw" in out


def test_records_compare_shows_percent(capsys):
    code, out, _ = run(capsys, "records", "--sport", "grip", "--lift", "rolling-thunder",
                       "--sex", "male", "--compare", "65.25", "--unit", "kg")
    assert code == 0
    assert "50.0% of this record" in out


def test_records_json_carries_sources(capsys):
    code, out, _ = run(capsys, "records", "--sport", "strongman", "--sex", "female", "--json")
    assert code == 0
    data = json.loads(out)
    assert data["as_of"]
    assert all(m["source"].startswith("http") for m in data["matches"])


def test_records_conflicting_filters_error(capsys):
    code, _, err = run(capsys, "records", "--sex", "male", "--class", "100",
                       "--bodyweight", "220")
    assert code == 1
    assert "error" in err


def test_records_too_many_matches_hint(capsys):
    code, out, _ = run(capsys, "records")
    assert code == 0
    assert "narrow with" in out


def test_records_no_match_message(capsys):
    code, out, _ = run(capsys, "records", "--sport", "grip", "--lift", "no-such-event")
    assert code == 0
    assert "No records match" in out


# --- top level ---

def test_no_subcommand_errors(capsys):
    with pytest.raises(SystemExit):
        run(capsys, "--json")
