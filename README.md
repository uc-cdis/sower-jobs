# sower-jobs
Repos for storing all sower jobs

## Metadata

### Metadata Ingestion

Contains job for ingesting metadata from a file.

> NOTE: These job configurations assume you have setup Service Accounts in k8s with fine-grained IAM roles in AWS to interact with an S3 bucket. See [Cloud Automation docs](https://github.com/uc-cdis/cloud-automation/blob/master/doc/iam-serviceaccount.md).

> IMPORTANT NOTE: You must supply the correct "serviceAccountName" in the following examples. By default these are in the form "sower-jobs-${hostname//./-}-sa". Example: `sower-jobs-example-planx-pla-net-sa`. Cloud Automation enables the creation of the necessary infrastructure (buckets, SAs, roles) by running `gen3 kube-setup-sower-jobs`.

```json
{
  "name": "ingest-metadata-manifest",
  "action": "ingest-metadata-manifest",
  "serviceAccountName": "sower-jobs-${hostname//./-}-sa",
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
        "subPath": "creds.json"
      }
    ],
    "cpu-limit": "1",
    "memory-limit": "1Gi"
  },
  "volumes": [
    {
      "name": "creds-volume",
      "secret": {
        "secretName": "sower-jobs-g3auto"
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
  "serviceAccountName": "sower-jobs-${hostname//./-}-sa",
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
        "subPath": "creds.json"
      }
    ],
    "cpu-limit": "1",
    "memory-limit": "1Gi"
  },
  "volumes": [
    {
      "name": "creds-volume",
      "secret": {
        "secretName": "sower-jobs-g3auto"
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
  "serviceAccountName": "sower-jobs-${hostname//./-}-sa",
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
        "name": "sower-jobs-creds-volume",
        "readOnly": true,
        "mountPath": "/creds.json",
        "subPath": "creds.json"
      }
    ],
    "cpu-limit": "1",
    "memory-limit": "1Gi"
  },
  "volumes": [
    {
      "name": "sower-jobs-creds-volume",
      "secret": {
        "secretName": "sower-jobs-g3auto"
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
  "serviceAccountName": "sower-jobs-${hostname//./-}-sa",
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
        "name": "sower-jobs-creds-volume",
        "readOnly": true,
        "mountPath": "/creds.json",
        "subPath": "creds.json"
      }
    ],
    "cpu-limit": "1",
    "memory-limit": "1Gi"
  },
  "volumes": [
    {
      "name": "sower-jobs-creds-volume",
      "secret": {
        "secretName": "sower-jobs-g3auto"
      }
    }
  ],
  "restart_policy": "Never"
}
```

The secret `sower-jobs-g3auto` should be setup automatically with Cloud Automation and contains a JSON blob with:

```json
{
  "index-object-manifest": {
    "job_requires": {
      "arborist_url": "http://arborist-service",
      "job_access_req": [
        {
          "resource": "/sower",
          "action": {
            "service": "job",
            "method": "access"
          }
        },
        {
          "resource": "/programs",
          "action": {
            "service": "indexd",
            "method": "write"
          }
        }
      ]
    },
    "bucket": "some-bucket",
    "indexd_user": "",
    "indexd_password": ""
  },
  "download-indexd-manifest": {
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
    "bucket": "some-bucket"
  },
  "get-dbgap-metadata": {
    "job_requires": {
      "arborist_url": "http://arborist-service",
      "job_access_req": [
        {
          "resource": "/sower",
          "action": {
            "service": "job",
            "method": "access"
          }
        },
        {
          "resource": "/mds_gateway",
          "action": {
            "service": "mds_gateway",
            "method": "access"
          }
        }
      ]
    },
    "bucket": "some-bucket"
  },
  "ingest-metadata-manifest": {
    "job_requires": {
      "arborist_url": "http://arborist-service",
      "job_access_req": [
        {
          "resource": "/sower",
          "action": {
            "service": "job",
            "method": "access"
          }
        },
        {
          "resource": "/mds_gateway",
          "action": {
            "service": "mds_gateway",
            "method": "access"
          }
        }
      ]
    },
    "bucket": "some-bucket"
  }
}
```

> NOTE: some of the above fields will get set to a default value if not provided or empty. Specifically you can leave out "arborist_url" and "job_access_req" and the default Arborist url and access requirements will be set. Also note that the "bucket" and AWS creds can be the same for all the jobs or different if necessary

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
