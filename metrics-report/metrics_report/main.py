"""Entry point of the metrics-report Sower job"""

import json
import os
import sys
from datetime import datetime, timezone
from typing import Any

import requests
from cdislogging import get_logger

from metrics_report.audit import AuditClient, AuditServiceError
from metrics_report.config import JobConfig, load_config
from metrics_report.permissions import check_user_permission, required_permissions
from metrics_report.reports import AUDIT_REPORTS, fetch_audit_report
from metrics_report.storage import ReportStorage

logger = get_logger(__name__, log_level="info")

OUTPUT_PREFIX = "[out] "
REPORTED_ERRORS = (ValueError, PermissionError, AuditServiceError)
UNEXPECTED_ERROR_MESSAGE = "The metrics report failed. See the job logs for details."


def main() -> int:
    """
    Run the job and print the result message line.

    Returns:
        int: The process exit code. Sower marks the job failed when it is not 0.
    """
    now = datetime.now(timezone.utc)
    try:
        config = load_config(os.environ, now)
        logger.info(
            f"Building reports for {config.month.label}, "
            f"excluding {len(config.excluded_subs)} subs"
        )
        urls = run(
            config,
            requests.Session(),
            ReportStorage.from_config(config.bucket),
            run_id=now.strftime("%Y%m%dT%H%M%SZ"),
        )
    except REPORTED_ERRORS as e:
        logger.error(f"Metrics report failed: {e}")
        write_output({"error": str(e)})
        return 1
    except Exception:
        logger.exception("Metrics report failed with an unexpected error")
        write_output({"error": UNEXPECTED_ERROR_MESSAGE})
        return 1

    write_output({"files": urls})
    return 0


def run(
    config: JobConfig,
    session: requests.Session,
    storage: ReportStorage,
    run_id: str,
) -> dict[str, str]:
    """
    Check the dispatcher's permissions, build reports, then upload the files.

    Args:
        config (JobConfig): The job configuration.
        session (requests.Session): HTTP session for Arborist and audit-service.
        storage (ReportStorage): Where the files go.
        run_id (str): Folder name for this run's files.

    Returns:
        dict[str, str]: Presigned download URL for each file name.

    Raises:
        PermissionError: If the dispatcher lacks a required grant. No data is
            read in that case.
        AuditServiceError: If audit-service rejects a query.
        requests.RequestException: If a service cannot be reached.
        botocore.exceptions.BotoCoreError: If an upload fails.
        botocore.exceptions.ClientError: If S3 rejects an upload.
    """
    check_user_permission(
        session,
        config.arborist_url,
        config.access_token,
        required_permissions(spec.category for spec in AUDIT_REPORTS),
    )

    audit = AuditClient(session, config.audit_service_url, config.access_token)
    reports = [
        fetch_audit_report(spec, audit, config.month, config.excluded_subs)
        for spec in AUDIT_REPORTS
    ]
    for report in reports:
        logger.info(f"{report.filename}: {len(report.rows)} rows")

    return {report.filename: storage.upload(run_id, report) for report in reports}


def write_output(result: dict[str, Any]) -> None:
    """Print `result` as the line that Sower's `GET /job/output` returns."""
    # Sower returns only the last log line that contains "[out] "
    print(f"{OUTPUT_PREFIX}{json.dumps(result)}", flush=True)


if __name__ == "__main__":
    sys.exit(main())
