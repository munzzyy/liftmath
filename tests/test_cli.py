import io
import json
import shutil
import subprocess
import sys

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
    assert "[powerlifting] Deadlift 100 [traditional] M raw (all-time)" in out
    assert "(tested)" in out


def test_records_bodyweight_resolves_class_in_lb(capsys):
    # 220lb ~ 99.8kg -> the 100kg class (traditional scheme by default)
    code, out, _ = run(capsys, "records", "--sport", "powerlifting", "--lift", "deadlift",
                       "--sex", "male", "--bodyweight", "220", "--equip", "raw")
    assert code == 0
    assert "Deadlift 100 [traditional] M raw" in out


def test_records_ipf_scheme_bodyweight(capsys):
    # 100kg bodyweight -> the IPF 105 class
    code, out, _ = run(capsys, "records", "--sport", "powerlifting", "--lift", "deadlift",
                       "--sex", "male", "--bodyweight", "100", "--scheme", "ipf",
                       "--equip", "raw", "--unit", "kg")
    assert code == 0
    assert "Deadlift 105 [ipf] M raw" in out


def test_records_track_event_with_time_compare(capsys):
    code, out, _ = run(capsys, "records", "--sport", "track", "--event", "100m",
                       "--sex", "male", "--level", "world", "--compare", "12.40")
    assert code == 0
    assert "[track] " in out
    assert "% of record pace" in out


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


def test_records_meter_compare_is_not_weight_converted(capsys):
    # A "7" against a meters record (keg toss) must read as 7 meters, not get
    # run through the lb->kg weight conversion - lb and kg display give the
    # same comparison. (The web tab had exactly this bug.)
    code_lb, out_lb, _ = run(capsys, "records", "--sport", "strongman", "--lift",
                             "keg-toss", "--compare", "7", "--unit", "lb")
    code_kg, out_kg, _ = run(capsys, "records", "--sport", "strongman", "--lift",
                             "keg-toss", "--compare", "7", "--unit", "kg")
    assert code_lb == 0 and code_kg == 0
    assert "your 7 = 90.1% of this record" in out_lb
    assert "your 7 = 90.1% of this record" in out_kg


def test_records_negative_bodyweight_errors_cleanly_in_lb(capsys):
    # A negative bodyweight in lb used to traceback (the lb->kg conversion ran
    # before the try block); it now prints a clean "error:" like the kg path.
    code, _, err = run(capsys, "records", "--sport", "powerlifting", "--lift",
                       "deadlift", "--sex", "male", "--bodyweight", "-220", "--equip", "raw")
    assert code == 1
    assert "error" in err


def test_records_nan_compare_does_not_traceback(capsys):
    # nan/inf compare marks used to crash deep in format_seconds (track) or
    # print "nanlb = nan%" (weight records); now the compare line is just
    # dropped and the records still list, exit 0.
    code, out, _ = run(capsys, "records", "--sport", "track", "--event", "1500m",
                       "--sex", "male", "--level", "world", "--compare", "nan")
    assert code == 0
    assert "% of record pace" not in out


def test_records_too_many_matches_hint(capsys):
    code, out, _ = run(capsys, "records")
    assert code == 0
    assert "narrow with" in out


def test_records_no_match_message(capsys):
    code, out, _ = run(capsys, "records", "--sport", "grip", "--lift", "no-such-event")
    assert code == 0
    assert "No records match" in out


# --- import ---

STRONG_CSV = (
    "Date,Workout Name,Duration,Exercise Name,Set Order,Weight,Reps,Distance,Seconds,"
    "Notes,Workout Notes,RPE\n"
    '2020-12-30 18:51:52,"Evening Workout",2h 38m,"Snatch (Barbell)",1,40.0,3,0,0,"","",\n'
    '2020-12-30 18:51:52,"Evening Workout",2h 38m,"Snatch (Barbell)",2,50.0,2,0,0,,,\n'
)

HEVY_CSV = (
    '"title","start_time","end_time","description","exercise_title","superset_id",'
    '"exercise_notes","set_index","set_type","weight_kg","reps","distance_km",'
    '"duration_seconds","rpe"\n'
    '"Morning workout","22 Dec 2025, 08:00","22 Dec 2025, 08:37","","Pull Up (Assisted)",,'
    '"",0,"normal",21,10,,0,8.5\n'
)


