FROM jrottenberg/ffmpeg:4.1-alpine311

WORKDIR /work

RUN \
    apk add --no-cache python3 && \
    if [ ! -e /usr/bin/python ]; then ln -sf python3 /usr/bin/python ; fi && \
    pip3 install --no-cache --upgrade pip setuptools wheel && \
    if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi
RUN \
    apk update && \
    pip3 install --upgrade pip && \
    # build tools (多分余分)
    apk add --update --no-cache --virtual .build-deps gcc g++ musl-dev linux-headers build-base python3-dev zlib-dev && \
    # moviepy dependecies
    apk add --update jpeg-dev && \
    # app install
    pip3 install moviepy mutagen && \
    # clean
    apk del .build-deps gcc g++ musl-dev linux-headers build-base python3-dev zlib-dev

ENTRYPOINT []