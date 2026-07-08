"""Prilepin's table + INOL - both from the same Hristov (2005) primary source.

Prilepin's table bands %1RM into four intensity zones, each with a
per-set rep range, a total-rep range for the session, and an "optimal"
total rep count. INOL (Hristov's own follow-up invention, same paper) fixes
the table's blind spot at zone boundaries: it's a single continuous number -
reps / (100 - %1RM), summed across sets - that lets you compare training
stress across DIFFERENT intensities on one scale instead of four disjoint
buckets.

Source (quoted verbatim where noted - read directly, full text):
    Hristov, H. (2005). "How to Design Strength Training Programs using
    Prilepin's Table." Originally published on Powerlifting Watch; archived
    copy at liftvault.com/wp-content/uploads/2024/02/prelipins.pdf.

    Prilepin's table, as printed (%1RM / rep range per set / total rep
    range / optimal total reps):
        <70%      3-6 reps/set   18-30 total   24 optimal
        70-79%    3-6 reps/set   12-24 total   18 optimal
        80-89%    2-4 reps/set   10-20 total   15 optimal
        >89%      1-2 reps/set    4-10 total    7 optimal

    Hristov's own framing (verbatim): "During the sixties and seventies of
    the 20th century, Soviet sports scientist A.S. Prilepin collected data
    from the training logs of more than 1000 World, Olympic, National and
    European weightlifting champions." This is a SECONDARY account of
    Prilepin's own Soviet-era work - no English translation of Prilepin's
    original publication was locatable when this module was written; the
    usual scholarly pointer is Prilepin via Laputin & Oleshko and via
    A.S. Medvedev's compilations, neither digitized/accessible. Every
    gym-facing reproduction of this table (70sBig, LiftVault,
    PowerliftingTechnique, T-Nation, EliteFTS, etc.) traces back to this
    same Hristov transcription, not to an independently-verified Prilepin
    original - well-corroborated by convergent secondary citation, but
    ultimately resting on one transcription chain.

    INOL formula (Hristov's own invention, same paper, exact): "INOL of a
    set = Number of Lifts (NOL) at a given intensity / (100 - intensity)" -
    i.e. INOL = reps / (100 - %1RM) for one set, summed across every set/
    exercise in scope.

    INOL bands, verbatim from the PDF:
        per-workout (one exercise, one session):
            <0.4    "too few reps, not enough stimulus?"
            0.4-1   "fresh, quite doable and optimal if you are not
                     accumulating fatigue"
            1-2     "tough, but good for loading phases"
            >2      "brutal"
        weekly (one exercise, summed across the week):
            <2      "easy, doable, good to do after more tiring weeks and
                     prepeaking"
            2-3     "tough but doable, good for loading phases between"
            3-4     "brutal, lots of fatigue, good for a limited time and
                     shock microcycles"
            >4      "Are you out of your mind?"

    Worked examples, pinned as this module's own test fixtures (same PDF):
        Bench Press 2x6@60%, 5x3@75% -> INOL = 2*(6/40) + 5*(3/25)
            = 0.3 + 0.6 = 0.9
        6x4@72% -> INOL = 24/28 = 0.86 (rounded)
        6x4@77% -> INOL = 24/23 = 1.04 (rounded)

    ADVERSARIAL-VERIFICATION NOTE: a different secondary site
    (olyliftplan.com) circulates DIFFERENT weekly INOL bands under a
    citation reading "Hristov, H. (2005). Functional periodization: INOL
    and practical application in weightlifting programming. Unpublished
    coaching manuscript" - that title and "unpublished" status don't match
    the real paper (real title above, published on Powerlifting Watch, not
    unpublished). That variant is treated as fabricated/derivative and NOT
    used here; the bands above are sourced directly from the primary PDF.

CAVEAT (surface this wherever this module's output surfaces - see
PRILEPIN_CAVEAT below): the table is derived from Olympic weightlifting
training logs (snatch/clean&jerk), not powerlifting-specific, though decades
of powerlifting-coach use support cross-application. It's also, per the
provenance note above, field consensus transcribed by one author - not an
independently verified original Prilepin document.

Evidence grade: expert-published heuristic (data-log synthesis, not an
RCT) for both the table and INOL - extremely high face-validity and
adoption in the field, but neither is a controlled-trial finding.
"""

from __future__ import annotations

from dataclasses import dataclass, field

