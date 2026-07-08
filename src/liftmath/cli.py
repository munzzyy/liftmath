"""Command-line interface for liftmath.

Subcommands:
    1rm         Estimate 1RM from a weight x reps set (multi-formula consensus + range)
    bw-onerm    Weighted bodyweight-movement 1RM (pull-up/chin-up/dip): total-load 1RM +
                the equivalent added-weight 1RM at your bodyweight
    reps        Given a 1RM, print the %%1RM -> predicted-reps / RIR load chart
    target      Weight for a target rep/RIR count at a given 1RM
    rpe         %%1RM <-> RPE/RIR, derived from the same Epley-based model as `reps`/`target`
    volume      Weekly hard-set landmarks per muscle (MEV/MAV/MRV) + audit a set count
    program     Whole-program volume audit: sum weekly sets per muscle across a split
    meso        Mesocycle set-progression: ramp a muscle MEV -> MRV over N weeks, then deload
    progression Double-progression: next session's weight/rep target from a rep range
    macros      Protein / calorie / fat / carb targets from bodyweight + goal
    cunningham  Cunningham (1980) lean-mass-based RMR/TDEE estimate
    bulkcut     Weekly bulk/cut rate-of-change target, banded by trainee tier
    plates      Plate-loading math for a target barbell weight (add --inventory for a
                finite per-side plate count instead of an unlimited supply)
    warmup      Warm-up ramp sets up to a working weight
    ffmi        Fat-free mass index (Kouri 1995) + natural-reference-ceiling flag
    navybf      Navy tape-measure body-fat %% estimate (Hodgdon & Beckett 1984)
    sessionload Session load / weekly load / training monotony / strain (Foster 2001)
    symmetry    Lift-ratio symmetry: squat/bench/deadlift (+ optional OHP) vs. expected ratios
    tm          Training max: pct of a 1RM, rounded down to an increment (Wendler)
    program531  Classic Wendler 5/3/1: one week's full percentage-based set list
    gzclp       GZCLP next-session prescription from current stage/weight/result (Lefever)
    nsuns       nSuns LP (4-day variant) T1 set list for one lift day
    standards   Relative-strength scoring: Wilks (original + 2020), DOTS, IPF GL points
    mcculloch   McCulloch age-adjusted total for masters lifters (WRPF)
    tier        Bodyweight-indexed strength tier (beginner->elite) for a total
    glossary    Plain-English + technical definitions for every term liftmath uses

All loads are unit-agnostic (kg or lb) unless a subcommand needs the unit; pass --unit.
Pass --json (before or after the subcommand) to get machine-readable JSON instead of
the formatted text, e.g. `liftmath 1rm --weight 225 --reps 5 --json`.

Most commands print a short plain-English aside the first time a piece of jargon (RIR,
TDEE, MEV, ...) shows up in their output. Run `liftmath glossary` for the full list, or
`liftmath glossary --term RIR` for one term.
"""

from __future__ import annotations

import argparse
import json
import sys

from liftmath import __version__
from liftmath._serialize import to_dict, to_json
from liftmath.bodycomp import ffmi as compute_ffmi
from liftmath.bodycomp import navy_body_fat
from liftmath.bodyweight import MOVEMENTS, weighted_bodyweight_one_rm
from liftmath.bulkcut import TIERS, rate_target
from liftmath.glossary import GLOSSARY, glossary_entry
from liftmath.loads import load_chart, target_load
from liftmath.macros import ACTIVITY_LEVELS, GOALS, cunningham_tdee, macro_targets
from liftmath.mesocycle import ramp_mesocycle
from liftmath.onerm import estimate_one_rm
from liftmath.plates import PRESETS, _parse_inventory_spec, load_plates, load_plates_from_inventory
from liftmath.program import ExerciseSet, audit_program
from liftmath.progression import next_progression_step
from liftmath.rpe import pct_1rm_from_reps_and_rir, rpe_from_reps_and_pct
from liftmath.sessionload import weekly_load
from liftmath.standards import mcculloch_score
from liftmath.standards import score as strength_score
from liftmath.symmetry import score_symmetry
from liftmath.templates import (
    NSUNS_4DAY_SCHEME,
    T1_STAGES,
    T2_STAGES,
    gzclp_next_session,
    nsuns_day,
    program_531,
    training_max,
)
from liftmath.tiers import TIER_NAMES, classify_tier
from liftmath.volume import LANDMARKS, landmarks_for
from liftmath.warmup import warmup_ramp

_LB_PER_KG = 0.45359237

# Shared plain-English explainer for the volume landmarks, used by both
# `volume` branches (per-muscle and full-table) and by `program`, so the
# four abbreviations are defined identically everywhere they show up.
_VOLUME_LANDMARK_EXPLAINER = (
    "MV is the least work that keeps a muscle from shrinking; MEV is the least that actually "
    "grows it; MAV is the productive sweet-spot range; MRV is the most you can still recover from."
)


def _hint(*keys: str) -> None:
    """Print a short plain-English aside for the given glossary term(s).

    One line per command call site (not one line per term - multi-term
    calls read as a single flowing sentence, see e.g. `cmd_meso`), gated by
    the caller to non-JSON output only. Silently skips an unknown key rather
    than raising - a typo here should never crash a command.
    """
    for key in keys:
        entry = GLOSSARY.get(key)
        if entry:
            print(f"  ({entry.term}: {entry.plain})")


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
    print("  e1RM = an estimated 1RM from a submaximal set, not a tested max. No single formula")
    print("  is most accurate across every rep range, so this runs six and takes the CONSENSUS")
    print("  (median) instead of picking one. Table below is sorted by value, not accuracy - no")
    print("  formula here is established as more accurate than another (see onerm.py).")
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


