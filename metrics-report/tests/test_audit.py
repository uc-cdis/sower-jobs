"""Tests for the audit-service client."""

import pytest
import requests

from metrics_report.audit import AuditClient, AuditServiceError

from .fakes import SEPTEMBER, FakeGen3

SEPTEMBER_START = "1788220800"  # 2026-09-01T00:00:00Z
OCTOBER_START = "1790812800"  # 2026-10-01T00:00:00Z


@pytest.fixture
def client(gen3: FakeGen3) -> AuditClient:
    """A client for the fake audit-service."""
    return AuditClient(requests.Session(), gen3.url, "token")


def test_query_covers_the_month_in_utc(client: AuditClient, gen3: FakeGen3) -> None:
    """`start` and `stop` are the month's UTC bounds, in epoch seconds."""
    client.fetch_grouped_counts("login", SEPTEMBER, groupby=["sub"], filters={})
    query = gen3.audit_requests()[0].query
    assert (dict(query)["start"], dict(query)["stop"]) == (
        SEPTEMBER_START,
        OCTOBER_START,
    )


def test_groupby_and_filters_repeat_query_params(
    client: AuditClient, gen3: FakeGen3
) -> None:
    """Each groupby column and filter value is its own query parameter."""
    client.fetch_grouped_counts(
        "presigned_url",
        SEPTEMBER,
        groupby=["sub", "resource_paths"],
        filters={"action": ["download"], "status_code": ["200", "302"]},
    )
    request = gen3.audit_requests()[0]
    assert (request.path, request.query[2:]) == (
        "/log/presigned_url",
        [
            ("groupby", "sub"),
            ("groupby", "resource_paths"),
            ("action", "download"),
            ("status_code", "200"),
            ("status_code", "302"),
        ],
    )


def test_query_sends_the_dispatchers_token(client: AuditClient, gen3: FakeGen3) -> None:
    """audit-service authorizes the query with the dispatcher's token."""
    client.fetch_grouped_counts("login", SEPTEMBER, groupby=["sub"], filters={})
    assert gen3.audit_requests()[0].headers["Authorization"] == "Bearer token"


def test_returns_the_groups(client: AuditClient, gen3: FakeGen3) -> None:
    """The client returns audit-service's groups unchanged."""
    groups = [{"sub": 1, "idp": "ras", "count": 3}]
    gen3.audit_groups["login"] = groups
    assert (
        client.fetch_grouped_counts(
            "login", SEPTEMBER, groupby=["sub", "idp"], filters={}
        )
        == groups
    )


@pytest.mark.parametrize("status", [400, 403, 500])
def test_error_status_raises(client: AuditClient, gen3: FakeGen3, status: int) -> None:
    """An audit-service error, such as a missing grant, fails the query."""
    gen3.audit_status = status
    with pytest.raises(AuditServiceError):
        client.fetch_grouped_counts("login", SEPTEMBER, groupby=["sub"], filters={})


def test_count_instead_of_groups_raises(client: AuditClient, gen3: FakeGen3) -> None:
    """A body whose `data` is not a list of groups is rejected."""
    gen3.audit_groups["login"] = 7
    with pytest.raises(AuditServiceError):
        client.fetch_grouped_counts("login", SEPTEMBER, groupby=["sub"], filters={})
