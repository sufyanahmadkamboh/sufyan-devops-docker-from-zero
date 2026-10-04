# Step 6: do not run as root. This is the same as ../Dockerfile.
FROM python:3.14-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
ENV APP_ENV=production \
    GREETING="Hello from simple-app"
RUN useradd --create-home --uid 10001 appuser
USER appuser
EXPOSE 5000
CMD ["python", "app.py"]
