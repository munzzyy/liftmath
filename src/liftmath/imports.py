"""Import workout history from Strong and Hevy CSV exports into a plain data model.

Both apps export one row per SET (not per workout), with `date`/`workout_name`
repeated on every row of a session. This module parses either format into a
flat list of `WorkoutSet` plus two derived views the single-shot calculators
can't give you from one set at a time: `e1rm_trend` (best estimated 1RM per
exercise per day, via `onerm.estimate_one_rm`) and `weekly_tonnage` (total
weight x reps per ISO week). "Sets per muscle per week" was also asked for in
the original request but needs a lift -> muscle-group mapping this project
doesn't have anywhere yet - left out rather than invented, same as this
project leaves other unverified things out (see onerm.py's own "flagged
rather than silently asserted" note).

Column layout is looked up by NAME, not position, because both apps' export
schemas have drifted and vary by platform - confirmed by comparing real
exports pulled from public workout-log archives and open-source importers,
not assumed from either app's docs (Hevy's own docs don't document the CSV
schema at all; Strong's help center says only that export exists, not its
columns):

    Strong: the canonical (iOS, most common) export is comma-delimited with
        no weight-unit column at all - Weight is just a number, in whatever
        unit the user had Strong set to, and the file gives no way to tell
        which. Some exports (seen on Android, and in some app versions/
        locales) add "Weight Unit"/"Distance Unit" columns instead. This
        parser's `unit` argument is the fallback for rows with no per-row
        unit column, and Strong's own most common export needs that fallback
        on every row. Only English column headers are handled; localized
        headers (a German export uses "Datum", "Gewicht", ...) raise
        ValueError rather than being silently misread.
    Hevy: exports weight_kg in kilograms only - no alternate-unit column was
        found in any sampled export or open-source Hevy importer, so this
        parser always treats weight_kg as kg and converts it into whatever
        `unit` the caller asked for.

Neither app's export records warmup-vs-working-set consistently: Strong
doesn't have the concept in its CSV at all; Hevy's `set_type` does distinguish
"warmup" but there's no established convention here for whether a warmup set
should count toward weekly tonnage, so `weekly_tonnage` counts every set with
a weight and reps recorded, warmups included - `WorkoutSet.set_type` is
exposed so a caller who wants a workups-excluded number can filter the list
themselves before calling it.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from datetime import date, datetime

from liftmath.convert import kg_to_lbs, lbs_to_kg
from liftmath.onerm import estimate_one_rm

_STRONG_REQUIRED = ("Date", "Workout Name", "Exercise Name", "Set Order", "Weight", "Reps")
_STRONG_DATE_FORMATS = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %I:%M:%S %p")
_STRONG_KG_UNIT_STRINGS = ("kg", "kgs")
_STRONG_LB_UNIT_STRINGS = ("lb", "lbs")

_HEVY_REQUIRED = (
    "title", "start_time", "end_time", "exercise_title",
    "set_index", "set_type", "weight_kg", "reps",
)
_HEVY_DATE_FORMAT = "%d %b %Y, %H:%M"


@dataclass
class WorkoutSet:
    """One set from an imported Strong or Hevy workout export.

    `date`, `workout_name`, and `workout_notes` repeat across every set in
    the same workout, same as the source CSVs. `weight`/`unit` are already
    normalized to `unit`. Fields that don't apply to a given set (bodyweight
    work, timed holds, cardio, a column the source format doesn't have) come
    through as None rather than a placeholder 0 or empty string, so "not
    recorded" stays distinguishable from "recorded as zero."
    """

    date: str  # ISO 8601 "YYYY-MM-DDTHH:MM:SS"
    workout_name: str
    exercise: str
    set_order: int | None
    weight: float | None
    unit: str
    reps: int | None
    rpe: float | None
    distance: float | None
    distance_unit: str | None
    seconds: float | None
    notes: str | None
    workout_notes: str | None
    set_type: str | None  # Hevy only: "normal"/"warmup"/"dropset"/"failure"; None for Strong
    source: str  # "strong" or "hevy"


def _num(raw: str | None) -> float | None:
    """Parse a CSV cell as a float; blank/missing/unparseable all come back None.

    One malformed cell shouldn't fail the whole import - a multi-year export
    mixing strength sets, cardio, and hand-edited rows is normal input here,
    not a validation target the way arguments to the calculators are.
    """
    if raw is None:
        return None
    raw = raw.strip()
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def _int(raw: str | None) -> int | None:
    value = _num(raw)
    return int(value) if value is not None else None


def _sniff_delimiter(header_line: str) -> str:
    """Strong exports use a comma (iOS, most common) or a semicolon (seen on Android)."""
    try:
        return csv.Sniffer().sniff(header_line, delimiters=",;").delimiter
    except csv.Error:
        return ","


def _parse_strong_date(raw: str) -> str:
    raw = raw.strip()
    for fmt in _STRONG_DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt).isoformat()
        except ValueError:
            continue
    raise ValueError(f"unrecognized Strong date {raw!r}")


def _parse_hevy_datetime(raw: str) -> str:
    return datetime.strptime(raw.strip(), _HEVY_DATE_FORMAT).isoformat()


def _row_date(raw: str, parser, date_errors: list[str] | None) -> str:
    """One row's timestamp, or "" when it can't be read.

    Same reasoning as `_num` above: a three-year export shouldn't be thrown
    away over one hand-edited row, and both apps' date formats have drifted
    across versions. The row still comes through with everything else it
    carried; it just has no date, which `e1rm_trend` and `weekly_tonnage`
    already skip. Callers that want to tell the user how many rows landed
    here pass a list for `date_errors` and get the raw values appended to it.
    """
    raw = raw.strip()
    if not raw:
        return ""
    try:
        return parser(raw)
    except ValueError:
        if date_errors is not None:
            date_errors.append(raw)
        return ""


def parse_strong_csv(csv_text: str, *, unit: str,
                     date_errors: list[str] | None = None) -> list[WorkoutSet]:
    """Parse a Strong app CSV workout export into a list of `WorkoutSet`.

    Args:
        csv_text: the full contents of an exported Strong CSV file.
        unit: "lb" or "kg" - the unit `Weight`/`Distance` are already in, for
            any row without its own "Weight Unit"/"Distance Unit" column
            (Strong's most common export has neither). Rows that DO carry a
            per-row unit are converted into this unit instead of assumed to
            already be it.
        date_errors: optional list. Every row whose Date this parser can't
            read gets its raw date appended here, so a caller can report
            "3 rows had an unreadable date" instead of the row vanishing
            silently. Those rows are still returned, with `date=""`.

    Returns:
        One `WorkoutSet` per set (per CSV row), in file order.

    Raises:
        ValueError: if `unit` isn't "lb"/"kg", the text is empty, or the
            header is missing one of Strong's required columns (Date,
            Workout Name, Exercise Name, Set Order, Weight, Reps) - the
            surest sign this isn't actually a Strong export, or is a
            localized (non-English) one this parser doesn't handle. A bad
            date in a single row is NOT one of these: it's a row-level
            problem, not a "this is the wrong file" problem.
    """
    if unit not in ("lb", "kg"):
        raise ValueError(f"unit must be 'lb' or 'kg', got {unit!r}")

    lines = csv_text.splitlines()
    if not lines or not lines[0].strip():
        raise ValueError("empty CSV")

    delimiter = _sniff_delimiter(lines[0])
    reader = csv.DictReader(io.StringIO(csv_text), delimiter=delimiter)
    fieldnames = reader.fieldnames or []
    missing = [c for c in _STRONG_REQUIRED if c not in fieldnames]
    if missing:
        raise ValueError(
            f"not a Strong export - missing column(s): {', '.join(missing)}"
        )

    sets = []
    for row in reader:
        weight = _num(row.get("Weight"))
        row_unit = (row.get("Weight Unit") or "").strip().lower()
        if weight is not None:
            if row_unit in _STRONG_KG_UNIT_STRINGS and unit == "lb":
                weight = kg_to_lbs(weight)
            elif row_unit in _STRONG_LB_UNIT_STRINGS and unit == "kg":
                weight = lbs_to_kg(weight)

        sets.append(WorkoutSet(
            date=_row_date(row.get("Date") or "", _parse_strong_date, date_errors),
            workout_name=row.get("Workout Name") or "",
            exercise=row.get("Exercise Name") or "",
            set_order=_int(row.get("Set Order")),
            weight=weight,
            unit=unit,
            reps=_int(row.get("Reps")),
            rpe=_num(row.get("RPE")),
            distance=_num(row.get("Distance")),
            distance_unit=(row.get("Distance Unit") or "").strip() or None,
            seconds=_num(row.get("Seconds")),
            notes=(row.get("Notes") or "").strip() or None,
            workout_notes=(row.get("Workout Notes") or "").strip() or None,
            set_type=None,
            source="strong",
        ))
    return sets


def parse_hevy_csv(csv_text: str, *, unit: str = "kg",
                   date_errors: list[str] | None = None) -> list[WorkoutSet]:
    """Parse a Hevy app CSV workout export into a list of `WorkoutSet`.

    Args:
        csv_text: the full contents of an exported Hevy CSV file.
        unit: "lb" or "kg" to report weight in. Hevy's own export always
            writes weight in kilograms (`weight_kg`), so unlike Strong this
            is purely an output choice, not an assumption about the source.
        date_errors: optional list, same contract as `parse_strong_csv` -
            rows with an unreadable `start_time` land in it and come back
            with `date=""` rather than failing the whole import. Hevy's
            format ("22 Dec 2025, 08:00") is the narrower of the two, so
            this matters more here.

    Returns:
        One `WorkoutSet` per set (per CSV row), in file order. `set_order`
        is Hevy's 0-based `set_index` converted to Strong's 1-based
        convention, so the two sources line up the same way.

    Raises:
        ValueError: if `unit` isn't "lb"/"kg", the text is empty, or the
            header is missing one of Hevy's required columns.
    """
    if unit not in ("lb", "kg"):
        raise ValueError(f"unit must be 'lb' or 'kg', got {unit!r}")

    lines = csv_text.splitlines()
    if not lines or not lines[0].strip():
        raise ValueError("empty CSV")

    reader = csv.DictReader(io.StringIO(csv_text))
    fieldnames = reader.fieldnames or []
    missing = [c for c in _HEVY_REQUIRED if c not in fieldnames]
    if missing:
        raise ValueError(
            f"not a Hevy export - missing column(s): {', '.join(missing)}"
        )

    sets = []
    for row in reader:
        weight_kg = _num(row.get("weight_kg"))
        weight = kg_to_lbs(weight_kg) if (weight_kg is not None and unit == "lb") else weight_kg

        set_index = _int(row.get("set_index"))
        distance_km = _num(row.get("distance_km"))
        sets.append(WorkoutSet(
            date=_row_date(row.get("start_time") or "", _parse_hevy_datetime, date_errors),
            workout_name=row.get("title") or "",
            exercise=row.get("exercise_title") or "",
            set_order=(set_index + 1) if set_index is not None else None,
            weight=weight,
            unit=unit,
            reps=_int(row.get("reps")),
            rpe=_num(row.get("rpe")),
            distance=distance_km,
            distance_unit="km" if distance_km is not None else None,
            seconds=_num(row.get("duration_seconds")),
            notes=(row.get("exercise_notes") or "").strip() or None,
            workout_notes=(row.get("description") or "").strip() or None,
            set_type=(row.get("set_type") or "").strip().lower() or None,
            source="hevy",
        ))
    return sets


def _check_single_unit(sets: list[WorkoutSet], fn_name: str) -> None:
    """Refuse a mixed-unit `sets` list rather than silently mixing kg and lb.

    Both parse functions stamp every `WorkoutSet` they return with the single
    `unit` the caller asked for, so one parse call is always consistent. The
    risk is a caller (a library user, or `import`'s own multi-file merge)
    concatenating lists parsed with different `unit` args - weight x reps
    would then add kilograms to pounds with no error, wrong by the ~2.2x
    factor between them. Callers should normalize everything to one unit
    (pass a matching `unit` to every parse call) before combining lists.
    """
    units = {s.unit for s in sets}
    if len(units) > 1:
        raise ValueError(
            f"{fn_name}: sets are in mixed units ({', '.join(sorted(units))}) - "
            "parse every source with the same `unit` before combining them"
        )


def e1rm_trend(sets: list[WorkoutSet]) -> dict[str, dict[str, float]]:
    """Best estimated 1RM per exercise per calendar day, from parsed sets.

    For each (exercise, day) pair, runs every applicable set through
    `estimate_one_rm` and keeps the best (highest consensus) estimate - the
    day's heaviest top set, not an average across every set including
    warmups, since a warmup set understates a lifter's true max the same way
    it would if you asked a person "what's your max" mid-warmup. Sets with
    no weight, no reps, non-positive weight, or reps < 1 are skipped rather
    than raising - a mixed-content export (strength + cardio + bodyweight)
    is normal input, not an error condition.

    Raises:
        ValueError: if `sets` mixes more than one `unit` - see
            `_check_single_unit`. Every set from one `parse_strong_csv`/
            `parse_hevy_csv` call already shares a unit; this only fires on
            a badly merged list.

    Returns:
        {exercise: {day ("YYYY-MM-DD"): best_e1rm}}, each inner dict sorted
        by day.
    """
    _check_single_unit(sets, "e1rm_trend")
    trend: dict[str, dict[str, float]] = {}
    for s in sets:
        if not s.date or not s.weight or s.weight <= 0 or not s.reps or s.reps < 1:
            continue
        day = s.date[:10]
        try:
            est = estimate_one_rm(s.weight, s.reps, unit=s.unit)
        except ValueError:
            continue
        by_day = trend.setdefault(s.exercise, {})
        if day not in by_day or est.consensus > by_day[day]:
            by_day[day] = est.consensus
    return {exercise: dict(sorted(days.items())) for exercise, days in trend.items()}


def weekly_tonnage(sets: list[WorkoutSet]) -> dict[str, float]:
    """Total tonnage (sum of weight x reps) per ISO week, across all sets.

    ISO week keys look like "2026-W03" (from `date.isocalendar()`), so they
    sort correctly as plain strings and a week that spans a Dec/Jan boundary
    stays in one bucket instead of splitting across a plain calendar-year
    key. Sets missing weight or reps contribute nothing, same rationale as
    `e1rm_trend`; warmup sets ARE included (see module docstring) - filter
    `sets` by `set_type` first if you want them excluded.

    Raises:
        ValueError: if `sets` mixes more than one `unit` - see
            `_check_single_unit`.
    """
    _check_single_unit(sets, "weekly_tonnage")
    tonnage: dict[str, float] = {}
    for s in sets:
        if not s.date or not s.weight or s.weight <= 0 or not s.reps or s.reps < 1:
            continue
        try:
            year, week, _ = date.fromisoformat(s.date[:10]).isocalendar()
        except ValueError:
            continue
        key = f"{year}-W{week:02d}"
        tonnage[key] = tonnage.get(key, 0.0) + s.weight * s.reps
    return dict(sorted(tonnage.items()))
