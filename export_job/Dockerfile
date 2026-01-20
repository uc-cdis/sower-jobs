ARG AZLINUX_BASE_VERSION=3.13-buildbase

FROM quay.io/cdis/amazonlinux-base:${AZLINUX_BASE_VERSION}

RUN pip install --upgrade pip && pip3 install poetry
RUN poetry config virtualenvs.create false

COPY --chown=gen3:gen3 *.py /gen3/
COPY pyproject.toml /gen3/
COPY poetry.lock /gen3/

WORKDIR /gen3

RUN poetry install
RUN mkdir export

# clean up any disk space in use from the /export dir once the job is complete
ENTRYPOINT [ "bash", "-c", "python export_zip_from_manifest_job.py; rm -rf export/" ]
