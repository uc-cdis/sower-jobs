"""Tests for a whole job run and the result line Sower returns."""

import json

import pytest
import requests

from metrics_report.audit import AuditServiceError
from metrics_report.config import JobConfig
from metrics_report.main import OUTPUT_PREFIX, main, run, write_output

from .fakes import FakeGen3, FakeStorage

RUN_ID = "20261014T120000Z"
LOGIN_GROUPS = [
    {"sub": 123, "idp": "ras", "count": 12},
    {"sub": 999, "idp": "ras", "count": 500},
]
DOWNLOAD_GROUPS = [
    {"sub": 123, "resource_paths": ["/programs/A"], "count": 30},
    {"sub": 999, "resource_paths": ["/programs/A"], "count": 900},
    {"sub": None, "resource_paths": ["/programs/open"], "count": 7},
]


@pytest.fixture
def excluding_999(job_config: JobConfig) -> JobConfig:
    """The test config with `sub` 999 on the exclusion list."""
    return JobConfig(**{**vars(job_config), "excluded_subs": frozenset({999})})


@pytest.fixture
def populated_gen3(gen3: FakeGen3) -> FakeGen3:
    """Fake services with September logins and downloads."""
    gen3.audit_groups = {"login": LOGIN_GROUPS, "presigned_url": DOWNLOAD_GROUPS}
    return gen3


def _output_lines(stdout: str) -> list[str]:
    return [line for line in stdout.splitlines() if OUTPUT_PREFIX in line]


def test_run_returns_a_link_for_each_file(
    excluding_999: JobConfig, populated_gen3: FakeGen3
) -> None:
    """A dispatch for a month returns a link to the logins and downloads files."""
    urls = run(excluding_999, requests.Session(), FakeStorage(), RUN_ID)
    assert urls == {
        "logins_2026-09.tsv": f"https://bucket.example/{RUN_ID}/logins_2026-09.tsv",
        "downloads_2026-09.tsv": f"https://bucket.example/{RUN_ID}/downloads_2026-09.tsv",
    }


def test_run_uploads_files_with_exclusions_applied(
    excluding_999: JobConfig, populated_gen3: FakeGen3
) -> None:
    """The uploaded files leave out excluded subs and keep anonymous downloads."""
    storage = FakeStorage()
    run(excluding_999, requests.Session(), storage, RUN_ID)
    assert storage.files == {
        f"{RUN_ID}/logins_2026-09.tsv": (
            b"month\tsub\tidp\tlogins\n2026-09\t123\tras\t12\n"
        ),
        f"{RUN_ID}/downloads_2026-09.tsv": (
            b"month\tsub\tresource\tdownloads\n"
            b"2026-09\t123\t/programs/A\t30\n"
            b"2026-09\t\t/programs/open\t7\n"
        ),
    }


def test_run_checks_sower_and_audit_grants(
    job_config: JobConfig, populated_gen3: FakeGen3
) -> None:
    """The dispatcher needs Sower access and audit read on both categories."""
    run(job_config, requests.Session(), FakeStorage(), RUN_ID)
    permission_check = populated_gen3.requests[0]
    assert [r["resource"] for r in permission_check.body["requests"]] == [
        "/sower",
        "/services/audit/login",
        "/services/audit/presigned_url",
    ]


def test_denied_dispatch_reads_no_data(
    job_config: JobConfig, populated_gen3: FakeGen3
) -> None:
    """A dispatcher without the grants fails before any audit-service query."""
    populated_gen3.arborist_auth = False
    with pytest.raises(PermissionError):
        run(job_config, requests.Session(), FakeStorage(), RUN_ID)
    assert populated_gen3.audit_requests() == []


def test_failed_query_uploads_nothing(
    job_config: JobConfig, populated_gen3: FakeGen3
) -> None:
    """If any audit-service query fails, no partial set of files is uploaded."""
    populated_gen3.audit_status = 500
    storage = FakeStorage()
    with pytest.raises(AuditServiceError):
        run(job_config, requests.Session(), storage, RUN_ID)
    assert storage.files == {}


def test_write_output_is_one_json_line(capsys: pytest.CaptureFixture[str]) -> None:
    """The whole result is on one `[out]` line, which is all Sower returns."""
    result = {
        "files": {
            "logins_2026-09.tsv": "https://a",
            "downloads_2026-09.tsv": "https://b",
        }
    }
    write_output(result)
    (line,) = _output_lines(capsys.readouterr().out)
    assert json.loads(line.removeprefix(OUTPUT_PREFIX)) == result


def test_main_reports_a_config_error_and_fails(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Without a token, the job exits non-zero and its last `[out]` line is an error."""
    monkeypatch.delenv("ACCESS_TOKEN", raising=False)
    exit_code = main()
    last_line = _output_lines(capsys.readouterr().out)[-1]
    assert (exit_code, list(json.loads(last_line.removeprefix(OUTPUT_PREFIX)))) == (
        1,
        ["error"],
    )
