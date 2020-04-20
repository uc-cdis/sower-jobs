FROM python:3.6

# RUN pip install gen3==2.2.3
RUN pip install -e git+https://github.com/uc-cdis/gen3sdk-python.git@97e8197cfd86e6a1cdf0c66f19fb0afce5e79edb#egg=gen3

RUN pip install boto3==1.11.11

COPY . /gen3

WORKDIR /gen3

ENTRYPOINT [ "python" ]
CMD [ "metadata_ingestion_job.py" ]
