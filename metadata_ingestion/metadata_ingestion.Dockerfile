FROM python:3.6

RUN pip install -e git+https://github.com/cdis/gen3sdk-python.git@feat/merge#egg=gen3
RUN pip install boto3==1.11.11

COPY . /gen3

WORKDIR /gen3

ENTRYPOINT [ "python" ]
CMD [ "metadata_ingestion_job.py" ]
