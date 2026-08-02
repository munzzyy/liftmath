"""Command-line interface for liftmath.

Subcommands:
    1rm         Estimate 1RM from a weight x reps set (multi-formula consensus + range)
    plates      Plate-loading math for a target barbell weight (add --inventory for a
                finite per-side plate count instead of an unlimited supply)
    standards   Relative-strength scoring: Wilks (original + 2020), DOTS, IPF GL points
    records     Search bundled records (powerlifting / strongman / grip / track & field)
                by lift or event, sex, weight class or bodyweight, equipment, and level
    convert     Convert a weight between lb and kg (exact avoirdupois pound)
    import      Import workout history from a Strong or Hevy CSV export - e1RM trend
                and weekly tonnage per exercise

All loads are unit-agnostic (kg or lb); pass --unit. Pass --json (before or after
the subcommand) for machine-readable JSON instead of the formatted text, e.g.
`liftmath 1rm --weight 225 --reps 5 --json`.
"""

from __future__ import annotations

import argparse
import os
import sys

from liftmath import __version__
from liftmath._serialize import to_json
from liftmath.convert import KG_PER_LB, convert_weight
from liftmath.convert import lbs_to_kg as _lbs_to_kg
from liftmath.imports import e1rm_trend, parse_hevy_csv, parse_strong_csv, weekly_tonnage
from liftmath.onerm import estimate_one_rm
from liftmath.plates import PRESETS, _parse_inventory_spec, load_plates, load_plates_from_inventory
from liftmath.records import (
    compare_value,
    format_seconds,
    percent_of_record,
    records_as_of,
    search_records,
)
from liftmath.standards import score as strength_score


def cmd_1rm(args: argparse.Namespace) -> int:
    try:
        est = estimate_one_rm(args.weight, args.reps, unit=args.unit)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if args.json:
        print(to_json(est))
        return 0

    if est.is_exact:
        print(f"That set IS a 1RM: {args.weight:g}{args.unit}.")
        return 0

    print(f"Estimated 1RM from {args.weight:g}{args.unit} x {args.reps} reps")
    print("  No single formula is most accurate across every rep range, so this runs six and")
    print("  takes the CONSENSUS (median) instead of picking one. Sorted by value, not accuracy.")
    print("-" * 46)
    for name, value in sorted(est.per_formula.items(), key=lambda kv: kv[1]):
        print(f"  {name:<9} {value:6.1f}{args.unit}")
    print("-" * 46)
    print(f"  CONSENSUS {est.consensus:6.1f}{args.unit}   (median; range {est.low:.1f}-{est.high:.1f})")

    if est.high_rep_warning:
        print("\n[!] r>12: rep-max equations lose accuracy; dropped the curvilinear ones and")
        print("    used the median, but treat this as soft. Test a heavier set of <=6 reps for a")
        print("    sharper estimate.")
    elif est.soft_estimate_warning:
        print("\n[!] Best accuracy is at <=8 reps; treat this as approximate.")
    return 0


def cmd_plates(args: argparse.Namespace) -> int:
    if args.inventory:
        try:
            inventory = _parse_inventory_spec(args.inventory)
            result = load_plates_from_inventory(args.target, inventory, unit=args.unit, bar=args.bar)
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            return 1

        if args.json:
            print(to_json(result))
            return 0

        print(f"Load {args.target:g}{args.unit} on a {result.bar:g}{args.unit} bar (from your inventory):")
        if result.plates:
            detail = ", ".join(f"{n}x{p:g}" for p, n in result.plates)
            print(f"  per side ({result.per_side:g}{args.unit}): {detail}")
        else:
            print("  (empty bar)")
        if not result.exact:
            print(f"  [!] can't make it exactly with this inventory - short "
                  f"{result.shortfall:g}{args.unit}/side.")
            if result.nearest_below is not None:
                print(f"      nearest achievable below: {result.nearest_below:g}{args.unit}")
            if result.nearest_above is not None:
                print(f"      nearest achievable above: {result.nearest_above:g}{args.unit}")
        return 0

    try:
        result = load_plates(args.target, unit=args.unit, bar=args.bar, plates=args.plates,
                             preset=args.preset)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if args.json:
        print(to_json(result))
        return 0

    print(f"Load {args.target:g}{args.unit} on a {result.bar:g}{args.unit} bar:")
    if result.plates:
        detail = ", ".join(f"{n}x{p:g}" for p, n in result.plates)
        print(f"  per side ({result.per_side:g}{args.unit}): {detail}")
    else:
        print("  (empty bar)")
    if not result.exact:
        print(f"  [!] can't make it exactly with these plates - short {result.shortfall:g}{args.unit}/side. "
              f"Closest below: {result.achievable:g}{args.unit}.")
    return 0


