import json

import pytest

from liftmath._serialize import to_dict, to_json
from liftmath.onerm import estimate_one_rm
from liftmath.plates import load_plates
from liftmath.program import ExerciseSet, audit_program


def test_to_dict_plain_dataclass_includes_fields():
    est = estimate_one_rm(225, 5, unit="lb")
    d = to_dict(est)
    assert d["weight"] == 225
    assert d["reps"] == 5
    assert d["per_formula"]["Epley"] == pytest.approx(262.5)


def test_to_dict_includes_read_only_properties():
    # is_exact is a @property on OneRmEstimate, not a dataclass field
    est = estimate_one_rm(315, 1, unit="lb")
    d = to_dict(est)
    assert d["is_exact"] is True


def test_to_dict_converts_tuples_in_lists_to_lists():
    result = load_plates(245, unit="lb")
    d = to_dict(result)
    assert d["plates"] == [[45, 2], [10, 1]]
    assert all(isinstance(p, list) for p in d["plates"])
    assert d["exact"] is True


def test_to_dict_handles_nested_dataclasses():
    audit = audit_program([ExerciseSet(name="Bench Press", sets=4, frequency=2)])
    d = to_dict(audit)
    assert isinstance(d["rows"], list)
    assert d["rows"][0]["muscle"] == "chest"


def test_to_json_produces_valid_json_string():
    est = estimate_one_rm(225, 5, unit="lb")
    s = to_json(est)
    assert isinstance(s, str)
    round_tripped = json.loads(s)
    assert round_tripped["reps"] == 5


def test_to_json_passes_through_kwargs():
    est = estimate_one_rm(225, 5, unit="lb")
    compact = to_json(est, indent=None)
    assert "\n" not in compact


def test_to_dict_passthrough_for_plain_values():
    assert to_dict(5) == 5
    assert to_dict("chest") == "chest"
    assert to_dict(None) is None
    assert to_dict([1, 2, 3]) == [1, 2, 3]
    assert to_dict({"a": 1}) == {"a": 1}
