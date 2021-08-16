FROM quay.io/cdis/python:3.7-stretch

RUN pip install git+https://github.com/uc-cdis/gen3sdk-python.git@feat/drs_download_federated_manifest
RUN pip install boto3==1.11.11
RUN pip install cdiserrors


COPY *.py /gen3/

WORKDIR /gen3

RUN mkdir export

ENTRYPOINT [ "python" ]
CMD [ "export_zip_from_manifest_job.py" ]
