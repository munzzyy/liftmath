"""Command-line interface for liftmath.

Subcommands:
    1rm         Estimate 1RM from a weight x reps set (multi-formula consensus + range)
    plates      Plate-loading math for a target barbell weight (add --inventory for a
                finite per-side plate count instead of an unlimited supply)
    standards   Relative-strength scoring: Wilks (original + 2020), DOTS, IPF GL points
    convert     Convert a weight between lb and kg (exact avoirdupois pound)

All loads are unit-agnostic (kg or lb); pass --unit. Pass --json (before or after
the subcommand) for machine-readable JSON instead of the formatted text, e.g.
`liftmath 1rm --weight 225 --reps 5 --json`.
"""

from __future__ import annotations

import argparse
import sys

from liftmath import __version__
from liftmath._serialize import to_json
from liftmath.convert import KG_PER_LB, convert_weight
from liftmath.convert import lbs_to_kg as _lbs_to_kg
from liftmath.onerm import estimate_one_rm
from liftmath.plates import PRESETS, _parse_inventory_spec, load_plates, load_plates_from_inventory
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

    s = sub.add_parser("convert", help="convert a weight between lb and kg", parents=[json_parent])
    s.add_argument("--weight", type=float, required=True)
    s.add_argument("--unit", default="lb", choices=["lb", "kg"], help="unit the --weight is already in")
    s.set_defaults(func=cmd_convert)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
