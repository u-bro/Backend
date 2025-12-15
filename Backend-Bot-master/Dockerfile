FROM python:3.13

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN mkdir /mining

WORKDIR /mining

COPY pyproject.toml poetry.lock ./

RUN pip install --upgrade pip && \
    pip install poetry && \
    poetry --version

RUN poetry config virtualenvs.create false && \
    poetry lock && \
    poetry install --without dev

COPY . .