def cmd_standards(args: argparse.Namespace) -> int:
    try:
        # Inside the try: the lb->kg conversion itself rejects negative input,
        # and that should print "error: ..." like every other bad-input path.
        bodyweight_kg = _lbs_to_kg(args.bodyweight) if args.unit == "lb" else args.bodyweight
        total_kg = _lbs_to_kg(args.total) if args.unit == "lb" else args.total
        result = strength_score(total_kg, bodyweight_kg, args.sex)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if args.json:
        print(to_json(result))
        return 0

    print(f"Relative-strength scores - {args.total:g}{args.unit} total @ {args.bodyweight:g}{args.unit} "
          f"bodyweight ({args.sex}):")
    print("  Each score below lets you compare lifters across bodyweights on one scale - Wilks")
    print("  and DOTS are two different curve-fit formulas for it; IPF GL is the federation's own.")
    print("-" * 40)
    print(f"  Wilks (2020)      {result.wilks:7.2f}")
    print(f"  Wilks (original)  {result.wilks_original:7.2f}")
    print(f"  DOTS              {result.dots:7.2f}")
    print(f"  IPF GL points     {result.ipf_gl:7.2f}")
    print("-" * 40)
    print("IPF GL uses classic (raw) powerlifting coefficients only. All four formulas are fit")
    print("to different samples and disagree slightly, especially at the extremes of the")
    print("bodyweight range - treat them as independent opinions, not a single ground truth.")
    print("Wilks-2020 is the IPF's current standard; original Wilks is kept for historical")
    print("comparison. [evidence tier] established as competition scoring CONVENTIONS (real")
    print("federation formulas fit to real competition samples), not evidence in the RCT sense.")
    return 0


def _record_value_text(r, display_unit: str) -> str:
    """A record's headline value: '433.5kg (956lb)', '1:40.91', '7.77m', '9126 pts'."""
    if r.unit == "kg":
        if display_unit == "lb":
            return f"{r.value:g}kg ({r.value / KG_PER_LB:.0f}lb)"
        return f"{r.value:g}kg"
    if r.display:
        return r.display + (" pts" if r.unit == "pts" else "m" if r.unit == "m" else "")
    if r.unit == "s":
        return format_seconds(r.value) if r.direction == "lower" else f"{r.value:g}s"
    return f"{r.value:g}{'m' if r.unit == 'm' else ' pts'}"


def _compare_line(r, compare_raw: str, display_unit: str) -> str | None:
    """The 'your X = Y% of this record' line, direction- and unit-aware."""
    try:
        value = compare_value(r, compare_raw, display_unit)
        pct = percent_of_record(value, r)
    except ValueError:
        return None
    yours = f"{float(compare_raw):g}{display_unit}" if r.unit == "kg" else compare_raw
    if r.direction == "lower":
        gap = value - r.value
        if gap <= 0:
            return f"      your {yours} = {pct:.1f}% of record pace - you'd have the record"
        gap_txt = format_seconds(gap) + ("s" if gap < 60 else "")
        return f"      your {yours} = {pct:.1f}% of record pace ({gap_txt} off)"
    gap = r.value - value
    if gap <= 0:
        return f"      your {yours} = {pct:.1f}% of this record - you'd have the record"
    if r.unit == "kg":
        gap_txt = f"{gap:g}kg" if display_unit == "kg" else f"{gap / KG_PER_LB:.0f}lb"
    else:
        gap_txt = f"{gap:g}{'m' if r.unit == 'm' else r.unit}"
    return f"      your {yours} = {pct:.1f}% of this record ({gap_txt} to go)"


