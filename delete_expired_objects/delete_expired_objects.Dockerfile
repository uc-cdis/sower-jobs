FROM quay.io/cdis/python:python3.9-buster-2.0.0

RUN pip install gen3==4.9.3

COPY . /gen3

WORKDIR /gen3

ENTRYPOINT [ "bash", "-c", "echo 'pod started'; python delete_expired_objects_job.py; echo 'pod ended'" ]
