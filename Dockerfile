FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    http_proxy= \
    https_proxy= \
    HTTP_PROXY= \
    HTTPS_PROXY= \
    no_proxy= \
    NO_PROXY=

WORKDIR /app

COPY constraints.txt requirements-admin.txt /tmp/

RUN python -m pip install --upgrade pip \
    && python -m pip install -c /tmp/constraints.txt -r /tmp/requirements-admin.txt

COPY . /app

ARG GAOKAO_ADMIN_BIND=0.0.0.0
ARG GAOKAO_ADMIN_PORT=8000
ENV GAOKAO_ADMIN_BIND=${GAOKAO_ADMIN_BIND} \
    GAOKAO_ADMIN_PORT=${GAOKAO_ADMIN_PORT}

EXPOSE 8000

CMD ["sh", "-c", "python -m admin.app --host ${GAOKAO_ADMIN_BIND} --port ${GAOKAO_ADMIN_PORT} --log-format json"]
