FROM python:3.8.0b2-alpine

WORKDIR /work

RUN \
    apk update && \
    pip install --upgrade pip && \
    # regex build tools
    apk add --no-cache --virtual .build-deps gcc musl-dev && \
    # moviepy dependencies
    apk add --no-cache ffmpeg openjpeg-dev tiff-dev jpeg-dev zlib-dev freetype-dev lcms2-dev tiff-dev tk-dev tcl-dev harfbuzz-dev fribidi-dev && \
    # apps
    pip install regex boto3 moviepy && \
    # clean build tools
    apk del .build-deps gcc musl-dev
