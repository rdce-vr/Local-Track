FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Jakarta

WORKDIR /app

# System deps (timezone + certs)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       tzdata ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Python deps (explicit, no requirements.txt)
RUN pip install --no-cache-dir \
    flask \
    requests \
    beautifulsoup4 \
    apscheduler

# App source
COPY app.py fetcher.py scheduler.py ./

# Runtime data volume (SQLite lives here)
VOLUME ["/app/data"]

EXPOSE 5000

# Default command overridden by docker-compose
CMD ["python", "app.py"]
