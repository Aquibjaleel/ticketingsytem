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

# 1. Use --chmod=755 to set permissions during the copy
# 2. Use 'tr' to strip any hidden Windows carriage returns (\r)
COPY entrypoint.sh /app/entrypoint.sh
RUN tr -d '\r' < /app/entrypoint.sh > /app/entrypoint.sh.tmp && \
    mv /app/entrypoint.sh.tmp /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

COPY . .

EXPOSE 5000

ENTRYPOINT ["/app/entrypoint.sh"]