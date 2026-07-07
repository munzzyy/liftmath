"""liftmath - evidence-based strength training math, pure Python stdlib.

This package is the calculator, not the coach. It estimates one-rep maxes
(with an RPE/RIR axis), builds percentage-based load charts, looks up and
audits weekly volume landmarks per muscle group, ramps a mesocycle, tracks
double progression, sets protein/calorie/macro targets (including a
lean-mass-based Cunningham TDEE alternative and bulk/cut rate targets),
computes body composition (FFMI, Navy tape body-fat %), tracks session
load/monotony/strain, scores relative strength (Wilks original + 2020, DOTS,
IPF GL, McCulloch age adjustment), and does plate/warm-up math. Every
formula and heuristic is cited in the module it lives in, with an explicit
evidence-tier note (established / emerging / speculative / practitioner
consensus) wherever the provenance isn't a straightforward peer-reviewed
finding.

None of this is medical or nutrition advice. See the README.
"""

from liftmath._serialize import to_dict, to_json
from liftmath.bodycomp import FfmiResult, NavyBodyFatResult, ffmi, navy_body_fat
from liftmath.bulkcut import TIERS, RateTarget, rate_target
from liftmath.loads import load_chart, pct_to_reps, reps_to_pct, target_load
from liftmath.macros import CunninghamTdee, MacroTargets, cunningham_tdee, macro_targets
from liftmath.mesocycle import ramp_mesocycle
from liftmath.onerm import OneRmEstimate, estimate_one_rm
from liftmath.plates import PlateLoad, load_plates
from liftmath.program import ExerciseSet, audit_program
from liftmath.progression import ProgressionStep, next_progression_step
from liftmath.rpe import (
    RepsRpeEstimate,
    RpeEstimate,
    pct_1rm_from_reps_and_rir,
    pct_1rm_from_reps_and_rpe,
    rir_to_rpe,
    rpe_from_reps_and_pct,
    rpe_to_rir,
)
from liftmath.sessionload import WeeklyLoad, session_load, weekly_load
from liftmath.standards import (
    MastersScore,
    StrengthScore,
    dots_score,
    ipf_gl_points,
    mcculloch_coefficient,
    mcculloch_score,
    score,
    wilks_original_score,
    wilks_score,
)
from liftmath.volume import LANDMARKS, MUSCLES, band_for, describe_band, resolve_muscle
from liftmath.warmup import warmup_ramp

__version__ = "1.0.0"

__all__ = [
    "estimate_one_rm",
    "OneRmEstimate",
    "pct_to_reps",
    "reps_to_pct",
    "load_chart",
    "target_load",
    "LANDMARKS",
    "MUSCLES",
    "band_for",
    "describe_band",
    "resolve_muscle",
    "audit_program",
    "ExerciseSet",
    "ramp_mesocycle",
    "macro_targets",
    "MacroTargets",
    "cunningham_tdee",
    "CunninghamTdee",
    "load_plates",
    "PlateLoad",
    "warmup_ramp",
    "score",
    "StrengthScore",
    "wilks_score",
    "wilks_original_score",
    "dots_score",
    "ipf_gl_points",
    "mcculloch_coefficient",
    "mcculloch_score",
    "MastersScore",
    "ffmi",
    "FfmiResult",
    "navy_body_fat",
    "NavyBodyFatResult",
    "session_load",
    "weekly_load",
    "WeeklyLoad",
    "next_progression_step",
    "ProgressionStep",
    "rate_target",
    "RateTarget",
    "TIERS",
    "pct_1rm_from_reps_and_rpe",
    "pct_1rm_from_reps_and_rir",
    "rpe_from_reps_and_pct",
    "rpe_to_rir",
    "rir_to_rpe",
    "RpeEstimate",
    "RepsRpeEstimate",
    "to_dict",
    "to_json",
    "__version__",
]
