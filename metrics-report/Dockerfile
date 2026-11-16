ARG AZLINUX_BASE_VERSION=3.13-buildbase

FROM quay.io/cdis/amazonlinux-base:${AZLINUX_BASE_VERSION}

RUN pip install --upgrade pip && pip3 install poetry
RUN poetry config virtualenvs.create false

COPY pyproject.toml /gen3/
COPY poetry.lock /gen3/
WORKDIR /gen3
COPY --chown=gen3:gen3 metrics_report /gen3/metrics_report

RUN poetry install --only main

ENTRYPOINT ["python", "-m", "metrics_report.main"]