PRILEPIN_CAVEAT = (
    "Derived from Olympic weightlifting training logs (snatch/clean&jerk), not powerlifting-"
    "specific - decades of powerlifting-coach use support cross-application, but it wasn't built "
    "from powerlifting data. The table itself is field consensus transcribed by Hristov (2005), "
    "not an independently-verified original Prilepin document (see prilepin.py's module docstring)."
)


@dataclass(frozen=True)
class PrilepinZone:
    """One row of Prilepin's table: a %1RM band and its rep prescriptions."""

    label: str
    min_pct: float
    max_pct: float | None  # None = no ceiling (the >89% zone)
    reps_per_set_low: int
    reps_per_set_high: int
    total_reps_low: int
    total_reps_high: int
    optimal_total_reps: int


# Verbatim from Hristov (2005) - see module docstring. Half-open bins at
# 70/80/90 for continuous %1RM inputs (a value like 89.5 falls in the
# "80-89%" zone, matching how these percentages are used in practice as
# whole numbers); only pct_1rm >= 90 crosses into ">89%".
ZONES: tuple[PrilepinZone, ...] = (
    PrilepinZone("<70%", 0.0, 70.0, 3, 6, 18, 30, 24),
    PrilepinZone("70-79%", 70.0, 80.0, 3, 6, 12, 24, 18),
    PrilepinZone("80-89%", 80.0, 90.0, 2, 4, 10, 20, 15),
    PrilepinZone(">89%", 90.0, None, 1, 2, 4, 10, 7),
)


def zone_for_pct(pct_1rm: float) -> PrilepinZone:
    """Look up the Prilepin zone a %1RM falls in.

    Args:
        pct_1rm: %1RM as a whole number (e.g. 75 for 75%), matching how
            Hristov's own table is printed - not a 0-1 fraction.

    Raises:
        ValueError: if pct_1rm <= 0.
    """
    if pct_1rm <= 0:
        raise ValueError("pct_1rm must be > 0")
    for zone in ZONES:
        if pct_1rm >= zone.min_pct and (zone.max_pct is None or pct_1rm < zone.max_pct):
            return zone
    raise AssertionError("unreachable - ZONES covers every positive pct_1rm")  # pragma: no cover


@dataclass
class SchemeEvaluation:
    """A planned sets x reps @ %1RM scheme, graded against its Prilepin zone."""

    sets: int
    reps: int
    pct_1rm: float
    zone: PrilepinZone
    total_reps: int
    verdict: str  # "under" | "optimal" | "over", vs. the zone's total-rep range
    reps_per_set_in_range: bool
    reps_to_optimal: int  # optimal_total_reps - total_reps (>0 below optimal, <0 above)


def evaluate_scheme(sets: int, reps: int, pct_1rm: float) -> SchemeEvaluation:
    """Grade a sets x reps @ %1RM scheme against Prilepin's zone for that %1RM.

    `verdict` is "under"/"optimal"/"over" relative to the zone's published
    TOTAL-rep range (not the single "optimal" number, which is a specific
    reference point inside that range - see `reps_to_optimal` for distance
    to that exact figure). `reps_per_set_in_range` separately flags whether
    the per-set rep count itself matches the zone's own prescription (e.g.
    doing sets of 8 at 80% is outside that zone's 2-4 rep/set guidance even
    if the total happens to land "optimal").

    Args:
        sets: number of sets in the scheme.
        reps: reps per set.
        pct_1rm: %1RM as a whole number (e.g. 75 for 75%).

    Raises:
        ValueError: if sets <= 0, reps <= 0, or pct_1rm <= 0.
    """
    if sets <= 0:
        raise ValueError("sets must be > 0")
    if reps <= 0:
        raise ValueError("reps must be > 0")
    zone = zone_for_pct(pct_1rm)
    total_reps = sets * reps

    if total_reps < zone.total_reps_low:
        verdict = "under"
    elif total_reps > zone.total_reps_high:
        verdict = "over"
    else:
        verdict = "optimal"

    return SchemeEvaluation(
        sets=sets,
        reps=reps,
        pct_1rm=pct_1rm,
        zone=zone,
        total_reps=total_reps,
        verdict=verdict,
        reps_per_set_in_range=zone.reps_per_set_low <= reps <= zone.reps_per_set_high,
        reps_to_optimal=zone.optimal_total_reps - total_reps,
    )


# --- INOL --------------------------------------------------------------------


