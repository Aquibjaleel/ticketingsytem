FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install gunicorn

# The --chmod=755 ensures the script is executable regardless of host OS
COPY --chmod=755 entrypoint.sh /app/entrypoint.sh

COPY . .

EXPOSE 5000

# Use only one ENTRYPOINT
ENTRYPOINT ["/app/entrypoint.sh"]