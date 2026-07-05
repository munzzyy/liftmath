"""liftmath - evidence-based strength training math, pure Python stdlib.

This package is the calculator, not the coach. It estimates one-rep maxes,
builds percentage-based load charts, looks up and audits weekly volume
landmarks per muscle group, ramps a mesocycle, sets protein/calorie/macro
targets, and does plate/warm-up math. Every formula and heuristic is cited
in the module it lives in.

None of this is medical or nutrition advice. See the README.
"""

from liftmath._serialize import to_dict, to_json
from liftmath.loads import load_chart, pct_to_reps, reps_to_pct, target_load
from liftmath.macros import MacroTargets, macro_targets
from liftmath.mesocycle import ramp_mesocycle
from liftmath.onerm import OneRmEstimate, estimate_one_rm
from liftmath.plates import PlateLoad, load_plates
from liftmath.program import ExerciseSet, audit_program
from liftmath.standards import StrengthScore, dots_score, ipf_gl_points, score, wilks_score
from liftmath.volume import LANDMARKS, MUSCLES, band_for, describe_band, resolve_muscle
from liftmath.warmup import warmup_ramp

__version__ = "0.1.0"

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
    "load_plates",
    "PlateLoad",
    "warmup_ramp",
    "score",
    "StrengthScore",
    "wilks_score",
    "dots_score",
    "ipf_gl_points",
    "to_dict",
    "to_json",
    "__version__",
]
