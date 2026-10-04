# Image Optimization

## What is it?

Making images **smaller and faster to build** without changing what the application does. The main tools:

- a **smaller base image** (`-slim` or `-alpine` instead of the full image)
- **multi-stage builds** (build tools in one stage, only the result in the final image)
- **`.dockerignore`** (do not send junk into the build)
- **layer order** (dependencies first, code last, so the cache works)
- **no unnecessary packages or files** (no `vim` "just in case", no package-manager caches)

## Why do we need it?

Every megabyte is pulled by every server, every CI job and every teammate, every time the image changes. Smaller
images download faster, start faster, cost less storage, and contain **fewer packages that can have
vulnerabilities**. Faster builds mean faster feedback for developers.

## How does it work?

**Base images.** The same Python, three sizes:

```text
python:3.14          Debian + compilers + headers + docs     very large
python:3.14-slim     Debian, only what Python needs          small
python:3.14-alpine   Alpine Linux (musl), minimal            smallest
```

**Multi-stage build.** One Dockerfile, several `FROM` lines. Only the **last** stage becomes the image; earlier
stages are thrown away after you copy what you need with `COPY --from=`:

```text
  Stage 1: builder  (FROM python:3.14-alpine AS builder)
  ┌──────────────────────────────────────────────┐
  │ build-base (gcc, make, headers ...)          │   discarded
  │ python -m venv /opt/venv                     │
  │ pip install -r requirements.txt  ─────┐      │
  └───────────────────────────────────────│──────┘
                                          │ COPY --from=builder /opt/venv /opt/venv
  Stage 2: runtime  (FROM python:3.14-alpine)    ▼
  ┌──────────────────────────────────────────────┐
  │ /opt/venv (Flask installed)                  │   this is your image
  │ app.py, USER appuser                         │
  └──────────────────────────────────────────────┘
```

The repository contains three versions of the simple-app image to compare:

| File | Base | What it does wrong / right |
|---|---|---|
| `examples/simple-app/optimization/fat.Dockerfile` | `python:3.14` | full image, `apt-get install build-essential curl vim`, apt lists and pip cache kept, `COPY . .` before `pip install` |
| `examples/simple-app/Dockerfile` | `python:3.14-slim` | slim base, dependencies first, `--no-cache-dir`, non-root |
| `examples/simple-app/optimization/multistage.Dockerfile` | `python:3.14-alpine` ×2 | builder stage with compilers, runtime stage with only the venv and `app.py` |

## Prerequisites

- [09-dockerfile.md](09-dockerfile.md), [10-image-layers.md](10-image-layers.md), [11-dockerignore.md](11-dockerignore.md)

## Hands-on Lab

Full lab: [labs/16-image-optimization](../labs/16-image-optimization/README.md). Build all three (the fat one takes a
few minutes the first time; that slowness is part of the lesson):

```bash
cd examples/simple-app
```

<!-- test: timeout=1500 -->
```bash
docker build -f optimization/fat.Dockerfile -t simple-app:fat .
```

<!-- test: timeout=600 -->
```bash
docker build -t simple-app:slim .
docker build -f optimization/multistage.Dockerfile -t simple-app:multistage .
```

<!-- test: output -->
```bash
docker images simple-app --format 'table {{.Repository}}:{{.Tag}}\t{{.Size}}'
```

```text
REPOSITORY:TAG          SIZE
simple-app:step5        212MB
simple-app:step3        212MB
simple-app:multistage   108MB
simple-app:fat          1.75GB
simple-app:mine         212MB
simple-app:slim         212MB
simple-app:1.0          212MB
simple-app:leaky        239MB
simple-app:step4        212MB
simple-app:fixed        212MB
simple-app:step2        189MB
simple-app:clean        189MB
simple-app:step1        189MB
```

## Expected Result

The `fat` image is **many times** the size of the others. `slim` is a fraction of it, and `multistage` (Alpine
based, no compilers) is the smallest. All three run the same application. (You may also see other `simple-app` tags
from earlier labs; compare the three tags you just built.)

## Experiment

Prove they behave the same:

```bash
docker run -d --name small -p 5000:5000 simple-app:multistage
```

