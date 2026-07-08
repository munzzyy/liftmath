"""liftmath - evidence-based strength training math, pure Python stdlib.

This package is the calculator, not the coach. It estimates one-rep maxes
(with an RPE/RIR axis, and a weighted-bodyweight-movement variant for
pull-ups/dips), builds percentage-based load charts, looks up and audits
weekly volume landmarks per muscle group, ramps a mesocycle, tracks double
progression, sets protein/calorie/macro targets (including a lean-mass-based
Cunningham TDEE alternative and bulk/cut rate targets), computes body
composition (FFMI, Navy tape body-fat %, Jackson-Pollock skinfold + Siri),
tracks session load/monotony/strain and tonnage (volume-load), scores
relative strength (Wilks original + 2020, DOTS, IPF GL, McCulloch age
adjustment), scores squat/bench/deadlift lift-ratio symmetry, computes
training maxes and named program templates (5/3/1, GZCLP, nSuns), does
plate/warm-up math (including a finite-inventory plate solver), looks up
Prilepin's table and INOL, recommends powerlifting meet attempts, detects
e1RM PRs, tracks gym-culture milestones (clubs), and estimates muscle-gain
rate. Every formula and heuristic is cited in the module it lives in, with
an explicit evidence-tier note (established / emerging / speculative /
practitioner consensus) wherever the provenance isn't a straightforward
peer-reviewed finding. A plain-English glossary (`glossary.py`) defines
every piece of jargon this package uses, beginner-friendly first and
technical second.

None of this is medical or nutrition advice. See the README.
"""

from liftmath._serialize import to_dict, to_json
from liftmath.attempts import (
    OPENER_PCT,
    OPENER_RANGE_PCT,
    SECOND_PCT,
    SECOND_RANGE_PCT,
    THIRD_PCT,
    AttemptSelection,
    attempt_selection,
)
from liftmath.bodycomp import FfmiResult, NavyBodyFatResult, ffmi, navy_body_fat
from liftmath.bodyweight import MOVEMENTS, WeightedBodyweightEstimate, weighted_bodyweight_one_rm
from liftmath.bulkcut import TIERS, RateTarget, rate_target
from liftmath.clubs import CULTURE_CAVEAT, ClubProgress, ClubsReport, evaluate_clubs
from liftmath.gainrate import (
    ARAGON_HELMS_MONTHLY_PCT_BW,
    LEVELS,
    MCDONALD_YEARLY_LB,
    GainRateEstimate,
    gain_rate,
)
from liftmath.glossary import GLOSSARY, Term, glossary_entry
from liftmath.loads import load_chart, pct_to_reps, reps_to_pct, target_load
from liftmath.macros import CunninghamTdee, MacroTargets, cunningham_tdee, macro_targets
from liftmath.mesocycle import ramp_mesocycle
from liftmath.onerm import OneRmEstimate, estimate_one_rm
from liftmath.plates import InventoryPlateLoad, PlateLoad, load_plates, load_plates_from_inventory
from liftmath.pr import PrCheck, check_pr
from liftmath.prilepin import (
    PRILEPIN_CAVEAT,
    ZONES,
    InolGroup,
    InolResult,
    PrilepinZone,
    SchemeEvaluation,
    classify_weekly_inol,
    classify_workout_inol,
    evaluate_scheme,
    inol_of_set,
    inol_total,
    zone_for_pct,
)
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
from liftmath.skinfold import (
    SkinfoldResult,
    jackson_pollock_men_3site,
    jackson_pollock_men_7site,
    jackson_pollock_women_3site,
    jackson_pollock_women_7site,
    siri_bodyfat_pct,
)
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
from liftmath.symmetry import EXPECTED_RATIOS, LiftRatio, SymmetryReport, score_symmetry
from liftmath.templates import (
    T1_STAGES,
    T2_STAGES,
    GzclpSession,
    NsunsDay,
    ProgramSet,
    ProgramWeek,
    TrainingMax,
    gzclp_next_session,
    nsuns_day,
    program_531,
    round_to_increment,
    training_max,
)
from liftmath.tiers import (
    MEN_TOTAL_KG,
    TIER_NAMES,
    WOMEN_TOTAL_KG,
    TierResult,
    TierThresholds,
    classify_tier,
    thresholds_at_bodyweight,
)
from liftmath.tonnage import TonnageReport, TonnageSet, session_tonnage
from liftmath.volume import LANDMARKS, MUSCLES, band_for, describe_band, resolve_muscle
from liftmath.warmup import warmup_ramp

__version__ = "1.4.0"

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
    "load_plates_from_inventory",
    "InventoryPlateLoad",
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
    "weighted_bodyweight_one_rm",
    "WeightedBodyweightEstimate",
    "MOVEMENTS",
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
    "score_symmetry",
    "SymmetryReport",
    "LiftRatio",
    "EXPECTED_RATIOS",
    "round_to_increment",
    "training_max",
    "TrainingMax",
    "program_531",
    "ProgramWeek",
    "ProgramSet",
    "gzclp_next_session",
    "GzclpSession",
    "T1_STAGES",
    "T2_STAGES",
    "nsuns_day",
    "NsunsDay",
    "thresholds_at_bodyweight",
    "classify_tier",
    "TierThresholds",
    "TierResult",
    "TIER_NAMES",
    "MEN_TOTAL_KG",
    "WOMEN_TOTAL_KG",
    "to_dict",
    "to_json",
    "GLOSSARY",
    "Term",
    "glossary_entry",
    "zone_for_pct",
    "evaluate_scheme",
    "PrilepinZone",
    "SchemeEvaluation",
    "ZONES",
    "inol_of_set",
    "inol_total",
    "classify_workout_inol",
    "classify_weekly_inol",
    "InolGroup",
    "InolResult",
    "PRILEPIN_CAVEAT",
    "attempt_selection",
    "AttemptSelection",
    "OPENER_PCT",
    "SECOND_PCT",
    "THIRD_PCT",
    "OPENER_RANGE_PCT",
    "SECOND_RANGE_PCT",
    "jackson_pollock_men_3site",
    "jackson_pollock_men_7site",
    "jackson_pollock_women_3site",
    "jackson_pollock_women_7site",
    "siri_bodyfat_pct",
    "SkinfoldResult",
    "session_tonnage",
    "TonnageSet",
    "TonnageReport",
    "check_pr",
    "PrCheck",
    "evaluate_clubs",
    "ClubProgress",
    "ClubsReport",
    "CULTURE_CAVEAT",
    "gain_rate",
    "GainRateEstimate",
    "LEVELS",
    "ARAGON_HELMS_MONTHLY_PCT_BW",
    "MCDONALD_YEARLY_LB",
    "__version__",
]
