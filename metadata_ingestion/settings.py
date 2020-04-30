JOB_REQUIRES = {
    "arborist_url": "http://arborist-service",
    "job_access_req": (
        [
            {"resource": "/sower", "action": {"service": "job", "method": "access"}},
            {
                "resource": "/mds_gateway",
                "action": {"service": "mds_gateway", "method": "access"},
            },
        ]
    ),
}
