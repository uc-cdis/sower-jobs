"""Tests for the dispatcher permission check."""

import pytest
import requests

from metrics_report.permissions import check_user_permission, required_permissions

from .fakes import FakeGen3

SOWER = {"resource": "/sower", "action": {"service": "job", "method": "access"}}


def _audit_read(category: str) -> dict:
    return {
        "resource": f"/services/audit/{category}",
        "action": {"service": "audit", "method": "read"},
    }


def test_required_permissions_cover_sower_and_each_category_once() -> None:
    """The job needs Sower access plus audit read on every category it reports."""
    assert required_permissions(["presigned_url", "login", "login"]) == [
        SOWER,
        _audit_read("login"),
        _audit_read("presigned_url"),
    ]


def test_allowed_user_passes(gen3: FakeGen3) -> None:
    """The check returns quietly when Arborist grants every request."""
    check_user_permission(requests.Session(), gen3.url, "token", [SOWER])


def test_check_sends_token_and_requests_to_arborist(gen3: FakeGen3) -> None:
    """Arborist evaluates the dispatcher's token against the job's requests."""
    check_user_permission(requests.Session(), gen3.url, "token", [SOWER])
    assert [(r.path, r.body) for r in gen3.requests] == [
        ("/auth/request", {"user": {"token": "token"}, "requests": [SOWER]})
    ]


def test_denied_user_is_rejected(gen3: FakeGen3) -> None:
    """A user missing any grant cannot run the job."""
    gen3.arborist_auth = False
    with pytest.raises(PermissionError):
        check_user_permission(requests.Session(), gen3.url, "token", [SOWER])


@pytest.mark.parametrize("status", [401, 500])
def test_arborist_error_is_a_denial(gen3: FakeGen3, status: int) -> None:
    """The check fails closed when Arborist returns an error."""
    gen3.arborist_status = status
    with pytest.raises(PermissionError):
        check_user_permission(requests.Session(), gen3.url, "token", [SOWER])