def test_import_strong_auto_detected(capsys, tmp_path):
    csv_file = tmp_path / "strong.csv"
    csv_file.write_text(STRONG_CSV)
    code, out, _ = run(capsys, "import", "--file", str(csv_file))
    assert code == 0
    assert "Imported 2 sets from a strong export" in out
    assert "Snatch (Barbell)" in out


def test_import_hevy_auto_detected(capsys, tmp_path):
    csv_file = tmp_path / "hevy.csv"
    csv_file.write_text(HEVY_CSV)
    code, out, _ = run(capsys, "import", "--file", str(csv_file))
    assert code == 0
    assert "Imported 1 sets from a hevy export" in out


def test_import_explicit_source_overrides_detection(capsys, tmp_path):
    csv_file = tmp_path / "strong.csv"
    csv_file.write_text(STRONG_CSV)
    code, out, _ = run(capsys, "import", "--file", str(csv_file), "--source", "strong")
    assert code == 0
    assert "strong export" in out


def test_import_json(capsys, tmp_path):
    csv_file = tmp_path / "strong.csv"
    csv_file.write_text(STRONG_CSV)
    code, out, _ = run(capsys, "import", "--file", str(csv_file), "--json")
    assert code == 0
    data = json.loads(out)
    assert data["source"] == "strong"
    assert len(data["sets"]) == 2
    assert "Snatch (Barbell)" in data["e1rm_trend"]


def test_import_missing_file_errors(capsys, tmp_path):
    code, _, err = run(capsys, "import", "--file", str(tmp_path / "nope.csv"))
    assert code == 1
    assert "error" in err


def test_import_non_utf8_file_errors_cleanly(capsys, tmp_path):
    # A Strong/Hevy export re-saved through Excel can come back as cp1252, not
    # UTF-8. That used to raise a raw UnicodeDecodeError traceback; it now
    # fails with the CLI's clean "error:" contract like every other bad input.
    csv_file = tmp_path / "strong_cp1252.csv"
    csv_file.write_bytes(
        "Date,Workout Name,Exercise Name,Set Order,Weight,Reps\n"
        "2024-01-01,A,Overhead Press (Élévation),1,69.1,5\n".encode("cp1252")
    )
    code, _, err = run(capsys, "import", "--file", str(csv_file))
    assert code == 1
    assert "error" in err
    assert "UTF-8" in err


MIXED_DATE_CSV = (
    "Date,Workout Name,Duration,Exercise Name,Set Order,Weight,Reps,Distance,Seconds,"
    "Notes,Workout Notes,RPE\n"
    '2026-06-01 18:00:00,"Push",1h,"Bench Press (Barbell)",1,185,5,0,0,,,\n'
    '2026-06-03,"Push",1h,"Bench Press (Barbell)",1,190,5,0,0,,,\n'
)


def test_import_reports_unreadable_dates_and_keeps_the_good_rows(capsys, tmp_path):
    # One date-only row used to abort the import and discard everything else.
    csv_file = tmp_path / "mixed.csv"
    csv_file.write_text(MIXED_DATE_CSV)
    code, out, _ = run(capsys, "import", "--file", str(csv_file))
    assert code == 0
    assert "Imported 2 sets" in out
    assert "1 row(s) have a date this can't read" in out
    assert "2026-06-03" in out
    assert "Bench Press (Barbell)" in out


def test_import_all_dates_unreadable_still_exits_zero(capsys, tmp_path):
    csv_file = tmp_path / "alldates.csv"
    csv_file.write_text(
        "Date,Workout Name,Duration,Exercise Name,Set Order,Weight,Reps,Distance,Seconds,"
        "Notes,Workout Notes,RPE\n"
        '03/06/2026,"Push",1h,"Bench Press (Barbell)",1,190,5,0,0,,,\n'
    )
    code, out, err = run(capsys, "import", "--file", str(csv_file))
    assert code == 0
    assert "Traceback" not in err
    assert "Total tonnage" not in out


def test_import_json_counts_unreadable_dates(capsys, tmp_path):
    csv_file = tmp_path / "mixed.csv"
    csv_file.write_text(MIXED_DATE_CSV)
    code, out, _ = run(capsys, "import", "--file", str(csv_file), "--json")
    assert code == 0
    data = json.loads(out)
    assert data["unreadable_dates"] == 1
    assert len(data["sets"]) == 2


