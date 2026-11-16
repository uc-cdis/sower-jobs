"""Fake Arborist, audit-service HTTP server, and in-memory storage."""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler
from typing import Any
from urllib.parse import SplitResult, parse_qsl, urlsplit

from metrics_report.month import ReportMonth
from metrics_report.reports import Report

NOW = datetime(2026, 10, 14, 12, 0, tzinfo=timezone.utc)
SEPTEMBER = ReportMonth(2026, 9)


@dataclass
class RecordedRequest:
    """One request the fake server received."""

    method: str
    path: str
    query: list[tuple[str, str]]
    headers: dict[str, str]
    body: Any


@dataclass
class FakeGen3:
    """Canned Arborist and audit-service responses, and the requests received."""

    url: str = ""
    arborist_status: int = 200
    arborist_auth: bool = True
    audit_status: int = 200
    audit_groups: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    requests: list[RecordedRequest] = field(default_factory=list)

    def audit_requests(self) -> list[RecordedRequest]:
        """Return the requests sent to audit-service."""
        return [r for r in self.requests if r.path.startswith("/log/")]


class FakeGen3Handler(BaseHTTPRequestHandler):
    """Request handler; subclasses set `fake` to the `FakeGen3` they serve."""

    fake: FakeGen3

    def do_GET(self) -> None:
        """Serve `GET /log/{category}` as audit-service does with `groupby`."""
        url = urlsplit(self.path)
        self._record(url, body=None)
        if self.fake.audit_status != 200:
            self._respond(self.fake.audit_status, {"detail": "audit query failed"})
            return
        category = url.path.removeprefix("/log/")
        data = self.fake.audit_groups.get(category, [])
        self._respond(200, {"nextTimeStamp": None, "data": data})

    def do_POST(self) -> None:
        """Serve Arborist's `POST /auth/request`."""
        url = urlsplit(self.path)
        length = int(self.headers.get("Content-Length", 0))
        self._record(url, body=json.loads(self.rfile.read(length)))
        self._respond(self.fake.arborist_status, {"auth": self.fake.arborist_auth})

    def log_message(self, format: str, *args: Any) -> None:
        """Keep test output quiet."""

    def _record(self, url: SplitResult, body: Any) -> None:
        self.fake.requests.append(
            RecordedRequest(
                method=self.command,
                path=url.path,
                query=parse_qsl(url.query),
                headers=dict(self.headers),
                body=body,
            )
        )

    def _respond(self, status: int, body: Any) -> None:
        payload = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


class FakeStorage:
    """Keeps uploaded files in memory and returns fake URLs."""

    def __init__(self) -> None:
        self.files: dict[str, bytes] = {}

    def upload(self, run_id: str, report: Report) -> str:
        """Store the file contents under `<run_id>/<file name>`."""
        self.files[f"{run_id}/{report.filename}"] = report.to_tsv()
        return f"https://bucket.example/{run_id}/{report.filename}"
