FROM quay.io/cdis/python:python3.9-buster-2.0.0

RUN pip install git+https://git@github.com/uc-cdis/gen3sdk-python.git@feat/auth-client#egg=gen3

COPY . /gen3

WORKDIR /gen3

ENTRYPOINT [ "bash", "-c", "python metadata_delete_expired_objects_job.py" ]
