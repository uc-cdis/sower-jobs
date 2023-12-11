FROM quay.io/cdis/python:python3.9-buster-2.0.0

RUN pip install --upgrade pip && pip3 install poetry
RUN poetry config virtualenvs.create false

COPY *.py /gen3/
COPY pyproject.toml /gen3/
COPY poetry.lock /gen3/

WORKDIR /gen3

RUN poetry install
RUN mkdir export

# clean up any disk space in use from the /export dir once the job is complete
ENTRYPOINT [ "bash", "-c", "python export_zip_from_manifest_job.py; rm -rf export/" ]
