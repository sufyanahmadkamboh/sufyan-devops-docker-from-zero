# The finished Dockerfile for simple-app.
# labs/05-first-dockerfile builds it up step by step (see dockerfile-steps/).

# 1. Start from an official, small Python image (pinned to a version, never "latest")
FROM python:3.14-slim

# 2. Every following command runs inside /app in the image
WORKDIR /app

# 3. Copy only the dependency list first, then install.
#    This layer is cached until requirements.txt changes (labs/06-layers-and-cache).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Now copy the application code (changes often, so it comes last)
COPY app.py .

# 5. Default configuration; override at run time with -e
ENV APP_ENV=production \
    GREETING="Hello from simple-app"

# 6. Do not run as root (labs/14-security-and-optimization)
RUN useradd --create-home --uid 10001 appuser
USER appuser

# 7. Documentation: the app listens on 5000 (publishing still needs -p)
EXPOSE 5000

# 8. The main process. When it stops, the container stops.
CMD ["python", "app.py"]
