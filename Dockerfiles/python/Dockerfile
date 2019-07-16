FROM python:3.8.0b2-alpine

WORKDIR /app

RUN \
    apk add --no-cache --virtual .build-deps gcc musl-dev && \
    pip install regex && \
    apk del .build-deps gcc musl-dev