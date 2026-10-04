# Lab 07 · Image Layers and the Build Cache

> **Goal:** see the layers inside an image, and learn why the *order* of a Dockerfile decides how fast it rebuilds.
> **Time:** about 25 minutes · **You need:** [Lab 06](../06-first-dockerfile/README.md) (you can build an image with `docker build`)

## What you will learn

- An image is a stack of **layers**: roughly one layer per Dockerfile instruction.
- `docker history` shows those layers, the instruction behind each one, and its size.
- Docker **caches** layers. If nothing changed, a step is not run again (`CACHED` in the build output).
- When one step changes, **every step after it** is rebuilt too.
- Why good Dockerfiles copy `requirements.txt` first and the code last.

```text
Dockerfile                               Image (read from the bottom up)
──────────────────────────────           ───────────────────────────────────
FROM python:3.14-slim          ───────►  layers of the base image
WORKDIR /app                   ───────►  layer: empty /app folder
COPY requirements.txt .        ───────►  layer: one small file
RUN pip install -r ...         ───────►  layer: Flask and its dependencies (the big one)
COPY app.py .                  ───────►  layer: your code (changes often)
CMD ["python", "app.py"]       ───────►  metadata only, no files
```

## Step 1 · Build two versions of the same app

We use the simple app from Lab 06 and two of its Dockerfiles:

- `dockerfile-steps/03.Dockerfile` copies **everything** (`COPY . .`) and *then* installs dependencies.
- `dockerfile-steps/05.Dockerfile` copies `requirements.txt` first, installs, and copies `app.py` **last**.

Both produce a working image. Let's build both.

```bash
cd examples/simple-app
docker build -f dockerfile-steps/03.Dockerfile -t simple-app:step3 .
```

<!-- test: contains=naming to -->
```bash
docker build -f dockerfile-steps/05.Dockerfile -t simple-app:step5 .
```

**What you see:** numbered build steps (`#1`, `#2`, ...). Each Dockerfile instruction becomes a step. If you already
built these images in Lab 06, many steps say `CACHED`; that is the cache at work, and we will look at it closely in a moment.

## Step 2 · Look inside an image with `docker history`

<!-- test: output=head:12; contains=pip install -->
```bash
docker history simple-app:step5
```

```text
IMAGE          CREATED          CREATED BY                                      SIZE      COMMENT
b07321e8274a   18 minutes ago   CMD ["python" "app.py"]                         0B        buildkit.dockerfile.v0
<missing>      18 minutes ago   EXPOSE [5000/tcp]                               0B        buildkit.dockerfile.v0
<missing>      18 minutes ago   ENV APP_ENV=production                          0B        buildkit.dockerfile.v0
<missing>      18 minutes ago   COPY app.py . # buildkit                        12.3kB    buildkit.dockerfile.v0
<missing>      18 minutes ago   RUN /bin/sh -c pip install --no-cache-dir -r…   16.9MB    buildkit.dockerfile.v0
<missing>      18 minutes ago   COPY requirements.txt . # buildkit              12.3kB    buildkit.dockerfile.v0
<missing>      28 minutes ago   WORKDIR /app                                    8.19kB    buildkit.dockerfile.v0
<missing>      2 days ago       CMD ["python3"]                                 0B        buildkit.dockerfile.v0
<missing>      2 days ago       RUN /bin/sh -c set -eux;  for src in idle3 p…   16.4kB    buildkit.dockerfile.v0
<missing>      2 days ago       RUN /bin/sh -c set -eux;   savedAptMark="$(a…   42MB      buildkit.dockerfile.v0
<missing>      2 days ago       ENV PYTHON_SHA256=c2215904f02b175596dc493515…   0B        buildkit.dockerfile.v0
...
```

**What you see:** one row per layer, **newest at the top**.

| Column | Meaning |
|---|---|
| `IMAGE` | the ID of the layer (often `<missing>` for layers built elsewhere, such as the base image; that is normal) |
| `CREATED` | when the layer was built |
| `CREATED BY` | the Dockerfile instruction that made the layer |
| `SIZE` | how much the layer adds to the image |
| `COMMENT` | extra information, usually empty or "buildkit.dockerfile.v0" |

Look at the `SIZE` column. The `RUN pip install` layer is large (it holds Flask), `COPY app.py` is tiny, and
`WORKDIR`, `ENV`, `EXPOSE` and `CMD` add 0 B because they only change settings, not files.

To see the full instructions without the `...` cut-off:

<!-- test: output=head:8 -->
```bash
docker history --no-trunc --format "{{.Size}}\t{{.CreatedBy}}" simple-app:step5
```

```text
0B	CMD ["python" "app.py"]
0B	EXPOSE [5000/tcp]
0B	ENV APP_ENV=production
12.3kB	COPY app.py . # buildkit
16.9MB	RUN /bin/sh -c pip install --no-cache-dir -r requirements.txt # buildkit
12.3kB	COPY requirements.txt . # buildkit
8.19kB	WORKDIR /app
0B	CMD ["python3"]
...
```

**Why it matters:** when an image is big, `docker history` tells you *which instruction* made it big. You will use
this again in [Lab 16](../16-image-optimization/README.md).

## Step 3 · Build again without changing anything

Run the same build a second time:

<!-- test: contains=CACHED -->
```bash
docker build -f dockerfile-steps/05.Dockerfile -t simple-app:step5 .
```

