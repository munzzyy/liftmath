"""Relative-strength scoring: Wilks (original + 2020), DOTS, IPF GL.

All of these take a competition total (or single-lift result), a bodyweight,
and a sex, and return a score that lets you compare lifters across bodyweight
classes. They disagree slightly at the extremes because each was fit to a
different sample and polynomial/exponential shape, so all are reported side by
side rather than picked as a single "correct" answer.

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
        Bodyweight is clamped to the domain the polynomial was fit over
        (men 40-201.9kg, women 26.51-154.53kg) before evaluating, same as
        wilks.rs's own clamp - past that range the denominator crosses zero
        and the score flips sign instead of leveling off at the boundary.
    Wilks, R. (revised 2020). The Wilks-2020 formula. Same polynomial form,
        but a **600** divisor (not 500) and a different a-f table from the
        original. Cross-checked against an OpenPowerlifting-derived
        TypeScript port (wilks.ts, storing this as COEFFICIENTS_2020 distinct
        from COEFFICIENTS_ORIGINAL) and matches Wikipedia's "2020
        Coefficients" table. (An early web-search snippet claimed Wilks-2020
        reuses the original's 500 divisor with new coefficients - that's
        wrong; resolved by reading two independent source-code
        implementations directly.) Same clamp-before-evaluate treatment as
        the original, bounded to wilks2020.rs's fitted domain (men
        40-200.95kg, women 40-150.95kg).
    DOTS (2019). Introduced by Tim Konertz / German Powerlifting Federation
        as a bodyweight-independent alternative to Wilks, adopted by USAPL/
        IPF in 2019-2020 as an interim/parallel standard. Coefficients:
        total * 500 / (a*x^4 + b*x^3 + c*x^2 + d*x + e), x = bodyweight in kg.
        Cross-checked against an OpenPowerlifting-derived TypeScript port
        (dots.ts) and an independent web source giving matching men's
        constants. Bodyweight is clamped to dots.rs's fitted domain (men
        40-210kg, women 40-150kg) before evaluating, for the same reason as
        Wilks above.
    International Powerlifting Federation (May 2020). The IPF GL Coefficients
        for Relative Scoring. IPF GL Coefficient = 100 / (A - B*e^(-C*Bwt));
        IPF GL Points = Coefficient * Total. Classic (raw) powerlifting
        coefficients only; equipped/bench-only coefficients are out of scope
        for this module. Fetched directly from the official IPF PDF
        (powerlifting.sport/fileadmin/ipf/data/ipf-formula/
        IPF_GL_Coefficients-2020.pdf). Coefficients are stated by the IPF as
        in effect May 1 2020 - Dec 31 2023 and are refreshed on a roughly
        4-year cycle; treat them as "current best known," not permanent.
        CURRENCY NOTE: coefficients below were re-verified against that same
        official PDF in mid-2026 - it's still the only coefficients document
        linked from the IPF's own formula page, with no newer table published
        despite being past its stated Dec 31 2023 window. IPF GL points
        computed here may drift from the IPF's own current live scoring once
        it next refreshes the table; re-check powerlifting.sport's own
        coefficients page periodically (roughly every 4 years, per the IPF's
        own cadence) and update `_IPF_GL` if a newer table is published.
        DOES need a floor clamp, same failure mode as Wilks/DOTS: the
        official PDF's own formula statement gives the coefficient equation a
        stated domain of "Bwt >= 40kg for men and Bwt >= 35kg for women," and
        that floor is load-bearing, not stylistic - the women's classic table
        has B > A (1045.59282 > 610.32796), so the denominator A - B*e^(-C*Bwt)
        is NEGATIVE at Bwt=0 and only crosses back to positive around
        17.66kg, well inside the region the IPF's own domain statement
        already excludes. Below that crossing point the coefficient (and so
        the points) flips sign; near it, the coefficient blows up toward
        +/-infinity. This is unreachable for any real adult female lifter
        (women's weight classes start at 44kg) but the function itself had no
        floor, so a bad upstream unit conversion or typo'd bodyweight could
        silently return a wildly wrong score instead of an error. Fixed by
        clamping to the IPF's own stated floor (40kg men / 35kg women) before
        evaluating, same treatment as `_clamp_bodyweight` gives Wilks/DOTS -
        comfortably inside the region where the men's table (A > B, never
        crosses zero) and the women's table (crosses at ~17.66kg) both stay
        positive. No upper clamp: the exponential's denominator approaches A
        (positive, since A > 0 in both tables) as bodyweight grows, so it
        never crosses zero again past the floor.
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

# Bodyweight domain the polynomial above was fit over, kg (min, max) per sex.
# Outside this range the denominator crosses zero and the score flips sign
# instead of leveling off, so it gets clamped in before evaluating - same
# approach as wilks.rs. See module docstring for the citation.
_WILKS_ORIGINAL_BW_RANGE = {"male": (40.0, 201.9), "female": (26.51, 154.53)}

# Wilks 2020 revision. a,b,c,d,e,f per sex; coefficient = 600 / (a+bx+cx^2+cx^3+ex^4+fx^5)
_WILKS_2020 = {
    "male": (47.46178854, 8.472061379, 0.07369410346, -0.001395833811,
             7.07665973070743e-06, -1.20804336482315e-08),
    "female": (-125.4255398, 13.71219419, -0.03307250631, -0.001050400051,
               9.38773881462799e-06, -2.3334613884954e-08),
}

# Same idea as _WILKS_ORIGINAL_BW_RANGE, per wilks2020.rs's clamp.
_WILKS_2020_BW_RANGE = {"male": (40.0, 200.95), "female": (40.0, 150.95)}

# DOTS. a,b,c,d,e per sex; score = total * 500 / (a*x^4 + b*x^3 + c*x^2 + d*x + e)
_DOTS = {
    "male": (-0.0000010930, 0.0007391293, -0.1918759221, 24.0900756, -307.75076),
    "female": (-0.0000010706, 0.0005158568, -0.1126655495, 13.6175032, -57.96288),
}

# Same idea again, per dots.rs's clamp.
_DOTS_BW_RANGE = {"male": (40.0, 210.0), "female": (40.0, 150.0)}

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

# The IPF's own formula statement gives this equation a domain floor of
# Bwt >= 40kg (men) / Bwt >= 35kg (women), and it's load-bearing here: the
# women's table has B > A, so the denominator is negative below ~17.66kg and
# only turns positive again above that. This floor sits safely above that
# crossing for both sexes. No upper bound needed - see module docstring.
_IPF_GL_BW_FLOOR = {"male": 40.0, "female": 35.0}

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


def _validate(total_kg: float, bodyweight_kg: float, sex: str) -> None:
    if sex not in _SEXES:
        raise ValueError(f"sex must be one of {_SEXES}, got {sex!r}")
    if not math.isfinite(total_kg) or total_kg <= 0:
        raise ValueError("total_kg must be a finite number > 0")
    if not math.isfinite(bodyweight_kg) or bodyweight_kg <= 0:
        raise ValueError("bodyweight_kg must be a finite number > 0")


def _clamp_bodyweight(bodyweight_kg: float, bw_range: dict, sex: str) -> float:
    """Clamp bodyweight into the domain a formula's polynomial was fit over.

    A lifter outside the fitted range still gets a score - just the one at
    the nearest domain edge, instead of a coefficient computed from a
    denominator that has extrapolated past its zero crossing.
    """
    low, high = bw_range[sex]
    return min(max(bodyweight_kg, low), high)


def wilks_original_score(total_kg: float, bodyweight_kg: float, sex: str) -> float:
    """Original Wilks (1994) score for a total at a given bodyweight.

    Superseded by `wilks_score` (the 2020 revision) as the IPF's current
    standard, but still widely quoted/compared historically, so it's offered
    alongside rather than dropped.
    """
    _validate(total_kg, bodyweight_kg, sex)
    a, b, c, d, e, f = _WILKS_ORIGINAL[sex]
    x = _clamp_bodyweight(bodyweight_kg, _WILKS_ORIGINAL_BW_RANGE, sex)
    denom = a + b * x + c * x**2 + d * x**3 + e * x**4 + f * x**5
    coefficient = 500.0 / denom
    return total_kg * coefficient


def wilks_score(total_kg: float, bodyweight_kg: float, sex: str) -> float:
    """Wilks (2020 revision) score for a total at a given bodyweight."""
    _validate(total_kg, bodyweight_kg, sex)
    a, b, c, d, e, f = _WILKS_2020[sex]
    x = _clamp_bodyweight(bodyweight_kg, _WILKS_2020_BW_RANGE, sex)
    denom = a + b * x + c * x**2 + d * x**3 + e * x**4 + f * x**5
    coefficient = 600.0 / denom
    return total_kg * coefficient


def dots_score(total_kg: float, bodyweight_kg: float, sex: str) -> float:
    """DOTS score for a total at a given bodyweight."""
    _validate(total_kg, bodyweight_kg, sex)
    a, b, c, d, e = _DOTS[sex]
    x = _clamp_bodyweight(bodyweight_kg, _DOTS_BW_RANGE, sex)
    denom = a * x**4 + b * x**3 + c * x**2 + d * x + e
    return total_kg * 500.0 / denom


def ipf_gl_points(total_kg: float, bodyweight_kg: float, sex: str) -> float:
    """IPF GL points for a total at a given bodyweight (classic/raw powerlifting).

    Matches the IPF's own published rounding: the equalization coefficient is
    rounded to 6 decimal places before multiplying by the total, same as the
    procedure in the IPF's official coefficients document. Bodyweight is
    floored at the IPF's own stated domain (40kg men / 35kg women) before
    evaluating - below that, the women's coefficient table inverts sign
    instead of leveling off; see the module docstring.
    """
    _validate(total_kg, bodyweight_kg, sex)
    a, b, c = _IPF_GL[sex]
    x = max(bodyweight_kg, _IPF_GL_BW_FLOOR[sex])
    coefficient = round(100.0 / (a - b * math.exp(-c * x)), 6)
    return coefficient * total_kg


def score(total_kg: float, bodyweight_kg: float, sex: str) -> StrengthScore:
    """Compute Wilks (original + 2020), DOTS, and IPF GL side by side.

    Args:
        total_kg: competition total (or single-lift result), in kilograms.
        bodyweight_kg: bodyweight, in kilograms.
        sex: "male" or "female". IPF GL uses classic (raw) powerlifting
            coefficients; there's no equipped/bench-only variant here.

    Raises:
        ValueError: if sex isn't "male"/"female", or total_kg/bodyweight_kg
            isn't a finite number > 0.
    """
    _validate(total_kg, bodyweight_kg, sex)
    return StrengthScore(
        total=total_kg,
        bodyweight_kg=bodyweight_kg,
        sex=sex,
        wilks=wilks_score(total_kg, bodyweight_kg, sex),
        wilks_original=wilks_original_score(total_kg, bodyweight_kg, sex),
        dots=dots_score(total_kg, bodyweight_kg, sex),
        ipf_gl=ipf_gl_points(total_kg, bodyweight_kg, sex),
    )
