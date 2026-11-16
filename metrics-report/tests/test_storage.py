"""Tests for uploading report files to S3."""

from collections.abc import Iterator
from urllib.parse import parse_qs, urlsplit

import pytest
from botocore.stub import Stubber

from metrics_report.config import BucketConfig
from metrics_report.reports import Report
from metrics_report.storage import ReportStorage

BUCKET = BucketConfig(
    name="test-bucket",
    aws_access_key_id="test-key-id",
    aws_secret_access_key="test-secret",  # pragma: allowlist secret
)
REPORT = Report(
    filename="logins_2026-09.tsv",
    columns=("month", "sub", "idp", "logins"),
    rows=(("2026-09", "123", "ras", "12"),),
)
KEY = "metrics-report/20261014T120000Z/logins_2026-09.tsv"


@pytest.fixture(autouse=True)
def isolated_aws_config(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the developer's AWS profile and region out of the tests."""
    monkeypatch.setenv("AWS_CONFIG_FILE", "/nonexistent")
    monkeypatch.setenv("AWS_SHARED_CREDENTIALS_FILE", "/nonexistent")
    for name in ("AWS_PROFILE", "AWS_DEFAULT_REGION", "AWS_REGION"):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def storage() -> Iterator[tuple[ReportStorage, Stubber]]:
    """Storage built from the credentials file settings, with S3 stubbed out."""
    storage = ReportStorage.from_config(BUCKET)
    with Stubber(storage.s3_client) as stubber:
        yield storage, stubber


def test_upload_puts_the_file_under_the_run_folder(
    storage: tuple[ReportStorage, Stubber],
) -> None:
    """Each run's files go to `metrics-report/<run id>/<file name>`."""
    report_storage, stubber = storage
    stubber.add_response(
        "put_object",
        {},
        expected_params={
            "Bucket": "test-bucket",
            "Key": KEY,
            "Body": REPORT.to_tsv(),
            "ContentType": "text/tab-separated-values",
        },
    )
    report_storage.upload("20261014T120000Z", REPORT)
    stubber.assert_no_pending_responses()


def test_upload_returns_a_signed_link_that_expires_in_an_hour(
    storage: tuple[ReportStorage, Stubber],
) -> None:
    """The link is a SigV4 presigned GET for the uploaded key."""
    report_storage, stubber = storage
    stubber.add_response("put_object", {})
    url = urlsplit(report_storage.upload("20261014T120000Z", REPORT))
    query = parse_qs(url.query)
    assert (
        url.netloc,
        url.path,
        query["X-Amz-Algorithm"],
        query["X-Amz-Expires"],
    ) == ("test-bucket.s3.amazonaws.com", f"/{KEY}", ["AWS4-HMAC-SHA256"], ["3600"])
