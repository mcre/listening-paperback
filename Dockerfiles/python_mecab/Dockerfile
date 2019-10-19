FROM mcre/mecab-bottle:20190822

WORKDIR /work

RUN \
    apt-get update && \
    apt-get -y install build-essential && \
    pip install --upgrade pip && \
    pip install mecab-python3 jaconv regex && \
    apt-get clean
CMD []