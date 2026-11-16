"""Tests for building the report files."""

import pytest
import requests

from metrics_report.audit import AuditClient
from metrics_report.reports import (
    DOWNLOADS,
    LOGINS,
    AuditReportSpec,
    Report,
    build_audit_report,
    fetch_audit_report,
)

from .fakes import SEPTEMBER, FakeGen3


def _rows(report: Report) -> list[tuple[str, ...]]:
    return list(report.rows)


@pytest.mark.parametrize(
    "spec, filename, columns",
    [
        (LOGINS, "logins_2026-09.tsv", ("month", "sub", "idp", "logins")),
        (
            DOWNLOADS,
            "downloads_2026-09.tsv",
            ("month", "sub", "resource", "downloads"),
        ),
    ],
)
def test_file_name_and_columns(
    spec: AuditReportSpec, filename: str, columns: tuple[str, ...]
) -> None:
    """Each report follows the agreed layout for its metric group."""
    report = build_audit_report(spec, SEPTEMBER, [], excluded_subs=())
    assert (report.filename, report.columns) == (filename, columns)


def test_one_row_per_sub_and_breakdown_sorted_by_sub() -> None:
    """Rows are keyed by `sub` and breakdown, and sorted numerically by `sub`."""
    groups = [
        {"sub": 456, "idp": "ras", "count": 2},
        {"sub": 123, "idp": "ras", "count": 12},
        {"sub": 123, "idp": "google", "count": 2},
        {"sub": 45, "idp": "ras", "count": 1},
    ]
    report = build_audit_report(LOGINS, SEPTEMBER, groups, excluded_subs=())
    assert _rows(report) == [
        ("2026-09", "45", "ras", "1"),
        ("2026-09", "123", "google", "2"),
        ("2026-09", "123", "ras", "12"),
        ("2026-09", "456", "ras", "2"),
    ]


def test_excluded_subs_are_left_out() -> None:
    """Non-researcher `sub`s from the exclusion list have no rows."""
    groups = [
        {"sub": 123, "idp": "ras", "count": 12},
        {"sub": 999, "idp": "ras", "count": 500},
    ]
    report = build_audit_report(LOGINS, SEPTEMBER, groups, excluded_subs={999})
    assert _rows(report) == [("2026-09", "123", "ras", "12")]


def test_events_without_sub_are_kept_with_an_empty_sub() -> None:
    """Anonymous downloads stay in the file, after the user rows, so totals match."""
    groups = [
        {"sub": None, "resource_paths": ["/open"], "count": 7},
        {"sub": 123, "resource_paths": ["/a"], "count": 30},
    ]
    report = build_audit_report(DOWNLOADS, SEPTEMBER, groups, excluded_subs={999})
    assert _rows(report) == [
        ("2026-09", "123", "/a", "30"),
        ("2026-09", "", "/open", "7"),
    ]


def test_resource_paths_in_any_order_count_as_one_resource() -> None:
    """Groups with the same resource paths in a different order are merged."""
    groups = [
        {"sub": 123, "resource_paths": ["/b", "/a"], "count": 3},
        {"sub": 123, "resource_paths": ["/a", "/b", "/a"], "count": 4},
    ]
    report = build_audit_report(DOWNLOADS, SEPTEMBER, groups, excluded_subs=())
    assert _rows(report) == [("2026-09", "123", "/a,/b", "7")]


@pytest.mark.parametrize("resource_paths", [None, []])
def test_missing_resource_paths_give_an_empty_resource(
    resource_paths: list[str] | None,
) -> None:
    """A download with no resource paths gets an empty `resource` cell."""
    groups = [{"sub": 123, "resource_paths": resource_paths, "count": 1}]
    report = build_audit_report(DOWNLOADS, SEPTEMBER, groups, excluded_subs=())
    assert _rows(report) == [("2026-09", "123", "", "1")]


def test_tsv_has_a_header_then_one_line_per_row() -> None:
    """The file is tab-separated, with a header line and a final newline."""
    report = Report(
        filename="logins_2026-09.tsv",
        columns=("month", "sub", "idp", "logins"),
        rows=(("2026-09", "123", "ras", "12"), ("2026-09", "", "ras", "1")),
    )
    assert report.to_tsv() == (
        b"month\tsub\tidp\tlogins\n2026-09\t123\tras\t12\n2026-09\t\tras\t1\n"
    )


def test_empty_report_has_only_the_header() -> None:
    """A month with no events still produces a file with its header."""
    report = build_audit_report(LOGINS, SEPTEMBER, [], excluded_subs=())
    assert report.to_tsv() == b"month\tsub\tidp\tlogins\n"


def test_downloads_count_only_successful_download_requests(gen3: FakeGen3) -> None:
    """The downloads query keeps download actions whose response issued a URL."""
    audit = AuditClient(requests.Session(), gen3.url, "token")
    fetch_audit_report(DOWNLOADS, audit, SEPTEMBER, excluded_subs=())
    query = gen3.audit_requests()[0].query
    assert sorted(p for p in query if p[0] in {"action", "status_code"}) == [
        ("action", "download"),
        ("status_code", "200"),
        ("status_code", "302"),
    ]


def test_fetch_groups_by_sub_and_breakdown(gen3: FakeGen3) -> None:
    """Each report asks audit-service for counts per `sub` and breakdown."""
    gen3.audit_groups["login"] = [{"sub": 123, "idp": "ras", "count": 12}]
    audit = AuditClient(requests.Session(), gen3.url, "token")
    report = fetch_audit_report(LOGINS, audit, SEPTEMBER, excluded_subs=())
    groupby = [v for k, v in gen3.audit_requests()[0].query if k == "groupby"]
    assert (groupby, _rows(report)) == (
        ["sub", "idp"],
        [("2026-09", "123", "ras", "12")],
    )
