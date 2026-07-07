"""Body composition: FFMI (Kouri 1995) and Navy tape-measure body-fat % (Hodgdon & Beckett 1984).

Both are stdlib-only (`math.log10`), field-expedient estimates - good for
tracking a trend over time, not a clinical body-composition reading.

Sources:
    Kouri, E.M., Pope, H.G., Katz, D.L., Oliva, P. (1995). Fat-free mass
        index in users and nonusers of anabolic-androgenic steroids.
        Clinical Journal of Sport Medicine, 5(4), 223-228.
        FFMI = lean_mass_kg / height_m^2. Normalized to a 1.80m reference
        height: normalized_FFMI = FFMI + 6.3 * (1.80 - height_m).
        Study population: 157 male athletes (74 non-users, 83 steroid
        users). Non-users' normalized FFMI topped out at 25.0 in this
        sample; historical (1939-1959) "Mr. America" winners averaged 25.4.
        Evidence grade: established as a descriptive reference from a real
        measured sample with a clear reported ceiling, but emerging/soft as
        a hard "natural limit" claim - n=157, all-male, one era/population,
        no cross-cultural or test-retest replication reported in the source,
        and genetics/frame/measurement variance mean individuals can
        legitimately sit above or below 25 without doping. Treat the 25.0
        line as "a reference ceiling from one 1995 sample," not a law.
    Hodgdon, J.A., Beckett, M.B. (1984). Prediction of percent body fat for
        U.S. Navy men and women from body circumferences and height. Naval
        Health Research Center, Report No. 84-11.
        Men:   BF% = 86.010*log10(waist-neck) - 70.041*log10(height) + 36.76
        Women: BF% = 163.205*log10(waist+hip-neck) - 97.684*log10(height) - 78.387
        All circumferences and height in inches. Waist at the navel, neck
        below the larynx, hip at the widest point (women only).
        Evidence grade: established as a field-expedient estimate -
        validated against hydrostatic weighing at r~=0.90 in the source
        study, but with a reported standard error of ~3-4 percentage points
        vs. underwater weighing, so the output should be read as a band
        ("~18% +/- 3-4"), not a precise figure.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

_FFMI_REFERENCE_HEIGHT_M = 1.80
_FFMI_NATURAL_CEILING = 25.0  # Kouri 1995 non-user sample ceiling, normalized FFMI

_SEXES = ("male", "female")


@dataclass
class FfmiResult:
    """Fat-free mass index for one height/weight/bodyfat combination."""

    weight_kg: float
    height_m: float
    bodyfat_pct: float
    lean_mass_kg: float
    ffmi: float
    normalized_ffmi: float

    @property
    def above_natural_reference_ceiling(self) -> bool:
        """True if normalized FFMI exceeds Kouri 1995's 25.0 non-user sample ceiling.

        This is a reference point from one 1995 sample of 157 male athletes,
        not a hard physiological law - individuals can legitimately sit above
        or below it without doping. See module docstring.
        """
        return self.normalized_ffmi > _FFMI_NATURAL_CEILING


def ffmi(weight_kg: float, height_m: float, bodyfat_pct: float) -> FfmiResult:
    """Compute FFMI and height-normalized FFMI (Kouri et al., 1995).

    Args:
        weight_kg: total bodyweight, kilograms.
        height_m: height, meters.
        bodyfat_pct: body-fat percentage as a whole number (e.g. 15 for 15%).

    Raises:
        ValueError: if weight_kg or height_m aren't positive, or bodyfat_pct
            isn't in [0, 100).
    """
    if weight_kg <= 0:
        raise ValueError("weight_kg must be > 0")
    if height_m <= 0:
        raise ValueError("height_m must be > 0")
    if not 0 <= bodyfat_pct < 100:
        raise ValueError("bodyfat_pct must be in [0, 100)")

    lean_mass_kg = weight_kg * (1 - bodyfat_pct / 100.0)
    raw_ffmi = lean_mass_kg / height_m**2
    normalized = raw_ffmi + 6.3 * (_FFMI_REFERENCE_HEIGHT_M - height_m)

    return FfmiResult(
        weight_kg=weight_kg,
        height_m=height_m,
        bodyfat_pct=bodyfat_pct,
        lean_mass_kg=lean_mass_kg,
        ffmi=raw_ffmi,
        normalized_ffmi=normalized,
    )


@dataclass
class NavyBodyFatResult:
    """Navy tape-measure body-fat % estimate (Hodgdon & Beckett 1984)."""

    sex: str
    height_in: float
    neck_in: float
    waist_in: float
    hip_in: float | None
    bodyfat_pct: float

    @property
    def error_band_pct(self) -> float:
        """Reported standard error vs. hydrostatic weighing, +/- percentage points."""
        return 3.5


def navy_body_fat(
    sex: str,
    height_in: float,
    neck_in: float,
    waist_in: float,
    hip_in: float | None = None,
) -> NavyBodyFatResult:
    """Estimate body-fat % from circumference measurements (Hodgdon & Beckett, 1984).

    Args:
        sex: "male" or "female".
        height_in: height, inches.
        neck_in: neck circumference below the larynx, inches.
        waist_in: waist circumference at the navel, inches.
        hip_in: hip circumference at the widest point, inches. Required for
            "female", ignored for "male".

    Raises:
        ValueError: if sex isn't "male"/"female", any measurement isn't
            positive, hip_in is missing for "female", or the log10 argument
            would be non-positive (e.g. waist <= neck for men).
    """
    if sex not in _SEXES:
        raise ValueError(f"sex must be one of {_SEXES}, got {sex!r}")
    for name, value in (("height_in", height_in), ("neck_in", neck_in), ("waist_in", waist_in)):
        if value <= 0:
            raise ValueError(f"{name} must be > 0")

    if sex == "male":
        span = waist_in - neck_in
        if span <= 0:
            raise ValueError("waist_in must be greater than neck_in")
        bf = 86.010 * math.log10(span) - 70.041 * math.log10(height_in) + 36.76
    else:
        if hip_in is None:
            raise ValueError("hip_in is required for sex='female'")
        if hip_in <= 0:
            raise ValueError("hip_in must be > 0")
        span = waist_in + hip_in - neck_in
        if span <= 0:
            raise ValueError("waist_in + hip_in must be greater than neck_in")
        bf = 163.205 * math.log10(span) - 97.684 * math.log10(height_in) - 78.387

    return NavyBodyFatResult(
        sex=sex,
        height_in=height_in,
        neck_in=neck_in,
        waist_in=waist_in,
        hip_in=hip_in,
        bodyfat_pct=bf,
    )
