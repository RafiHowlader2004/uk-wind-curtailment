from datetime import datetime, timedelta, timezone

import pytest

from src.curtailment import Segment, curtailment_mwh, parse_segments

T0 = datetime(2026, 9, 16, 12, 0, tzinfo=timezone.utc)
HOUR = timedelta(hours=1)


def test_flat_reduction():
    """Planned 100 MW, instructed 30 MW, for an hour -> 70 MWh lost."""
    pn = [Segment(T0, T0 + HOUR, 100, 100)]
    boal = [Segment(T0, T0 + HOUR, 30, 30)]
    assert curtailment_mwh(pn, boal) == pytest.approx(70.0, abs=0.1)


def test_no_instruction_means_no_curtailment():
    pn = [Segment(T0, T0 + HOUR, 100, 100)]
    assert curtailment_mwh(pn, []) == 0.0


def test_instruction_above_plan_is_not_curtailment():
    """Being told to generate MORE is an offer, not curtailment."""
    pn = [Segment(T0, T0 + HOUR, 50, 50)]
    boal = [Segment(T0, T0 + HOUR, 90, 90)]
    assert curtailment_mwh(pn, boal) == 0.0


def test_ramped_instruction():
    """Ramp 100 -> 0 against a flat 100 MW plan: average gap 50 MW."""
    pn = [Segment(T0, T0 + HOUR, 100, 100)]
    boal = [Segment(T0, T0 + HOUR, 100, 0)]
    assert curtailment_mwh(pn, boal) == pytest.approx(50.0, abs=0.5)


def test_parse_segments_sorts_by_time():
    rows = [
        {"timeFrom": "2026-09-16T06:00:00Z", "timeTo": "2026-09-16T06:29:00Z",
         "levelFrom": 80, "levelTo": 80},
        {"timeFrom": "2026-09-16T05:30:00Z", "timeTo": "2026-09-16T05:59:00Z",
         "levelFrom": 87, "levelTo": 87},
    ]
    segments = parse_segments(rows)
    assert segments[0].level_from == 87
    assert segments[1].level_from == 80


def test_later_acceptance_wins_where_they_overlap():
    """Re-instructed mid-hour: the newer acceptance governs the overlap."""
    pn = [Segment(T0, T0 + HOUR, 100, 100)]
    boal = [
        Segment(T0, T0 + HOUR, 60, 60, priority=1),
        Segment(T0 + HOUR / 2, T0 + HOUR, 20, 20, priority=2),
    ]
    # first half: gap 40 MW for 0.5h = 20 MWh
    # second half: gap 80 MW for 0.5h = 40 MWh
    assert curtailment_mwh(pn, boal) == pytest.approx(60.0, abs=0.5)
