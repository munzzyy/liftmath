"""liftmath - a simple gym calculator, pure Python stdlib.

Three things, done well, that you actually reach for at the gym:

  - estimate a one-rep max from a weight x reps set (six validated formulas,
    reported with their median consensus and range),
  - work out which plates to load for a target barbell weight (with a
    finite-inventory solver for home gyms and travel kits), and
  - score relative strength across bodyweights with Wilks (original + 2020),
    DOTS, and IPF GL points.

Plus one lookup: records for powerlifting (computed from the OpenPowerlifting
public-domain database), strongman and grip sport (hand-curated with
citations), and track & field (world / US collegiate / US high-school
levels), searchable by lift/event, sex, weight class, equipment, and level
(`search_records`, `percent_of_record`, `weight_class_for`, `parse_mark`,
`format_seconds`).

And one small utility the others lean on: exact lb<->kg conversion
(`convert_weight`, `lbs_to_kg`, `kg_to_lbs`), the same 0.45359237 factor
`standards.py` already needed for its own unit handling.

Plus importing your own workout history from a Strong or Hevy CSV export
(`parse_strong_csv`, `parse_hevy_csv`), turned into e1RM trend and weekly
tonnage (`e1rm_trend`, `weekly_tonnage`) - the two things a single set can't
tell you that a logged history can.

Every formula is cited in the module it lives in. Nothing here is medical or
nutrition advice - see the README.
"""

from liftmath._serialize import to_dict, to_json
from liftmath.convert import WeightConversion, convert_weight, kg_to_lbs, lbs_to_kg
from liftmath.imports import (
    WorkoutSet,
    e1rm_trend,
    parse_hevy_csv,
    parse_strong_csv,
    weekly_tonnage,
)
from liftmath.onerm import OneRmEstimate, estimate_one_rm
from liftmath.plates import (
    InventoryPlateLoad,
    PlateLoad,
    load_plates,
    load_plates_from_inventory,
)
from liftmath.records import (
    Record,
    format_seconds,
    parse_mark,
    percent_of_record,
    records_as_of,
    search_records,
    weight_class_for,
)
from liftmath.standards import (
    StrengthScore,
    dots_score,
    ipf_gl_points,
    score,
    wilks_original_score,
    wilks_score,
)

__version__ = "2.4.0"

__all__ = [
    "estimate_one_rm",
    "OneRmEstimate",
    "load_plates",
    "PlateLoad",
    "load_plates_from_inventory",
    "InventoryPlateLoad",
    "score",
    "StrengthScore",
    "search_records",
    "Record",
    "percent_of_record",
    "weight_class_for",
    "records_as_of",
    "parse_mark",
    "format_seconds",
    "wilks_score",
    "wilks_original_score",
    "dots_score",
    "ipf_gl_points",
    "lbs_to_kg",
    "kg_to_lbs",
    "convert_weight",
    "WeightConversion",
    "to_dict",
    "to_json",
    "WorkoutSet",
    "parse_strong_csv",
    "parse_hevy_csv",
    "e1rm_trend",
    "weekly_tonnage",
    "__version__",
]
