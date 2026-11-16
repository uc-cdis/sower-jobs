"""Client for metrics-report job to read audit-service."""

from collections.abc import Mapping, Sequence
from typing import Any

import requests

from metrics_report.month import ReportMonth

AUDIT_CONNECT_TIMEOUT_SECONDS = 10
AUDIT_READ_TIMEOUT_SECONDS = 300
ERROR_DETAIL_MAX_CHARS = 500


class AuditServiceError(Exception):
    """audit-service rejected a query or returned an unexpected body."""


class AuditClient:
    """Client to read from audit-service with the dispatcher's token."""

    def __init__(
        self, session: requests.Session, base_url: str, access_token: str
    ) -> None:
        self.session = session
        self.base_url = base_url
        self.access_token = access_token

    def fetch_grouped_counts(
        self,
        category: str,
        month: ReportMonth,
        groupby: Sequence[str],
        filters: Mapping[str, Sequence[str]],
    ) -> list[dict[str, Any]]:
        """
        Query `GET /log/{category}` and count the grouped events in `month`.

        For example:
        ```
        audit = AuditClient(session, audit_service_url, access_token)

        audit.fetch_grouped_counts(
            "presigned_url", month,
            groupby=("sub", "resource_paths"),
            filters={"action": ("download",), "status_code": ("200", "302")},
        )
        ```

        would request:
        ```
        GET http://revproxy-service/audit/log/presigned_url
            ?start=<month start>
            &stop=<month end>
            &groupby=sub&groupby=resource_paths
            &action=download
            &status_code=200&status_code=302
        Authorization: Bearer <access_token>
        ```

        Args:
            category (str): audit-service category.
            month (ReportMonth): The month to count.
            groupby (Sequence[str]): Columns to group by.
            filters (Mapping[str, Sequence[str]]): Column values to keep.

        Returns:
            list[dict[str, Any]]: One dict per group, with the `groupby` columns
                and a `count`.

        Raises:
            AuditServiceError: If audit-service returns an error status or a body
                without a list of groups.
            requests.RequestException: If audit-service cannot be reached or
                returns a body that is not JSON.
        """
        params = [
            ("start", int(month.start.timestamp())),
            ("stop", int(month.stop.timestamp())),
        ]
        params += [("groupby", field) for field in groupby]
        params += [(key, value) for key, values in filters.items() for value in values]

        response = self.session.get(
            f"{self.base_url}/log/{category}",
            params=params,
            headers={"Authorization": f"Bearer {self.access_token}"},
            timeout=(AUDIT_CONNECT_TIMEOUT_SECONDS, AUDIT_READ_TIMEOUT_SECONDS),
        )
        if response.status_code != 200:
            raise AuditServiceError(
                f"audit-service returned status {response.status_code} for "
                f"'{category}': {response.text[:ERROR_DETAIL_MAX_CHARS]}"
            )

        groups = response.json().get("data")
        if not isinstance(groups, list):
            raise AuditServiceError(
                f"audit-service returned no list of groups for '{category}'"
            )
        return groups
