FROM python:3.8-alpine

ENV APP_ROOT /src
ENV CONFIG_ROOT /config
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN mkdir ${CONFIG_ROOT}
COPY requirements.txt ${CONFIG_ROOT}/requirements.txt

RUN apk add --no-cache --virtual .build-deps gcc musl-dev libffi-dev openssl-dev python3-dev cargo\
    && apk add libxml2-dev libxslt-dev \
    && apk add --no-cache mariadb-dev \
    && pip install --upgrade pip \
    && pip install --no-cache-dir -r ${CONFIG_ROOT}/requirements.txt \
    && apk del .build-deps

WORKDIR ${APP_ROOT}

ADD . ${APP_ROOT}

RUN adduser appUser -D -h ${APP_ROOT} -s /bin/sh \
    && chown -R appUser ${APP_ROOT}
USER appUser
