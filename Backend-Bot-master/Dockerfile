FROM python:3.13-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt

RUN apt-get update && apt-get install -y \
    ca-certificates \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

COPY certs/russian_trusted_root_ca_pem.crt /usr/local/share/ca-certificates/russian-trusted-root-ca.crt
COPY certs/russian_trusted_sub_ca_2024_pem.crt /usr/local/share/ca-certificates/russian-trusted-sub-ca-2024.crt

RUN update-ca-certificates

RUN mkdir /project

WORKDIR /project

COPY pyproject.toml ./

RUN pip install --upgrade pip && \
    pip install poetry && \
    poetry --version

RUN poetry config virtualenvs.create false && \
    poetry lock && \
    poetry install --without dev

COPY . .