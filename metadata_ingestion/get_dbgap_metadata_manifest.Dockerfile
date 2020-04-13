FROM python:3.6

# RUN pip install gen3==2.2.3
RUN pip install -e git+https://github.com/uc-cdis/gen3sdk-python.git@707bcad8ad5c55cf33a2161e44469ec373c97e51#egg=gen3

RUN pip install boto3==1.11.11

RUN apt-get update
RUN apt-get install -y git
RUN apt install -y pipenv

COPY . /gen3

WORKDIR /gen3

# get the dbgap extract tool and pull latest release/tag
RUN git clone https://github.com/uc-cdis/dbgap-extract.git \
    && cd dbgap-extract \
    && git pull origin master \
    && git fetch --tags \
    && tag=$(git describe --tags `git rev-list --tags --max-count=1`) \
    && git checkout $tag -b latest \
    && pipenv install \
    && cd ..

ENTRYPOINT [ "python" ]
CMD [ "get_dbgap_metadata_manifest.py" ]
