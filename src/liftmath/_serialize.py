"""Shared dataclass -> dict/JSON helper for the public result types.

Every public function in liftmath returns a plain @dataclass (OneRmEstimate,
PlateLoad, InventoryPlateLoad, StrengthScore, Record, WeightConversion,
WorkoutSet). This module turns any of them into a plain dict (or a JSON
string) suitable for logging, an API response, or the CLI's --json flag,
without callers having to hand-roll dataclasses.asdict()
and remember to include the read-only @property values (like PlateLoad.exact
or OneRmEstimate.is_exact) that asdict() alone would drop.
"""

from __future__ import annotations

import dataclasses
import json
from typing import Any


def to_dict(obj: Any) -> Any:
    """Recursively convert a dataclass (or a list/dict/tuple of them) to plain dicts.

    Nested dataclasses, lists, dicts, and tuples are all handled. Read-only
    properties defined on a dataclass (e.g. `is_exact`, `exact`, `achievable`)
    are included alongside its fields so the JSON output carries the same
    derived info the human-readable CLI text does. Tuples are converted to
    lists (JSON has no tuple type).
    """
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        result = {f.name: to_dict(getattr(obj, f.name)) for f in dataclasses.fields(obj)}
        for name in dir(type(obj)):
            attr = getattr(type(obj), name, None)
            if isinstance(attr, property) and name not in result:
                result[name] = to_dict(getattr(obj, name))
        return result
    if isinstance(obj, dict):
        return {k: to_dict(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_dict(v) for v in obj]
    return obj


def to_json(obj: Any, **kwargs: Any) -> str:
    """Serialize a dataclass (or nested structure of them) straight to a JSON string.

    Extra keyword arguments are passed through to `json.dumps` (e.g. `indent=2`).
    """
    kwargs.setdefault("indent", 2)
    return json.dumps(to_dict(obj), **kwargs)
