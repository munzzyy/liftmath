
from liftmath.warmup import warmup_ramp


def test_275lb_ramp_reference_values():
    # bar=45, steps rounded to nearest 5lb: 45, 140, 190, 235, 260
    ramp = warmup_ramp(275, unit="lb")
    loads = [s.load for s in ramp.steps]
    assert loads == [45, 140, 190, 235, 260]


def test_100kg_ramp_reference_values():
    # bar=20, steps rounded to nearest 2.5kg: 20, 50, 70, 85, 95
    ramp = warmup_ramp(100, unit="kg")
    loads = [s.load for s in ramp.steps]
    assert loads == [20.0, 50.0, 70.0, 85.0, 95.0]


def test_bar_step_never_below_bar_weight():
    ramp = warmup_ramp(50, unit="lb")  # a very light working weight
    assert all(s.load >= ramp.bar for s in ramp.steps)


def test_custom_bar_weight_is_respected():
    ramp = warmup_ramp(275, unit="lb", bar=35)
    assert ramp.bar == 35
    assert ramp.steps[0].load == 35
