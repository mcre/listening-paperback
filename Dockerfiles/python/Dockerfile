FROM python:3.8.0b2-alpine

WORKDIR /work

RUN \
    # regex dependencies
    apk add --no-cache --virtual .build-deps gcc musl-dev && \
    # Pillow dependencies
    apk add --no-cache --virtual jpeg-dev zlib-dev freetype-dev lcms2-dev openjpeg-dev tiff-dev tk-dev tcl-dev harfbuzz-dev fribidi-dev && \
    pip install --upgrade pip && \
    pip install regex boto3 moviepy && \
    apk del .build-deps gcc musl-dev jpeg-dev zlib-dev freetype-dev lcms2-dev openjpeg-dev tiff-dev tk-dev tcl-dev harfbuzz-dev fribidi-dev
