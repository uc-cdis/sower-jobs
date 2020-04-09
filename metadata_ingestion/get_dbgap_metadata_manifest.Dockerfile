FROM python:3.6

# RUN pip install gen3==2.2.3
RUN pip install -e git+https://github.com/uc-cdis/gen3sdk-python.git@8964ff49150360c60675eb4aa74016ee53f1a875#egg=gen3

RUN pip install boto3==1.11.11

RUN apt-get update
RUN apt-get install -y git

COPY . /gen3

WORKDIR /gen3

RUN git clone https://github.com/uc-cdis/dbgap-extract.git
RUN cd dbgap-extract
RUN git pull origin master

# get the latest release/tag
RUN git fetch --tags
RUN tag=$(git describe --tags `git rev-list --tags --max-count=1`)
RUN git checkout $tag -b latest

RUN pipenv install
RUN ..

ENTRYPOINT [ "python" ]
CMD [ "get_dbgap_metadata_manifest.py" ]
