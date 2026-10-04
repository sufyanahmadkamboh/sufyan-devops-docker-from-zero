# Lab 16 · Image optimization

> Goal: build the same application three ways, measure the image sizes, and understand which decisions make an image
> big or small. · Time: 40 minutes · You need: labs 06, 07, 08 and 15.

Image size is not vanity. A big image takes longer to build, push, pull and start, uses more disk on every server,
and contains more software that can have vulnerabilities. The good news: most of the size comes from a few habits that
are easy to change.

We build **one** application (`examples/simple-app`) three ways:

| Tag | Dockerfile | Idea |
|---|---|---|
| `simple-app:fat` | `optimization/fat.Dockerfile` | A typical first attempt: full base image, extra tools, bad order |
| `simple-app:slim` | `Dockerfile` | Slim base image, cache-friendly order, no pip cache, non-root |
| `simple-app:multistage` | `optimization/multistage.Dockerfile` | Build tools in a first stage, a small Alpine runtime in the second |

## What you will learn

- How the base image, extra packages and leftover caches add up
- How to compare images with `docker images` and find big layers with `docker history`
- What a multi-stage build is, and why the build tools do not end up in the final image
- How to check that the optimized image still works

## Step 1 · Read the fat Dockerfile

From the repository root:

```bash
cd examples/simple-app
```

<!-- test: output; contains=build-essential -->
```bash
cat optimization/fat.Dockerfile
```

```text
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
```

Every problem is on purpose:

- `FROM python:3.14`: the **full** Python image, based on a full Debian with compilers and development headers.
- `apt-get install -y build-essential curl vim`: tools "just in case". The app needs none of them.
- No `rm -rf /var/lib/apt/lists/*`: the package index stays inside the image.
- `COPY . .` before `pip install`: any code change re-runs the dependency install (lab 07).
- `pip install` without `--no-cache-dir`: pip's download cache stays inside the image.
- No `USER`: it runs as root (lab 15).

## Step 2 · Build all three

The fat image downloads a lot. Give it a few minutes the first time.

<!-- test: timeout=1200; output=tail:4 -->
```bash
docker build -f optimization/fat.Dockerfile -t simple-app:fat .
```

```text
...
#11 unpacking to docker.io/library/simple-app:fat 0.9s done
#11 DONE 3.4s

View build details: docker-desktop://dashboard/build/desktop-linux/desktop-linux/nfbyg924wexhm1j8vqxyg43bv
```

<!-- test: timeout=600; output=tail:4 -->
```bash
docker build -t simple-app:slim .
```

```text
...
#11 unpacking to docker.io/library/simple-app:slim done
#11 DONE 0.1s

View build details: docker-desktop://dashboard/build/desktop-linux/desktop-linux/mpa8j2x5z7qsk4q84nbj12rgo
```

<!-- test: timeout=900; output=tail:4 -->
```bash
docker build -f optimization/multistage.Dockerfile -t simple-app:multistage .
```

```text
...
#14 unpacking to docker.io/library/simple-app:multistage 0.3s done
#14 DONE 1.1s

View build details: docker-desktop://dashboard/build/desktop-linux/desktop-linux/oy9tm9qhtcbreflt6qpej9kg8
```

## Step 3 · Compare the sizes

<!-- test: output; contains=fat; contains=slim; contains=multistage -->
```bash
docker images simple-app
```

```text
WARNING: This output is designed for human readability. For machine-readable output, please use --format.
IMAGE                   ID             DISK USAGE   CONTENT SIZE   EXTRA
simple-app:1.0          99fca8fc867b        212MB         51.9MB        
simple-app:fat          aef00de3ea70       1.75GB          454MB        
simple-app:fixed        18b09356d161        212MB         51.9MB        
simple-app:multistage   f6c6f818fa19        108MB         26.1MB        
simple-app:slim         8ece4caa4c45        212MB         51.9MB        
simple-app:step1        c28c9280bf77        189MB         46.5MB        
simple-app:step2        85904782ffb9        189MB         46.5MB        
simple-app:step4        e0d9c69ee329        212MB         51.9MB        
```

Look at the `DISK USAGE` column (Docker 29 and newer; older versions call it `SIZE`). `CONTENT SIZE` is the compressed download size. Same
application, same code, same Flask version, and a huge difference between `fat` and the other two. The multi-stage
Alpine image is the smallest.

> Sizes differ a little between machines, Docker versions and image updates. The ranking does not.

## Step 4 · Where does the size come from?

`docker history` shows every layer and how much it added:

<!-- test: output=head:12 -->
```bash
docker history simple-app:fat
```