def cmd_records(args: argparse.Namespace) -> int:
    try:
        # Inside the try: the lb->kg conversion rejects negative bodyweight, and
        # that should print "error: ..." like the kg path already does, not a
        # raw traceback (same pattern as cmd_standards above).
        bodyweight_kg = None
        if args.bodyweight is not None:
            bodyweight_kg = _lbs_to_kg(args.bodyweight) if args.unit == "lb" else args.bodyweight
        matches = search_records(sport=args.sport, lift=args.lift, sex=args.sex,
                                 weight_class=args.weight_class, bodyweight_kg=bodyweight_kg,
                                 equipment=args.equip, scope=args.scope,
                                 level=args.level, scheme=args.scheme)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if args.json:
        print(to_json({"as_of": records_as_of(), "matches": matches}))
        return 0

    if not matches:
        print("No records match those filters. Lift/event keys are e.g. squat, bench, deadlift,")
        print("total (powerlifting), log-lift, atlas-stone, two-hands-pinch, 100m, pole-vault -")
        print("run with just --sport strongman/grip/track to list a sport's events.")
        return 0

    if len(matches) > 40 and not args.all:
        print(f"{len(matches)} records match - narrow with --sport/--lift/--sex/--class/--equip/")
        print("--level/--scheme, or pass --all (or --json) to print everything.")
        return 0

    print(f"Records matching your filters (snapshot of {records_as_of()}):")
    print("  Powerlifting rows are computed from the OpenPowerlifting database - all-time =")
    print("  any sanctioned federation, tested = drug-tested meets only. Strongman, grip, and")
    print("  track & field are curated with per-entry citations (--json carries the sources).")
    print("-" * 84)
    for r in matches:
        value = _record_value_text(r, args.unit)
        cls = f" {r.weight_class}" if r.weight_class else ("" if r.sport == "track" else " open")
        scheme = f" [{r.scheme}]" if r.scheme else ""
        equip = f" {r.equipment}" if r.equipment else ""
        level = f" {r.level}" if r.level else ""
        detail = ", ".join(x for x in (r.competition or r.federation, r.date) if x)
        who = ", ".join(x for x in (r.athlete, r.country) if x)
        print(f"  [{r.sport}] {r.lift_display}{level}{cls}{scheme} {r.sex}{equip} ({r.scope})")
        print(f"      {value:<18} {who}  ({detail})")
        if r.sport == "powerlifting" and (r.bodyweight_kg or r.dots):
            extras = []
            if r.bodyweight_kg:
                extras.append(f"@ {r.bodyweight_kg:g}kg bw")
            if r.dots:
                extras.append(f"{r.dots:g} Dots")
            if r.goodlift:
                extras.append(f"{r.goodlift:g} IPF GL")
            print(f"      {' - '.join(extras)}")
        if args.compare is not None:
            line = _compare_line(r, args.compare, args.unit)
            if line:
                print(line)
    print("-" * 84)
    print("Records move; a bundled snapshot can trail the current record. Official federation")
    print("lists (e.g. the IPF's) are curated separately and differ from all-time-in-the-data.")
    return 0


def cmd_convert(args: argparse.Namespace) -> int:
    try:
        result = convert_weight(args.weight, unit=args.unit)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if args.json:
        print(to_json(result))
        return 0

    print(f"{args.weight:g}{args.unit} = {result.result:.2f}{result.result_unit}")
    print(f"(exact: 1lb = {KG_PER_LB}kg, the international avoirdupois pound)")
    return 0


def _detect_import_source(csv_text: str) -> str | None:
    """Guess "strong" or "hevy" from the export's own header row, or None if neither matches."""
    header = csv_text.splitlines()[0] if csv_text.splitlines() else ""
    if "exercise_title" in header:
        return "hevy"
    if "Exercise Name" in header:
        return "strong"
    return None


