"""Calendar months that a report covers, bounded by UTC midnights."""

import re
from dataclasses import dataclass
from datetime import datetime, timezone

MONTH_PATTERN = re.compile(r"(\d{4})-(\d{2})", re.ASCII)


@dataclass(frozen=True)
class ReportMonth:
    """One calendar month, from UTC midnight on the 1st to UTC midnight on the next 1st."""

    year: int
    month: int

    def __post_init__(self) -> None:
        if not 1 <= self.month <= 12:
            raise ValueError(f"Month must be between 1 and 12, got {self.month}")

    @classmethod
    def parse(cls, value: str) -> "ReportMonth":
        """
        Parse a month written as `YYYY-MM`.

        Args:
            value (str): The month, for example `2026-09`.

        Returns:
            ReportMonth: The parsed month.

        Raises:
            ValueError: If `value` is not a valid `YYYY-MM` month.
        """
        match = MONTH_PATTERN.fullmatch(value)
        if not match:
            raise ValueError(f"Month must be in YYYY-MM format, got {value!r}")
        return cls(year=int(match[1]), month=int(match[2]))

    @classmethod
    def last_full_month(cls, now: datetime) -> "ReportMonth":
        """Return the most recent month that ended before `now`, in UTC."""
        now = now.astimezone(timezone.utc)
        if now.month == 1:
            return cls(year=now.year - 1, month=12)
        return cls(year=now.year, month=now.month - 1)

    @property
    def label(self) -> str:
        """The month as `YYYY-MM`, used in file names and the `month` column."""
        return f"{self.year:04d}-{self.month:02d}"

    @property
    def start(self) -> datetime:
        """The first instant of the month, inclusive."""
        return datetime(self.year, self.month, 1, tzinfo=timezone.utc)

    @property
    def stop(self) -> datetime:
        """The first instant after the month, exclusive."""
        if self.month == 12:
            return datetime(self.year + 1, 1, 1, tzinfo=timezone.utc)
        return datetime(self.year, self.month + 1, 1, tzinfo=timezone.utc)

    def has_ended(self, now: datetime) -> bool:
        """Return True if the whole month is before `now`."""
        return self.stop <= now