```text
IMAGE          CREATED          CREATED BY                                      SIZE      COMMENT
aef00de3ea70   22 seconds ago   CMD ["python" "app.py"]                         0B        buildkit.dockerfile.v0
<missing>      22 seconds ago   RUN /bin/sh -c pip install -r requirements.t…   18.4MB    buildkit.dockerfile.v0
<missing>      25 seconds ago   COPY . . # buildkit                             16.4kB    buildkit.dockerfile.v0
<missing>      25 seconds ago   WORKDIR /app                                    8.19kB    buildkit.dockerfile.v0
<missing>      25 seconds ago   RUN /bin/sh -c apt-get update && apt-get ins…   74.5MB    buildkit.dockerfile.v0
<missing>      2 days ago       CMD ["python3"]                                 0B        buildkit.dockerfile.v0
<missing>      2 days ago       RUN /bin/sh -c set -eux;  for src in idle3 p…   16.4kB    buildkit.dockerfile.v0
<missing>      2 days ago       RUN /bin/sh -c set -eux;   savedAptMark="$(a…   83.3MB    buildkit.dockerfile.v0
<missing>      2 days ago       ENV PYTHON_SHA256=c2215904f02b175596dc493515…   0B        buildkit.dockerfile.v0
<missing>      2 days ago       ENV PYTHON_VERSION=3.14.8                       0B        buildkit.dockerfile.v0
<missing>      2 days ago       RUN /bin/sh -c set -eux;  apt-get update;  a…   19.9MB    buildkit.dockerfile.v0
...
```

Read it from the top (newest layer) down. The `apt-get install build-essential curl vim` layer is one of the biggest,
and below our own layers come the layers of the full `python:3.14` base image, which is already large before we add
anything.

Now the multi-stage image. Check that the build tools from the first stage did **not** make it into the final image:

<!-- test: output; absent=build-base -->
```bash
docker history --format '{{.Size}}\t{{.CreatedBy}}' simple-app:multistage
```

```text
0B	CMD ["python" "app.py"]
0B	EXPOSE [5000/tcp]
0B	USER appuser
41kB	RUN /bin/sh -c adduser -D -u 10001 appuser #…
12.3kB	COPY app.py . # buildkit
8.19kB	WORKDIR /app
0B	ENV PATH=/opt/venv/bin:/usr/local/bin:/usr/l…
20.2MB	COPY /opt/venv /opt/venv # buildkit
0B	CMD ["python3"]
16.4kB	RUN /bin/sh -c set -eux;  for src in idle3 p…
49.7MB	RUN /bin/sh -c set -eux;   apk add --no-cach…
0B	ENV PYTHON_SHA256=c2215904f02b175596dc493515…
0B	ENV PYTHON_VERSION=3.14.8
2.83MB	RUN /bin/sh -c set -eux;  apk add --no-cache…
0B	ENV PATH=/usr/local/bin:/usr/local/sbin:/usr…
0B	CMD ["/bin/sh"]
9.08MB	ADD alpine-minirootfs-3.24.2-x86_64.tar.gz /…
```

There is no `build-base` layer. The final image only contains the Alpine Python base, the copied virtual environment,
`app.py` and the user.

## Step 5 · How a multi-stage build works

<!-- test: output; contains=AS builder; contains=COPY --from=builder -->
```bash
cat optimization/multistage.Dockerfile
```

```text
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
```

```text
 Stage 1 "builder"                          Stage 2 (the final image)
 FROM python:3.14-alpine AS builder         FROM python:3.14-alpine
 + build-base (gcc, make, ...)              + /opt/venv  <-- COPY --from=builder
 + /opt/venv with Flask installed           + app.py, appuser
            |                                        |
            +--- thrown away after the build         +--- this is what you ship
```

- `FROM ... AS builder` names the first stage.
- Everything in the builder stage, including compilers, is **not** part of the result.
- `COPY --from=builder /opt/venv /opt/venv` copies just the finished virtual environment into a fresh image.

Multi-stage builds matter most when building needs heavy tools: compilers for Go, Java, C, Node.js front ends, or
Python packages with C extensions. The tools stay in the first stage; only the result is shipped.

## Step 6 · Make sure it still works

A smaller image that does not work is not an optimization. Run the multi-stage image:

```bash
docker run -d --name small -p 5000:5000 simple-app:multistage
```

<!-- test: retry=15; output; contains=Hello from simple-app -->
```bash
curl -s http://localhost:5000/
```

```text
Hello from simple-app!
environment: production
container hostname: 0409b71667fc
```

<!-- test: contains=appuser -->
```bash
docker exec small whoami
```

It answers, and it runs as a normal user.

> macOS: if port 5000 is taken by AirPlay Receiver, use `-p 5050:5000` and `http://localhost:5050`.

## Summary: what made the difference

| Technique | Effect |
|---|---|
| Slim or Alpine base image instead of the full one | The biggest single saving |
| Do not install tools "just in case" (`curl`, `vim`, compilers) | Smaller and fewer vulnerabilities |
| `pip install --no-cache-dir`, `rm -rf /var/lib/apt/lists/*` | No caches inside the image |
| Copy dependency files first, code last | Faster rebuilds (cache), not smaller |
| `.dockerignore` | Nothing unnecessary in the build context (lab 08) |
| Multi-stage build | Build tools stay out of the final image |

Alpine uses a different C library (musl) than Debian (glibc). Most Python packages work, but some need to be compiled
or behave differently. `-slim` (Debian) is the safe default; Alpine is the size champion when it works for your app.

## Break it

