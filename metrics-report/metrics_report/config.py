"""Job configuration from the Sower environment and the mounted credentials file."""

import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime

from metrics_report.month import ReportMonth

CREDS_PATH = "/metrics-report-creds.json"
DEFAULT_AUDIT_SERVICE_URL = "http://revproxy-service/audit"
DEFAULT_ARBORIST_URL = "http://arborist-service"
INPUT_KEYS = frozenset({"month"})
BUCKET_KEYS = ("manifest_bucket_name", "aws_access_key_id", "aws_secret_access_key")


@dataclass(frozen=True)
class BucketConfig:
    """The S3 bucket that receives the report files, and the keys to write to it."""

    name: str
    aws_access_key_id: str
    aws_secret_access_key: str


@dataclass(frozen=True)
class JobConfig:
    """Everything one run of the job needs."""

    access_token: str
    month: ReportMonth
    excluded_subs: frozenset[int]
    audit_service_url: str
    arborist_url: str
    bucket: BucketConfig


def load_config(
    environ: Mapping[str, str], now: datetime, creds_path: str = CREDS_PATH
) -> JobConfig:
    """
    Build the job configuration.

    Sower sets `ACCESS_TOKEN` (the dispatcher's token) and `INPUT_DATA` (the
    dispatch `input` as JSON). The Sower job config can set `EXCLUDED_SUBS`,
    `AUDIT_SERVICE_URL`, and `ARBORIST_URL`.

    Args:
        environ (Mapping[str, str]): The process environment.
        now (datetime): The current time, timezone-aware.
        creds_path (str): Path of the mounted JSON file with the bucket keys.

    Returns:
        JobConfig: The validated configuration.

    Raises:
        ValueError: If any setting is missing or invalid.
    """
    access_token = environ.get("ACCESS_TOKEN")
    if not access_token:
        raise ValueError("Missing ACCESS_TOKEN in environment")

    return JobConfig(
        access_token=access_token,
        month=parse_report_month(environ.get("INPUT_DATA"), now),
        excluded_subs=parse_excluded_subs(environ.get("EXCLUDED_SUBS", "")),
        audit_service_url=environ.get(
            "AUDIT_SERVICE_URL", DEFAULT_AUDIT_SERVICE_URL
        ).rstrip("/"),
        arborist_url=environ.get("ARBORIST_URL", DEFAULT_ARBORIST_URL).rstrip("/"),
        bucket=load_bucket_config(creds_path),
    )


def parse_report_month(input_data: str | None, now: datetime) -> ReportMonth:
    """
    Read the report month from the dispatch input.

    Args:
        input_data (str | None): The `INPUT_DATA` JSON, for example
            `{"month": "2026-09"}`. Sower sends `null` when the dispatch has no
            `input`.
        now (datetime): The current time, timezone-aware.

    Returns:
        ReportMonth: The requested month, or the last full month if the input
            has no `month`.

    Raises:
        ValueError: If the input is not a JSON object, has unknown keys, or
            names a month that is invalid or has not ended.
    """
    parsed = json.loads(input_data) if input_data else None
    if parsed is None:
        parsed = {}
    if not isinstance(parsed, dict):
        raise ValueError("INPUT_DATA must be a JSON object")

    unknown = set(parsed) - INPUT_KEYS
    if unknown:
        raise ValueError(f"Unknown INPUT_DATA keys: {sorted(unknown)}")

    value = parsed.get("month")
    if value is None:
        return ReportMonth.last_full_month(now)
    if not isinstance(value, str):
        raise ValueError(f"month must be a YYYY-MM string, got {value!r}")

    month = ReportMonth.parse(value)
    # A month in progress would produce a partial report labeled as a full month.
    if not month.has_ended(now):
        raise ValueError(f"Month {month.label} has not ended yet")
    return month


def parse_excluded_subs(value: str) -> frozenset[int]:
    """
    Parse the comma-separated list of user `sub`s to leave out of the reports.

    Args:
        value (str): For example `"12, 34"`. Empty entries are ignored.

    Returns:
        frozenset[int]: The excluded `sub`s.

    Raises:
        ValueError: If an entry is not a non-negative integer.
    """
    subs = set()
    for entry in value.split(","):
        entry = entry.strip()
        if not entry:
            continue
        if not (entry.isascii() and entry.isdigit()):
            raise ValueError(f"EXCLUDED_SUBS entries must be integers, got {entry!r}")
        subs.add(int(entry))
    return frozenset(subs)


def load_bucket_config(creds_path: str) -> BucketConfig:
    """
    Read the bucket name and AWS keys from the mounted credentials file.

    The keys match the `pelicanservice-g3auto` `config.json`, so a commons can
    mount that secret as is.

    Args:
        creds_path (str): Path of the JSON file.

    Returns:
        BucketConfig: The bucket settings.

    Raises:
        ValueError: If the file is missing, is not a JSON object, or lacks a key.
    """
    try:
        with open(creds_path) as f:
            creds = json.load(f)
    except FileNotFoundError:
        raise ValueError(f"Missing credentials file {creds_path}") from None

    if not isinstance(creds, dict):
        raise ValueError(f"{creds_path} must contain a JSON object")
    missing = [key for key in BUCKET_KEYS if not creds.get(key)]
    if missing:
        raise ValueError(f"{creds_path} is missing {missing}")

    return BucketConfig(
        name=creds["manifest_bucket_name"],
        aws_access_key_id=creds["aws_access_key_id"],
        aws_secret_access_key=creds["aws_secret_access_key"],
    )
