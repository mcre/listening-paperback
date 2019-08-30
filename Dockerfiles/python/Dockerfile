FROM python:3.8.0b2-alpine

WORKDIR /work

RUN \
    apk update && \
    pip install --upgrade pip && \
    apk add --update --no-cache --virtual .build-deps gcc musl-dev zlib-dev && \
    apk add --update jpeg-dev freetype-dev && \
    pip install regex boto3 mutagen Pillow jaconv && \
    apk del .build-deps gcc musl-dev zlib-dev
