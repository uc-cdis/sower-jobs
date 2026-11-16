"""Shared fixtures."""

import threading
from collections.abc import Iterator
from http.server import ThreadingHTTPServer

import pytest

from metrics_report.config import BucketConfig, JobConfig

from .fakes import SEPTEMBER, FakeGen3, FakeGen3Handler


@pytest.fixture
def gen3() -> Iterator[FakeGen3]:
    """A running fake Arborist and audit-service on a free local port."""
    fake = FakeGen3()
    handler = type("Handler", (FakeGen3Handler,), {"fake": fake})
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(
        target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True
    )
    thread.start()
    fake.url = f"http://127.0.0.1:{server.server_port}"
    yield fake
    server.shutdown()
    server.server_close()


@pytest.fixture
def job_config(gen3: FakeGen3) -> JobConfig:
    """A September 2026 job config that points at the fake services."""
    return JobConfig(
        access_token="test-token",
        month=SEPTEMBER,
        excluded_subs=frozenset(),
        audit_service_url=gen3.url,
        arborist_url=gen3.url,
        bucket=BucketConfig(
            name="test-bucket",
            aws_access_key_id="test-key-id",
            aws_secret_access_key="test-secret",  # pragma: allowlist secret
        ),
    )
