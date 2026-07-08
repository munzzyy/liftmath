"""Whole-program weekly volume audit: sum sets per muscle across a split, then grade.

Each exercise contributes a fraction of a weekly hard set to every muscle it
trains: 1.0 for the prime mover, roughly 0.3-0.7 for a strong synergist. This
mirrors how Renaissance-Periodization-style volume counting treats compounds,
so indirect arm/delt/hamstring volume from presses, rows, and squats is
counted instead of ignored.

Exercise name matching is longest-key-first on a whole-word/whole-phrase basis
(not raw substring), so a more specific key like "leg curl" is preferred over
a generic "curl", "leg extension" over "extension", and a short key like
"chin" doesn't fire inside an unrelated word like "machine". Unknown exercise
names must supply explicit fractions.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from liftmath.volume import BAND_SHORT, LANDMARKS, band_for, resolve_muscle

# exercise name (lowercase) -> {muscle_key: fraction}. Longest key wins on substring match.
EXERCISE_FRACTIONS: dict[str, dict[str, float]] = {
    "incline press":      {"chest": 1.0, "triceps": 0.5, "sidedelts": 0.4},
    "bench":              {"chest": 1.0, "triceps": 0.5, "sidedelts": 0.3},
    "press":              {"chest": 1.0, "triceps": 0.5, "sidedelts": 0.3},  # unqualified chest press
    "chest fly":          {"chest": 1.0},
    "pec deck":           {"chest": 1.0},
    "cable crossover":    {"chest": 1.0},
    "fly":                {"chest": 1.0},
    "dip":                {"chest": 0.8, "triceps": 0.6},
    "overhead press":     {"sidedelts": 1.0, "triceps": 0.5},
    "shoulder press":     {"sidedelts": 1.0, "triceps": 0.5},
    "landmine press":     {"sidedelts": 1.0, "chest": 0.5, "triceps": 0.5},
    "ohp":                {"sidedelts": 1.0, "triceps": 0.5},
    "cuban press":        {"reardelts": 0.8, "sidedelts": 0.5},
    "lateral raise":      {"sidedelts": 1.0},
    "lateral":            {"sidedelts": 1.0},
    "rear delt":          {"reardelts": 1.0},
    "reverse fly":        {"reardelts": 1.0},
    "face pull":          {"reardelts": 1.0, "traps": 0.3},
    "row":                {"back": 1.0, "biceps": 0.5, "reardelts": 0.3},
    "pendlay row":        {"back": 1.0, "biceps": 0.5, "reardelts": 0.3},
    "meadows row":        {"back": 1.0, "biceps": 0.5, "reardelts": 0.3},
    "pulldown":           {"back": 1.0, "biceps": 0.5},
    "pull-up":            {"back": 1.0, "biceps": 0.5},
    "pull up":            {"back": 1.0, "biceps": 0.5},
    "pullup":             {"back": 1.0, "biceps": 0.5},
    "chin":               {"back": 1.0, "biceps": 0.6},
    "romanian deadlift":  {"hamstrings": 1.0, "glutes": 0.7, "back": 0.3},
    "rdl":                {"hamstrings": 1.0, "glutes": 0.7, "back": 0.3},
    "deadlift":           {"back": 0.7, "hamstrings": 0.7, "glutes": 0.7},
    "leg curl":           {"hamstrings": 1.0},
    "nordic curl":        {"hamstrings": 1.0},
    "leg extension":      {"quads": 1.0},
    "hack squat":         {"quads": 1.0, "glutes": 0.5},
    "split squat":        {"quads": 0.9, "glutes": 0.8},
    "squat":              {"quads": 1.0, "glutes": 0.6},
    "sissy squat":        {"quads": 1.0, "glutes": 0.2},
    "goblet squat":       {"quads": 1.0, "glutes": 0.6},
    "leg press":          {"quads": 1.0, "glutes": 0.5},
    "lunge":              {"quads": 0.8, "glutes": 0.8},
    "hip thrust":         {"glutes": 1.0, "hamstrings": 0.3},
    "reverse hyper":      {"glutes": 1.0, "hamstrings": 0.5, "back": 0.3},
    "back extension":     {"back": 1.0, "glutes": 0.5, "hamstrings": 0.3},
    "calf":               {"calves": 1.0},
    "hammer curl":        {"biceps": 1.0, "forearms": 0.4},
    "preacher curl":      {"biceps": 1.0},
    "concentration curl": {"biceps": 1.0},
    "curl":               {"biceps": 1.0},
    "pushdown":           {"triceps": 1.0},
    "skull crusher":      {"triceps": 1.0},
    "skull":              {"triceps": 1.0},
    "triceps extension":  {"triceps": 1.0},
    "overhead extension": {"triceps": 1.0},
    "kickback":           {"triceps": 1.0},
    "cable crunch":       {"abs": 1.0},
    "crunch":             {"abs": 1.0},
    "leg raise":          {"abs": 1.0},
    "plank":              {"abs": 1.0},
    "copenhagen plank":   {"abs": 1.0},
    "shrug":              {"traps": 1.0},
    "wrist curl":         {"forearms": 1.0},
}


@dataclass
class ExerciseSet:
    """One exercise's weekly contribution: `sets` performed `frequency` times/week."""

    name: str
    sets: float
    frequency: float
    fractions: dict[str, float] | None = None  # explicit muscle=fraction overrides

    @property
    def weekly_sets(self) -> float:
        return self.sets * self.frequency


