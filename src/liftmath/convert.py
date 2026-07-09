"""Weight-unit conversion: lb <-> kg.

Uses the exact international avoirdupois pound (1 lb = 0.45359237 kg exactly,
fixed by the 1959 international yard-and-pound agreement, not a measured or
rounded approximation) - see plates.py and standards.py, which both convert
between the two units and now import KG_PER_LB from here instead of each
keeping their own copy of the constant.

This is display/input conversion only - it has no opinion about which unit a
training number "should" be in. If you need the finer per-gram end of the
scale (competition plates go down to 0.5kg/1lb increments), pass `round_to`;
otherwise you get the full-precision float, same as the rest of the library
(see plates.py/onerm.py - rounding is a display concern, done at the CLI/web
layer, except where a formula's own published spec requires it, as in
standards.py's IPF GL coefficient).
"""

from __future__ import annotations

from dataclasses import dataclass

KG_PER_LB = 0.45359237


@dataclass
class WeightConversion:
    """One conversion: an input value/unit and the equivalent in the other unit."""

    value: float
    unit: str
    result: float
    result_unit: str


def lbs_to_kg(lbs: float, *, round_to: int | None = None) -> float:
    """Convert pounds to kilograms using the exact avoirdupois pound (1 lb = 0.45359237 kg).

    Args:
        lbs: weight in pounds. Must be >= 0.
        round_to: if given, round the result to this many decimal places
            (Python's round(), banker's rounding) before returning; omitted
            (the default) returns the full-precision float.

    Raises:
        ValueError: if lbs < 0.
    """
    if lbs < 0:
        raise ValueError("lbs must be >= 0")
    kg = lbs * KG_PER_LB
    return round(kg, round_to) if round_to is not None else kg


def kg_to_lbs(kg: float, *, round_to: int | None = None) -> float:
    """Convert kilograms to pounds using the exact avoirdupois pound (1 lb = 0.45359237 kg).

    Args:
        kg: weight in kilograms. Must be >= 0.
        round_to: if given, round the result to this many decimal places
            (Python's round(), banker's rounding) before returning; omitted
            (the default) returns the full-precision float.

    Raises:
        ValueError: if kg < 0.
    """
    if kg < 0:
        raise ValueError("kg must be >= 0")
    lbs = kg / KG_PER_LB
    return round(lbs, round_to) if round_to is not None else lbs


def convert_weight(value: float, *, unit: str, round_to: int | None = None) -> WeightConversion:
    """Convert a weight to the other unit ("lb" -> "kg" or "kg" -> "lb").

    A thin wrapper around `lbs_to_kg`/`kg_to_lbs` that returns both sides of
    the conversion as a single result, for the CLI's `convert` command and
    anywhere else a paired before/after is more useful than a bare float.

    Args:
        value: weight in `unit`. Must be >= 0.
        unit: "lb" or "kg" - the unit `value` is already in.
        round_to: passed through to the underlying conversion function.

    Raises:
        ValueError: if unit isn't "lb"/"kg", or value < 0.
    """
    if unit not in ("lb", "kg"):
        raise ValueError(f"unit must be 'lb' or 'kg', got {unit!r}")
    if unit == "lb":
        result, result_unit = lbs_to_kg(value, round_to=round_to), "kg"
    else:
        result, result_unit = kg_to_lbs(value, round_to=round_to), "lb"
    return WeightConversion(value=value, unit=unit, result=result, result_unit=result_unit)