def cmd_import(args: argparse.Namespace) -> int:
    try:
        with open(args.file, encoding="utf-8-sig") as f:
            text = f.read()
    except OSError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    except UnicodeDecodeError:
        # A Strong/Hevy export re-saved through Excel can land as cp1252 rather
        # than UTF-8. Fail with the CLI's clean "error:" contract instead of a
        # raw decode traceback, and tell the user how to fix it.
        print(f"error: {args.file} isn't UTF-8 encoded - re-export from the app "
              "or convert it to UTF-8", file=sys.stderr)
        return 1

    source = args.source or _detect_import_source(text)
    if source is None:
        print("error: couldn't tell if this is a Strong or Hevy export - pass --source strong|hevy",
              file=sys.stderr)
        return 1

    try:
        sets = parse_strong_csv(text, unit=args.unit) if source == "strong" \
            else parse_hevy_csv(text, unit=args.unit)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    trend = e1rm_trend(sets)
    tonnage = weekly_tonnage(sets)

    if args.json:
        print(to_json({"source": source, "sets": sets, "e1rm_trend": trend, "weekly_tonnage": tonnage}))
        return 0

    dates = sorted(s.date[:10] for s in sets if s.date)
    exercises = sorted({s.exercise for s in sets if s.exercise})
    span = f" ({dates[0]} to {dates[-1]})" if dates else ""
    print(f"Imported {len(sets)} sets from a {source} export{span}.")
    print(f"  {len(exercises)} distinct exercises.")

    if trend:
        print("-" * 46)
        print("  Best estimated 1RM per exercise, most recent session:")
        for exercise in sorted(trend):
            last_day = max(trend[exercise])
            print(f"  {exercise:<28} {trend[exercise][last_day]:7.1f}{args.unit}  ({last_day})")

    if tonnage:
        print("-" * 46)
        print("  Total tonnage (weight x reps) per week:")
        for week in sorted(tonnage):
            print(f"  {week}   {tonnage[week]:10.0f}{args.unit}")

    return 0


def _json_parent(*, suppress_default: bool) -> argparse.ArgumentParser:
    """Shared --json flag, usable before or after the subcommand name.

    Both the top-level parser and every subparser carry this flag so
    `liftmath --json plates ...` and `liftmath plates --json ...` both work.
    argparse re-applies each parser's own default when it runs, so the
    subparsers' copy must suppress its default instead of resetting a
    True value set by the top-level parser back to False.
    """
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument("--json", action="store_true",
                        default=argparse.SUPPRESS if suppress_default else False,
                        help="print machine-readable JSON instead of formatted text")
    return parent


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="liftmath", description="A simple gym calculator.",
                                parents=[_json_parent(suppress_default=False)])
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)
    json_parent = _json_parent(suppress_default=True)

    s = sub.add_parser("1rm", help="estimate 1RM from a weight x reps set", parents=[json_parent])
    s.add_argument("--weight", type=float, required=True)
    s.add_argument("--reps", type=int, required=True)
    s.add_argument("--unit", default="lb", choices=["lb", "kg"])
    s.set_defaults(func=cmd_1rm)

    s = sub.add_parser("plates", help="plate-loading math", parents=[json_parent])
    s.add_argument("--target", type=float, required=True)
    s.add_argument("--bar", type=float, help="bar weight (default 20kg / 45lb)")
    s.add_argument("--unit", default="lb", choices=["lb", "kg"])
    s.add_argument("--plates", type=float, nargs="*", help="available plate denominations (per side)")
    s.add_argument("--preset", choices=sorted(PRESETS),
                   help="named non-standard setup (kg-only): "
                        "'womens' = 15kg bar, 'metric-no-45' = metric gym with no 45lb-equivalent plate")
    s.add_argument("--inventory", metavar="SPEC",
                   help="finite per-side plate counts you actually have, as 'SIZExCOUNT,...' "
                        "(e.g. '45x4,25x1,10x2,5x2,2.5x1') - overrides --plates/--preset and "
                        "respects exact counts instead of assuming unlimited supply")
    s.set_defaults(func=cmd_plates)

    s = sub.add_parser("standards", help="relative-strength scoring: Wilks/DOTS/IPF GL",
                       parents=[json_parent])
    s.add_argument("--total", type=float, required=True, help="competition total (or single-lift result)")
    s.add_argument("--bodyweight", type=float, required=True)
    s.add_argument("--sex", required=True, choices=["male", "female"])
    s.add_argument("--unit", default="lb", choices=["lb", "kg"])
    s.set_defaults(func=cmd_standards)

    s = sub.add_parser("records",
                       help="search records: powerlifting/strongman/grip/track & field",
                       parents=[json_parent])
    s.add_argument("--sport", choices=["powerlifting", "strongman", "grip", "track"])
    s.add_argument("--lift", "--event", dest="lift",
                   help="lift or event key: squat/bench/deadlift/total, log-lift, atlas-stone, "
                        "rolling-thunder, 100m, pole-vault, ... (list a sport's events with "
                        "just --sport)")
    s.add_argument("--sex", choices=["male", "female"])
    s.add_argument("--class", dest="weight_class", metavar="CLASS",
                   help="weight class label: e.g. 82.5, 140+, u105, or 'open'")
    s.add_argument("--bodyweight", type=float,
                   help="your bodyweight (in --unit) - resolves the weight class for you "
                        "(powerlifting; needs --sex; uses --scheme, default traditional)")
    s.add_argument("--equip", choices=["raw", "wraps", "single-ply", "multi-ply"],
                   help="powerlifting equipment filter")
    s.add_argument("--scheme", choices=["traditional", "ipf"],
                   help="powerlifting weight-class scheme (traditional all-time classes or "
                        "current IPF classes); open-class rows match either")
    s.add_argument("--level", choices=["world", "college", "high-school"],
                   help="track & field level filter")
    s.add_argument("--scope", choices=["all-time", "tested", "official", "unofficial", "pending"],
                   help="powerlifting: all-time (any sanctioned fed) or tested (drug-tested "
                        "meets); curated sports: official/unofficial (track ratifications "
                        "in progress show 'pending')")
    s.add_argument("--compare", metavar="MARK",
                   help="your lift (in --unit) or track mark ('10.85', '4:12.3') - shown as "
                        "%% of each matching record")
    s.add_argument("--all", action="store_true", help="print every match, however many")
    s.add_argument("--unit", default="lb", choices=["lb", "kg"])
    s.set_defaults(func=cmd_records)

    s = sub.add_parser("convert", help="convert a weight between lb and kg", parents=[json_parent])
    s.add_argument("--weight", type=float, required=True)
    s.add_argument("--unit", default="lb", choices=["lb", "kg"], help="unit the --weight is already in")
    s.set_defaults(func=cmd_convert)

    s = sub.add_parser("import", help="import workout history from a Strong or Hevy CSV export",
                       parents=[json_parent])
    s.add_argument("--file", required=True, metavar="PATH", help="path to the exported CSV file")
    s.add_argument("--source", choices=["strong", "hevy"],
                   help="export format; auto-detected from the header row if omitted")
    s.add_argument("--unit", default="lb", choices=["lb", "kg"],
                   help="unit to report weights in - also the assumed unit for a Strong "
                        "export's own Weight column, which doesn't record one (Hevy always "
                        "records kg, so this only affects Hevy's *output*)")
    s.set_defaults(func=cmd_import)

    return p


