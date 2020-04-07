FROM python:3.6

# RUN pip install gen3==2.2.3
RUN pip install -e git+https://github.com/uc-cdis/gen3sdk-python.git@8964ff49150360c60675eb4aa74016ee53f1a875#egg=gen3

RUN pip install boto3==1.11.11

COPY . /gen3

WORKDIR /gen3

ENTRYPOINT [ "python" ]
CMD [ "metadata_ingestion_job.py" ]