def cmd_bw_onerm(args: argparse.Namespace) -> int:
    try:
        r = weighted_bodyweight_one_rm(args.movement, args.bodyweight, args.added, args.reps,
                                        unit=args.unit)
    except (KeyError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if args.json:
        print(to_json(r))
        return 0

    verb = "assisted by" if r.is_assisted else "with"
    print(f"Weighted {args.movement}: {args.bodyweight:g}{args.unit} bodyweight {verb} "
          f"{abs(args.added):g}{args.unit} x {args.reps} reps")
    if args.reps > 1:
        _hint("e1rm")
    print(f"  total system load   {r.total_load:6.1f}{args.unit}")
    est = r.total_load_estimate
    if not est.is_exact:
        print(f"  total-load 1RM      {est.consensus:6.1f}{args.unit}   "
              f"(median; range {est.low:.1f}-{est.high:.1f})")
    else:
        print(f"  total-load 1RM      {est.consensus:6.1f}{args.unit}   (that set IS a 1RM)")
    print(f"  added-weight 1RM    {r.added_weight_one_rm:6.1f}{args.unit}   "
          f"(what you could add for 1 rep at this bodyweight)")
    print(f"  added weight        {r.added_weight_pct_bodyweight:5.1f}%  of bodyweight")
    if r.is_assisted:
        print("\n[!] Assisted set: added weight is negative (net assistance), so the added-weight")
        print("    1RM being negative just means you'd still need some assistance for 1 rep.")
    elif not est.is_exact and est.high_rep_warning:
        print("\n[!] r>12: rep-max equations lose accuracy on the total-load estimate; treat the")
        print("    added-weight 1RM as soft too. Test a heavier set of <=6 reps for a sharper read.")
    elif not est.is_exact and est.soft_estimate_warning:
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
    try:
        result = target_load(args.onerm, args.reps, rir=args.rir)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if args.json:
        print(to_json(result))
        return 0

    print(f"To do ~{args.reps} reps (to failure) with a {args.onerm:g}{args.unit} 1RM:")
    print(f"  load ~= {result.load:.1f}{args.unit}  ({result.pct*100:.0f}% 1RM)")
    if args.rir:
        print(f"  at {args.rir} RIR (stop at {args.reps}, ~{result.rir_max_reps} rep max): "
              f"{result.rir_load:.1f}{args.unit}  ({result.rir_pct*100:.0f}% 1RM)")
        _hint("rir")
    return 0


def cmd_rpe(args: argparse.Namespace) -> int:
    try:
        if args.rpe is not None and args.pct is not None:
            print("error: pass exactly one of --rpe or --pct, not both", file=sys.stderr)
            return 1
        if args.rpe is not None:
            result = pct_1rm_from_reps_and_rir(args.reps, 10 - args.rpe)
            if args.json:
                print(to_json(result))
                return 0
            print(f"{args.reps} reps @ RPE {args.rpe:g} ({result.rir:g} RIR) ~= {result.pct_1rm*100:.1f}% 1RM")
        elif args.pct is not None:
            result = rpe_from_reps_and_pct(args.reps, args.pct / 100.0)
            if args.json:
                print(to_json(result))
                return 0
            print(f"{args.reps} reps @ {args.pct:g}% 1RM ~= RPE {result.rpe:.1f} ({result.rir:.1f} RIR)")
        else:
            print("error: pass --rpe or --pct", file=sys.stderr)
            return 1
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if not args.json:
        print("  (RPE is a 0-10 gut check on how hard a set felt, where 10 is failure. RIR is the")
        print("   same idea counted backward - how many more reps you had left before failure.)")
        print("[!] Derived from the same Epley-based model as `reps`/`target`, not the popular")
        print("    RTS/Tuchscherer chart - that chart is mostly a practitioner heuristic, not")
        print("    RCT data (Zourdos 2016 only measured 3 anchor points). Treat this as soft,")
        print("    same as high-rep 1RM estimates.")
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
        print(f"\n  {_VOLUME_LANDMARK_EXPLAINER}")
        print("[evidence tier] Practitioner consensus/expert heuristic (Israetel/RP), NOT a")
        print("peer-reviewed per-muscle table.")
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
    print(f"{_VOLUME_LANDMARK_EXPLAINER}")
    print("Count a 'hard set' as a working set taken to ~0-4 reps in reserve.")
    print("Directly-trained isolation counts fully; a compound counts fully for its prime")
    print("mover and ~0.5 for strong synergists. Titrate up from MEV until progress stalls or")
    print("recovery suffers - these numbers are a map, not the territory.")
    print("[evidence tier] Practitioner consensus/expert heuristic, NOT a peer-reviewed")
    print("per-muscle table - no primary source publishes these exact cutoffs.")
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
    if sets <= 0 or freq <= 0:
        raise ValueError(
            f"bad 'sets x freq' in '{spec}': sets and freq must both be > 0 "
            "(want e.g. '4x2' = 4 sets, 2 sessions/wk)"
        )

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
    print("Prime mover counts fully, synergists ~0.3-0.7. Same MEV/MAV/MRV bands as `volume`:")
    print(f"{_VOLUME_LANDMARK_EXPLAINER}")
    print("[evidence tier] MEV/MAV/MRV bands are practitioner consensus, not peer-reviewed data.")
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
    print("  (a mesocycle is a training block that ramps volume toward a peak; a deload is the")
    print("   planned easy week after it that lets fatigue dissipate before the next block)")
    print(f"{'week':>5}{'sets':>7}{'%MRV':>7}   note")
    print("-" * 46)
    for w in meso.weeks:
        print(f"{w.week:>5}{w.sets:>7}{w.pct_mrv:>6.0f}%   {w.note}")
    print("-" * 46)
    print("Progress LOAD/reps within these set counts by double progression each week.")
    print("If top-set reps stall two weeks running, deload early rather than grinding.")
    print("[evidence tier] MEV/MRV endpoints are practitioner consensus, not peer-reviewed data.")
    return 0


def cmd_progression(args: argparse.Namespace) -> int:
    try:
        step = next_progression_step(args.reps_low, args.reps_high, args.weight, args.reps_achieved,
                                      args.increment, previous_reps_achieved=args.previous_reps_achieved)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if args.json:
        print(to_json(step))
        return 0

    print(f"Range {args.reps_low}-{args.reps_high}, {args.weight:g}{args.unit} x {args.reps_achieved} reps:")
    print(f"  {step.note}")
    print("Practitioner bookkeeping method (mechanism trivially sound), not a cited RCT finding -")
    print("double progression is an accounting scheme, not a physiological claim.")
    return 0


def cmd_macros(args: argparse.Namespace) -> int:
    height_m = None
    if args.height is not None:
        height_m = args.height * 0.0254 if args.height_unit == "in" else args.height / 100.0
    try:
        m = macro_targets(args.bodyweight, args.goal, unit=args.unit, tdee=args.tdee, activity=args.activity,
                           age=args.age, height_m=height_m, sex=args.sex, bodyfat_pct=args.bodyfat)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if args.json:
        print(to_json(m))
        return 0

    method_label = {
        "supplied": " (you supplied)",
        "cunningham": " (Cunningham, from body fat %)",
        "mifflin": " (Mifflin-St Jeor estimate)",
        "quick_estimate": " (quick estimate)",
    }[m.tdee_method]
    print(f"Targets for {args.bodyweight:g}{args.unit} ({m.bodyweight_kg:.1f}kg), goal = {args.goal}")
    _hint("tdee")
    print("-" * 46)
    print(f"  Maintenance (TDEE){method_label:<30} {m.tdee:6.0f} kcal")
    print(f"  Calorie target                {m.actual_kcal:6.0f} kcal")
    print("-" * 46)
    print(f"  Protein   {m.protein_g:5.0f} g  ({m.protein_g_per_kg:.1f} g/kg, {m.protein_kcal:.0f} kcal)")
    print(f"  Fat       {m.fat_g:5.0f} g  ({m.fat_g_per_kg:.1f} g/kg floor, {m.fat_kcal:.0f} kcal)")
    print(f"  Carbs     {m.carb_g:5.0f} g  (remainder, {m.carb_kcal:.0f} kcal)")
    print("-" * 46)
    print("  Protein and fat are set first, as biological minimums; carbs fill whatever calorie")
    print("  budget is left - that's why carbs move the most between a gain and a cut.")
    print(f"  Per-meal protein target: ~{m.per_meal_protein_g:.0f} g across 3-5 meals (leucine threshold).")
    if args.goal == "gain":
        print("  Expect ~0.25-0.5% bodyweight/wk; faster = mostly fat. Adjust if scale stalls/runs.")
    elif args.goal == "cut":
        print("  Aim ~0.5-1% bodyweight/wk; keep protein high + training hard to hold muscle.")
    elif args.goal == "recomp":
        _hint("recomp")
        print("  Recomp (eat at maintenance): slow, best for novices/returners/higher body fat.")
    if m.shortfall:
        print(f"\n  [!] Protein + fat floor is {m.actual_kcal:.0f} kcal, above your {m.target_kcal:.0f} kcal")
        print("      goal. Options: accept the smaller deficit (shown), raise calories, or drop")
        print("      protein toward 2.2 g/kg. Carbs are already at zero.")
    if m.tdee_method == "quick_estimate":
        print("\n  [!] TDEE is a QUICK ESTIMATE (bodyweight x an activity factor) - not a named,")
        print("      published equation. Pass --age/--height/--sex for a Mifflin-St Jeor estimate,")
        print("      or --bodyfat for a Cunningham (lean-mass) estimate - either is more accurate.")
    elif m.tdee_method == "mifflin":
        print("\n  Mifflin-St Jeor: the best general-population TDEE equation in head-to-head")
        print("  comparisons (Frankenfield et al. 2005). Pass --bodyfat instead if you know it -")
        print("  Cunningham (lean-mass-based) is even better for a lean, trained body specifically.")
    elif m.tdee_method == "cunningham":
        print("\n  Cunningham: meaningfully better than a bodyweight-only estimate for lean, trained")
        print("  individuals specifically - see `liftmath cunningham` for the number on its own.")
    if m.tdee_is_estimate:
        print("  Track bodyweight 2 wks and adjust calories to the real trend either way.")
    return 0


def cmd_cunningham(args: argparse.Namespace) -> int:
    try:
        if args.lean_mass is not None:
            if args.bodyweight is not None or args.bodyfat is not None:
                print("error: pass --lean-mass, OR --bodyweight and --bodyfat, not both", file=sys.stderr)
                return 1
            lean_mass_kg = args.lean_mass * _LB_PER_KG if args.unit == "lb" else args.lean_mass
            result = cunningham_tdee(lean_mass_kg, activity=args.activity)
        elif args.bodyweight is not None and args.bodyfat is not None:
            bw_kg = args.bodyweight * _LB_PER_KG if args.unit == "lb" else args.bodyweight
            result = cunningham_tdee(activity=args.activity, bodyweight_kg=bw_kg, bodyfat_pct=args.bodyfat)
        else:
            print("error: pass --lean-mass, or both --bodyweight and --bodyfat "
                  "(e.g. the body-fat %% `navybf` or `ffmi` gave you)", file=sys.stderr)
            return 1
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if args.json:
        print(to_json(result))
        return 0

    lean_display = result.lean_mass_kg / _LB_PER_KG if args.unit == "lb" else result.lean_mass_kg
    print(f"Cunningham (1980) RMR/TDEE for {lean_display:.1f}{args.unit} lean mass ({args.activity}):")
    _hint("cunningham")
    print(f"  RMR   {result.rmr_kcal:6.0f} kcal  (500 + 22*lean_kg)")
    print(f"  TDEE  {result.tdee:6.0f} kcal  (RMR x {result.activity_multiplier:g})")
    print("Established for ATHLETES specifically (2023 Sports Medicine systematic review); a")
    print("general-population comparison found this equation overestimates by ~14-15% for")
    print("non-athletes. Use `macros` (bodyweight-based, or --age/--height/--sex for Mifflin-St")
    print("Jeor) if lean mass or a body-fat %% isn't known.")
    return 0


def cmd_bulkcut(args: argparse.Namespace) -> int:
    bodyweight_kg = args.bodyweight * _LB_PER_KG if args.unit == "lb" else args.bodyweight
    try:
        result = rate_target(bodyweight_kg, args.goal, tier=args.tier)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if args.json:
        print(to_json(result))
        return 0

    conv = 1.0 if args.unit == "kg" else 1.0 / _LB_PER_KG
    print(f"{args.goal} target for {args.bodyweight:g}{args.unit} ({args.tier}):")
    print(f"  {result.rate_low_pct:g}-{result.rate_high_pct:g}% bodyweight/week = "
          f"{result.weekly_change_low_kg*conv:.2f}-{result.weekly_change_high_kg*conv:.2f}{args.unit}/week")
    _hint("partition")
    print(f"  {result.partition_note}")
    print("[evidence tier] emerging - Garthe 2013 is one well-designed trial in elite athletes;")
    print("Helms's tier thresholds are expert synthesis, not a single dated RCT.")
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

        print(f"Load {args.target:g}{args.unit} on a {result.bar:g}{args.unit} bar "
              f"(from your inventory):")
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


# Display label per tier key - shared between `standards --tier` and `tier`
# so the two surfaces never drift into describing the same tier differently.
_TIER_LABELS = {
    "below_beginner": "below beginner",
    "beginner": "BEGINNER",
    "novice": "NOVICE",
    "intermediate": "INTERMEDIATE",
    "advanced": "ADVANCED",
    "elite": "ELITE",
}


def _print_tier_block(result, unit: str, bodyweight_display: float) -> None:
    """Shared strength-tier text block for `tier` and `standards --tier`.

    `result` is a `liftmath.tiers.TierResult`; `bodyweight_display` is the
    bodyweight in the CALLER's original --unit (for the header line only -
    all the actual conversion happens via `conv` below).
    """
    conv = 1.0 if unit == "kg" else 1.0 / _LB_PER_KG
    th = result.thresholds
    print(f"  bodyweight-indexed tier thresholds at {bodyweight_display:g}{unit} (interpolated):")
    for name, value in zip(TIER_NAMES, (th.beginner, th.novice, th.intermediate, th.advanced, th.elite)):
        marker = " <- your tier" if name == result.tier else ""
        print(f"    {name:<14}{value * conv:9.1f}{unit}{marker}")
    print(f"  tier: {_TIER_LABELS.get(result.tier, result.tier)}")
    if result.pct_into_tier is not None:
        print(f"    {result.pct_into_tier:.0f}% of the way through this tier")
    if result.next_tier is not None and result.total_to_next_kg is not None:
        print(f"    {result.total_to_next_kg * conv:.1f}{unit} to "
              f"{_TIER_LABELS.get(result.next_tier, result.next_tier)}")
    elif result.tier == "elite":
        print("    already at the top published tier - no higher threshold on this table")
    if th.clamped == "below_min":
        print(f"  [!] {bodyweight_display:g}{unit} is below the table's lightest bodyweight bracket "
              f"({th.clamp_bracket_kg * conv:g}{unit}) - using")
        print("      that bracket's thresholds rather than extrapolating lighter.")
    elif th.clamped == "above_max":
        print(f"  [!] {bodyweight_display:g}{unit} is above the table's heaviest bodyweight bracket "
              f"({th.clamp_bracket_kg * conv:g}{unit}) - using")
        print("      that bracket's thresholds rather than extrapolating heavier.")
    print("Source: Strength Level's published TOTAL standards (5th/20th/50th/80th/95th percentile,")
    print("bodyweight-indexed), cross-checked against ExRx/Kilgore (same ballpark, 3-18% apart, no")
    print("wild divergence). [!] Self-reported population percentiles - Strength Level's own FAQ")
    print("says its loggers skew stronger than the general population; this is NOT a training-age")
    print("guarantee and NOT a judge-verified competition result.")


def cmd_standards(args: argparse.Namespace) -> int:
    bodyweight_kg = args.bodyweight * _LB_PER_KG if args.unit == "lb" else args.bodyweight
    total_kg = args.total * _LB_PER_KG if args.unit == "lb" else args.total
    try:
        result = strength_score(total_kg, bodyweight_kg, args.sex)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    # --tier is additive and opt-in: with it omitted, output below (both JSON
    # and text) is byte-identical to before this flag existed. See `tier` for
    # the same computation as its own dedicated subcommand.
    tier_result = None
    tier_error = None
    if args.tier:
        try:
            tier_result = classify_tier(total_kg, bodyweight_kg, args.sex)
        except ValueError as e:
            tier_error = str(e)

    if args.json:
        payload = to_dict(result)
        if args.tier:
            payload["tier"] = to_dict(tier_result) if tier_result is not None else None
            if tier_error is not None:
                payload["tier_error"] = tier_error
        print(json.dumps(payload, indent=2))
        return 0

    print(f"Relative-strength scores - {args.total:g}{args.unit} total @ {args.bodyweight:g}{args.unit} "
          f"bodyweight ({args.sex}):")
    print("  Each score below lets you compare lifters across bodyweights on one scale - Wilks")
    print("  and DOTS are two different curve-fit formulas for it (what \"DOTS\" stands for is")
    print("  disputed, so this app doesn't guess); IPF GL is the federation's own official version.")
    print("-" * 40)
    print(f"  Wilks (2020)      {result.wilks:7.2f}")
    print(f"  Wilks (original)  {result.wilks_original:7.2f}")
    print(f"  DOTS              {result.dots:7.2f}")
    print(f"  IPF GL points     {result.ipf_gl:7.2f}")
    print("-" * 40)
    print("IPF GL uses classic (raw) powerlifting coefficients only. All four formulas")
    print("are fit to different samples and will disagree slightly, especially at the")
    print("extremes of the bodyweight range - treat them as independent opinions, not a")
    print("single ground truth. Wilks-2020 is the IPF's current standard; original Wilks")
    print("is kept for historical comparison. [evidence tier] established as competition")
    print("scoring CONVENTIONS (real federation formulas fit to real competition samples),")
    print("not evidence in the causal/RCT sense.")

    if args.tier:
        print()
        if tier_error is not None:
            print(f"error computing strength tier: {tier_error}", file=sys.stderr)
        else:
            print("Strength tier (bodyweight-indexed percentile, see `liftmath tier --help`):")
            _print_tier_block(tier_result, args.unit, args.bodyweight)
    return 0


def cmd_mcculloch(args: argparse.Namespace) -> int:
    total_kg = args.total * _LB_PER_KG if args.unit == "lb" else args.total
    try:
        result = mcculloch_score(total_kg, args.age)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if args.json:
        print(to_json(result))
        return 0

    adjusted = result.adjusted_total / _LB_PER_KG if args.unit == "lb" else result.adjusted_total
    print(f"McCulloch age adjustment - {args.total:g}{args.unit} total @ age {args.age}:")
    print("  \"Masters\" means 40+ - strength-vs-age curves differ from open-age competition, so")
    print("  this answers \"how does this total compare once age is accounted for\" the same way")
    print("  Wilks/DOTS answer it for bodyweight.")
    print(f"  coefficient      {result.coefficient:.3f}")
    print(f"  adjusted total   {adjusted:.1f}{args.unit}")
    print("Source: WRPF (2022) McCulloch Coefficients for Masters. [evidence tier] established")
    print("as a competition convention (federation table from real masters-competition data),")
    print("though the WRPF's own document doesn't publish the per-age curve's derivation")
    print("methodology (unlike IPF GL, which does) - treat the curve's shape as less")
    print("independently verifiable than IPF GL's, even though the numbers are the")
    print("federation's own published table.")
    return 0


def cmd_tier(args: argparse.Namespace) -> int:
    if args.total is not None:
        if args.squat is not None or args.bench is not None or args.deadlift is not None:
            print("error: pass --total, OR --squat/--bench/--deadlift, not both", file=sys.stderr)
            return 1
        total = args.total
    else:
        if args.squat is None or args.bench is None or args.deadlift is None:
            print("error: pass --total, or all three of --squat/--bench/--deadlift", file=sys.stderr)
            return 1
        total = args.squat + args.bench + args.deadlift

    bodyweight_kg = args.bodyweight * _LB_PER_KG if args.unit == "lb" else args.bodyweight
    total_kg = total * _LB_PER_KG if args.unit == "lb" else total
    try:
        result = classify_tier(total_kg, bodyweight_kg, args.sex)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if args.json:
        print(to_json(result))
        return 0

    print(f"Strength tier - {total:g}{args.unit} total @ {args.bodyweight:g}{args.unit} bodyweight ({args.sex}):")
    _hint("strength_tier")
    _print_tier_block(result, args.unit, args.bodyweight)
    return 0


def cmd_ffmi(args: argparse.Namespace) -> int:
    weight_kg = args.weight * _LB_PER_KG if args.unit == "lb" else args.weight
    height_m = args.height * 0.0254 if args.height_unit == "in" else args.height / 100.0
    try:
        result = compute_ffmi(weight_kg, height_m, args.bodyfat)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if args.json:
        print(to_json(result))
        return 0

    print(f"FFMI for {args.weight:g}{args.unit}, {args.bodyfat:g}% body fat:")
    _hint("ffmi")
    print(f"  lean mass          {result.lean_mass_kg:.1f} kg")
    print(f"  FFMI               {result.ffmi:.2f}")
    print(f"  normalized FFMI    {result.normalized_ffmi:.2f}  (adjusted to 1.80m reference height)")
    if result.above_natural_reference_ceiling:
        print("  [!] above 25.0, the natural-sample ceiling from Kouri et al. (1995, n=157")
        print("      male athletes) - a reference point from one 1995 sample, not a hard")
        print("      physiological law. Individuals can legitimately sit above/below it.")
    return 0


def cmd_navybf(args: argparse.Namespace) -> int:
    height_in = args.height if args.height_unit == "in" else args.height / 2.54
    try:
        result = navy_body_fat(args.sex, height_in, args.neck, args.waist, hip_in=args.hip)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if args.json:
        print(to_json(result))
        return 0

    print(f"Navy tape body-fat estimate ({args.sex}):")
    _hint("navy_bf")
    print(f"  ~{result.bodyfat_pct:.1f}%  (+/- {result.error_band_pct:g} points vs. hydrostatic weighing)")
    print("Source: Hodgdon & Beckett (1984), Naval Health Research Center Report 84-11.")
    print("Field-expedient estimate for tracking trend over time, not a clinical reading.")
    if result.less_reliable_at_extremes:
        print("[!] Under ~12% or over ~25% body fat, this regression fits worst - very lean or")
        print("    unusually muscular bodies push the real error past the usual +/-3-4 points.")
        print("    Read this as a rough trend line here, not even the usual band.")
    return 0


def cmd_sessionload(args: argparse.Namespace) -> int:
    try:
        result = weekly_load(args.load)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if args.json:
        print(to_json(result))
        return 0

    print(f"Session-load summary over {len(result.loads)} logged sessions:")
    print("  (session load = how hard a session felt x how long it took; monotony = how same-y")
    print("   the week's loads were; strain = weekly load scaled up by monotony)")
    print(f"  weekly load   {result.weekly_load:8.1f}")
    print(f"  mean load     {result.mean_load:8.1f}")
    print(f"  monotony      {result.monotony:8.2f}  (mean / population SD)")
    print(f"  strain        {result.strain:8.1f}  (weekly load x monotony)")
    print("Source: Foster et al. (2001). [evidence tier] established for session-RPE as a")
    print("load MEASUREMENT method; emerging/contested for monotony+strain as injury/illness")
    print("PREDICTORS - the source paper floats that only as a hypothesis, not a finding.")
    print("Log multiple same-day sessions as separate --load entries, not pre-summed (matches")
    print("how the paper's own worked example computes monotony).")
    return 0


def cmd_symmetry(args: argparse.Namespace) -> int:
    try:
        report = score_symmetry(args.squat, args.bench, args.deadlift, args.sex,
                                 ohp=args.ohp, bodyweight=args.bodyweight)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if args.json:
        print(to_json(report))
        return 0

    print(f"Lift-ratio symmetry ({args.sex}) - total {report.total:g}{args.unit}:")
    _hint("symmetry")
    print("-" * 62)
    print(f"{'lift':<10}{'weight':>9}{'% of DL':>10}{'expected':>10}{'% of total':>12}   verdict")
    print("-" * 62)
    for lift in ("squat", "bench", "deadlift", "ohp"):
        if lift not in report.lifts:
            continue
        lr = report.lifts[lift]
        print(f"{lift:<10}{lr.weight:>8.1f}{lr.ratio_to_deadlift*100:>9.1f}%"
              f"{lr.expected_ratio*100:>9.1f}%{lr.ratio_to_total*100:>11.1f}%   {lr.verdict}")
    print("-" * 62)
    if "ohp" in report.lifts:
        print("[!] OHP's expected ratio is single-sourced (Strength Level only - Symmetric")
        print("    Strength publishes no OHP figure to cross-check it against), unlike")
        print("    squat/bench which are corroborated across two independent methodologies.")
    print("[evidence tier] population heuristics from two independent secondary sources")
    print("(Symmetric Strength's world-record-median method, Strength Level's >20M-lift")
    print("intermediate-tier standards) - NOT a physiological law. Individual 'correct'")
    print("ratios vary with limb length, technique, and training history.")
    return 0


def _print_set_table(sets, unit: str) -> None:
    print(f"{'set':>4}{'%TM':>7}{'weight':>10}{'reps':>7}   amrap")
    print("-" * 40)
    for s in sets:
        amrap = "yes (+)" if s.amrap else ""
        print(f"{s.set_number:>4}{s.pct_tm*100:>6.0f}%{s.weight:>9.1f}{unit}{s.reps:>7}   {amrap}")


def cmd_tm(args: argparse.Namespace) -> int:
    # Two ways in: a known 1RM directly, or an AMRAP set (weight x reps) this
    # cycle's last top set - derived via the same six-formula consensus `1rm`
    # uses, then fed straight into `training_max` (no new math, just wiring
    # two already-shipped functions together).
    onerm = args.onerm
    derived_est = None
    if onerm is None:
        if args.amrap_weight is None or args.amrap_reps is None:
            print("error: pass --onerm, or both --amrap-weight and --amrap-reps", file=sys.stderr)
            return 1
        try:
            derived_est = estimate_one_rm(args.amrap_weight, args.amrap_reps, unit=args.unit)
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            return 1
        onerm = derived_est.consensus
    elif args.amrap_weight is not None or args.amrap_reps is not None:
        print("error: pass --onerm, OR --amrap-weight/--amrap-reps, not both", file=sys.stderr)
        return 1

    try:
        result = training_max(onerm, pct=args.pct, increment=args.increment, unit=args.unit)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if args.json:
        print(to_json(result))
        return 0

    if derived_est is not None:
        print(f"AMRAP set {args.amrap_weight:g}{args.unit} x {args.amrap_reps} reps -> e1RM "
              f"{derived_est.consensus:.1f}{args.unit} (median of six formulas)")
    print(f"Training max from a {onerm:g}{args.unit} 1RM at {result.pct*100:.0f}%:")
    _hint("training_max")
    print(f"  {result.training_max:g}{args.unit}  (rounded down to the nearest {result.increment:g}{args.unit})")
    print("Source: Wendler's 5/3/1 - 90% of a tested 1RM is the published default, kept")
    print("deliberately submaximal so percentage-based sets stay achievable across a cycle.")
    return 0


def cmd_program531(args: argparse.Namespace) -> int:
    try:
        week = program_531(args.tm, args.week, increment=args.increment)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if args.json:
        print(to_json(week))
        return 0

    label = "deload" if week.is_deload else f"week {week.week}"
    print(f"5/3/1 - {label} (TM {args.tm:g}{args.unit}):")
    _hint("training_max")
    _print_set_table(week.sets, args.unit)
    if not week.is_deload:
        print("\n'+' sets are AMRAP (as many reps as possible at or past the listed count).")
        print("Source: Wendler's 5/3/1. TM progression after a completed cycle (not applied")
        print("automatically - it depends on your AMRAP result): +5lb/2.5kg upper, +10lb/5kg lower.")
    else:
        print("\nDeload week: no AMRAP sets, keep effort light - the point is to recover.")
    return 0


def cmd_gzclp(args: argparse.Namespace) -> int:
    try:
        result = gzclp_next_session(args.tier, args.stage, args.weight, args.made,
                                     lift_type=args.lift_type, unit=args.unit,
                                     amrap_reps=args.amrap_reps)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if args.json:
        print(to_json(result))
        return 0

    print(f"GZCLP {args.tier.upper()} ({args.lift_type}) - {result.note}")
    _hint("t1t2t3")
    if args.tier == "t3":
        _hint("amrap")
    print(f"  next: {result.next_stage} @ {result.next_weight:g}{args.unit}")
    if result.needs_retest:
        print("\n[!] A retest is a real training event this library can't compute for you -")
        print("    go test a fresh 5RM, then start the next cycle at 85% of that number.")
    print("Source: Cody Lefever's GZCL method / GZCLP. T1 stages 5x3->6x2->10x1, T2 stages")
    print("3x10->3x8->3x6, T3 single-stage (progress by weight once the AMRAP hits 25 reps).")
    return 0


def cmd_nsuns(args: argparse.Namespace) -> int:
    try:
        day = nsuns_day(args.day, args.tm, increment=args.increment)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if args.json:
        print(to_json(day))
        return 0

    print(f"nSuns LP (4-day) - {args.day}, Scheme {day.scheme} (TM {args.tm:g}{args.unit}):")
    _hint("training_max")
    _print_set_table(day.sets, args.unit)
    print("\n'+' sets are AMRAP (as many reps as possible at or past the listed count). T1 (this")
    print("table) only - T2 (the paired secondary lift) isn't computed here; its exact per-set")
    print("percentages couldn't be independently corroborated with the same confidence as T1's,")
    print("so it's left out rather than guessed (see templates.py's module docstring).")
    return 0


def cmd_glossary(args: argparse.Namespace) -> int:
    if args.term:
        entry = glossary_entry(args.term)
        if entry is None:
            print(f"error: unknown term '{args.term}'. Run `liftmath glossary` for the full list.",
                  file=sys.stderr)
            return 1
        if args.json:
            print(to_json(entry))
            return 0
        print(entry.term)
        print(f"  plain:     {entry.plain}")
        print(f"  technical: {entry.technical}")
        return 0

    if args.json:
        print(json.dumps(
            {k: {"term": v.term, "plain": v.plain, "technical": v.technical} for k, v in GLOSSARY.items()},
            indent=2,
        ))
        return 0

    print("liftmath glossary - plain-English first, technical meaning second.")
    print("Look up one term with `liftmath glossary --term <name>`.")
    print("=" * 66)
    for entry in GLOSSARY.values():
        print(f"\n{entry.term}")
        print(f"  {entry.plain}")
        print(f"  (technical: {entry.technical})")
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

    s = sub.add_parser("bw-onerm", help="weighted bodyweight-movement 1RM (pull-up/chin-up/dip)",
                        parents=[json_parent])
    s.add_argument("--movement", required=True, choices=sorted(MOVEMENTS))
    s.add_argument("--bodyweight", type=float, required=True)
    s.add_argument("--added", type=float, required=True,
                   help="external weight added for the tested set (negative = assisted)")
    s.add_argument("--reps", type=int, required=True)
    s.add_argument("--unit", default="lb", choices=["lb", "kg"])
    s.set_defaults(func=cmd_bw_onerm)

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

    s = sub.add_parser("rpe", help="%%1RM <-> RPE/RIR, Epley-derived (not the RTS chart)",
                        parents=[json_parent])
    s.add_argument("--reps", type=int, required=True, help="reps performed in the set")
    s.add_argument("--rpe", type=float, help="rated exertion, 0-10 (10 = failure)")
    s.add_argument("--pct", type=float, help="%%1RM used for the set (e.g. 80 for 80%%)")
    s.set_defaults(func=cmd_rpe)

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

    s = sub.add_parser("progression", help="double-progression: next weight/rep target",
                        parents=[json_parent])
    s.add_argument("--reps-low", type=int, required=True, help="bottom of the working rep range")
    s.add_argument("--reps-high", type=int, required=True, help="top of the working rep range")
    s.add_argument("--weight", type=float, required=True, help="weight used for the set just performed")
    s.add_argument("--reps-achieved", type=int, required=True, help="reps completed at that weight")
    s.add_argument("--increment", type=float, required=True,
                   help="load jump once reps-high is reached (~2.5-5lb upper / ~5-10lb lower)")
    s.add_argument("--previous-reps-achieved", type=int,
                   help="reps completed at this weight the PRIOR session (optional) - only used "
                        "to flag a two-sessions-running stall at the bottom of the range")
    s.add_argument("--unit", default="lb", choices=["lb", "kg"])
    s.set_defaults(func=cmd_progression)

    s = sub.add_parser("macros", help="protein/calorie/fat/carb targets", parents=[json_parent])
    s.add_argument("--bodyweight", type=float, required=True)
    s.add_argument("--goal", default="maintain", choices=list(GOALS))
    s.add_argument("--unit", default="lb", choices=["lb", "kg"])
    s.add_argument("--tdee", type=float, help="maintenance kcal if known (else estimated)")
    s.add_argument("--activity", default="moderate", choices=list(ACTIVITY_LEVELS))
    s.add_argument("--age", type=int,
                   help="age in years - combine with --height and --sex (all three) for a "
                        "Mifflin-St Jeor TDEE estimate instead of the quick bodyweight-only one")
    s.add_argument("--height", type=float, help="height - combine with --age and --sex")
    s.add_argument("--height-unit", default="in", choices=["in", "cm"])
    s.add_argument("--sex", choices=["male", "female"], help="combine with --age and --height")
    s.add_argument("--bodyfat", type=float,
                   help="body-fat %% (e.g. 15 for 15%%) - if given, TDEE routes through Cunningham "
                        "(lean-mass-based) automatically instead; takes priority over --age/--height/--sex")
    s.set_defaults(func=cmd_macros)

    s = sub.add_parser("cunningham", help="Cunningham (1980) lean-mass-based RMR/TDEE",
                        parents=[json_parent])
    s.add_argument("--lean-mass", type=float, help="fat-free mass (give this, OR --bodyweight + --bodyfat)")
    s.add_argument("--bodyweight", type=float, help="total bodyweight - combine with --bodyfat "
                                                      "instead of --lean-mass")
    s.add_argument("--bodyfat", type=float,
                   help="body-fat %% (e.g. 15 for 15%%, the same number `navybf`/`ffmi` compute) - "
                        "combine with --bodyweight instead of --lean-mass")
    s.add_argument("--unit", default="lb", choices=["lb", "kg"])
    s.add_argument("--activity", default="moderate", choices=list(ACTIVITY_LEVELS))
    s.set_defaults(func=cmd_cunningham)

    s = sub.add_parser("bulkcut", help="weekly bulk/cut rate target by trainee tier",
                        parents=[json_parent])
    s.add_argument("--bodyweight", type=float, required=True)
    s.add_argument("--goal", required=True, choices=["gain", "cut"])
    s.add_argument("--tier", default="intermediate", choices=list(TIERS))
    s.add_argument("--unit", default="lb", choices=["lb", "kg"])
    s.set_defaults(func=cmd_bulkcut)

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

    s = sub.add_parser("warmup", help="warm-up ramp to a working weight", parents=[json_parent])
    s.add_argument("--weight", type=float, required=True)
    s.add_argument("--bar", type=float, help="bar weight (default 20kg / 45lb)")
    s.add_argument("--unit", default="lb", choices=["lb", "kg"])
    s.set_defaults(func=cmd_warmup)

    s = sub.add_parser("ffmi", help="fat-free mass index (Kouri 1995)", parents=[json_parent])
    s.add_argument("--weight", type=float, required=True)
    s.add_argument("--unit", default="lb", choices=["lb", "kg"])
    s.add_argument("--height", type=float, required=True)
    s.add_argument("--height-unit", default="in", choices=["in", "cm"])
    s.add_argument("--bodyfat", type=float, required=True, help="body-fat %% (e.g. 15 for 15%%)")
    s.set_defaults(func=cmd_ffmi)

    s = sub.add_parser("navybf", help="Navy tape-measure body-fat %% (Hodgdon & Beckett 1984)",
                        parents=[json_parent])
    s.add_argument("--sex", required=True, choices=["male", "female"])
    s.add_argument("--height", type=float, required=True)
    s.add_argument("--height-unit", default="in", choices=["in", "cm"])
    s.add_argument("--neck", type=float, required=True, help="neck circumference, inches")
    s.add_argument("--waist", type=float, required=True, help="waist circumference at the navel, inches")
    s.add_argument("--hip", type=float, help="hip circumference, inches (required for sex=female)")
    s.set_defaults(func=cmd_navybf)

    s = sub.add_parser("sessionload", help="session load / weekly load / monotony / strain (Foster 2001)",
                        parents=[json_parent])
    s.add_argument("--load", type=float, nargs="+", required=True, metavar="RPE_TIMES_MIN",
                   help="one load value per logged session (RPE * duration_minutes); "
                        "log same-day multiple sessions as separate values, not pre-summed")
    s.set_defaults(func=cmd_sessionload)

    s = sub.add_parser("symmetry", help="lift-ratio symmetry: squat/bench/deadlift vs. expected ratios",
                        parents=[json_parent])
    s.add_argument("--squat", type=float, required=True)
    s.add_argument("--bench", type=float, required=True)
    s.add_argument("--deadlift", type=float, required=True)
    s.add_argument("--ohp", type=float, help="overhead press best 1RM (optional)")
    s.add_argument("--bodyweight", type=float, help="carried through on the report for context only")
    s.add_argument("--sex", required=True, choices=["male", "female"])
    s.add_argument("--unit", default="lb", choices=["lb", "kg"])
    s.set_defaults(func=cmd_symmetry)

    s = sub.add_parser("tm", help="training max: pct of a 1RM, rounded down (Wendler)",
                        parents=[json_parent])
    s.add_argument("--onerm", type=float, help="a known/tested 1RM (give this, OR --amrap-weight + --amrap-reps)")
    s.add_argument("--amrap-weight", type=float,
                   help="weight from an AMRAP top set (e.g. this cycle's 5/3/1 week-3 set) - "
                        "combine with --amrap-reps instead of --onerm to derive an e1RM first")
    s.add_argument("--amrap-reps", type=int, help="reps completed on that AMRAP set")
    s.add_argument("--pct", type=float, default=0.90, help="training-max %% of 1RM, 0.80-1.00 (default 0.90)")
    s.add_argument("--increment", type=float, help="rounding increment (default 5lb / 2.5kg)")
    s.add_argument("--unit", default="lb", choices=["lb", "kg"])
    s.set_defaults(func=cmd_tm)

    s = sub.add_parser("program531", help="classic Wendler 5/3/1: one week's full set list",
                        parents=[json_parent])
    s.add_argument("--tm", type=float, required=True, help="training max (see `tm`)")
    s.add_argument("--week", type=int, required=True, choices=[1, 2, 3, 4],
                   help="1-3 = working weeks, 4 = deload")
    s.add_argument("--increment", type=float, default=5.0, help="rounding increment (default 5; use 2.5 for kg)")
    s.add_argument("--unit", default="lb", choices=["lb", "kg"])
    s.set_defaults(func=cmd_program531)

    s = sub.add_parser("gzclp", help="GZCLP next-session prescription from current state (Lefever)",
                        parents=[json_parent])
    s.add_argument("--tier", required=True, choices=["t1", "t2", "t3"])
    s.add_argument("--stage", default="", help=f"current stage: {T1_STAGES} for t1, {T2_STAGES} for t2")
    s.add_argument("--weight", type=float, required=True, help="weight used for the session just performed")
    s.add_argument("--made", action="store_true", help="pass if the session's target was hit")
    s.add_argument("--missed", dest="made", action="store_false", help="pass if the session was missed")
    s.set_defaults(made=True)
    s.add_argument("--lift-type", default="upper", choices=["upper", "lower"],
                   help="selects which increment table applies")
    s.add_argument("--unit", default="lb", choices=["lb", "kg"])
    s.add_argument("--amrap-reps", type=int, help="t3 only: total reps on the AMRAP set")
    s.set_defaults(func=cmd_gzclp)

    s = sub.add_parser("nsuns", help="nSuns LP (4-day) T1 set list for one lift day",
                        parents=[json_parent])
    s.add_argument("--day", required=True, choices=sorted(NSUNS_4DAY_SCHEME))
    s.add_argument("--tm", type=float, required=True, help="training max (see `tm`)")
    s.add_argument("--increment", type=float, default=5.0, help="rounding increment (default 5; use 2.5 for kg)")
    s.add_argument("--unit", default="lb", choices=["lb", "kg"])
    s.set_defaults(func=cmd_nsuns)

    s = sub.add_parser("standards", help="relative-strength scoring: Wilks/DOTS/IPF GL",
                        parents=[json_parent])
    s.add_argument("--total", type=float, required=True, help="competition total (or single-lift result)")
    s.add_argument("--bodyweight", type=float, required=True)
    s.add_argument("--sex", required=True, choices=["male", "female"])
    s.add_argument("--unit", default="lb", choices=["lb", "kg"])
    s.add_argument("--tier", action="store_true",
                   help="also classify a bodyweight-indexed strength tier (beginner-elite) from "
                        "this same total/bodyweight/sex - see the `tier` subcommand for the full "
                        "breakdown. Omit this flag and output is unchanged from before it existed.")
    s.set_defaults(func=cmd_standards)

    s = sub.add_parser("mcculloch", help="McCulloch age-adjusted total for masters lifters (WRPF)",
                        parents=[json_parent])
    s.add_argument("--total", type=float, required=True, help="competition total (or single-lift result)")
    s.add_argument("--age", type=int, required=True, help="lifter's age in whole years, 40-90")
    s.add_argument("--unit", default="lb", choices=["lb", "kg"])
    s.set_defaults(func=cmd_mcculloch)

    s = sub.add_parser("tier", help="bodyweight-indexed strength tier (beginner->elite) for a total",
                        parents=[json_parent])
    s.add_argument("--total", type=float, help="competition total (give this, OR --squat/--bench/--deadlift)")
    s.add_argument("--squat", type=float, help="squat 1RM - combine with --bench/--deadlift instead of --total")
    s.add_argument("--bench", type=float, help="bench 1RM - combine with --squat/--deadlift instead of --total")
    s.add_argument("--deadlift", type=float,
                   help="deadlift 1RM - combine with --squat/--bench instead of --total")
    s.add_argument("--bodyweight", type=float, required=True)
    s.add_argument("--sex", required=True, choices=["male", "female"])
    s.add_argument("--unit", default="lb", choices=["lb", "kg"])
    s.set_defaults(func=cmd_tier)

    s = sub.add_parser("glossary", help="plain-English + technical definitions for every term liftmath uses",
                        parents=[json_parent])
    s.add_argument("--term", help="look up one term (e.g. 'RIR', 'IPF GL') - omit for the full glossary")
    s.set_defaults(func=cmd_glossary)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
