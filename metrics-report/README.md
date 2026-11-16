# Metrics Report Job

The `metrics-report` job writes the monthly Enhanced Metrics report files for one calendar month. It reads event counts from audit-service, writes one TSV file for each metric group, uploads the files to S3, and returns a presigned link for each file.

## Report files

| File | Columns | What one event is |
|---|---|---|
| `logins_<month>.tsv` | `month`, `sub`, `idp`, `logins` | One `login` audit event. Fence records it after the user authenticates. |
| `downloads_<month>.tsv` | `month`, `sub`, `resource`, `downloads` | One `presigned_url` audit event with `action` `download` and status `200` or `302`, which are the responses that issue a URL. A bulk DRS request is one event. |

Rules for all files:

- `month` is a UTC calendar month, for example `2026-09`.
- Each row is one user `sub` and one breakdown value. A user with no events in the month has no row.
- The `sub` is the Fence user id. The files never contain a username. Anyone with Fence database access can map a `sub` back to a user, so treat the files as pseudonymized, not anonymous.
- An empty `sub` holds the events with no user, such as anonymous downloads of public data.
- `resource` holds the file's resource paths, sorted and joined with commas.
- The job leaves out every `sub` in `EXCLUDED_SUBS`.
- A month with no events gives a file with only the header line.

## Dispatch

The `input` is optional. Without a `month`, the job reports the last full month. The job rejects a month that has not ended.

```bash
curl -X POST "https://$COMMONS/job/dispatch" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action": "metrics-report", "input": {"month": "2026-09"}}'

curl "https://$COMMONS/job/status?UID=$UID" -H "Authorization: Bearer $ACCESS_TOKEN"
curl "https://$COMMONS/job/output?UID=$UID" -H "Authorization: Bearer $ACCESS_TOKEN"
```

When the job succeeds, the `output` is one JSON object with a link for each file:

```json
{"files": {"logins_2026-09.tsv": "https://...", "downloads_2026-09.tsv": "https://..."}}
```

When the job fails, the `output` is `{"error": "<reason>"}`, and Sower shows the job as failed.

The links expire 1 hour after the upload. Sower deletes the job pod, and with it the output, 1 hour after the job ends. Download the files within that hour.

## Required grants

The dispatcher needs all of these:

- `access` on `/sower` (service `job`), which Sower itself checks.
- `read` on `/services/audit/login` and `/services/audit/presigned_url` (service `audit`).

Sower's check is the same for every action. So the job asks Arborist for all of these grants before it reads any data, and fails if one is missing. Example `user.yaml`:

```yaml
authz:
  policies:
    - id: sower
      role_ids: [sower_user]
      resource_paths: [/sower]
    - id: audit_reader
      role_ids: [audit_reader]
      resource_paths: [/services/audit]
  roles:
    - id: sower_user
      permissions:
        - id: sower_access
          action: {service: job, method: access}
    - id: audit_reader
      permissions:
        - id: audit_reader_action
          action: {service: audit, method: read}
  users:
    operator@example.org:
      policies: [sower, audit_reader]
```

## Configuration

### Credentials file

The job reads the bucket name and AWS keys from `/metrics-report-creds.json`. The keys match the `config.json` of the `pelicanservice-g3auto` secret, so a commons can mount that secret:

```json
{
  "manifest_bucket_name": "my-bucket",
  "aws_access_key_id": "",
  "aws_secret_access_key": ""
}
```

The job writes each file to `metrics-report/<run time>/<file name>`, for example `metrics-report/20261002T140000Z/logins_2026-09.tsv`. Each run uses a new folder, so a re-run does not overwrite earlier files. The keys need `s3:PutObject` and `s3:GetObject` on `metrics-report/*`. To delete old files automatically, add an S3 lifecycle rule for the `metrics-report/` prefix.

### Environment variables

| Variable | Default | Description |
|---|---|---|
| `EXCLUDED_SUBS` | empty | Comma-separated `sub`s to leave out, for example `12,34`. Use the same list as the Grafana dashboards. The job fails if an entry is not an integer. |
| `AUDIT_SERVICE_URL` | `http://revproxy-service/audit` | Base URL of audit-service. The default goes through revproxy (see below). |
| `ARBORIST_URL` | `http://arborist-service` | Base URL of Arborist. |

Sower sets `ACCESS_TOKEN` and `INPUT_DATA`.

The job reads audit-service through revproxy, which forwards only `GET` requests to audit-service. If `global.netPolicy.enabled` is `true`, audit-service admits revproxy but not Sower job pods (label `app: sowerjob`), so setting `AUDIT_SERVICE_URL` to `http://audit-service` makes the job fail with a connection timeout after 10 seconds. With network policies, the revproxy route needs a gen3-helm version where the audit-service pods have the label `public: "yes"`. Arborist admits all pods, so the job calls `http://arborist-service` directly.

If audit-service sets `QUERY_TIMEBOX_MAX_DAYS` to less than 31, it rejects a one-month query, and the job fails with that error.

### Sower job configuration

Add this to `sower.sowerConfig` in the commons `values.yaml`:

```yaml
- name: metrics-report
  action: metrics-report
  container:
    name: job-task
    image: quay.io/cdis/metrics-report:master
    pull_policy: Always
    cpu-limit: "1"
    memory-limit: "256Mi"
    env:
      - name: EXCLUDED_SUBS
        value: ""
    volumeMounts:
      - name: metrics-report-creds-volume
        mountPath: /metrics-report-creds.json
        subPath: config.json
        readOnly: true
  restart_policy: Never
  volumes:
    - name: metrics-report-creds-volume
      secret:
        secretName: pelicanservice-g3auto
```

## Development

Run the unit tests:

```bash
poetry install
poetry run pytest
```
