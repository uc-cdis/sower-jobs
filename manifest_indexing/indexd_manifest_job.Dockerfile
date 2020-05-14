FROM python:3.6

RUN pip install gen3==2.3.0
RUN pip install boto3==1.11.11

COPY . /gen3

WORKDIR /gen3

ENTRYPOINT [ "python" ]
CMD [ "indexd_manifest_job.py" ]
