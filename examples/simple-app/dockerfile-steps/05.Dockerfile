# Step 5: cache-friendly order. Dependencies first, code last.
# Changing app.py no longer re-runs "pip install".
FROM python:3.14-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
ENV APP_ENV=production
EXPOSE 5000
CMD ["python", "app.py"]
