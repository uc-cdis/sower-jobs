JOB_REQUIRES = {
    "arborist_url": "http://arborist-service",
    "job_access_req": (
        [
            #  use indexd permission until more granular sower permissions are
            #  implemented (https://ctds-planx.atlassian.net/browse/PXP-6462)
            {"resource": "/sower", "action": {"service": "job", "method": "access"}},
            {
                "resource": "/programs",
                "action": {"service": "indexd", "method": "write"},
            },
        ]
    ),
}