The classic multi-stage mistake: forgetting to copy the result of the builder stage. This Dockerfile is passed on the
command line (`-f -` reads it from standard input). Don't fix it yet, we broke it on purpose.

<!-- test: timeout=600 -->
```bash
docker build -t simple-app:broken -f - . <<'EOF'
FROM python:3.14-alpine AS builder
RUN python -m venv /opt/venv
COPY requirements.txt .
RUN /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

FROM python:3.14-alpine
WORKDIR /app
COPY app.py .
CMD ["python", "app.py"]
EOF
```

The build succeeds. Now run it:

<!-- test: fail; contains=No module named 'flask' -->
```bash
docker run --rm simple-app:broken
```

## Troubleshoot it

**Observe.** The image builds, but the container exits immediately with `ModuleNotFoundError: No module named 'flask'`.
Before changing anything, let's investigate.

**Investigate.** Is the virtual environment in the final image?

<!-- test: fail; contains=No such file or directory -->
```bash
docker run --rm simple-app:broken ls /opt/venv
```

It is not. And the history shows no `COPY --from=builder` layer:

<!-- test: output; absent=--from -->
```bash
docker history --format '{{.CreatedBy}}' simple-app:broken
```

```text
CMD ["python" "app.py"]
COPY app.py . # buildkit
WORKDIR /app
CMD ["python3"]
RUN /bin/sh -c set -eux;  for src in idle3 p…
RUN /bin/sh -c set -eux;   apk add --no-cach…
ENV PYTHON_SHA256=c2215904f02b175596dc493515…
ENV PYTHON_VERSION=3.14.8
RUN /bin/sh -c set -eux;  apk add --no-cache…
ENV PATH=/usr/local/bin:/usr/local/sbin:/usr…
CMD ["/bin/sh"]
ADD alpine-minirootfs-3.24.2-x86_64.tar.gz /…
```

**Root cause.** Flask was installed in the **builder** stage, and the builder stage is thrown away. The final stage
never received it.

**Fix.** Copy the virtual environment and put it on the `PATH`, exactly like `optimization/multistage.Dockerfile`:

```dockerfile
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
```

**Verify.** The correct file builds an image that runs:

<!-- test: contains=flask -->
```bash
docker run --rm simple-app:multistage python -c "import flask; print('flask', flask.__version__)"
```

## Challenge

**Task:** Build a **single-stage** Alpine version, `simple-app:alpine`, and compare it with the multi-stage one.

**Requirements:**
- One `FROM python:3.14-alpine`, no second stage.
- Dependencies installed with `--no-cache-dir`, cache-friendly order, non-root user.
- Compare the sizes of `simple-app:alpine` and `simple-app:multistage` with `docker images`.

**Hints:**
- Start from the final `Dockerfile` and change the base image.
- Alpine has no `useradd`; it uses `adduser -D -u 10001 appuser`.

<details><summary>Solution</summary>

<!-- test: timeout=600 -->
```bash
docker build -t simple-app:alpine -f - . <<'EOF'
FROM python:3.14-alpine
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
RUN adduser -D -u 10001 appuser
USER appuser
EXPOSE 5000
CMD ["python", "app.py"]
EOF
```

<!-- test: output; contains=alpine; contains=multistage -->
```bash
docker images simple-app
```

```text
WARNING: This output is designed for human readability. For machine-readable output, please use --format.
IMAGE                   ID             DISK USAGE   CONTENT SIZE   EXTRA
simple-app:1.0          99fca8fc867b        212MB         51.9MB        
simple-app:alpine       530cbf450a8c        104MB         25.8MB        
simple-app:broken       ae8091872455         82MB         20.4MB        
simple-app:fat          aef00de3ea70       1.75GB          454MB        
simple-app:fixed        18b09356d161        212MB         51.9MB        
simple-app:multistage   f6c6f818fa19        108MB         26.1MB   U    
simple-app:slim         8ece4caa4c45        212MB         51.9MB        
simple-app:step1        c28c9280bf77        189MB         46.5MB        
simple-app:step2        85904782ffb9        189MB         46.5MB        
simple-app:step4        e0d9c69ee329        212MB         51.9MB        
```

Look at the two numbers. The difference is small, and it can go either way: Flask needs no compiler, so the builder
stage has nothing heavy to leave behind, and the copied virtual environment even brings its own copy of `pip`.
Multi-stage builds shine when the build needs big tools (compilers, SDKs). The lesson: **measure**, don't assume.

</details>

## Verify

- [ ] I can name the habits that make an image big
- [ ] I can compare image sizes with `docker images` and find large layers with `docker history`
- [ ] I can explain `FROM ... AS builder` and `COPY --from=builder`
- [ ] I checked that the optimized image still works and runs as a normal user

## Clean up

```bash
docker rm -f small
docker rmi simple-app:fat simple-app:slim simple-app:multistage simple-app:broken simple-app:alpine 2>/dev/null || true
cd ../..
```

## Next

- Concept lesson: [docs/20-image-optimization.md](../../docs/20-image-optimization.md)
- Next lab: [Lab 17 · Docker Hub and registries](../17-docker-hub/README.md)
