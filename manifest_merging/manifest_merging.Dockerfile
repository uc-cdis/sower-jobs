FROM python:3.6

RUN pip install gen3==2.5.0
RUN pip install boto3==1.11.11

COPY . /gen3

WORKDIR /gen3

ENTRYPOINT [ "python" ]
CMD [ "manifest_merging_job.py" ]