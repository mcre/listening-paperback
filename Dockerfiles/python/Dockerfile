FROM python:3.8.0b2-alpine

WORKDIR /work

RUN \
    apk update && \
    pip install --upgrade pip && \
    apk add --update --no-cache --virtual .build-deps gcc musl-dev && \
    pip install regex boto3 && \
    apk del .build-deps gcc musl-dev
