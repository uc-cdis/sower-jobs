JOB_REQUIRES = {
    "arborist_url": "http://arborist-service",
    "job_access_req": (
        [
            {"resource": "/sower", "action": {"service": "job", "method": "access"}},
            {
                "resource": "/programs",
                "action": {"service": "indexd", "method": "write"},
            },
        ],
    ),
}
