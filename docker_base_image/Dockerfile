# event_reactor/handlers/rfid/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# system deps for mysql / mqtt if needed
RUN apt-get update && apt-get install -y \
    ca-certificates \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip  && pip install -r /app/requirements.txt

ENV PYTHONUNBUFFERED=1
USER root