# sower-jobs
Repos for storing all sower jobs


### Manifest Indexing

It contains jobs for indexing manifest and downloading indexd manifest

#### indexing manifest

The following is a manifest config for indexing manifest job and downloading indexd manifest

```
{
      "name": "manifest-indexing",
      "action": "index-object-manifest",
      "container": {
        "name": "job-task",
        "image": "quay.io/cdis/manifest-indexing:master",
        "pull_policy": "Always",
        "env": [
          {
            "name": "GEN3_HOSTNAME",
            "valueFrom": {
              "configMapKeyRef": {
                "name": "manifest-global",
                "key": "hostname"
              }
            }
          }
        ],
        "volumeMounts": [
          {
            "name": "manifest-indexing-creds-volume",
            "readOnly": true,
            "mountPath": "/manifest-indexing-creds.json",
            "subPath": "config.json"
          }
        ],
        "cpu-limit": "1",
        "memory-limit": "1Gi"
      },
      "volumes": [
        {
          "name": "manifest-indexing-creds-volume",
          "secret": {
            "secretName": "manifestindexing-g3auto"
          }
        }
      ],
      "restart_policy": "Never"
    }
```

```
{
      "name": "indexd-manifest",
      "action": "download-indexd-manifest",
      "container": {
        "name": "job-task",
        "image": "quay.io/cdis/download-indexd-manifest:master",
        "pull_policy": "Always",
        "env": [
          {
            "name": "GEN3_HOSTNAME",
            "valueFrom": {
              "configMapKeyRef": {
                "name": "manifest-global",
                "key": "hostname"
              }
            }
          }
        ],
        "volumeMounts": [
          {
            "name": "manifest-indexing-creds-volume",
            "readOnly": true,
            "mountPath": "/manifest-indexing-creds.json",
            "subPath": "config.json"
          }
        ],
        "cpu-limit": "1",
        "memory-limit": "1Gi"
      },
      "volumes": [
        {
          "name": "manifest-indexing-creds-volume",
          "secret": {
            "secretName": "manifestindexing-g3auto"
          }
        }
      ],
      "restart_policy": "Never"
    }
```