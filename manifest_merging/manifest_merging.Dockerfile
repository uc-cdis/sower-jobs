FROM python:3.6

RUN pip install git+https://github.com/uc-cdis/gen3sdk-python.git@feat/merge
RUN pip install boto3==1.11.11

COPY . /gen3

WORKDIR /gen3

ENTRYPOINT [ "python" ]
CMD [ "manifest_merging_job.py" ]
