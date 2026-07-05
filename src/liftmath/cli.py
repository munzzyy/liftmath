"""Command-line interface for liftmath.

Subcommands:
    1rm       Estimate 1RM from a weight x reps set (multi-formula consensus + range)
    reps      Given a 1RM, print the %1RM -> predicted-reps / RIR load chart
    target    Weight for a target rep/RIR count at a given 1RM
    volume    Weekly hard-set landmarks per muscle (MEV/MAV/MRV) + audit a set count
    program   Whole-program volume audit: sum weekly sets per muscle across a split
    meso      Mesocycle set-progression: ramp a muscle MEV -> MRV over N weeks, then deload
    macros    Protein / calorie / fat / carb targets from bodyweight + goal
    plates    Plate-loading math for a target barbell weight
    warmup    Warm-up ramp sets up to a working weight
    standards Relative-strength scoring: Wilks (2020), DOTS, IPF GL points

All loads are unit-agnostic (kg or lb) unless a subcommand needs the unit; pass --unit.
Pass --json (before or after the subcommand) to get machine-readable JSON instead of
the formatted text, e.g. `liftmath 1rm --weight 225 --reps 5 --json`.
"""

from __future__ import annotations

import argparse
import json
import sys

from liftmath import __version__
from liftmath._serialize import to_json
from liftmath.loads import load_chart, target_load
from liftmath.macros import ACTIVITY_LEVELS, GOALS, macro_targets
from liftmath.mesocycle import ramp_mesocycle
from liftmath.onerm import estimate_one_rm
from liftmath.plates import PRESETS, load_plates
from liftmath.program import ExerciseSet, audit_program
from liftmath.standards import score as strength_score
from liftmath.volume import LANDMARKS, landmarks_for
from liftmath.warmup import warmup_ramp


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
    print("-" * 46)
    for name, value in sorted(est.per_formula.items(), key=lambda kv: kv[1]):
        print(f"  {name:<9} {value:6.1f}{args.unit}")
    print("-" * 46)
    print(f"  CONSENSUS {est.consensus:6.1f}{args.unit}   (median; range {est.low:.1f}-{est.high:.1f})")

    print(f"\nWorking loads off consensus 1RM ({est.consensus:.1f}{args.unit}):")
    chart = load_chart(est.consensus, unit=args.unit,
                        bands=((0.95, ""), (0.90, ""), (0.85, ""), (0.80, ""),
                               (0.75, ""), (0.70, ""), (0.65, "")))
    for row in chart.rows:
        print(f"  {int(row.pct*100)}%  {row.load:6.1f}{args.unit}   ~{row.max_reps} reps")

    if est.high_rep_warning:
        print("\n[!] r>12: rep-max equations lose accuracy; dropped the curvilinear ones and")
        print("    used the median, but treat this as soft. Test a heavier set of <=6 reps for a")
        print("    sharper estimate.")
    elif est.soft_estimate_warning:
        print("\n[!] Best accuracy is at <=8 reps; treat this as approximate.")
    return 0


def cmd_reps(args: argparse.Namespace) -> int:
    one = args.onerm
    if args.json:
        print(to_json(load_chart(one, unit=args.unit)))
        return 0

    print(f"%1RM load & effort chart (1RM = {one:g}{args.unit})")
    print("-" * 54)
    print(f"{'%1RM':>5} {'load':>9} {'~max reps':>10}   typical use")
    print("-" * 54)
    chart = load_chart(one, unit=args.unit)
    for row in chart.rows:
        print(f"{int(row.pct*100):>4}% {row.load:8.1f}{args.unit} {row.max_reps:>9}   {row.use}")
    print("-" * 54)
    print("Effort: proximity to failure only WEAKLY affects hypertrophy at matched volume")
    print("(Refalo 2023 meta) - 0-3 RIR all grow muscle; use 1-4 RIR for strength. To hit N RIR")
    print("at a given load, stop N reps short of the ~max-reps shown (75% ~= 10 max -> stop at 8")
    print("for 2 RIR). For the load that lets you do R reps AT N RIR, use `target --reps R --rir N`.")
    return 0


def cmd_target(args: argparse.Namespace) -> int:
    result = target_load(args.onerm, args.reps, rir=args.rir)
    if args.json:
        print(to_json(result))
        return 0

    print(f"To do ~{args.reps} reps (to failure) with a {args.onerm:g}{args.unit} 1RM:")
    print(f"  load ~= {result.load:.1f}{args.unit}  ({result.pct*100:.0f}% 1RM)")
    if args.rir:
        print(f"  at {args.rir} RIR (stop at {args.reps}, ~{result.rir_max_reps} rep max): "
              f"{result.rir_load:.1f}{args.unit}  ({result.rir_pct*100:.0f}% 1RM)")
    return 0


