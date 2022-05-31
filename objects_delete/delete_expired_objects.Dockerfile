FROM quay.io/cdis/python:python3.9-buster-2.0.0

RUN pip install gen3==4.9.3

COPY . /gen3

WORKDIR /gen3

ENTRYPOINT [ "python" ]
CMD [ "delete_expired_objects_job.py" ]