def test_import_undetectable_source_errors(capsys, tmp_path):
    csv_file = tmp_path / "mystery.csv"
    csv_file.write_text("Column A,Column B\n1,2\n")
    code, _, err = run(capsys, "import", "--file", str(csv_file))
    assert code == 1
    assert "couldn't tell" in err


def test_import_missing_required_columns_errors(capsys, tmp_path):
    csv_file = tmp_path / "bad.csv"
    csv_file.write_text('"exercise_title"\nx\n')
    code, _, err = run(capsys, "import", "--file", str(csv_file), "--source", "hevy")
    assert code == 1
    assert "error" in err


# --- console encoding ---

def _cp1252_stdout(monkeypatch):
    """Swap sys.stdout for a cp1252 stream, the way a Windows console behaves."""
    raw = io.BytesIO()
    monkeypatch.setattr(sys, "stdout", io.TextIOWrapper(raw, encoding="cp1252", newline=""))
    return raw


def test_records_dataset_still_has_a_non_cp1252_name():
    # The guard below is only meaningful while the dataset actually contains a
    # name cp1252 can't encode. If a regen ever drops all of them, this fails
    # loudly instead of leaving a test that passes without testing anything.
    from liftmath import _records_data

    def offenders(value):
        if isinstance(value, str):
            try:
                value.encode("cp1252")
            except UnicodeEncodeError:
                return 1
            return 0
        if isinstance(value, dict):
            return sum(offenders(v) for v in value.values())
        if isinstance(value, (list, tuple)):
            return sum(offenders(v) for v in value)
        return 0

    total = sum(offenders(getattr(_records_data, name))
                for name in dir(_records_data) if not name.startswith("__"))
    assert total > 0


def test_records_on_a_cp1252_console_does_not_crash(monkeypatch):
    # This exact query used to die with a UnicodeEncodeError partway through
    # printing, on any Windows console using a Western code page.
    raw = _cp1252_stdout(monkeypatch)
    code = main(["records", "--sport", "powerlifting", "--lift", "bench",
                 "--sex", "female", "--class", "60"])
    sys.stdout.flush()
    assert code == 0
    assert b"Records matching your filters" in raw.getvalue()


def test_every_non_cp1252_record_still_prints(monkeypatch):
    # Wider net than the single query above: --all renders every bundled
    # record, so any name the console can't encode would show up here.
    raw = _cp1252_stdout(monkeypatch)
    code = main(["records", "--all"])
    sys.stdout.flush()
    assert code == 0
    assert len(raw.getvalue()) > 10_000


# --- interrupted output ---

def test_broken_pipe_exits_141_instead_of_raising(monkeypatch):
    # Stand-in for the reader hanging up mid-render. sys.stdout is swapped for
    # a throwaway stream because the handler closes it.
    monkeypatch.setattr(sys, "stdout", io.TextIOWrapper(io.BytesIO(), encoding="utf-8"))

    def hang_up(_args):
        raise BrokenPipeError(32, "Broken pipe")

    monkeypatch.setattr("liftmath.cli.cmd_records", hang_up)
    assert main(["records", "--all"]) == 141


def test_ctrl_c_exits_130_instead_of_raising(monkeypatch):
    def interrupt(_args):
        raise KeyboardInterrupt

    monkeypatch.setattr("liftmath.cli.cmd_records", interrupt)
    assert main(["records", "--all"]) == 130


@pytest.mark.skipif(shutil.which("head") is None, reason="needs head(1)")
def test_records_all_piped_into_head_prints_no_traceback():
    # `liftmath records --all | head -3` used to dump a BrokenPipeError
    # traceback plus an "Exception ignored while flushing sys.stdout" line.
    dump = subprocess.Popen([sys.executable, "-m", "liftmath", "records", "--all"],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    head = subprocess.Popen([shutil.which("head"), "-3"], stdin=dump.stdout,
                            stdout=subprocess.DEVNULL)
    dump.stdout.close()
    head.wait()
    err = dump.communicate()[1]
    assert b"Traceback" not in err
    assert b"Exception ignored" not in err


# --- top level ---

def test_no_subcommand_errors(capsys):
    with pytest.raises(SystemExit):
        run(capsys, "--json")
