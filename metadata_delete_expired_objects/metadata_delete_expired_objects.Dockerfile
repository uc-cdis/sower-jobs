ARG AZLINUX_BASE_VERSION=3.13-buildbase

FROM quay.io/cdis/amazonlinux-base:${AZLINUX_BASE_VERSION}

RUN pip install "gen3>=4.16.0,<5.0.0"

COPY . /gen3

WORKDIR /gen3

ENTRYPOINT [ "bash", "-c", "python metadata_delete_expired_objects_job.py" ]
