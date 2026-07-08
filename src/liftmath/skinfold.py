"""Jackson-Pollock skinfold body density -> Siri %BF.

Four generalized regression equations (Jackson & Pollock's own site-reduced
models, fit from their larger multi-site datasets) plus the Siri equation
that turns any of their body-density outputs into a %BF. Skinfold
measurements are in millimeters (as usually read off skinfold calipers),
age in years.

MEN'S 3-SITE SITE-COMBO AMBIGUITY - read before using: more than one
"generalized" 3-site men's equation circulates under the Jackson-Pollock
name. This module ships ONLY chest + triceps + subscapular (consistently
reproduced by a single long-standing secondary reference, topendsports.com).
Other sources describe chest + abdomen + thigh as "the" men's 3-site classic
instead, with a DIFFERENT coefficient set - Jackson & Pollock's 1978 paper is
known to publish more than one reduced-site regression from the same larger
dataset, and the paywalled original text wasn't independently checked this
session to confirm which combination(s) it actually contains. Every result
from this module names its sites explicitly (`SkinfoldResult.sites_mm`) so
it's never ambiguous which combination was used - deliberately not shipping
a second, unverified chest+abdomen+thigh coefficient set under the same
"Jackson-Pollock 3-site" name.

Sources:
    Jackson, A.S., Pollock, M.L. (1978). Generalized equations for
        predicting body density of men. British Journal of Nutrition, 40(3),
        497-504. DOI: 10.1079/BJN19780152. (Citation verified via
        bibliographic databases; original text is paywalled and wasn't read
        directly - equations below are reproduced from topendsports.com's
        long-standing, consistently-cited transcription.)
    Jackson, A.S., Pollock, M.L., Ward, A. (1980). Generalized equations for
        predicting body density of women. Medicine and Science in Sports
        and Exercise, 12(3), 175-181. DOI: 10.1249/00005768-198023000-00009.
        (Same verification status as the men's citation above.)
    Siri, W.E. (1961). Body composition from fluid spaces and density:
        analysis of methods. In Techniques for Measuring Body Composition
        (Brozek & Henschel, eds.), National Academy of Sciences, 223-244.
        %BF = 495/BD - 450. Assumes fat density 0.9 g/mL and fat-free-mass
        density 1.10 g/mL - this assumption is exactly why Siri diverges
        slightly from the Brozek equation at extreme leanness/fatness; read
        the output as an estimate under those stated assumptions, not a
        direct physical measurement.

Evidence grade: peer-reviewed regression equations, textbook-standard in
exercise science - modulo the men's-3-site ambiguity flagged above, which is
a real open question about which coefficient set the "3-site" name refers
to, not a soft or contested finding about the science itself.
"""

from __future__ import annotations

from dataclasses import dataclass


def siri_bodyfat_pct(body_density: float) -> float:
    """Siri (1961): %BF = 495/BD - 450.

    Raises:
        ValueError: if body_density <= 0.
    """
    if body_density <= 0:
        raise ValueError("body_density must be > 0")
    return 495.0 / body_density - 450.0


@dataclass
class SkinfoldResult:
    """Body density + Siri %BF from a named set of skinfold sites."""

    sex: str
    method: str  # "3-site" or "7-site"
    sites_mm: dict[str, float]
    sum_mm: float
    age: float
    body_density: float
    bodyfat_pct: float


def _check_positive(age: float, **sites: float) -> None:
    if age <= 0:
        raise ValueError("age must be > 0")
    for name, value in sites.items():
        if value <= 0:
            raise ValueError(f"{name} must be > 0")


def jackson_pollock_men_3site(
    chest_mm: float, triceps_mm: float, subscapular_mm: float, age: float
) -> SkinfoldResult:
    """Men's 3-site (chest + triceps + subscapular) body density + Siri %BF.

    See module docstring for the men's-3-site site-combo ambiguity - this is
    specifically chest+triceps+subscapular, not chest+abdomen+thigh.

    Raises:
        ValueError: if any measurement or age isn't > 0.
    """
    _check_positive(age, chest_mm=chest_mm, triceps_mm=triceps_mm, subscapular_mm=subscapular_mm)
    s = chest_mm + triceps_mm + subscapular_mm
    bd = 1.1125025 - 0.0013125 * s + 0.0000055 * s**2 - 0.000244 * age
    return SkinfoldResult(
        sex="male",
        method="3-site",
        sites_mm={"chest_mm": chest_mm, "triceps_mm": triceps_mm, "subscapular_mm": subscapular_mm},
        sum_mm=s,
        age=age,
        body_density=bd,
        bodyfat_pct=siri_bodyfat_pct(bd),
    )


