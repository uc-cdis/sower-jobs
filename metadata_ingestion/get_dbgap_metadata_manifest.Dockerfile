ARG AZLINUX_BASE_VERSION=3.13-buildbase

FROM quay.io/cdis/amazonlinux-base:${AZLINUX_BASE_VERSION}

RUN python3.13 -m pip install --upgrade pip
RUN pip3 install pipenv

COPY . /gen3

WORKDIR /gen3

# get the dbgap extract tool and pull latest release/tag
RUN git clone https://github.com/uc-cdis/dbgap-extract.git \
    && cd dbgap-extract \
    && git pull origin master \
    && git fetch --tags \
    && tag=$(git describe --tags `git rev-list --max-count=1 --tags`) \
    && git checkout $tag -b latest \
    && pipenv install \
    && pipenv install gen3>=2.4.0 \
    && pipenv install boto3>=1.41.3 \
    && cd ..

ENTRYPOINT [ "python" ]
CMD [ "get_dbgap_metadata_manifest.py" ]
