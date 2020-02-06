FROM python:3.6

RUN pip install -e git+https://git@github.com/uc-cdis/wool.git#egg=wool

RUN git clone --single-branch --branch  feat/indexd_utils https://github.com/uc-cdis/gen3sdk-python ./gen3 && cd ./gen3 && git checkout 81d704d277779c68dbc45652f7273bac4ceec323 && cd ..

RUN pip install boto3==1.11.11

COPY . /gen3

WORKDIR /gen3

RUN python setup.py install

ENTRYPOINT [ "python" ]
CMD [ "manifest_indexing_job.py" ]