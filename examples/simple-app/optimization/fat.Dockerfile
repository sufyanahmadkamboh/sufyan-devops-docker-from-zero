# A typical "first try" Dockerfile. It works, but the image is huge.
# Problems (on purpose):
#   - full python image (includes compilers, docs, dev headers)
#   - apt-get install of build tools "just in case", apt lists left behind
#   - pip cache kept inside the image
#   - COPY . . sends everything, before installing dependencies (bad cache order)
FROM python:3.14
RUN apt-get update && apt-get install -y build-essential curl vim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "app.py"]
