FROM python:3.13.0-alpine

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# RUN apt-get update && apt-get install -y \
#     libpango-1.0-0 \
#     libpangocairo-1.0-0 \
#     libgdk-pixbuf-2.0-0 \
#     libffi-dev \
#     shared-mime-info \
#     && rm -rf /var/lib/apt/lists/*

RUN mkdir /project

WORKDIR /project

COPY pyproject.toml poetry.lock ./

RUN pip install --upgrade pip && \
    pip install poetry && \
    poetry --version

RUN poetry config virtualenvs.create false && \
    poetry lock && \
    poetry install --without dev

COPY . .