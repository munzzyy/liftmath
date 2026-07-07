"""Protein / calorie / fat / carb targets from bodyweight and a training goal.

Protein: Morton et al. (2018), a meta-analysis in the British Journal of
Sports Medicine, puts ~1.6 g/kg/day as the intake beyond which added protein
gives no further hypertrophy benefit on average, with intakes up to ~2.2 g/kg
shown harmless. Protein is raised in a deficit (per Helms, Aragon & Fitschen,
2014, ISSN position stand on natural bodybuilding contest prep) to better
spare lean mass while calories are restricted.

Calories: a lean surplus (~12% above maintenance) for "gain", maintenance
calories for "maintain" and "recomp" (recomp trains at maintenance kcal with
elevated protein - it is a slow strategy best suited to novices, returning
trainees, or higher body-fat individuals), and a moderate deficit (~20% below
maintenance) for "cut".

Fat floor: ~0.9 g/kg at maintenance/surplus for hormone production, relaxed
to ~0.6 g/kg in an aggressive deficit to leave more calories for protein and
performance.

The calorie identity is enforced here: the reported calorie target always
equals what protein + fat + carbs actually sum to. If the protein+fat floor
alone exceeds the requested calorie target (can happen on an aggressive cut
for a heavier person), carbs are set to zero and a shortfall flag is raised
rather than silently printing a target the macros don't add up to.

Cunningham TDEE (`cunningham_tdee`): an alternative RMR estimate using fat-
free (lean) mass instead of total bodyweight - meaningfully better than a
flat bodyweight*factor heuristic for lean, trained individuals.

Cunningham, D.J. (1980). A reanalysis of the factors influencing basal
metabolic rate in normal adults. American Journal of Clinical Nutrition,
33(11), 2372-2374. RMR_kcal = 500 + 22 * lean_mass_kg; TDEE = RMR * an
activity multiplier.

Evidence grade: established-for-athletes specifically. A 2023 systematic
review and meta-analysis (Sports Medicine) found Cunningham (1980) among a
small set of equations (with Harris-Benedict 1918, Cunningham 1991, De
Lorenzo, Ten-Haaf) whose predicted RMR did NOT differ significantly from
measured RMR in athlete populations, while Mifflin-St Jeor and several
others significantly under/over-estimated in that same athlete-specific
analysis. Caveat: a separate general-population comparison (498 measured
adults, not athletes) found Cunningham OVERESTIMATED by 14-15% - so this
equation's advantage is specific to trained individuals with a known or
estimated lean mass, not the general population. This module offers it
alongside the existing bodyweight*factor estimate rather than replacing it -
each is validated for a different population, and the tool says which.

The activity multipliers used for the Cunningham path are standard PAL
(physical activity level) ratios (sedentary ~1.2, light ~1.375, moderate
~1.55, active ~1.725 - the widely-used Harris-Benedict-style PAL bands),
reusing this module's existing activity-level NAMES for consistency, but
NOT the same numeric flat kcal/kg factors used by the bodyweight-based
`macro_targets` estimate above (that path bundles "RMR * activity" into one
flat per-kg number; Cunningham needs a real two-step RMR-then-multiplier).
"""

from __future__ import annotations

from dataclasses import dataclass

LB_PER_KG = 2.2046226

# grams of protein per kg bodyweight, by goal
PROTEIN_G_PER_KG = {"gain": 1.6, "maintain": 1.6, "recomp": 2.2, "cut": 2.4}

# calorie multiplier applied to maintenance (TDEE), by goal
CALORIE_MULTIPLIER = {"gain": 1.12, "maintain": 1.0, "recomp": 1.0, "cut": 0.80}

# rough TDEE = bodyweight_kg * factor, by self-reported activity level
ACTIVITY_FACTORS = {"sedentary": 28, "light": 31, "moderate": 34, "active": 38}

# Standard PAL (physical activity level) multipliers applied to Cunningham
# RMR - a real two-step RMR*activity model, distinct from ACTIVITY_FACTORS
# above (see module docstring).
CUNNINGHAM_ACTIVITY_MULTIPLIERS = {"sedentary": 1.2, "light": 1.375, "moderate": 1.55, "active": 1.725}

GOALS = tuple(PROTEIN_G_PER_KG.keys())
ACTIVITY_LEVELS = tuple(ACTIVITY_FACTORS.keys())


@dataclass
class MacroTargets:
    bodyweight_kg: float
    goal: str
    tdee: float
    tdee_is_estimate: bool
    target_kcal: float
    actual_kcal: float
    protein_g: float
    protein_g_per_kg: float
    fat_g: float
    fat_g_per_kg: float
    carb_g: float
    protein_kcal: float
    fat_kcal: float
    carb_kcal: float
    shortfall: bool

    @property
    def per_meal_protein_g(self) -> float:
        """Rough per-meal protein target across 3-5 meals (leucine-threshold heuristic)."""
        return 0.4 * self.bodyweight_kg


