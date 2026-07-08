"""Relative-strength scoring: Wilks (original + 2020), DOTS, IPF GL, McCulloch.

All of these take a competition total (or single-lift result), a bodyweight,
and a sex, and return a score that lets you compare lifters across bodyweight
classes (McCulloch instead adjusts for age). They disagree slightly at the
extremes because each was fit to a different sample and polynomial/exponential
shape, so all are reported side by side rather than picked as a single
"correct" answer.

Evidence grade: established as *competition scoring conventions* - these are
the actual formulas real federations use, fit by regression to real
competition samples (the IPF's own methodology document describes fitting to
"Golden Standard Samples," >=16% of world records, IPF/EPF competitions from
2011 onward). They are not "evidence" in the causal/RCT sense; they're
measurement conventions, same category as a ruler, not a treatment effect.

Sources:
    Wilks, R. (1994). The original Wilks formula. Coefficient = 500 /
        (a + bx + cx^2 + dx^3 + ex^4 + fx^5), x = bodyweight in kg. Score =
        coefficient * total. Coefficients cross-checked against
        OpenPowerlifting's `coefficients` Rust crate (wilks.rs, MIT-licensed,
        gitlab.com/openpowerlifting/opl-data), which ships this exact table
        with its own pinned unit tests, and matches Wikipedia's "Wilks
        coefficient" page and europowerlifting.org's formula sheet.
    Wilks, R. (revised 2020). The Wilks-2020 formula. Same polynomial form,
        but a **600** divisor (not 500) and a different a-f table from the
        original. Cross-checked against an OpenPowerlifting-derived
        TypeScript port (wilks.ts, storing this as COEFFICIENTS_2020 distinct
        from COEFFICIENTS_ORIGINAL) and matches Wikipedia's "2020
        Coefficients" table. (An early web-search snippet claimed Wilks-2020
        reuses the original's 500 divisor with new coefficients - that's
        wrong; resolved by reading two independent source-code
        implementations directly.)
    DOTS (2019). Introduced by Tim Konertz / German Powerlifting Federation
        as a bodyweight-independent alternative to Wilks, adopted by USAPL/
        IPF in 2019-2020 as an interim/parallel standard. Coefficients:
        total * 500 / (a*x^4 + b*x^3 + c*x^2 + d*x + e), x = bodyweight in kg.
        Cross-checked against an OpenPowerlifting-derived TypeScript port
        (dots.ts) and an independent web source giving matching men's
        constants.
    International Powerlifting Federation (May 2020). The IPF GL Coefficients
        for Relative Scoring. IPF GL Coefficient = 100 / (A - B*e^(-C*Bwt));
        IPF GL Points = Coefficient * Total. Classic (raw) powerlifting
        coefficients only; equipped/bench-only coefficients are out of scope
        for this module. Fetched directly from the official IPF PDF
        (powerlifting.sport/fileadmin/ipf/data/ipf-formula/
        IPF_GL_Coefficients-2020.pdf). Coefficients are stated by the IPF as
        in effect May 1 2020 - Dec 31 2023 and are refreshed on a roughly
        4-year cycle; treat them as "current best known," not permanent.
        CURRENCY NOTE: coefficients below were verified current as of the
        liftmath 1.3.0 release (mid-2026) - that's already past the IPF's
        own stated Dec 31 2023 window for this table, with no newer official
        publication found as of that check. IPF GL points computed here may
        drift from the IPF's own current live scoring once it next refreshes
        the table; re-check powerlifting.sport's own coefficients page
        periodically (roughly every 4 years, per the IPF's own cadence) and
        update `_IPF_GL` if a newer table is published.
    World Raw Powerlifting Federation (2022 edition). McCulloch Coefficients
        for Masters - an age-based adjustment (ages 40-90) applied to a total,
        for comparing masters lifters against open-age standards. Table
        transcribed from the WRPF's own published PDF. The per-age curve's
        derivation methodology isn't published in that document (unlike IPF
        GL, which publishes its regression method), so treat the *shape* of
        the age curve as less independently verifiable than IPF GL, even
        though the numbers themselves come from the federation's own table.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# Wilks, original (1994). a,b,c,d,e,f per sex; coefficient = 500 / (a+bx+cx^2+dx^3+ex^4+fx^5)
_WILKS_ORIGINAL = {
    "male": (-216.0475144, 16.2606339, -0.002388645, -0.00113732,
             7.01863e-06, -1.291e-08),
    "female": (594.31747775582, -27.23842536447, 0.82112226871, -0.00930733913,
               4.731582e-05, -9.054e-08),
}

# Wilks 2020 revision. a,b,c,d,e,f per sex; coefficient = 600 / (a+bx+cx^2+cx^3+ex^4+fx^5)
_WILKS_2020 = {
    "male": (47.46178854, 8.472061379, 0.07369410346, -0.001395833811,
             7.07665973070743e-06, -1.20804336482315e-08),
    "female": (-125.4255398, 13.71219419, -0.03307250631, -0.001050400051,
               9.38773881462799e-06, -2.3334613884954e-08),
}

# DOTS. a,b,c,d,e per sex; score = total * 500 / (a*x^4 + b*x^3 + c*x^2 + d*x + e)
_DOTS = {
    "male": (-0.0000010930, 0.0007391293, -0.1918759221, 24.0900756, -307.75076),
    "female": (-0.0000010706, 0.0005158568, -0.1126655495, 13.6175032, -57.96288),
}

# IPF GL, classic (raw) powerlifting only. A,B,C per sex.
# Coefficient = 100 / (A - B*e^(-C*Bwt)); points = coefficient * total.
# CURRENCY: the IPF states this table in effect May 2020 - Dec 2023 and
# refreshes it roughly every 4 years; verified current as of liftmath 1.3.0
# (mid-2026, already past that stated window with no newer table found) -
# re-check powerlifting.sport's published coefficients periodically and
# update this table if the IPF has issued a newer one. See module docstring.
_IPF_GL = {
    "male": (1199.72839, 1025.18162, 0.00921),
    "female": (610.32796, 1045.59282, 0.03048),
}

# McCulloch age coefficients (WRPF, 2022 edition), age -> multiplier applied to total.
# Identity at 40 (no masters adjustment), monotonically increasing, plateaus at 2.060
# for ages 79-90 (WRPF publishes no further increase past 79).
_MCCULLOCH: dict[int, float] = {
    40: 1.000, 41: 1.008, 42: 1.016, 43: 1.024, 44: 1.032, 45: 1.042,
    46: 1.052, 47: 1.062, 48: 1.072, 49: 1.082, 50: 1.150, 51: 1.163,
    52: 1.176, 53: 1.189, 54: 1.202, 55: 1.215, 56: 1.228, 57: 1.241,
    58: 1.254, 59: 1.267, 60: 1.280, 61: 1.295, 62: 1.310, 63: 1.325,
    64: 1.340, 65: 1.355, 66: 1.370, 67: 1.385, 68: 1.400, 69: 1.415,
    70: 1.430, 71: 1.460, 72: 1.490, 73: 1.520, 74: 1.550, 75: 1.580,
    76: 1.610, 77: 1.640, 78: 1.670, 79: 2.060, 80: 2.060, 81: 2.060,
    82: 2.060, 83: 2.060, 84: 2.060, 85: 2.060, 86: 2.060, 87: 2.060,
    88: 2.060, 89: 2.060, 90: 2.060,
}

_SEXES = ("male", "female")


@dataclass
class StrengthScore:
    """Relative-strength scores for one total (or lift) at one bodyweight."""

    total: float
    bodyweight_kg: float
    sex: str
    wilks: float
    wilks_original: float
    dots: float
    ipf_gl: float


def _validate(bodyweight_kg: float, sex: str) -> None:
    if sex not in _SEXES:
        raise ValueError(f"sex must be one of {_SEXES}, got {sex!r}")
    if bodyweight_kg <= 0:
        raise ValueError("bodyweight_kg must be > 0")


def wilks_original_score(total_kg: float, bodyweight_kg: float, sex: str) -> float:
    """Original Wilks (1994) score for a total at a given bodyweight.

    Superseded by `wilks_score` (the 2020 revision) as the IPF's current
    standard, but still widely quoted/compared historically, so it's offered
    alongside rather than dropped.
    """
    _validate(bodyweight_kg, sex)
    a, b, c, d, e, f = _WILKS_ORIGINAL[sex]
    x = bodyweight_kg
    denom = a + b * x + c * x**2 + d * x**3 + e * x**4 + f * x**5
    coefficient = 500.0 / denom
    return total_kg * coefficient


def wilks_score(total_kg: float, bodyweight_kg: float, sex: str) -> float:
    """Wilks (2020 revision) score for a total at a given bodyweight."""
    _validate(bodyweight_kg, sex)
    a, b, c, d, e, f = _WILKS_2020[sex]
    x = bodyweight_kg
    denom = a + b * x + c * x**2 + d * x**3 + e * x**4 + f * x**5
    coefficient = 600.0 / denom
    return total_kg * coefficient


def dots_score(total_kg: float, bodyweight_kg: float, sex: str) -> float:
    """DOTS score for a total at a given bodyweight."""
    _validate(bodyweight_kg, sex)
    a, b, c, d, e = _DOTS[sex]
    x = bodyweight_kg
    denom = a * x**4 + b * x**3 + c * x**2 + d * x + e
    return total_kg * 500.0 / denom


def ipf_gl_points(total_kg: float, bodyweight_kg: float, sex: str) -> float:
    """IPF GL points for a total at a given bodyweight (classic/raw powerlifting).

    Matches the IPF's own published rounding: the equalization coefficient is
    rounded to 6 decimal places before multiplying by the total, same as the
    procedure in the IPF's official coefficients document.
    """
    _validate(bodyweight_kg, sex)
    a, b, c = _IPF_GL[sex]
    coefficient = round(100.0 / (a - b * math.exp(-c * bodyweight_kg)), 6)
    return coefficient * total_kg


def score(total_kg: float, bodyweight_kg: float, sex: str) -> StrengthScore:
    """Compute Wilks (original + 2020), DOTS, and IPF GL side by side.

    Args:
        total_kg: competition total (or single-lift result), in kilograms.
        bodyweight_kg: bodyweight, in kilograms.
        sex: "male" or "female". IPF GL uses classic (raw) powerlifting
            coefficients; there's no equipped/bench-only variant here.

    Raises:
        ValueError: if sex isn't "male"/"female" or bodyweight_kg <= 0.
    """
    _validate(bodyweight_kg, sex)
    return StrengthScore(
        total=total_kg,
        bodyweight_kg=bodyweight_kg,
        sex=sex,
        wilks=wilks_score(total_kg, bodyweight_kg, sex),
        wilks_original=wilks_original_score(total_kg, bodyweight_kg, sex),
        dots=dots_score(total_kg, bodyweight_kg, sex),
        ipf_gl=ipf_gl_points(total_kg, bodyweight_kg, sex),
    )


_MCCULLOCH_MIN_AGE = min(_MCCULLOCH)
_MCCULLOCH_MAX_AGE = max(_MCCULLOCH)


@dataclass
class MastersScore:
    """McCulloch age-adjusted total for a masters lifter."""

    total: float
    age: int
    coefficient: float
    adjusted_total: float


def mcculloch_coefficient(age: int) -> float:
    """Look up the McCulloch age-adjustment multiplier for `age` (40-90).

    Raises:
        ValueError: if age is outside the WRPF's published 40-90 table.
    """
    if age not in _MCCULLOCH:
        raise ValueError(
            f"McCulloch coefficients only cover ages {_MCCULLOCH_MIN_AGE}-{_MCCULLOCH_MAX_AGE}, got {age}"
        )
    return _MCCULLOCH[age]


def mcculloch_score(total_kg: float, age: int) -> MastersScore:
    """Age-adjust a total for a masters lifter using the WRPF McCulloch table.

    Args:
        total_kg: competition total (or single-lift result), in kilograms.
        age: lifter's age in whole years, 40-90 (below 40 there's no masters
            adjustment - use the total as-is).

    Raises:
        ValueError: if age is outside the WRPF's published 40-90 table.
    """
    coefficient = mcculloch_coefficient(age)
    return MastersScore(
        total=total_kg,
        age=age,
        coefficient=coefficient,
        adjusted_total=total_kg * coefficient,
    )