<!-- test: retry=15; contains=Hello from simple-app -->
```bash
curl -s http://localhost:5000
```

And see **where** the size of the fat image comes from, layer by layer:

<!-- test: output=head:8 -->
```bash
docker history simple-app:fat --format 'table {{.Size}}\t{{.CreatedBy}}'
```

```text
SIZE      CREATED BY
0B        CMD ["python" "app.py"]
18.4MB    RUN /bin/sh -c pip install -r requirements.t…
16.4kB    COPY . . # buildkit
8.19kB    WORKDIR /app
74.5MB    RUN /bin/sh -c apt-get update && apt-get ins…
0B        CMD ["python3"]
16.4kB    RUN /bin/sh -c set -eux;  for src in idle3 p…
...
```

Read the sizes from the top (newest layer) down. Most of the weight comes from the layers of the full `python:3.14`
base image itself, and the `apt-get install` layer adds more on top. Your own code is a few kilobytes.

## Break It

The multi-stage file copies the venv from the builder. Ask Docker to copy from a stage that does not exist:

```bash
sed 's/--from=builder/--from=buildr/' optimization/multistage.Dockerfile > broken.Dockerfile
```

<!-- test: fail -->
```bash
docker build -f broken.Dockerfile -t simple-app:broken .
```

## Troubleshoot It

Read the build error: Docker tries to treat `buildr` as an **image name** to pull, because no stage is called that,
and fails. Compare the stage names:

<!-- test: contains=AS builder; contains=--from=buildr -->
```bash
grep -n "AS \|--from" broken.Dockerfile
```

Root cause: the name after `--from=` must match a name after `AS`. Fix by using the original file, and verify:

```bash
rm broken.Dockerfile
docker build -f optimization/multistage.Dockerfile -t simple-app:multistage .
```

```bash
docker rm -f small
```

## Common Mistakes

- `apt-get update` and `apt-get install` in different `RUN` lines (stale cache) and never cleaning `/var/lib/apt/lists`.
- Installing debugging tools "just in case" into production images.
- `COPY . .` as the first instruction: every code change reinstalls all dependencies.
- Deleting files in a later `RUN`: the earlier layer still contains them, so the image does not shrink.
- Switching to Alpine without testing: some Python packages need extra work on musl. Test, do not assume.

## Best Practices

- Start from `-slim`; try Alpine or multi-stage when size matters and the app supports it.
- Dependencies first, code last.
- `--no-cache-dir` for pip, `--no-install-recommends` and `rm -rf /var/lib/apt/lists/*` for apt.
- Multi-stage whenever you need compilers or build tools.
- Keep `.dockerignore` up to date.
- Measure: `docker images` and `docker history` before and after every change.

## Challenge

**Task:** the fat image keeps the pip download cache. Without changing anything else, how much smaller does it get if
`pip install` uses `--no-cache-dir`? Build it as `simple-app:fat-nocache` and compare.

## Solution

<details><summary>Solution</summary>

```bash
sed 's/pip install -r/pip install --no-cache-dir -r/' optimization/fat.Dockerfile > fat-nocache.Dockerfile
```

<!-- test: timeout=1500 -->
```bash
docker build -f fat-nocache.Dockerfile -t simple-app:fat-nocache .
```

<!-- test: contains=fat-nocache -->
```bash
docker images simple-app --format '{{.Tag}} {{.Size}}'
rm fat-nocache.Dockerfile
```

The pip cache is a few megabytes here: a small win compared to choosing the right base image. **Optimize the biggest
layer first.**
</details>

## Verification

- [ ] I can compare image sizes with `docker images` and find the big layer with `docker history`.
- [ ] I can explain what a multi-stage build keeps and what it throws away.
- [ ] I can name five ways to make an image smaller.

## Real-World Usage

Teams optimize images to speed up CI pipelines and deployments, reduce registry storage and egress costs, and shrink
the attack surface that security scanners report on. "Why is this image 1.5 GB?" is a common code review question.

## Key Takeaways

- The base image is the biggest lever.
- Multi-stage builds leave build tools behind.
- Layer order decides how much the cache can reuse.
- Measure before and after; optimize the biggest layer first.

Next: [21-docker-hub.md](21-docker-hub.md)