def _force_utf8_output() -> None:
    """Print UTF-8 no matter what code page the console is on.

    The bundled record set has Polish and other diacritic athlete names in it
    (an l-stroke in 'Malgorzata Kopiec', and about two dozen more). On Windows
    a redirected stdout uses the locale code page, usually cp1252, which can't
    encode those characters, so `liftmath records` died with a
    UnicodeEncodeError halfway through printing. Re-encoding as UTF-8 with
    errors='replace' means the worst case is a replacement character in one
    name, not a traceback and a half-written table.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            # Already detached, or a stream that won't take a new encoding -
            # leave it as it was rather than failing before the command runs.
            pass


def _discard_rest_of_stdout() -> None:
    """Point stdout at the void after the reader on the other end hung up.

    Closing stdout on its own isn't enough: the interpreter flushes it again
    while shutting down and prints "Exception ignored while flushing
    sys.stdout" on top of the error we already handled. Re-pointing the file
    descriptor at os.devnull gives that last flush somewhere harmless to go.
    Under pytest's capture there is no real descriptor, so every step here is
    allowed to be a no-op.
    """
    try:
        fd = sys.stdout.fileno()
    except (OSError, ValueError, AttributeError):
        fd = None
    try:
        sys.stdout.close()
    except (BrokenPipeError, OSError, ValueError):
        pass
    if fd is None:
        return
    try:
        os.dup2(os.open(os.devnull, os.O_WRONLY), fd)
    except OSError:
        pass


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    _force_utf8_output()
    try:
        return args.func(args)
    except BrokenPipeError:
        # `liftmath records --all | head -3` is the obvious way to use --all,
        # and head closing the pipe is not an error worth a traceback. 141 is
        # the usual shell convention for "killed by SIGPIPE".
        _discard_rest_of_stdout()
        return 141
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
