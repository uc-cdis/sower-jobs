# sower-jobs
Repos for storing all sower jobs

## Metadata

### Metadata Ingestion

Contains job for ingesting metadata from a file.

```json
{
  "name": "ingest-metadata-manifest",
  "action": "ingest-metadata-manifest",
  "container": {
    "name": "job-task",
    "image": "quay.io/cdis/metadata-manifest-ingestion:master",
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
        "name": "creds-volume",
        "readOnly": true,
        "mountPath": "/creds.json",
        "subPath": "config.json"
      }
    ],
    "cpu-limit": "1",
    "memory-limit": "1Gi"
  },
  "volumes": [
    {
      "name": "creds-volume",
      "secret": {
        "secretName": "manifestindexing-g3auto"
      }
    }
  ],
  "restart_policy": "Never"
}
```

### Get dbGaP Metadata File

Contains job to parse dbGaP and associate samples to indexed file objects and returns the file. You can then QA the file and use the "Metadata Ingestion" job above to get the metadata into a commons.

```json
{
  "name": "get-dbgap-metadata",
  "action": "get-dbgap-metadata",
  "container": {
    "name": "job-task",
    "image": "quay.io/cdis/get-dbgap-metadata:master",
    "pull_policy": "Always",
    "env": [],
    "volumeMounts": [
      {
        "name": "creds-volume",
        "readOnly": true,
        "mountPath": "/creds.json",
        "subPath": "config.json"
      }
    ],
    "cpu-limit": "1",
    "memory-limit": "1Gi"
  },
  "volumes": [
    {
      "name": "creds-volume",
      "secret": {
        "secretName": "manifestindexing-g3auto"
      }
    }
  ],
  "restart_policy": "Never"
}
```

### Manifest Indexing

It contains jobs for indexing manifest and downloading indexd manifest

#### indexing manifest

The following is a manifest config for indexing manifest job and downloading indexd manifest

```json
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

```json
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


The secret `manifestindexing-g3auto` should be a JSON blob with:

```json
{
  "job_requires": {
    "arborist_url": "http://arborist-service",
    "job_access_req": [
      {
        "resource": "/sower",
        "action": {
          "service": "job",
          "method": "access"
        }
      }
    ]
  },
  "aws_access_key_id": "foo",
  "aws_secret_access_key": "bar"
}
```


## Setting up Image Build in Quay

* Go to quay.io and "Create a new repository" by clicking the plus at the top
* Use whatever name you want, you'll need to use this same name in the "image" option in the above example configurations
  * For example, we can use `get-dbgap-metadata` and then reference the image with `quay.io/cdis/get-dbgap-metadata:master`
* Select "Public" visibility and "Link to a Github Repository Push"
* Click "Create Public Repo" button
* Select the uc-cdis org and find this repo (sower-jobs)
* Keep default "Trigger for all branches and tags (default)" option
* Hit "Continue" button
* Leave defaults for "Configure Tagging" section
* Hit "Continue" button
* For "Select Dockerfile" enter the path to the new Dockerfile you're trying to build
  * NOTE: If you're trying to build something on a branch for testing this box won't autopopulate but you can still type the path to the file on the branch and it'll work
  * Example: `/metadata_ingestion/get_dbgap_metadata_manifest.Dockerfile`
* For "Select Context" section, enter the folder path to where the Dockerfile is
  * Example: `/metadata_ingestion`
* If the dockerfile is on a branch you may get a warning "Verification Warning: Specified Dockerfile path for the trigger was not found on the main branch. This trigger may fail."
  * This is fine. Hit "Continue" button
* Hit final green "Continue" button!
