# Capstone API image: everything from the labs in one Dockerfile.

# ---- Stage 1: build the dependencies (labs/14: multi-stage builds) ----
FROM python:3.14-slim AS builder
RUN python -m venv /opt/venv
COPY requirements.txt .
RUN /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# ---- Stage 2: the image that actually runs ----
FROM python:3.14-slim
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app
COPY app.py .

# Run as an ordinary user, never as root (labs/14: security)
RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin app
USER app

EXPOSE 5000

# Docker asks the app "are you healthy?" every 10 s (docker ps shows the result)
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/api/health', timeout=2)"]

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--access-logfile", "-", "app:app"]