def cmd_volume(args: argparse.Namespace) -> int:
    if args.muscle:
        try:
            info = landmarks_for(args.muscle, sets=args.sets)
        except KeyError as e:
            print(f"error: {e}", file=sys.stderr)
            return 1
        if args.json:
            print(to_json(info))
            return 0
        print(f"{info.muscle} - weekly hard-set landmarks (sets to ~0-4 RIR):")
        print(f"  MV  (maintain)          {info.mv}")
        print(f"  MEV (min effective)     {info.mev}")
        print(f"  MAV (productive range)  {info.mav_low}-{info.mav_high}")
        print(f"  MRV (max recoverable)   {info.mrv}")
        if args.sets is not None:
            print(f"\n  Your {args.sets} sets/wk: {info.verdict}")
        return 0

    if args.json:
        table = {
            m: {"mv": mv, "mev": mev, "mav_low": mlo, "mav_high": mhi, "mrv": mrv}
            for m, (mv, mev, mlo, mhi, mrv) in LANDMARKS.items()
        }
        print(json.dumps(table, indent=2))
        return 0

    print("Weekly hard-set landmarks per muscle (Israetel/RP heuristics - starting points):")
    print(f"{'muscle':<12}{'MV':>4}{'MEV':>5}{'MAV':>10}{'MRV':>6}")
    print("-" * 40)
    for m, (mv, mev, mlo, mhi, mrv) in LANDMARKS.items():
        print(f"{m:<12}{mv:>4}{mev:>5}{str(mlo)+'-'+str(mhi):>10}{mrv:>6}")
    print("-" * 40)
    print("Count a 'hard set' as a working set taken to ~0-4 reps in reserve.")
    print("Directly-trained isolation counts fully; a compound counts fully for its prime")
    print("mover and ~0.5 for strong synergists. Titrate up from MEV until progress stalls or")
    print("recovery suffers - these numbers are a map, not the territory.")
    return 0


def _parse_exercise_spec(spec: str) -> ExerciseSet:
    parts = [p.strip() for p in spec.split("|")]
    if len(parts) < 2:
        raise ValueError(
            f"bad --exercise '{spec}'. Format: 'Name | sets x freq | muscle=frac,...' "
            "(fractions optional for known lifts)"
        )
    name = parts[0]
    sf = parts[1].lower().replace(" ", "")
    try:
        sets_s, freq_s = sf.split("x", 1)
        sets, freq = float(sets_s), float(freq_s)
    except ValueError:
        raise ValueError(f"bad 'sets x freq' in '{spec}' (want e.g. '4x2' = 4 sets, 2 sessions/wk)")

    explicit = None
    if len(parts) > 2 and parts[2]:
        explicit = {}
        for part in parts[2].split(","):
            if "=" not in part:
                raise ValueError(f"bad fraction '{part}' - want 'muscle=frac'")
            mus, fr = part.split("=", 1)
            explicit[mus] = float(fr)

    return ExerciseSet(name=name, sets=sets, frequency=freq, fractions=explicit)


