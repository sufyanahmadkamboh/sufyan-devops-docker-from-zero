# Step 2: put our code into the image and say what to run.
FROM python:3.14-slim
WORKDIR /app
COPY . .
CMD ["python", "app.py"]