**What you see:** almost every step says `CACHED` and the build finishes in about a second. Docker compared each
instruction (and the files it copies) with what it built last time, found no difference, and reused the layer.

## Step 4 · Change the code, and watch the cache break

Now make a tiny change to the application code. First keep a copy of the original so we can put it back later:

```bash
cp app.py app.py.backup
echo "# a tiny change to test the build cache" >> app.py
```

Rebuild the **cache-unfriendly** version (step 3, `COPY . .` before `pip install`):

<!-- test: contains=Successfully installed -->
```bash
docker build -f dockerfile-steps/03.Dockerfile -t simple-app:step3 .
```

**What you see:** `pip install` runs again, and you can watch Flask being downloaded and installed
(`Successfully installed ...`). We only added a comment to `app.py`! But `COPY . .` copies `app.py`, so that layer
changed, and **every layer after a changed layer is rebuilt**, including the slow `pip install`.

Now rebuild the **cache-friendly** version (step 5):

<!-- test: contains=CACHED; absent=Successfully installed -->
```bash
docker build -f dockerfile-steps/05.Dockerfile -t simple-app:step5 .
```

**What you see:** `COPY requirements.txt` and `RUN pip install` are `CACHED`. Only `COPY app.py .` (and what follows
it) runs again. Same app, same change, much faster build.

Put the original file back:

```bash
mv app.py.backup app.py
```

**Why it matters:** in a real project you rebuild images dozens of times a day. Dependencies change rarely, code
changes constantly. Ordering the Dockerfile from **"changes rarely"** to **"changes often"** saves minutes on every build.

```text
Cache rule:   step 1 ✔ cached → step 2 ✔ cached → step 3 ✘ changed → step 4 rebuilt → step 5 rebuilt
                                                   ▲
                                 the first changed step invalidates everything below it
```

## Break it

Don't fix anything yet: this one is broken on purpose. The **build context** is the folder you pass at the end of
`docker build` (the `.`). Docker can only `COPY` files from inside it. Let's give it the wrong folder: the repository
root (`../..`) instead of `examples/simple-app`.

<!-- test: fail; contains=not found -->
```bash
docker build -f dockerfile-steps/05.Dockerfile -t simple-app:broken ../..
```

The build stops at `COPY requirements.txt .` with an error that ends in `"/requirements.txt": not found`.

## Troubleshoot it

1. **Observe:** the error names a file: `/requirements.txt: not found`. The Dockerfile itself was found, so the
   problem is not the `-f` path.
2. **Investigate:** where does Docker look for `requirements.txt`? In the build context, the last argument of
   `docker build`. Look at what is in that folder:

   ```bash
   ls ../.. | head -20
   ```

   There is no `requirements.txt` in the repository root. It lives in `examples/simple-app`.
3. **Root cause:** `-f` says *which Dockerfile* to use; the last argument says *which folder the files come from*.
   We pointed the context at the wrong folder.
4. **Fix and verify:** use the folder that contains the files (`.` because we are inside `examples/simple-app`):

   <!-- test: contains=naming to -->
   ```bash
   docker build -f dockerfile-steps/05.Dockerfile -t simple-app:step5 .
   ```

Another way to break the cache (not an error, just slow): `docker build --no-cache ...` ignores every cached layer.
It is useful when you *want* a completely fresh build, for example to pick up security updates of the base image.

## Challenge

**Task:** predict, then prove, which steps are rebuilt when `requirements.txt` changes.

**Requirements:**
- Use `dockerfile-steps/05.Dockerfile`.
- Change `requirements.txt` without adding a new package (a comment line is enough).
- Before building, write down which steps you expect to be `CACHED`.
- Restore the original file afterwards.

**Hints:** a comment changes the file's content, and Docker compares the content of copied files.

**Expected result:** `FROM` and `WORKDIR` are cached; `COPY requirements.txt`, `RUN pip install` and `COPY app.py` run again.

<details><summary>Solution</summary>

```bash
cp requirements.txt requirements.txt.backup
echo "# pinned for Docker From Zero" >> requirements.txt
```

<!-- test: contains=Successfully installed -->
```bash
docker build -f dockerfile-steps/05.Dockerfile -t simple-app:step5 .
```

```bash
mv requirements.txt.backup requirements.txt
```

**Explanation:** `COPY requirements.txt .` now copies different content, so its layer changes. Every following layer,
including `pip install` and `COPY app.py`, must be rebuilt. That is why dependency changes are slow and code changes are fast.

</details>

## Verify

- [ ] I can show the layers of an image with `docker history`.
- [ ] I can explain why `WORKDIR`, `ENV` and `CMD` layers are 0 B.
- [ ] I can recognise `CACHED` steps in build output.
- [ ] I can explain why `COPY requirements.txt` comes before `COPY app.py`.
- [ ] I know the difference between `-f` (the Dockerfile) and the build context (the last argument).

## Clean up

```bash
docker rmi simple-app:step3 simple-app:step5
```

(If `app.py.backup` or `requirements.txt.backup` still exists because you stopped halfway, move it back over the original.)

<!-- test-run: if [ -f app.py.backup ]; then mv app.py.backup app.py; fi; if [ -f requirements.txt.backup ]; then mv requirements.txt.backup requirements.txt; fi -->

## Next

- Next lab: [Lab 08 · .dockerignore](../08-dockerignore/README.md)
- Concept lesson: [docs/10-image-layers.md](../../docs/10-image-layers.md)
