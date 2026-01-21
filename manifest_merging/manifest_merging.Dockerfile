ARG AZLINUX_BASE_VERSION=3.13-buildbase

FROM quay.io/cdis/amazonlinux-base:${AZLINUX_BASE_VERSION}

RUN pip install gen3>=2.4.0
RUN pip install boto3>=1.41.3

COPY . /gen3

WORKDIR /gen3

ENTRYPOINT [ "python" ]
CMD [ "manifest_merging_job.py" ]