def macro_targets(
    bodyweight: float,
    goal: str,
    *,
    unit: str = "lb",
    tdee: float | None = None,
    activity: str = "moderate",
) -> MacroTargets:
    """Compute protein/calorie/fat/carb targets from bodyweight and a goal.

    Args:
        bodyweight: bodyweight in `unit`.
        goal: one of "gain", "maintain", "recomp", "cut".
        unit: "lb" or "kg" for `bodyweight`.
        tdee: maintenance kcal/day if known. If omitted, TDEE is estimated as
            bodyweight_kg * an activity factor (a rough estimate - track
            bodyweight over 1-2 weeks and adjust to the real trend).
        activity: activity level used only when `tdee` is not supplied.

    Raises:
        ValueError: for an unrecognized goal, activity level, or non-positive bodyweight.
    """
    if goal not in PROTEIN_G_PER_KG:
        raise ValueError(f"unknown goal '{goal}'. Choose from: {', '.join(GOALS)}")
    if bodyweight <= 0:
        raise ValueError("bodyweight must be positive")

    bw_kg = bodyweight / LB_PER_KG if unit == "lb" else bodyweight

    tdee_is_estimate = tdee is None
    if tdee is None:
        if activity not in ACTIVITY_FACTORS:
            raise ValueError(f"unknown activity '{activity}'. Choose from: {', '.join(ACTIVITY_LEVELS)}")
        tdee = bw_kg * ACTIVITY_FACTORS[activity]

    protein_gkg = PROTEIN_G_PER_KG[goal]
    protein_g = protein_gkg * bw_kg
    target_kcal = tdee * CALORIE_MULTIPLIER[goal]

    fat_gkg = 0.6 if goal == "cut" else 0.9
    fat_g = fat_gkg * bw_kg

    protein_kcal = protein_g * 4
    fat_kcal = fat_g * 9
    floor_kcal = protein_kcal + fat_kcal

    carb_kcal = max(0.0, target_kcal - floor_kcal)
    carb_g = carb_kcal / 4

    actual_kcal = floor_kcal + carb_kcal
    shortfall = actual_kcal > target_kcal + 1

    return MacroTargets(
        bodyweight_kg=bw_kg,
        goal=goal,
        tdee=tdee,
        tdee_is_estimate=tdee_is_estimate,
        target_kcal=target_kcal,
        actual_kcal=actual_kcal,
        protein_g=protein_g,
        protein_g_per_kg=protein_gkg,
        fat_g=fat_g,
        fat_g_per_kg=fat_gkg,
        carb_g=carb_g,
        protein_kcal=protein_kcal,
        fat_kcal=fat_kcal,
        carb_kcal=carb_kcal,
        shortfall=shortfall,
    )


@dataclass
class CunninghamTdee:
    """Cunningham (1980) lean-mass-based RMR/TDEE estimate."""

    lean_mass_kg: float
    activity: str
    rmr_kcal: float
    activity_multiplier: float
    tdee: float


def cunningham_tdee(lean_mass_kg: float, activity: str = "moderate") -> CunninghamTdee:
    """Cunningham (1980) RMR/TDEE estimate from lean (fat-free) body mass.

    Established-for-athletes specifically (see module docstring): better
    than a flat bodyweight*factor estimate for lean, trained individuals
    with a known or estimated lean mass, but shown to overestimate in a
    general (non-athlete) population comparison - this is an alternative to
    `macro_targets`' bodyweight-based TDEE estimate, not a universal
    replacement for it.

    Args:
        lean_mass_kg: fat-free mass, kilograms (e.g. from `bodycomp.ffmi`
            or `bodycomp.navy_body_fat` combined with total bodyweight).
        activity: one of ACTIVITY_LEVELS; applies a standard PAL multiplier
            (CUNNINGHAM_ACTIVITY_MULTIPLIERS), NOT the same numeric table as
            the flat bodyweight-based estimate above.

    Raises:
        ValueError: if lean_mass_kg <= 0 or activity is unrecognized.
    """
    if lean_mass_kg <= 0:
        raise ValueError("lean_mass_kg must be > 0")
    if activity not in CUNNINGHAM_ACTIVITY_MULTIPLIERS:
        raise ValueError(f"unknown activity '{activity}'. Choose from: {', '.join(ACTIVITY_LEVELS)}")

    rmr = 500.0 + 22.0 * lean_mass_kg
    multiplier = CUNNINGHAM_ACTIVITY_MULTIPLIERS[activity]
    return CunninghamTdee(
        lean_mass_kg=lean_mass_kg,
        activity=activity,
        rmr_kcal=rmr,
        activity_multiplier=multiplier,
        tdee=rmr * multiplier,
    )
