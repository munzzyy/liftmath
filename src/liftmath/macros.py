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

TDEE estimate - `macro_targets` picks one of four methods, in this priority
order, each documented with what it's actually good for rather than treated
as interchangeable:

    1. Supplied directly (`tdee=`) - always wins if given; nothing below runs.
    2. `bodyfat_pct` given (with `bodyweight`): routes through Cunningham
       (see below) via lean_mass_kg = bodyweight_kg * (1 - bodyfat_pct/100) -
       the most accurate option when a real (or estimated, e.g. from
       `bodycomp.navy_body_fat`) body-fat reading is available, since it's
       the one method here actually keyed to how much of you is lean tissue.
       Wins over Mifflin-St Jeor below if both are supplied, since it's the
       more specific input.
    3. `age`, `height_m`, and `sex` all given: Mifflin-St Jeor - see below.
       This is the new default whenever those three are available; previously
       this module had no age/height-aware estimate at all.
    4. None of the above: the flat `bodyweight_kg * activity_factor`
       heuristic this module has always used as its no-input fallback. This
       is a QUICK ESTIMATE, not a named/published equation - it stays only
       because the tool needs to return something useful from a bodyweight
       and an activity guess alone. Prefer method 2 or 3 whenever the extra
       inputs are available.

`age`, `height_m`, and `sex` must be supplied together (all three) to reach
method 3 - partial input raises `ValueError` rather than silently falling
through to the quick estimate.

Mifflin-St Jeor (1990): the best general-population resting-energy-
expenditure equation in a head-to-head comparison of predictive equations
(Frankenfield, Roth-Yousey & Compher, 2005, a systematic review in the
Journal of the American Dietetic Association, 105(5), 775-789, which found
Mifflin-St Jeor had the best combination of accuracy and precision among the
equations it compared, across both obese and non-obese subjects).

    Mifflin, M.D., St Jeor, S.T., Hill, L.A., Scott, B.J., Daugherty, S.A.,
    Koh, Y.O. (1990). A new predictive equation for resting energy
    expenditure in healthy individuals. American Journal of Clinical
    Nutrition, 51(2), 241-247.
    RMR_kcal = 10*weight_kg + 6.25*height_cm - 5*age_years + 5 (men) or
    - 161 (women); TDEE = RMR * a standard PAL activity multiplier (the same
    CUNNINGHAM_ACTIVITY_MULTIPLIERS table `cunningham_tdee` already uses,
    reused here rather than a second copy - see that constant's own note).
    The coefficients (10, 6.25, 5, +5/-161) were cross-checked against
    multiple independent secondary sources reproducing the 1990 equation
    (the primary text itself is paywalled and wasn't pulled directly); every
    source checked reproduces the same four numbers identically.

Cunningham TDEE (`cunningham_tdee`): an alternative RMR estimate using fat-
free (lean) mass instead of total bodyweight - meaningfully better than the
flat bodyweight*factor heuristic for lean, trained individuals. Accepts
either a known `lean_mass_kg` directly, or the raw `bodyweight_kg` +
`bodyfat_pct` that `bodycomp.ffmi`/`bodycomp.navy_body_fat` already compute,
so a caller doesn't have to hand-derive lean mass first.

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
alongside the Mifflin-St Jeor and bodyweight*factor estimates rather than
replacing them - each is validated for a different population/input
availability, and the tool says which was used (`MacroTargets.tdee_method`).

The activity multipliers used for the Cunningham and Mifflin-St Jeor paths
are standard PAL (physical activity level) ratios (sedentary ~1.2, light
~1.375, moderate ~1.55, active ~1.725 - the widely-used Harris-Benedict-style
PAL bands), reusing this module's existing activity-level NAMES for
consistency, but NOT the same numeric flat kcal/kg factors used by the
bodyweight-based quick-estimate fallback above (that path bundles "RMR *
activity" into one flat per-kg number; Cunningham and Mifflin-St Jeor both
need a real two-step RMR-then-multiplier).
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
# and Mifflin-St Jeor RMR - a real two-step RMR*activity model, distinct from
# ACTIVITY_FACTORS above (see module docstring).
CUNNINGHAM_ACTIVITY_MULTIPLIERS = {"sedentary": 1.2, "light": 1.375, "moderate": 1.55, "active": 1.725}

# Mifflin-St Jeor (1990) sex constant: RMR = 10*wt_kg + 6.25*ht_cm - 5*age + this.
MIFFLIN_SEX_CONSTANT = {"male": 5.0, "female": -161.0}

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
    # Which TDEE method actually ran: "supplied", "cunningham", "mifflin", or
    # "quick_estimate" - see the module docstring's priority-order list.
    tdee_method: str = "quick_estimate"

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
    age: int | None = None,
    height_m: float | None = None,
    sex: str | None = None,
    bodyfat_pct: float | None = None,
) -> MacroTargets:
    """Compute protein/calorie/fat/carb targets from bodyweight and a goal.

    Args:
        bodyweight: bodyweight in `unit`.
        goal: one of "gain", "maintain", "recomp", "cut".
        unit: "lb" or "kg" for `bodyweight`.
        tdee: maintenance kcal/day if known. If omitted, TDEE is estimated by
            the best method the given inputs support - see the module
            docstring's priority-ordered list (bodyfat_pct -> Cunningham;
            age+height_m+sex -> Mifflin-St Jeor; otherwise a quick bodyweight
            * activity-factor estimate).
        activity: activity level, used by whichever estimate method actually
            runs (ignored if `tdee` is supplied directly).
        age: age in years. Combine with `height_m` and `sex` (all three, or
            none) for a Mifflin-St Jeor TDEE estimate.
        height_m: height in meters. Combine with `age` and `sex`.
        sex: "male" or "female". Combine with `age` and `height_m`.
        bodyfat_pct: body-fat percentage (e.g. 15 for 15%). If given, TDEE
            routes through `cunningham_tdee` via lean_mass_kg = bodyweight_kg
            * (1 - bodyfat_pct/100) - takes priority over the Mifflin-St Jeor
            inputs above if both are given, since it's the more specific input.

    Raises:
        ValueError: for an unrecognized goal, activity level, or non-positive
            bodyweight, or if only some of `age`/`height_m`/`sex` are given
            (they must be all-or-nothing).
    """
    if goal not in PROTEIN_G_PER_KG:
        raise ValueError(f"unknown goal '{goal}'. Choose from: {', '.join(GOALS)}")
    if bodyweight <= 0:
        raise ValueError("bodyweight must be positive")

    mifflin_inputs = (age, height_m, sex)
    if any(v is not None for v in mifflin_inputs) and not all(v is not None for v in mifflin_inputs):
        raise ValueError(
            "age, height, and sex must all be given together for a Mifflin-St Jeor "
            "estimate, or all omitted"
        )

    bw_kg = bodyweight / LB_PER_KG if unit == "lb" else bodyweight

    tdee_is_estimate = tdee is None
    tdee_method = "supplied"
    if tdee is None:
        if bodyfat_pct is not None:
            tdee = cunningham_tdee(activity=activity, bodyweight_kg=bw_kg, bodyfat_pct=bodyfat_pct).tdee
            tdee_method = "cunningham"
        elif age is not None:
            if sex not in ("male", "female"):
                raise ValueError(f"sex must be 'male' or 'female' for a Mifflin-St Jeor estimate, got {sex!r}")
            if age <= 0:
                raise ValueError("age must be > 0")
            if height_m <= 0:
                raise ValueError("height_m must be > 0")
            if activity not in CUNNINGHAM_ACTIVITY_MULTIPLIERS:
                raise ValueError(f"unknown activity '{activity}'. Choose from: {', '.join(ACTIVITY_LEVELS)}")
            rmr = 10.0 * bw_kg + 6.25 * (height_m * 100.0) - 5.0 * age + MIFFLIN_SEX_CONSTANT[sex]
            tdee = rmr * CUNNINGHAM_ACTIVITY_MULTIPLIERS[activity]
            tdee_method = "mifflin"
        else:
            if activity not in ACTIVITY_FACTORS:
                raise ValueError(f"unknown activity '{activity}'. Choose from: {', '.join(ACTIVITY_LEVELS)}")
            tdee = bw_kg * ACTIVITY_FACTORS[activity]
            tdee_method = "quick_estimate"

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
        tdee_method=tdee_method,
    )


