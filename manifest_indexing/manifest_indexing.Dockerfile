FROM python:3.6

RUN git clone --single-branch --branch  feat/indexd_utils https://github.com/uc-cdis/gen3sdk-python ./gen3 && cd ./gen3 && git checkout 7513b8242f7e7acfed10b9dda8ab59e6fb0e4c7a && cd ..

RUN pip install boto3==1.11.11

COPY . /gen3

WORKDIR /gen3

RUN python setup.py install

ENTRYPOINT [ "python" ]
CMD [ "manifest_indexing_job.py" ]