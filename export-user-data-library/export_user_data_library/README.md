# Flow

1. Get list and items from data library
2. Create export urls for each
    3. Use type, a class for each type
4. Create export response
    5. one for normal
    6. one for manifest

```json
{
  "lists": {
    "021d2d9a-9dd0-4ade-9d37-bb9e8fa1df05": {
      "version": 0,
      "creator": "2161",
      "authz": {
        "authz": [
          "/users/2161/user-data-library/lists/021d2d9a-9dd0-4ade-9d37-bb9e8fa1df05"
        ],
        "version": 0
      },
      "name": "Test New",
      "created_time": "2026-04-07T16:50:34.868712+00:00",
      "updated_time": "2026-04-06T17:35:02.965278+00:00",
      "items": {
        "d502d180-c579-4dd3-9946-2b6febd5f4ce": {
          "guid": "d502d180-c579-4dd3-9946-2b6febd5f4ce",
          "name": "Test PFB",
          "type": "GA4GH_DRS",
          "description": "Serialized PFB created with test data from data-simulator",
          "dataset_guid": "phs000007.v31.p12.c1",
          "display_name": "Test PFB"
        },
        "dg.4503/753cc1c8-3986-41cc-9a1f-5aa8ffa7093a": {
          "guid": "dg.4503/753cc1c8-3986-41cc-9a1f-5aa8ffa7093a",
          "name": "Test Open Access Datasets PFB",
          "type": "GA4GH_DRS",
          "description": "PFB of all open access datasets in BDC Staging",
          "dataset_guid": "phs000007.v31.p12.c1",
          "display_name": "Test Open Access Datasets PFB"
        },
        "dg.4503/a8a8e955-b205-446a-b480-145f505e4c95": {
          "guid": "dg.4503/a8a8e955-b205-446a-b480-145f505e4c95",
          "name": "Test PFB Many Files",
          "type": "GA4GH_DRS",
          "description": "Serialized PFB with 200k+ files in reference_file node",
          "dataset_guid": "phs000007.v31.p12.c1",
          "display_name": "Test PFB Many Files"
        },
        "dg.712C/60215853-eb94-4c06-8ea5-8b6ff6e2c1fe": {
          "guid": "dg.712C/60215853-eb94-4c06-8ea5-8b6ff6e2c1fe",
          "name": "Test Raw PFB",
          "type": "GA4GH_DRS",
          "description": "Raw Serialized PFB created with drs guids from data-simulator",
          "dataset_guid": "phs000007.v31.p12.c1",
          "display_name": "Test Raw PFB"
        }
      }
    },
    "20257133-a5a4-47d1-a0a3-a72206a7f1d5": {
      "version": 0,
      "creator": "2161",
      "authz": {
        "authz": [
          "/users/2161/user-data-library/lists/20257133-a5a4-47d1-a0a3-a72206a7f1d5"
        ],
        "version": 0
      },
      "name": "My Saved 123123123123 12312123",
      "created_time": "2025-04-30T22:01:10.831048+00:00",
      "updated_time": "2025-04-30T21:58:20.173137+00:00",
      "items": {}
    },
    "95aac745-fb7d-4681-9212-8f5fd9d3e0e0": {
      "version": 0,
      "creator": "2161",
      "authz": {
        "authz": [
          "/users/2161/user-data-library/lists/95aac745-fb7d-4681-9212-8f5fd9d3e0e0"
        ],
        "version": 0
      },
      "name": "A new list",
      "created_time": "2026-04-07T19:13:37.265979+00:00",
      "updated_time": "2026-04-06T17:35:02.965278+00:00",
      "items": {
        "d502d180-c579-4dd3-9946-2b6febd5f4ce": {
          "guid": "d502d180-c579-4dd3-9946-2b6febd5f4ce",
          "name": "Test PFB",
          "type": "GA4GH_DRS",
          "description": "Serialized PFB created with test data from data-simulator",
          "dataset_guid": "phs000007.v31.p12.c1",
          "display_name": "Test PFB"
        },
        "dg.4503/753cc1c8-3986-41cc-9a1f-5aa8ffa7093a": {
          "guid": "dg.4503/753cc1c8-3986-41cc-9a1f-5aa8ffa7093a",
          "name": "Test Open Access Datasets PFB",
          "type": "GA4GH_DRS",
          "description": "PFB of all open access datasets in BDC Staging",
          "dataset_guid": "phs000007.v31.p12.c1",
          "display_name": "Test Open Access Datasets PFB"
        },
        "dg.4503/a8a8e955-b205-446a-b480-145f505e4c95": {
          "guid": "dg.4503/a8a8e955-b205-446a-b480-145f505e4c95",
          "name": "Test PFB Many Files",
          "type": "GA4GH_DRS",
          "description": "Serialized PFB with 200k+ files in reference_file node",
          "dataset_guid": "phs000007.v31.p12.c1",
          "display_name": "Test PFB Many Files"
        },
        "dg.712C/60215853-eb94-4c06-8ea5-8b6ff6e2c1fe": {
          "guid": "dg.712C/60215853-eb94-4c06-8ea5-8b6ff6e2c1fe",
          "name": "Test Raw PFB",
          "type": "GA4GH_DRS",
          "description": "Raw Serialized PFB created with drs guids from data-simulator",
          "dataset_guid": "phs000007.v31.p12.c1",
          "display_name": "Test Raw PFB"
        }
      }
    },
    "ad95834a-8ba7-4385-b7aa-22ccd7384bd0": {
      "version": 0,
      "creator": "2161",
      "authz": {
        "authz": [
          "/users/2161/user-data-library/lists/ad95834a-8ba7-4385-b7aa-22ccd7384bd0"
        ],
        "version": 0
      },
      "name": "Test 3",
      "created_time": "2025-04-02T19:00:59.164882+00:00",
      "updated_time": "2025-04-02T18:18:20.626198+00:00",
      "items": {
        "d502d180-c579-4dd3-9946-2b6febd5f4ce": {
          "guid": "d502d180-c579-4dd3-9946-2b6febd5f4ce",
          "name": "Test PFB",
          "type": "GA4GH_DRS",
          "description": "Serialized PFB created with test data from data-simulator",
          "dataset_guid": "phs000007.v31.p12.c1",
          "display_name": "Test PFB"
        },
        "dg.712C/60215853-eb94-4c06-8ea5-8b6ff6e2c1fe": {
          "guid": "dg.712C/60215853-eb94-4c06-8ea5-8b6ff6e2c1fe",
          "name": "Test Raw PFB",
          "type": "GA4GH_DRS",
          "description": "Raw Serialized PFB created with drs guids from data-simulator",
          "dataset_guid": "phs000007.v31.p12.c1",
          "display_name": "Test Raw PFB"
        }
      }
    },
    "c6f0e9b9-1695-44ca-ba14-222459db19ab": {
      "version": 0,
      "creator": "2161",
      "authz": {
        "authz": [
          "/users/2161/user-data-library/lists/c6f0e9b9-1695-44ca-ba14-222459db19ab"
        ],
        "version": 0
      },
      "name": "Jacob List",
      "created_time": "2025-03-07T17:57:40.823528+00:00",
      "updated_time": "2025-11-19T21:06:58.825426+00:00",
      "items": {
        "d502d180-c579-4dd3-9946-2b6febd5f4ce": {
          "guid": "d502d180-c579-4dd3-9946-2b6febd5f4ce",
          "name": "Test PFB",
          "type": "GA4GH_DRS",
          "description": "Serialized PFB created with test data from data-simulator",
          "dataset_guid": "phs000007.v31.p12.c1",
          "display_name": "Test PFB"
        },
        "dg.712C/60215853-eb94-4c06-8ea5-8b6ff6e2c1fe": {
          "guid": "dg.712C/60215853-eb94-4c06-8ea5-8b6ff6e2c1fe",
          "name": "Test Raw PFB",
          "type": "GA4GH_DRS",
          "description": "Raw Serialized PFB created with drs guids from data-simulator",
          "dataset_guid": "phs000007.v31.p12.c1",
          "display_name": "Test Raw PFB"
        }
      }
    },
    "d3d94b00-f5f2-430f-8b9f-b74b7e2e6a49": {
      "version": 0,
      "creator": "2161",
      "authz": {
        "authz": [
          "/users/2161/user-data-library/lists/d3d94b00-f5f2-430f-8b9f-b74b7e2e6a49"
        ],
        "version": 0
      },
      "name": "New list",
      "created_time": "2025-04-02T18:20:32.909074+00:00",
      "updated_time": "2025-04-02T18:39:54.687115+00:00",
      "items": {}
    },
    "d7e3c20f-030c-44c0-a9bc-ee5548b6e593": {
      "version": 0,
      "creator": "2161",
      "authz": {
        "authz": [
          "/users/2161/user-data-library/lists/d7e3c20f-030c-44c0-a9bc-ee5548b6e593"
        ],
        "version": 0
      },
      "name": "Test 2",
      "created_time": "2025-04-02T18:39:30.502704+00:00",
      "updated_time": "2025-04-02T18:18:20.626198+00:00",
      "items": {}
    },
    "f6c9b51b-3b8a-431d-9edb-5a821574323d": {
      "version": 0,
      "creator": "2161",
      "authz": {
        "authz": [
          "/users/2161/user-data-library/lists/f6c9b51b-3b8a-431d-9edb-5a821574323d"
        ],
        "version": 0
      },
      "name": "Test",
      "created_time": "2025-04-02T18:27:02.453331+00:00",
      "updated_time": "2025-04-02T18:18:20.748680+00:00",
      "items": {
        "d502d180-c579-4dd3-9946-2b6febd5f4ce": {
          "guid": "d502d180-c579-4dd3-9946-2b6febd5f4ce",
          "name": "Test PFB",
          "type": "GA4GH_DRS",
          "description": "Serialized PFB created with test data from data-simulator",
          "dataset_guid": "phs000007.v31.p12.c2",
          "display_name": "Test PFB"
        },
        "dg.712C/60215853-eb94-4c06-8ea5-8b6ff6e2c1fe": {
          "guid": "dg.712C/60215853-eb94-4c06-8ea5-8b6ff6e2c1fe",
          "name": "Test Raw PFB",
          "type": "GA4GH_DRS",
          "description": "Raw Serialized PFB created with drs guids from data-simulator",
          "dataset_guid": "phs000007.v31.p12.c2",
          "display_name": "Test Raw PFB"
        }
      }
    }
  }
}
```
