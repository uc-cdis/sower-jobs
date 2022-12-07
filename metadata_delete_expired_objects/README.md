# Metadata Delete Expired Objects Job

The `metadata delete expired objects` job performs a query to fetch the current metadata objects that have an `_expires_at` field and performs a `delete operation` on all the objects that are expired. The `_expires_at` value is expected to be a timestamp.

This job requires:
- Metadata Service >= 1.7.0 or 2022.06
- Arborist => 4.0.0 or 2022.12
- Fence => 6.1.0 or 2022.10
- Gen3 SDK >= 4.16.0
- Pelican export >= ? (TODO add `_expires_at` logic)

This job requires providing a configuration file in a `metadata-delete-expired-objects-g3auto` secret. The path to the configuration file can be set using the environment variable `CONFIG_PATH` (default: `/mnt/config.json`).
```
{
  "hostname": "https://my-commons.org",
  "oidc_client_id": "",
  "oidc_client_secret": ""
}
```

The `oidc_client_id` and `oidc_client_secret` and credentials for an OIDC client with the "client_credentials" grant and "delete" access in Metadata Service and Fence.

Sower job configuration:
```json
{
  "name": "metadata-delete-expired-objects",
  "action": "meatdata_delete_expired_objects",
  "container": {
    "name": "metadata-delete-job-task",
    "image": "quay.io/cdis/metadata-delete-expired-objects:master",
    "pull_policy": "Always",
    "volumeMounts": [
      {
        "name": "config-volume",
        "mountPath": "/mnt"
      }
    ],
    "cpu-limit": "1",
    "memory-limit": "4Gi"
  },
  "volumes": [
    {
      "name": "config-volume",
      "secret": {
        "secretName": "metadata-delete-expired-objects-g3auto"
      }
    }
  ],
  "restart_policy": "Never"
}
```

Note: For cloud-automation users, this job can also be set up as a cronjob by running `gen3 kube-setup-metadata-delete-expired-objects-job`.
