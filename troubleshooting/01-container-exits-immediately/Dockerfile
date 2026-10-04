# Broken on purpose. Build it, run it, and find out why the container stops.
FROM python:3.14-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
CMD ["python", "main.py"]
