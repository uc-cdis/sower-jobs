FROM quay.io/cdis/python:3.6

RUN pip install gen3==4.9.3

COPY . /gen3

WORKDIR /gen3

ENTRYPOINT [ "python" ]
CMD [ "delete_temp_objects_job.py" ]