def inol_of_set(reps: int, pct_1rm: float) -> float:
    """INOL contributed by ONE set: reps / (100 - %1RM) (Hristov, 2005).

    Args:
        reps: reps performed in the set.
        pct_1rm: %1RM as a whole number (e.g. 75 for 75%), same convention
            as `zone_for_pct` - not a 0-1 fraction.

    Raises:
        ValueError: if reps <= 0, or pct_1rm isn't strictly between 0 and 100.
    """
    if reps <= 0:
        raise ValueError("reps must be > 0")
    if not 0 < pct_1rm < 100:
        raise ValueError("pct_1rm must be between 0 and 100 (exclusive)")
    return reps / (100.0 - pct_1rm)


@dataclass(frozen=True)
class InolGroup:
    """One block of identical sets at the same reps/%1RM, e.g. '5x3@75%'."""

    num_sets: int
    reps: int
    pct_1rm: float

    @property
    def inol(self) -> float:
        """This group's INOL contribution: num_sets * inol_of_set(reps, pct_1rm)."""
        return self.num_sets * inol_of_set(self.reps, self.pct_1rm)


# Per-workout and weekly guideline strings, verbatim from Hristov (2005) - see
# module docstring. Each "A-B" printed label is treated as the CLOSED
# interval [A, B]; the band below it is exclusive of A, so e.g. an INOL of
# exactly 0.4 reads as "0.4-1" (not "<0.4"), and exactly 1.0 also reads as
# "0.4-1" (not "1-2") - the next band only starts strictly above its floor.
WORKOUT_UNDER = "too few reps, not enough stimulus?"
WORKOUT_OPTIMAL = "fresh, quite doable and optimal if you are not accumulating fatigue"
WORKOUT_TOUGH = "tough, but good for loading phases"
WORKOUT_BRUTAL = "brutal"

WEEKLY_EASY = "easy, doable, good to do after more tiring weeks and prepeaking"
WEEKLY_TOUGH = "tough but doable, good for loading phases between"
WEEKLY_BRUTAL = "brutal, lots of fatigue, good for a limited time and shock microcycles"
WEEKLY_INSANE = "Are you out of your mind?"


def classify_workout_inol(total_inol: float) -> str:
    """Per-workout INOL guideline string for one exercise's session total (Hristov, 2005)."""
    if total_inol < 0.4:
        return WORKOUT_UNDER
    if total_inol <= 1.0:
        return WORKOUT_OPTIMAL
    if total_inol <= 2.0:
        return WORKOUT_TOUGH
    return WORKOUT_BRUTAL


def classify_weekly_inol(total_inol: float) -> str:
    """Weekly INOL guideline string for one exercise's week total (Hristov, 2005)."""
    if total_inol < 2.0:
        return WEEKLY_EASY
    if total_inol <= 3.0:
        return WEEKLY_TOUGH
    if total_inol <= 4.0:
        return WEEKLY_BRUTAL
    return WEEKLY_INSANE


@dataclass
class InolResult:
    """Total INOL across a set of groups, with both guideline bands attached.

    Both `workout_band` and `weekly_band` are always reported off the SAME
    `total` - it's the caller's context (one session vs. a full week of that
    exercise) that decides which one is the relevant read, not this module.
    """

    groups: list[InolGroup] = field(default_factory=list)
    total: float = 0.0
    workout_band: str = ""
    weekly_band: str = ""


def inol_for_groups(groups: list[InolGroup]) -> InolResult:
    """Sum INOL across `groups` and classify the total against both guideline bands.

    Raises:
        ValueError: if groups is empty, or any group's reps/pct_1rm is invalid
            (see `inol_of_set`).
    """
    if not groups:
        raise ValueError("groups must not be empty")
    total = sum(g.inol for g in groups)
    return InolResult(
        groups=list(groups),
        total=total,
        workout_band=classify_workout_inol(total),
        weekly_band=classify_weekly_inol(total),
    )


def inol_total(specs: list[tuple[int, int, float]]) -> InolResult:
    """Convenience wrapper: build groups from (num_sets, reps, pct_1rm) triples and sum.

    Example: `inol_total([(2, 6, 60), (5, 3, 75)])` reproduces Hristov's own
    worked example (2x6@60%, 5x3@75% -> INOL 0.9).

    Raises:
        ValueError: if specs is empty, or any triple is invalid (see
            `inol_of_set`).
    """
    groups = [InolGroup(num_sets=n, reps=r, pct_1rm=p) for n, r, p in specs]
    return inol_for_groups(groups)