@dataclass
class CunninghamTdee:
    """Cunningham (1980) lean-mass-based RMR/TDEE estimate."""

    lean_mass_kg: float
    activity: str
    rmr_kcal: float
    activity_multiplier: float
    tdee: float


def cunningham_tdee(
    lean_mass_kg: float | None = None,
    activity: str = "moderate",
    *,
    bodyweight_kg: float | None = None,
    bodyfat_pct: float | None = None,
) -> CunninghamTdee:
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
            Give this directly, OR give `bodyweight_kg` + `bodyfat_pct`
            instead and lean mass is derived as bodyweight_kg *
            (1 - bodyfat_pct/100) - the same raw inputs `bodycomp.ffmi`/
            `bodycomp.navy_body_fat` already compute a body-fat % from, so a
            caller who just ran `navybf` doesn't have to hand-derive lean
            mass first.
        activity: one of ACTIVITY_LEVELS; applies a standard PAL multiplier
            (CUNNINGHAM_ACTIVITY_MULTIPLIERS), NOT the same numeric table as
            the flat bodyweight-based estimate above.
        bodyweight_kg: total bodyweight, kilograms - alternative to
            `lean_mass_kg` (see above); must be paired with `bodyfat_pct`.
        bodyfat_pct: body-fat percentage (e.g. 15 for 15%) - alternative to
            `lean_mass_kg` (see above); must be paired with `bodyweight_kg`.

    Raises:
        ValueError: if neither `lean_mass_kg` nor both `bodyweight_kg` and
            `bodyfat_pct` are given (or both forms are given at once), if
            the resulting lean mass isn't > 0, if `bodyfat_pct` is outside
            [0, 100), or if `activity` is unrecognized.
    """
    if lean_mass_kg is None:
        if bodyweight_kg is None or bodyfat_pct is None:
            raise ValueError("give lean_mass_kg, or both bodyweight_kg and bodyfat_pct")
        if bodyweight_kg <= 0:
            raise ValueError("bodyweight_kg must be > 0")
        if not 0 <= bodyfat_pct < 100:
            raise ValueError("bodyfat_pct must be in [0, 100)")
        lean_mass_kg = bodyweight_kg * (1 - bodyfat_pct / 100.0)
    elif bodyweight_kg is not None or bodyfat_pct is not None:
        raise ValueError("give either lean_mass_kg OR (bodyweight_kg and bodyfat_pct), not both")

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
