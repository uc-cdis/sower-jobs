FROM python:3.6

RUN git clone --single-branch --branch  feat/indexd_utils https://github.com/uc-cdis/gen3sdk-python ./gen3 && cd ./gen3 && git checkout b6b6b96e89ff42679f058cde7c4d8bd00bf81aa8 && cd ..

RUN pip install boto3==1.11.11

COPY . /gen3

WORKDIR /gen3

RUN python setup.py install

ENTRYPOINT [ "python" ]
CMD [ "manifest_indexing_job.py" ]