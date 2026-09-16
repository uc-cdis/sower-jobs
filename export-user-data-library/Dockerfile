ARG AZLINUX_BASE_VERSION=3.13-buildbase

FROM quay.io/cdis/amazonlinux-base:${AZLINUX_BASE_VERSION}

RUN pip install --upgrade pip && pip3 install poetry
RUN poetry config virtualenvs.create false

COPY pyproject.toml /gen3/
COPY poetry.lock /gen3/
WORKDIR /gen3
COPY --chown=gen3:gen3 export_user_data_library /gen3/export_user_data_library

RUN poetry install
RUN mkdir export


ENTRYPOINT [ "bash", "-c", "python -m export_user_data_library.main"]