def cmd_program(args: argparse.Namespace) -> int:
    try:
        exercises = [_parse_exercise_spec(spec) for spec in args.exercise]
        audit = audit_program(exercises)
    except (ValueError, KeyError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if args.json:
        print(to_json(audit))
        return 0

    print("Program volume audit - weekly hard sets per muscle:")
    print("-" * 66)
    print(f"{'muscle':<12}{'sets/wk':>8}{'MEV':>5}{'MRV':>5}   verdict")
    print("-" * 66)
    for row in audit.rows:
        mev = row.mev if row.mev is not None else "-"
        mrv = row.mrv if row.mrv is not None else "-"
        print(f"{row.muscle:<12}{row.weekly_sets:>8.1f}{mev:>5}{mrv:>5}   {row.verdict}")
    print("-" * 66)
    if audit.untrained:
        print("Untrained (MEV>0 muscles absent from the split): " + ", ".join(audit.untrained))
    print("Prime mover counts fully, synergists ~0.3-0.7. Same MEV/MAV/MRV bands as `volume`.")
    return 0


def cmd_meso(args: argparse.Namespace) -> int:
    try:
        meso = ramp_mesocycle(args.muscle, weeks=args.weeks)
    except (KeyError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if args.json:
        print(to_json(meso))
        return 0

    print(f"{meso.muscle} mesocycle - {args.weeks} weeks: ramp MEV({meso.mev}) -> MRV({meso.mrv}), then deload")
    print(f"{'week':>5}{'sets':>7}{'%MRV':>7}   note")
    print("-" * 46)
    for w in meso.weeks:
        print(f"{w.week:>5}{w.sets:>7}{w.pct_mrv:>6.0f}%   {w.note}")
    print("-" * 46)
    print("Progress LOAD/reps within these set counts by double progression each week.")
    print("If top-set reps stall two weeks running, deload early rather than grinding.")
    return 0


def cmd_macros(args: argparse.Namespace) -> int:
    try:
        m = macro_targets(args.bodyweight, args.goal, unit=args.unit, tdee=args.tdee, activity=args.activity)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if args.json:
        print(to_json(m))
        return 0

    est = " (estimated)" if m.tdee_is_estimate else " (you supplied)"
    print(f"Targets for {args.bodyweight:g}{args.unit} ({m.bodyweight_kg:.1f}kg), goal = {args.goal}")
    print("-" * 46)
    print(f"  Maintenance (TDEE){est:<12} {m.tdee:6.0f} kcal")
    print(f"  Calorie target                {m.actual_kcal:6.0f} kcal")
    print("-" * 46)
    print(f"  Protein   {m.protein_g:5.0f} g  ({m.protein_g_per_kg:.1f} g/kg, {m.protein_kcal:.0f} kcal)")
    print(f"  Fat       {m.fat_g:5.0f} g  ({m.fat_g_per_kg:.1f} g/kg floor, {m.fat_kcal:.0f} kcal)")
    print(f"  Carbs     {m.carb_g:5.0f} g  (remainder, {m.carb_kcal:.0f} kcal)")
    print("-" * 46)
    print(f"  Per-meal protein target: ~{m.per_meal_protein_g:.0f} g across 3-5 meals (leucine threshold).")
    if args.goal == "gain":
        print("  Expect ~0.25-0.5% bodyweight/wk; faster = mostly fat. Adjust if scale stalls/runs.")
    elif args.goal == "cut":
        print("  Aim ~0.5-1% bodyweight/wk; keep protein high + training hard to hold muscle.")
    elif args.goal == "recomp":
        print("  Recomp (eat at maintenance): slow, best for novices/returners/higher body fat.")
    if m.shortfall:
        print(f"\n  [!] Protein + fat floor is {m.actual_kcal:.0f} kcal, above your {m.target_kcal:.0f} kcal")
        print("      goal. Options: accept the smaller deficit (shown), raise calories, or drop")
        print("      protein toward 2.2 g/kg. Carbs are already at zero.")
    if m.tdee_is_estimate:
        print("  [!] TDEE is a rough estimate. Track weight 2 wks and adjust cals to the real trend.")
    return 0


def cmd_plates(args: argparse.Namespace) -> int:
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


def cmd_warmup(args: argparse.Namespace) -> int:
    ramp = warmup_ramp(args.weight, unit=args.unit, bar=args.bar)
    if args.json:
        print(to_json(ramp))
        return 0

    print(f"Warm-up ramp to {args.weight:g}{args.unit} (working weight):")
    for step in ramp.steps:
        print(f"  {step.label:<12} ~{step.load:g}{args.unit}")
    print(f"  then work sets @ {args.weight:g}{args.unit}")
    print("Rest 1-3 min between warm-ups; the goal is to prime, not fatigue.")
    return 0


_LB_PER_KG = 0.45359237


def cmd_standards(args: argparse.Namespace) -> int:
    bodyweight_kg = args.bodyweight * _LB_PER_KG if args.unit == "lb" else args.bodyweight
    total_kg = args.total * _LB_PER_KG if args.unit == "lb" else args.total
    try:
        result = strength_score(total_kg, bodyweight_kg, args.sex)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if args.json:
        print(to_json(result))
        return 0

    print(f"Relative-strength scores - {args.total:g}{args.unit} total @ {args.bodyweight:g}{args.unit} "
          f"bodyweight ({args.sex}):")
    print("-" * 40)
    print(f"  Wilks (2020)   {result.wilks:7.2f}")
    print(f"  DOTS           {result.dots:7.2f}")
    print(f"  IPF GL points  {result.ipf_gl:7.2f}")
    print("-" * 40)
    print("IPF GL uses classic (raw) powerlifting coefficients only. All three formulas")
    print("are fit to different samples and will disagree slightly, especially at the")
    print("extremes of the bodyweight range - treat them as three independent opinions,")
    print("not a single ground truth.")
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
    p = argparse.ArgumentParser(prog="liftmath", description="Strength & hypertrophy training math.",
                                 parents=[_json_parent(suppress_default=False)])
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)
    json_parent = _json_parent(suppress_default=True)

    s = sub.add_parser("1rm", help="estimate 1RM from a weight x reps set", parents=[json_parent])
    s.add_argument("--weight", type=float, required=True)
    s.add_argument("--reps", type=int, required=True)
    s.add_argument("--unit", default="lb", choices=["lb", "kg"])
    s.set_defaults(func=cmd_1rm)

    s = sub.add_parser("reps", help="%%1RM load & effort chart from a known 1RM", parents=[json_parent])
    s.add_argument("--onerm", type=float, required=True)
    s.add_argument("--unit", default="lb", choices=["lb", "kg"])
    s.set_defaults(func=cmd_reps)

    s = sub.add_parser("target", help="weight for a target rep count from a 1RM", parents=[json_parent])
    s.add_argument("--onerm", type=float, required=True)
    s.add_argument("--reps", type=int, required=True)
    s.add_argument("--rir", type=int, default=0, help="reps in reserve (stop short of failure)")
    s.add_argument("--unit", default="lb", choices=["lb", "kg"])
    s.set_defaults(func=cmd_target)

    s = sub.add_parser("volume", help="weekly set landmarks per muscle + audit", parents=[json_parent])
    s.add_argument("--muscle", help="one muscle (omit for full table)")
    s.add_argument("--sets", type=int, help="your current weekly hard sets, to audit")
    s.set_defaults(func=cmd_volume)

    s = sub.add_parser("program", help="whole-program weekly volume audit per muscle", parents=[json_parent])
    s.add_argument("--exercise", action="append", required=True, metavar="SPEC",
                   help="'Name | sets x freq | muscle=frac,...' - repeat per exercise; "
                        "fractions optional for known lifts (e.g. 'Bench Press | 4x2')")
    s.set_defaults(func=cmd_program)

    s = sub.add_parser("meso", help="ramp a muscle MEV->MRV over N weeks + deload", parents=[json_parent])
    s.add_argument("--muscle", required=True)
    s.add_argument("--weeks", type=int, default=5, help="total weeks incl. a final deload (default 5)")
    s.set_defaults(func=cmd_meso)

    s = sub.add_parser("macros", help="protein/calorie/fat/carb targets", parents=[json_parent])
    s.add_argument("--bodyweight", type=float, required=True)
    s.add_argument("--goal", default="maintain", choices=list(GOALS))
    s.add_argument("--unit", default="lb", choices=["lb", "kg"])
    s.add_argument("--tdee", type=float, help="maintenance kcal if known (else estimated)")
    s.add_argument("--activity", default="moderate", choices=list(ACTIVITY_LEVELS))
    s.set_defaults(func=cmd_macros)

    s = sub.add_parser("plates", help="plate-loading math", parents=[json_parent])
    s.add_argument("--target", type=float, required=True)
    s.add_argument("--bar", type=float, help="bar weight (default 20kg / 45lb)")
    s.add_argument("--unit", default="lb", choices=["lb", "kg"])
    s.add_argument("--plates", type=float, nargs="*", help="available plate denominations (per side)")
    s.add_argument("--preset", choices=sorted(PRESETS),
                   help="named non-standard setup (kg-only): "
                        "'womens' = 15kg bar, 'metric-no-45' = metric gym with no 45lb-equivalent plate")
    s.set_defaults(func=cmd_plates)

    s = sub.add_parser("warmup", help="warm-up ramp to a working weight", parents=[json_parent])
    s.add_argument("--weight", type=float, required=True)
    s.add_argument("--bar", type=float, help="bar weight (default 20kg / 45lb)")
    s.add_argument("--unit", default="lb", choices=["lb", "kg"])
    s.set_defaults(func=cmd_warmup)

    s = sub.add_parser("standards", help="relative-strength scoring: Wilks/DOTS/IPF GL",
                        parents=[json_parent])
    s.add_argument("--total", type=float, required=True, help="competition total (or single-lift result)")
    s.add_argument("--bodyweight", type=float, required=True)
    s.add_argument("--sex", required=True, choices=["male", "female"])
    s.add_argument("--unit", default="lb", choices=["lb", "kg"])
    s.set_defaults(func=cmd_standards)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
