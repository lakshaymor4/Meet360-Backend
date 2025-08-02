
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    portaudio19-dev \
    python3-dev \
    pkg-config \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p ./videos

EXPOSE 8080

ENV PYTHONPATH=/app
ENV PORT=8080

CMD exec gunicorn --bind 0.0.0.0:$PORT --worker-class eventlet -w 1 wsgi:app
