"""Monthly report files built from audit-service event counts."""

import csv
import io
from collections import Counter
from collections.abc import Collection, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from metrics_report.audit import AuditClient
from metrics_report.month import ReportMonth


@dataclass(frozen=True)
class AuditReportSpec:
    """
    Defines a report file for an audit-service query.

    Attributes:
        name (str): File name prefix and the name of the count column.
        category (str): audit-service category to query.
        breakdown_field (str): audit-service column grouped by, next to `sub`.
        breakdown_column (str): Name of the breakdown column in the file.
        filters (Mapping[str, tuple[str, ...]]): audit-service filters that
            define which events count.
    """

    name: str
    category: str
    breakdown_field: str
    breakdown_column: str
    filters: Mapping[str, tuple[str, ...]] = field(
        default_factory=lambda: MappingProxyType({})
    )


LOGINS = AuditReportSpec(
    name="logins",
    category="login",
    breakdown_field="idp",
    breakdown_column="idp",
)

# 200 and 302 (`/data/download/<guid>?redirect`) are the responses that issue a URL.
DOWNLOADS = AuditReportSpec(
    name="downloads",
    category="presigned_url",
    breakdown_field="resource_paths",
    breakdown_column="resource",
    filters=MappingProxyType({"action": ("download",), "status_code": ("200", "302")}),
)

AUDIT_REPORTS = (LOGINS, DOWNLOADS)  # TODO - add export_data here


@dataclass(frozen=True)
class Report:
    """A data structure for one report file."""

    filename: str
    columns: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]

    def to_tsv(self) -> bytes:
        """Return the file contents: a header line, then one line per row."""
        buffer = io.StringIO()
        writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
        writer.writerow(self.columns)
        writer.writerows(self.rows)
        return buffer.getvalue().encode("utf-8")


def fetch_audit_report(
    spec: AuditReportSpec,
    audit: AuditClient,
    month: ReportMonth,
    excluded_subs: Collection[int],
) -> Report:
    """
    Query audit-service for one report and build the file.

    Args:
        spec (AuditReportSpec): The report to build.
        audit (AuditClient): audit-service client.
        month (ReportMonth): The month to report.
        excluded_subs (Collection[int]): subs to leave out.

    Returns:
        Report: The report file.

    Raises:
        AuditServiceError: If audit-service rejects the query.
        requests.RequestException: If audit-service cannot be reached.
    """
    groups = audit.fetch_grouped_counts(
        spec.category,
        month,
        groupby=("sub", spec.breakdown_field),
        filters=spec.filters,
    )
    return build_audit_report(spec, month, groups, excluded_subs)


def build_audit_report(
    spec: AuditReportSpec,
    month: ReportMonth,
    groups: list[dict[str, Any]],
    excluded_subs: Collection[int],
) -> Report:
    """
    Turn audit-service groups into report rows.

    The result has one row per user (sub) and breakdown value, with the event count.
    Events with no `sub` (anonymous) are kept in an empty `sub` row.
    Rows are sorted by `sub`, with the empty `sub` last, then by breakdown.

    Args:
        spec (AuditReportSpec): The report to build.
        month (ReportMonth): The reported month.
        groups (list[dict[str, Any]]): Groups from `AuditClient.fetch_grouped_counts`.
        excluded_subs (Collection[int]): `sub`s to leave out. Rows with no `sub`
            are always kept.

    Returns:
        Report: The report file.
    """
    counts = Counter()
    for group in groups:
        sub = group["sub"]
        if sub is not None and sub in excluded_subs:
            continue
        counts[(sub, _breakdown_text(group[spec.breakdown_field]))] += group["count"]

    ordered = sorted(
        counts.items(),
        key=lambda item: (item[0][0] is None, item[0][0] or 0, item[0][1]),
    )
    rows = tuple(
        (month.label, "" if sub is None else str(sub), breakdown, str(count))
        for (sub, breakdown), count in ordered
    )
    return Report(
        filename=f"{spec.name}_{month.label}.tsv",
        columns=("month", "sub", spec.breakdown_column, spec.name),
        rows=rows,
    )


def _breakdown_text(value: Any) -> str:
    """
    TODO: this is in place to support files that requre multiple resource paths.
    DO we need to support this?

    If breakdowns ara a list (like multple resource_paths) then merge so a download
    protected by several resources counts once.

    E.g `resource_paths` `["/b", "/a"]` and `["/a", "/b"]` will be in same breakdown.
    """
    if value is None:
        return ""
    if isinstance(value, list):
        return ",".join(sorted(set(value)))
    return str(value)
