FROM quay.io/cdis/python:3.8-buster

RUN pip install git+https://github.com/uc-cdis/gen3sdk-python.git@ca58b94ebcc1377122da10b716d7a01722cfc69b
RUN pip install boto3==1.11.11
RUN pip install cdiserrors


COPY *.py /gen3/

WORKDIR /gen3

RUN mkdir export

# clean up any disk space in use from the /export dir once the job is complete
ENTRYPOINT [ "bash", "-c", "python export_zip_from_manifest_job.py; rm -rf export/" ]
