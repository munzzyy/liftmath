"""Weekly hard-set volume landmarks per muscle group.

MV (maintenance volume), MEV (minimum effective volume), MAV (maximum
adaptive volume, a productive range given as a low-high pair), and MRV
(maximum recoverable volume) are population heuristics popularized by
Dr. Mike Israetel and Renaissance Periodization's volume landmark framework.

EVIDENCE TIER, stated explicitly: the specific per-muscle numbers in
LANDMARKS below (e.g. chest MEV=10/MRV=22) come from Israetel's/RP's own
coaching materials and popularized content, NOT a peer-reviewed table - a
research pass specifically looking for a primary peer-reviewed source
publishing these exact per-muscle MEV/MAV/MRV numbers did not find one. This
is a PRACTITIONER FRAMEWORK / expert-consensus heuristic (tier 4), not
peer-reviewed per-muscle data. Say so anywhere these numbers surface (CLI
text, not just this module comment) - see cli.py's volume/program/meso
output.

These are starting points to titrate from, not fixed laws. Dose-response
literature (Schoenfeld, Grgic & Krieger, 2017, meta-analysis in Journal of
Sports Sciences; Baz-Valle et al., 2022, systematic review in PeerJ; Pelland,
Robinson & Nuckols, 2024, review of set-volume dose-response) shows
hypertrophy keeps rising with added volume with diminishing returns, and
that high responders can productively exceed these numbers. Individualize
by recovery and rate of progress. That broader dose-response literature is
established (peer-reviewed meta-analyses/systematic reviews); it's only the
exact per-muscle MEV/MAV/MRV cutoffs below that are practitioner-tier, not
the general "more volume helps, with diminishing returns" finding.

A "hard set" is a working set taken to roughly 0-4 reps in reserve. A
directly-trained isolation exercise counts fully toward a muscle's weekly
total; a compound lift counts fully for its prime mover and partially
(~0.3-0.7) for its strong synergists (see program.py).
"""

from __future__ import annotations

from dataclasses import dataclass

# muscle -> (MV, MEV, MAV_low, MAV_high, MRV), all in weekly hard sets.
# EVIDENCE TIER: practitioner consensus / expert heuristic (Israetel/RP), NOT
# a peer-reviewed per-muscle table - no primary source publishes these exact
# numbers. See module docstring.
LANDMARKS: dict[str, tuple[int, int, int, int, int]] = {
    "chest":       (8, 10, 12, 20, 22),
    "back":        (8, 10, 14, 22, 25),
    "quads":       (6, 8, 12, 18, 20),
    "hamstrings":  (4, 6, 10, 16, 20),
    "glutes":      (0, 4, 8, 16, 16),
    "sidedelts":   (6, 8, 16, 22, 26),
    "reardelts":   (0, 6, 10, 18, 20),
    "biceps":      (5, 8, 14, 20, 26),
    "triceps":     (4, 6, 10, 14, 18),
    "calves":      (6, 8, 12, 16, 20),
    "abs":         (0, 0, 16, 25, 25),
    "traps":       (0, 4, 12, 20, 26),
    "forearms":    (0, 2, 8, 16, 20),
}

MUSCLES: tuple[str, ...] = tuple(LANDMARKS.keys())

ALIASES: dict[str, str] = {
    "shoulders": "sidedelts", "delts": "sidedelts", "side-delts": "sidedelts",
    "rear-delts": "reardelts", "lats": "back", "hams": "hamstrings",
    "legs": "quads", "bis": "biceps", "tris": "triceps", "pecs": "chest",
}

# Band codes, worst to best, plus the "grows from indirect work" special case.
BAND_SHORT: dict[str, str] = {
    "below_mv": "BELOW maintenance",
    "maint": "maintenance only",
    "sub_mav": "below productive (add sets)",
    "productive": "productive",
    "high": "high (near MRV)",
    "over_mrv": "over MRV heuristic",
    "indirect_ok": "ok (indirect only)",
}

BAND_LONG: dict[str, str] = {
    "below_mv": "BELOW maintenance - this muscle is likely losing size",
    "maint": "maintenance only - holds size but below the growth threshold; add sets to grow",
    "sub_mav": "above MEV but below the productive range - growing; add sets toward MAV",
    "productive": "in the productive (MAV) range - a good place to progress from",
    "high": "high - near max recoverable volume; only if recovery + progress support it",
    "over_mrv": (
        "above the population MRV heuristic - diminishing returns and more fatigue, not "
        "automatically wasted (Pelland/Nuckols 2024); justify only by recovery + progress"
    ),
    "indirect_ok": (
        "0 direct sets is fine here - this muscle grows from compound/indirect work; "
        "add direct sets only to bring it up further"
    ),
}


def resolve_muscle(name: str) -> str:
    """Normalize a muscle name/alias to its canonical landmark key.

    Raises:
        KeyError: if the name (after alias resolution) is not a known muscle.
    """
    key = name.lower().replace(" ", "")
    key = ALIASES.get(key, key)
    if key not in LANDMARKS:
        raise KeyError(
            f"unknown muscle '{name}'. Known: {', '.join(sorted(LANDMARKS))}"
        )
    return key


def band_for(muscle: str, sets: float) -> str:
    """Classify weekly hard `sets` for a canonical `muscle` key into a volume-band code.

    This is the single source of truth so per-muscle and whole-program audits
    can never grade the same set count differently.
    """
    mv, mev, mav_lo, mav_hi, mrv = LANDMARKS[muscle]
    if mev == 0:
        # Grows from indirect/compound work (abs, glutes tolerate ~0 direct sets).
        if sets == 0:
            return "indirect_ok"
        if sets <= mav_hi:
            return "productive"
        if sets <= mrv:
            return "high"
        return "over_mrv"
    if sets < mv:
        return "below_mv"
    if sets < mev:
        return "maint"
    if sets < mav_lo:
        return "sub_mav"
    if sets <= mav_hi:
        return "productive"
    if sets <= mrv:
        return "high"
    return "over_mrv"


def describe_band(muscle: str, sets: float, *, long: bool = False) -> str:
    """Human-readable verdict for `sets` weekly hard sets on `muscle`."""
    band = band_for(muscle, sets)
    return BAND_LONG[band] if long else BAND_SHORT[band]


@dataclass
class MuscleLandmarks:
    muscle: str
    mv: int
    mev: int
    mav_low: int
    mav_high: int
    mrv: int
    sets: float | None = None
    band: str | None = None
    verdict: str | None = None


def landmarks_for(muscle: str, sets: float | None = None) -> MuscleLandmarks:
    """Look up the landmark row for one muscle, optionally auditing a set count."""
    key = resolve_muscle(muscle)
    mv, mev, mav_lo, mav_hi, mrv = LANDMARKS[key]
    result = MuscleLandmarks(muscle=key, mv=mv, mev=mev, mav_low=mav_lo, mav_high=mav_hi, mrv=mrv)
    if sets is not None:
        result.sets = sets
        result.band = band_for(key, sets)
        result.verdict = BAND_LONG[result.band]
    return result
