"""Permissions utils for metrics-reports."""

from collections.abc import Iterable

import requests

ARBORIST_TIMEOUT_SECONDS = 30


def required_permissions(audit_categories: Iterable[str]) -> list[dict]:
    """
    Helper to build and return a list of Arborist requests required.

    Args:
        audit_categories (Iterable[str]): audit-service categories.

    Returns:
        list[dict]: Requests in the format of Arborist's `/auth/request`.
    """
    permissions = [
        {"resource": "/sower", "action": {"service": "job", "method": "access"}}
    ]
    for category in sorted(set(audit_categories)):
        permissions.append(
            {
                "resource": f"/services/audit/{category}",
                "action": {"service": "audit", "method": "read"},
            }
        )
    return permissions


def check_user_permission(
    session: requests.Session,
    arborist_url: str,
    access_token: str,
    permissions: list[dict],
) -> None:
    """
    Check that Arborist grants the token holder all required permissions.

    Args:
        session (requests.Session): HTTP session.
        arborist_url (str): Base URL of Arborist.
        access_token (str): The job dispatcher's access token.
        permissions (list[dict]): Requests from `required_permissions`.

    Raises:
        PermissionError: If Arborist denies the request or returns an error.
        requests.RequestException: If Arborist cannot be reached or returns
            a body that is not JSON.
    """
    response = session.post(
        f"{arborist_url}/auth/request",
        json={"user": {"token": access_token}, "requests": permissions},
        timeout=ARBORIST_TIMEOUT_SECONDS,
    )
    if response.status_code != 200:
        raise PermissionError(
            f"Arborist returned status {response.status_code} for the permission check"
        )
    if response.json().get("auth") is not True:
        resources = sorted(p["resource"] for p in permissions)
        raise PermissionError(
            f"The dispatching user needs access to all of {resources} to run this job"
        )
