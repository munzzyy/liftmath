import pytest

from liftmath.clubs import CULTURE_CAVEAT, evaluate_clubs


def test_plate_club_thresholds_lb():
    r = evaluate_clubs(squat=300, bench=200, deadlift=350, ohp=100, unit="lb")
    thresholds = {c.name: c.threshold for c in r.plate_clubs}
    assert thresholds == {"1-plate": 135.0, "2-plate": 225.0, "3-plate": 315.0, "4-plate": 405.0}


def test_plate_club_achieved_flags():
    r = evaluate_clubs(squat=315, bench=225, deadlift=400, ohp=135, unit="lb")
    achieved = {c.name: c.achieved for c in r.plate_clubs}
    assert achieved == {"1-plate": True, "2-plate": True, "3-plate": True, "4-plate": False}


def test_plate_club_remaining():
    r = evaluate_clubs(squat=300, bench=200, deadlift=350, unit="lb")
    by_name = {c.name: c for c in r.plate_clubs}
    assert by_name["2-plate"].remaining == pytest.approx(25.0)  # 225 - 200
    assert by_name["3-plate"].remaining == pytest.approx(15.0)  # 315 - 300
    assert by_name["4-plate"].remaining == pytest.approx(55.0)  # 405 - 350


def test_ohp_club_omitted_without_ohp():
    r = evaluate_clubs(squat=300, bench=200, deadlift=350, unit="lb")
    names = [c.name for c in r.plate_clubs]
    assert "1-plate" not in names
    assert len(r.plate_clubs) == 3


def test_thousand_lb_club_threshold_and_achieved():
    r = evaluate_clubs(squat=405, bench=315, deadlift=495, unit="lb")
    assert r.thousand_lb_club.threshold == pytest.approx(1000.0)
    assert r.thousand_lb_club.current == pytest.approx(405 + 315 + 495)
    assert r.thousand_lb_club.achieved is True


def test_thousand_lb_club_not_achieved():
    r = evaluate_clubs(squat=200, bench=150, deadlift=250, unit="lb")
    assert r.thousand_lb_club.achieved is False
    assert r.thousand_lb_club.remaining == pytest.approx(1000 - 600)


def test_thousand_lb_club_kg_conversion():
    r = evaluate_clubs(squat=200, bench=150, deadlift=250, unit="kg")
    assert r.thousand_lb_club.threshold == pytest.approx(1000.0 * 0.45359237)


def test_two_three_four_club_achieved():
    r = evaluate_clubs(squat=315, bench=225, deadlift=405, unit="lb")
    assert r.two_three_four_club_achieved is True


def test_two_three_four_club_not_achieved_when_one_lift_short():
    r = evaluate_clubs(squat=315, bench=220, deadlift=405, unit="lb")
    assert r.two_three_four_club_achieved is False


def test_plate_club_kg_conversion():
    r = evaluate_clubs(squat=150, bench=100, deadlift=180, unit="kg")
    by_name = {c.name: c for c in r.plate_clubs}
    assert by_name["2-plate"].threshold == pytest.approx(225.0 * 0.45359237)
    assert by_name["3-plate"].threshold == pytest.approx(315.0 * 0.45359237)


def test_caveat_present_and_honest():
    r = evaluate_clubs(squat=300, bench=200, deadlift=350, unit="lb")
    assert r.caveat == CULTURE_CAVEAT
    assert "not sanctioned" in r.caveat.lower() or "no governing body" in r.caveat.lower()


def test_rejects_bad_unit():
    with pytest.raises(ValueError):
        evaluate_clubs(squat=300, bench=200, deadlift=350, unit="stone")


def test_rejects_nonpositive_lifts():
    with pytest.raises(ValueError):
        evaluate_clubs(squat=0, bench=200, deadlift=350)
    with pytest.raises(ValueError):
        evaluate_clubs(squat=300, bench=-1, deadlift=350)


def test_rejects_nonpositive_ohp():
    with pytest.raises(ValueError):
        evaluate_clubs(squat=300, bench=200, deadlift=350, ohp=0)
