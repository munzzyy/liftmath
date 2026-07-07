"""RPE/RIR <-> %1RM, derived from the same Epley-based model as loads.py.

RPE (Rating of Perceived Exertion, Borg CR-10 style, 10 = failure) and RIR
(Reps In Reserve) are the same axis by definition: RPE = 10 - RIR (Zourdos
et al., 2016). This module exposes that axis directly for the reps/target
commands, which already do %1RM<->reps<->RIR internally but didn't surface
an RPE label.

Provenance note - read this before trusting the grid as "the RPE chart":
the widely-circulated RTS/Tuchscherer RPE-to-%1RM chart is NOT primarily RCT
data. Zourdos et al. (2016, J Strength Cond Res, 29 trained squatters) only
directly measured THREE points: a 1RM (100%, RPE 10, 0 RIR, by definition),
a single rep at 90% 1RM (reported ~RPE 9-9.5), and an 8-rep set at 70% 1RM
(reported ~RPE 7). Every other cell in the popular grids is either Helms et
al.'s (2016) estimation built around those anchors, or Tuchscherer's own
practitioner chart - which Reactive Training Systems' own site describes as
"determined entirely from Tuchscherer's practical experience coaching
hundreds of athletes," not a validated dataset. That's a tier-4 (expert
consensus / practitioner heuristic) source for most of the grid, not tier-2.

Rather than hand-copy that secondhand chart (and risk it quietly disagreeing
with this library's own Epley-based reps<->%1RM conversion elsewhere), this
module derives RPE/RIR the same way `loads.target_load` already does: RIR
converts to an effective max-rep count, and the existing inverse-Epley
`reps_to_pct` converts that to %1RM. This keeps one internally-consistent
rep-max model instead of two tables that will occasionally disagree, at the
cost of being an extrapolation past reps ~1-8 rather than measured data.

Evidence grade: emerging for the 3 real Zourdos anchor points, blended with
speculative-labeled Epley extrapolation for every other cell. Say so in any
CLI/consumer-facing output, same as `cmd_1rm` already flags high-rep
uncertainty.

Sources:
    Zourdos, M.C. et al. (2016). Novel Resistance Training-Specific Rating
        of Perceived Exertion Scale Measuring Repetitions in Reserve.
        Journal of Strength and Conditioning Research, 30(1), 267-275.
    Helms, E.R. et al. (2016). Application of the Repetitions in Reserve-
        Based Rating of Perceived Exertion Scale for Resistance Training.
        Strength and Conditioning Journal, 38(4), 42-49.
"""

from __future__ import annotations

from dataclasses import dataclass

from liftmath.loads import pct_to_reps, reps_to_pct

# The only 3 points Zourdos (2016) actually measured, kept here purely as an
# informational sanity check (see test_rpe.py), never as hardcoded table cells.
ZOURDOS_2016_ANCHORS = {
    "1rm": {"pct_1rm": 1.00, "rpe": 10.0, "rir": 0},
    "single_at_90pct": {"pct_1rm": 0.90, "rpe_approx": 9.25, "rir_approx": 0.75},
    "eight_at_70pct": {"pct_1rm": 0.70, "rpe_approx": 7.0, "rir_approx": 3.0},
}


def rpe_to_rir(rpe: float) -> float:
    """RIR from RPE, by definition (Zourdos 2016): RIR = 10 - RPE."""
    return 10.0 - rpe


def rir_to_rpe(rir: float) -> float:
    """RPE from RIR, by definition (Zourdos 2016): RPE = 10 - RIR."""
    return 10.0 - rir


@dataclass
class RpeEstimate:
    """%1RM estimated from reps performed + RPE (or RIR), Epley-derived."""

    reps: int
    rpe: float
    rir: float
    pct_1rm: float
    is_extrapolated: bool = True


def pct_1rm_from_reps_and_rpe(reps: int, rpe: float) -> RpeEstimate:
    """%1RM for `reps` performed at a given RPE (Epley-derived, see module docstring).

    A single rep at RPE 10 (0 RIR) is the definitional 1RM anchor (Zourdos
    2016) and is special-cased to exactly 100% rather than run through the
    Epley inversion, matching how `onerm.estimate_one_rm` already treats a
    1-rep set as exact rather than an estimate.

    Args:
        reps: reps actually performed in the set.
        rpe: rated exertion for that set, 0-10 (10 = failure).

    Raises:
        ValueError: if reps < 1 or rpe is outside 0-10.
    """
    if reps < 1:
        raise ValueError("reps must be >= 1")
    if not 0 <= rpe <= 10:
        raise ValueError("rpe must be between 0 and 10")
    rir = rpe_to_rir(rpe)
    if reps == 1 and rir == 0:
        return RpeEstimate(reps=reps, rpe=rpe, rir=rir, pct_1rm=1.0, is_extrapolated=False)
    effective_max_reps = reps + rir
    pct = reps_to_pct(effective_max_reps)
    return RpeEstimate(reps=reps, rpe=rpe, rir=rir, pct_1rm=pct)


def pct_1rm_from_reps_and_rir(reps: int, rir: float) -> RpeEstimate:
    """%1RM for `reps` performed at a given RIR. Same math as the RPE form."""
    return pct_1rm_from_reps_and_rpe(reps, rir_to_rpe(rir))


@dataclass
class RepsRpeEstimate:
    """RPE/RIR estimated from reps performed + a known %1RM, Epley-derived."""

    reps: int
    pct_1rm: float
    rpe: float
    rir: float
    is_extrapolated: bool = True


def rpe_from_reps_and_pct(reps: int, pct_1rm: float) -> RepsRpeEstimate:
    """RPE/RIR for a set of `reps` at a known `pct_1rm` (Epley-derived, see docstring).

    A single rep at 100% 1RM is the definitional RPE-10/0-RIR anchor
    (Zourdos 2016) and is special-cased rather than run through the Epley
    inversion, same as `pct_1rm_from_reps_and_rpe`.

    Args:
        reps: reps actually performed.
        pct_1rm: fraction of 1RM used for the set (e.g. 0.80 for 80%).

    Raises:
        ValueError: if reps < 1 or pct_1rm is outside (0, 1].
    """
    if reps < 1:
        raise ValueError("reps must be >= 1")
    if not 0 < pct_1rm <= 1:
        raise ValueError("pct_1rm must be between 0 (exclusive) and 1 (inclusive)")
    if reps == 1 and pct_1rm >= 1.0:
        return RepsRpeEstimate(reps=reps, pct_1rm=pct_1rm, rpe=10.0, rir=0.0, is_extrapolated=False)
    max_reps_at_pct = pct_to_reps(pct_1rm)
    rir = max(0.0, max_reps_at_pct - reps)
    rpe = rir_to_rpe(rir)
    return RepsRpeEstimate(reps=reps, pct_1rm=pct_1rm, rpe=rpe, rir=rir)