def jackson_pollock_men_7site(
    chest_mm: float,
    axilla_mm: float,
    triceps_mm: float,
    subscapular_mm: float,
    abdominal_mm: float,
    suprailiac_mm: float,
    thigh_mm: float,
    age: float,
) -> SkinfoldResult:
    """Men's 7-site body density + Siri %BF.

    Sites: chest, axilla, triceps, subscapular, abdominal, suprailiac, thigh.

    Raises:
        ValueError: if any measurement or age isn't > 0.
    """
    _check_positive(
        age,
        chest_mm=chest_mm,
        axilla_mm=axilla_mm,
        triceps_mm=triceps_mm,
        subscapular_mm=subscapular_mm,
        abdominal_mm=abdominal_mm,
        suprailiac_mm=suprailiac_mm,
        thigh_mm=thigh_mm,
    )
    s = chest_mm + axilla_mm + triceps_mm + subscapular_mm + abdominal_mm + suprailiac_mm + thigh_mm
    bd = 1.112 - 0.00043499 * s + 0.00000055 * s**2 - 0.00028826 * age
    return SkinfoldResult(
        sex="male",
        method="7-site",
        sites_mm={
            "chest_mm": chest_mm,
            "axilla_mm": axilla_mm,
            "triceps_mm": triceps_mm,
            "subscapular_mm": subscapular_mm,
            "abdominal_mm": abdominal_mm,
            "suprailiac_mm": suprailiac_mm,
            "thigh_mm": thigh_mm,
        },
        sum_mm=s,
        age=age,
        body_density=bd,
        bodyfat_pct=siri_bodyfat_pct(bd),
    )


def jackson_pollock_women_3site(
    triceps_mm: float, thigh_mm: float, suprailiac_mm: float, age: float
) -> SkinfoldResult:
    """Women's 3-site (triceps + thigh + suprailiac) body density + Siri %BF.

    Raises:
        ValueError: if any measurement or age isn't > 0.
    """
    _check_positive(age, triceps_mm=triceps_mm, thigh_mm=thigh_mm, suprailiac_mm=suprailiac_mm)
    s = triceps_mm + thigh_mm + suprailiac_mm
    bd = 1.0994921 - 0.0009929 * s + 0.0000023 * s**2 - 0.0001392 * age
    return SkinfoldResult(
        sex="female",
        method="3-site",
        sites_mm={"triceps_mm": triceps_mm, "thigh_mm": thigh_mm, "suprailiac_mm": suprailiac_mm},
        sum_mm=s,
        age=age,
        body_density=bd,
        bodyfat_pct=siri_bodyfat_pct(bd),
    )


def jackson_pollock_women_7site(
    chest_mm: float,
    axilla_mm: float,
    triceps_mm: float,
    subscapular_mm: float,
    abdominal_mm: float,
    suprailiac_mm: float,
    thigh_mm: float,
    age: float,
) -> SkinfoldResult:
    """Women's 7-site body density + Siri %BF (same 7 sites as the men's 7-site equation).

    Raises:
        ValueError: if any measurement or age isn't > 0.
    """
    _check_positive(
        age,
        chest_mm=chest_mm,
        axilla_mm=axilla_mm,
        triceps_mm=triceps_mm,
        subscapular_mm=subscapular_mm,
        abdominal_mm=abdominal_mm,
        suprailiac_mm=suprailiac_mm,
        thigh_mm=thigh_mm,
    )
    s = chest_mm + axilla_mm + triceps_mm + subscapular_mm + abdominal_mm + suprailiac_mm + thigh_mm
    bd = 1.097 - 0.00046971 * s + 0.00000056 * s**2 - 0.00012828 * age
    return SkinfoldResult(
        sex="female",
        method="7-site",
        sites_mm={
            "chest_mm": chest_mm,
            "axilla_mm": axilla_mm,
            "triceps_mm": triceps_mm,
            "subscapular_mm": subscapular_mm,
            "abdominal_mm": abdominal_mm,
            "suprailiac_mm": suprailiac_mm,
            "thigh_mm": thigh_mm,
        },
        sum_mm=s,
        age=age,
        body_density=bd,
        bodyfat_pct=siri_bodyfat_pct(bd),
    )
