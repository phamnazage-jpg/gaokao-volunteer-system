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

COPY requirements-admin.txt /tmp/requirements-admin.txt

RUN python -m pip install --upgrade pip \
    && python -m pip install -r /tmp/requirements-admin.txt

COPY . /app

EXPOSE 8000

CMD ["python", "-m", "admin.app", "--host", "0.0.0.0", "--port", "8000", "--log-format", "json"]