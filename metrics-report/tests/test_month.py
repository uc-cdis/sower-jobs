"""Tests for report months and their UTC bounds."""

from datetime import datetime, timedelta, timezone

import pytest

from metrics_report.month import ReportMonth


@pytest.mark.parametrize(
    "now, expected",
    [
        (datetime(2026, 10, 14, 12, tzinfo=timezone.utc), ReportMonth(2026, 9)),
        (datetime(2026, 1, 3, tzinfo=timezone.utc), ReportMonth(2025, 12)),
        (datetime(2026, 3, 1, tzinfo=timezone.utc), ReportMonth(2026, 2)),
        # 01:00 on Oct 1 at UTC+5 is still Sep 30 in UTC.
        (
            datetime(2026, 10, 1, 1, tzinfo=timezone(timedelta(hours=5))),
            ReportMonth(2026, 8),
        ),
    ],
)
def test_last_full_month_is_the_previous_utc_month(
    now: datetime, expected: ReportMonth
) -> None:
    """The default month is the last calendar month that ended, in UTC."""
    assert ReportMonth.last_full_month(now) == expected


def test_bounds_are_utc_midnights() -> None:
    """A month runs from UTC midnight on the 1st to UTC midnight on the next 1st."""
    month = ReportMonth.parse("2026-09")
    assert (month.start, month.stop) == (
        datetime(2026, 9, 1, tzinfo=timezone.utc),
        datetime(2026, 10, 1, tzinfo=timezone.utc),
    )


def test_december_stops_at_next_january() -> None:
    """December's stop bound rolls over into the next year."""
    assert ReportMonth(2026, 12).stop == datetime(2027, 1, 1, tzinfo=timezone.utc)


def test_label_is_zero_padded() -> None:
    """The label used in file names is `YYYY-MM`."""
    assert ReportMonth(2026, 3).label == "2026-03"


@pytest.mark.parametrize(
    "value",
    [
        "2026-13",
        "2026-00",
        "2026-9",
        "26-09",
        "2026-09-01",
        "",
        "２０２６-09",  # full-width digits
    ],
)
def test_parse_rejects_invalid_months(value: str) -> None:
    """Anything other than a `YYYY-MM` month from 01 to 12 is rejected."""
    with pytest.raises(ValueError):
        ReportMonth.parse(value)


@pytest.mark.parametrize(
    "now, ended",
    [
        (datetime(2026, 10, 1, tzinfo=timezone.utc), True),
        (datetime(2026, 9, 30, 23, 59, 59, tzinfo=timezone.utc), False),
    ],
)
def test_has_ended_at_the_stop_bound(now: datetime, ended: bool) -> None:
    """A month has ended once `now` reaches its exclusive stop bound."""
    assert ReportMonth(2026, 9).has_ended(now) is ended