def resolve_fractions(name: str, explicit: dict[str, float] | None = None) -> dict[str, float]:
    """Return {muscle_key: fraction} for an exercise name, honoring explicit overrides."""
    if explicit:
        resolved = {}
        for muscle, frac in explicit.items():
            key = resolve_muscle(muscle)
            resolved[key] = frac
        return resolved
    lowered = name.lower()
    for key in sorted(EXERCISE_FRACTIONS, key=len, reverse=True):
        # Whole-word/whole-phrase match only: a bare substring test would let a
        # short key like "chin" fire inside an unrelated word like "machine".
        pattern = r"(?<!\w)" + re.escape(key) + r"(?!\w)"
        if re.search(pattern, lowered):
            return dict(EXERCISE_FRACTIONS[key])
    return {}


@dataclass
class MuscleAudit:
    muscle: str
    weekly_sets: float
    mev: int | None
    mrv: int | None
    verdict: str


@dataclass
class ProgramAudit:
    totals: dict[str, float] = field(default_factory=dict)
    rows: list[MuscleAudit] = field(default_factory=list)
    untrained: list[str] = field(default_factory=list)


def audit_program(exercises: list[ExerciseSet]) -> ProgramAudit:
    """Sum weekly hard sets per muscle across a list of exercises and grade each.

    Raises:
        ValueError: if an exercise name is unrecognized and has no explicit fractions.
    """
    totals: dict[str, float] = {}
    for ex in exercises:
        fracs = resolve_fractions(ex.name, ex.fractions)
        if not fracs:
            raise ValueError(
                f"unknown exercise '{ex.name}' - pass explicit fractions, e.g. "
                f"{{'chest': 1.0, 'triceps': 0.5}}"
            )
        for muscle, frac in fracs.items():
            totals[muscle] = totals.get(muscle, 0.0) + ex.weekly_sets * frac

    rows = []
    for muscle in sorted(totals, key=lambda k: -totals[k]):
        sets = totals[muscle]
        if muscle in LANDMARKS:
            mev, mrv = LANDMARKS[muscle][1], LANDMARKS[muscle][4]
            verdict = BAND_SHORT[band_for(muscle, sets)]
        else:
            mev = mrv = None
            verdict = "(no landmark)"
        rows.append(MuscleAudit(muscle=muscle, weekly_sets=sets, mev=mev, mrv=mrv, verdict=verdict))

    untrained = [m for m in LANDMARKS if m not in totals and LANDMARKS[m][1] > 0]
    return ProgramAudit(totals=totals, rows=rows, untrained=sorted(untrained))
