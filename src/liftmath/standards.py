"""Relative-strength scoring: Wilks (2020), DOTS, and IPF GL points.

All three take a competition total (or single-lift result), a bodyweight, and
a sex, and return a score that lets you compare lifters across bodyweight
classes. They disagree slightly at the extremes because each was fit to a
different sample and polynomial/exponential shape, so all three are reported
side by side rather than picked as a single "correct" answer.

Sources:
    Wilks, R. (1994, revised 2020). The Wilks Formula. International
        Powerlifting Federation. Coefficients: 600 / (a + bx + cx^2 + cx^3
        + ex^4 + fx^5), x = bodyweight in kg. This module uses the 2020
        revision (numerator 600), which is the version in current use.
    DOTS (2019). Introduced by Tim Konertz / German Powerlifting Federation
        as a bodyweight-independent alternative to Wilks. Coefficients:
        total * 500 / (a*x^4 + b*x^3 + c*x^2 + d*x + e), x = bodyweight in kg.
    International Powerlifting Federation (May 2020). The IPF GL Coefficients
        for Relative Scoring. IPF GL Coefficient = 100 / (A - B*e^(-C*Bwt));
        IPF GL Points = Coefficient * Total. Classic (raw) powerlifting
        coefficients only; equipped/bench-only coefficients are out of scope
        for this module.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

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
_IPF_GL = {
    "male": (1199.72839, 1025.18162, 0.00921),
    "female": (610.32796, 1045.59282, 0.03048),
}

_SEXES = ("male", "female")


@dataclass
class StrengthScore:
    """Relative-strength scores for one total (or lift) at one bodyweight."""

    total: float
    bodyweight_kg: float
    sex: str
    wilks: float
    dots: float
    ipf_gl: float


def _validate(bodyweight_kg: float, sex: str) -> None:
    if sex not in _SEXES:
        raise ValueError(f"sex must be one of {_SEXES}, got {sex!r}")
    if bodyweight_kg <= 0:
        raise ValueError("bodyweight_kg must be > 0")


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
    """Compute Wilks, DOTS, and IPF GL side by side for one total + bodyweight.

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
        dots=dots_score(total_kg, bodyweight_kg, sex),
        ipf_gl=ipf_gl_points(total_kg, bodyweight_kg, sex),
    )
