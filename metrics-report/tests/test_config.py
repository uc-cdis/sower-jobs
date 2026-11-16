"""Tests for reading the job configuration."""

import json
from pathlib import Path

import pytest

from metrics_report.config import (
    BUCKET_KEYS,
    DEFAULT_ARBORIST_URL,
    DEFAULT_AUDIT_SERVICE_URL,
    BucketConfig,
    JobConfig,
    load_bucket_config,
    load_config,
    parse_excluded_subs,
    parse_report_month,
)
from metrics_report.month import ReportMonth

from .fakes import NOW

BUCKET_CREDS = {
    "manifest_bucket_name": "test-bucket",
    "aws_access_key_id": "test-key-id",
    "aws_secret_access_key": "test-secret",  # pragma: allowlist secret
}


@pytest.fixture
def creds_path(tmp_path: Path) -> str:
    """A valid credentials file."""
    path = tmp_path / "creds.json"
    path.write_text(json.dumps(BUCKET_CREDS))
    return str(path)


def test_load_config_reads_sower_environment(creds_path: str) -> None:
    """Every setting comes from the environment and the credentials file."""
    environ = {
        "ACCESS_TOKEN": "token",
        "INPUT_DATA": '{"month": "2026-08"}',
        "EXCLUDED_SUBS": "12,34",
        "AUDIT_SERVICE_URL": "http://audit.example/",
        "ARBORIST_URL": "http://arborist.example/",
    }
    assert load_config(environ, NOW, creds_path) == JobConfig(
        access_token="token",
        month=ReportMonth(2026, 8),
        excluded_subs=frozenset({12, 34}),
        audit_service_url="http://audit.example",
        arborist_url="http://arborist.example",
        bucket=BucketConfig("test-bucket", "test-key-id", "test-secret"),
    )


def test_load_config_defaults(creds_path: str) -> None:
    """Without optional settings, the job reports last month with no exclusions."""
    config = load_config({"ACCESS_TOKEN": "token"}, NOW, creds_path)
    assert (
        config.month,
        config.excluded_subs,
        config.audit_service_url,
        config.arborist_url,
    ) == (
        ReportMonth(2026, 9),
        frozenset(),
        DEFAULT_AUDIT_SERVICE_URL,
        DEFAULT_ARBORIST_URL,
    )


@pytest.mark.parametrize("environ", [{}, {"ACCESS_TOKEN": ""}])
def test_load_config_requires_access_token(
    environ: dict[str, str], creds_path: str
) -> None:
    """The job cannot run without the dispatcher's token."""
    with pytest.raises(ValueError):
        load_config(environ, NOW, creds_path)


@pytest.mark.parametrize("input_data", [None, "", "null", "{}", '{"month": null}'])
def test_missing_month_defaults_to_last_full_month(input_data: str | None) -> None:
    """A dispatch without a month reports the last full month."""
    assert parse_report_month(input_data, NOW) == ReportMonth(2026, 9)


def test_explicit_month_is_used() -> None:
    """A dispatch can name any month that has ended."""
    assert parse_report_month('{"month": "2025-02"}', NOW) == ReportMonth(2025, 2)


@pytest.mark.parametrize(
    "input_data",
    [
        "not json",
        "[]",
        '"2026-09"',
        '{"month": 202609}',
        '{"month": "2026-9"}',
        '{"Month": "2026-09"}',
        '{"month": "2026-09", "extra": 1}',
        '{"month": "2026-10"}',  # the current month
        '{"month": "2027-01"}',
        '{"month": "2026-00"}',
        '{"month": "0000-01"}',
        '{"month": "9999-12"}',  # its stop bound is past datetime's last year
    ],
)
def test_invalid_input_is_rejected(input_data: str) -> None:
    """Malformed input, unknown keys, and invalid or unfinished months are rejected."""
    with pytest.raises(ValueError):
        parse_report_month(input_data, NOW)


@pytest.mark.parametrize(
    "value, expected",
    [
        ("", frozenset()),
        ("12", frozenset({12})),
        (" 12, 34,,56 ,", frozenset({12, 34, 56})),
        ("12,12", frozenset({12})),
    ],
)
def test_parse_excluded_subs(value: str, expected: frozenset[int]) -> None:
    """The exclusion list is comma-separated, and blanks are ignored."""
    assert parse_excluded_subs(value) == expected


@pytest.mark.parametrize(
    "value", ["abc", "-1", "1.5", "12;34", "١٢"]  # Arabic-Indic digits
)
def test_parse_excluded_subs_rejects_non_integers(value: str) -> None:
    """An entry that is not a plain integer fails the job instead of being skipped."""
    with pytest.raises(ValueError):
        parse_excluded_subs(value)


def test_load_bucket_config(creds_path: str) -> None:
    """The bucket settings use the `pelicanservice-g3auto` key names."""
    assert load_bucket_config(creds_path) == BucketConfig(
        "test-bucket", "test-key-id", "test-secret"
    )


def test_load_bucket_config_requires_the_file(tmp_path: Path) -> None:
    """A missing credentials file is a configuration error."""
    with pytest.raises(ValueError):
        load_bucket_config(str(tmp_path / "missing.json"))


@pytest.mark.parametrize("contents", ["[]", '"bucket"'])
def test_load_bucket_config_requires_an_object(tmp_path: Path, contents: str) -> None:
    """The credentials file must hold a JSON object."""
    path = tmp_path / "creds.json"
    path.write_text(contents)
    with pytest.raises(ValueError):
        load_bucket_config(str(path))


@pytest.mark.parametrize("key", BUCKET_KEYS)
@pytest.mark.parametrize("value", [None, ""])
def test_load_bucket_config_requires_every_key(
    tmp_path: Path, key: str, value: str | None
) -> None:
    """Each bucket key must be present and non-empty."""
    creds = {**BUCKET_CREDS, key: value}
    path = tmp_path / "creds.json"
    path.write_text(json.dumps(creds))
    with pytest.raises(ValueError):
        load_bucket_config(str(path))
