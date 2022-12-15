FROM quay.io/cdis/python:python3.9-buster-2.0.0

RUN pip install "gen3>=4.16.0,<5.0.0"

COPY . /gen3

WORKDIR /gen3

ENTRYPOINT [ "bash", "-c", "python metadata_delete_expired_objects_job.py" ]
