# Multi-stage build: stage 1 has the build tools, stage 2 only has what runs.
#
# Stage 1 "builder": install dependencies into a virtual environment.
# build-base (gcc, make, ...) is here because real projects often compile
# Python packages. None of it reaches the final image.
FROM python:3.14-alpine AS builder
RUN apk add --no-cache build-base
RUN python -m venv /opt/venv
COPY requirements.txt .
RUN /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# Stage 2 "runtime": a fresh, small image. Copy only the finished venv and the code.
FROM python:3.14-alpine
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    APP_ENV=production
WORKDIR /app
COPY app.py .
RUN adduser -D -u 10001 appuser
USER appuser
EXPOSE 5000
CMD ["python", "app.py"]
