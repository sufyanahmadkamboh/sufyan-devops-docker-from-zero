# Image Layers

> Lesson 10 · about 40 minutes · you need: [09 · Dockerfile](09-dockerfile.md)

## What is it?

An image is not one big file. It is a **stack of read-only layers**. Every instruction in a
Dockerfile that changes files (`FROM`, `COPY`, `RUN`) adds one layer on top of the previous ones.
Instructions that only change settings (`ENV`, `EXPOSE`, `CMD`, `USER`) add metadata, with a
layer of size 0.

```text
   Dockerfile (step 5)                                  Image layers (bottom to top)
   ---------------------------------------------       -----------------------------
   FROM python:3.14-slim                          -->  [ debian slim + python    ]  ~120 MB
   WORKDIR /app                                   -->  [ empty /app folder       ]  0 B
   COPY requirements.txt .                        -->  [ requirements.txt        ]  tiny
   RUN pip install --no-cache-dir -r requirements.txt  [ flask + dependencies    ]  a few MB
   COPY app.py .                                  -->  [ app.py                  ]  tiny
   ENV / EXPOSE / CMD                             -->  ( metadata only, 0 B )

   container = all of the above (read-only)  +  [ its own writable layer ]
```

## Why do we need it?

Layers make Docker fast and economical:

- **Sharing:** ten images built `FROM python:3.14-slim` store the Python layers **once** on disk.
- **Caching:** when you rebuild, Docker reuses every layer whose inputs did not change. A rebuild
  after a one-line code change can take one second instead of a minute.
- **Transfer:** pushing and pulling only moves layers the other side does not already have.

## How does it work?

### The build cache rule

For each instruction, Docker asks: "Have I already built **this exact instruction** on top of
**this exact parent layer**, with **these exact files**?" If yes, it reuses the layer (`CACHED`).
If no, it rebuilds this layer **and every layer after it**.

```text
   Bad order (step 3)                          Good order (step 5)
   FROM python:3.14-slim       cached          FROM python:3.14-slim          cached
   WORKDIR /app                cached          WORKDIR /app                   cached
   COPY . .                    CHANGED (app.py)COPY requirements.txt .        cached
   RUN pip install ...         REBUILT  (slow) RUN pip install ...            cached  (fast!)
                                               COPY app.py .                  CHANGED -> rebuilt (tiny)
```

`COPY` decides "changed" by looking at the **content** of the copied files. So `COPY . .` breaks
the cache whenever **any** file in the context changes, and everything after it runs again.

### Order rule of thumb

Put what changes **rarely** at the top and what changes **often** at the bottom:
base image → system packages → dependency list → install dependencies → your code.

## Prerequisites

- `examples/simple-app/` and the step files 03 and 05 from lesson 09.

## Hands-on Lab

```bash
cd examples/simple-app
```

Build step 5 and look at its layers with `docker history` (newest layer at the top):

<!-- test: timeout=600; contains=pip install; output -->
```bash
docker build -q -f dockerfile-steps/05.Dockerfile -t simple-app:step5 .
docker history simple-app:step5 --format 'table {{.CreatedBy}}\t{{.Size}}' | head -12
```

```text
sha256:bcb05088365fac70886ec410303b7ecf91170caf17f542bd0e8c9b8fab30809c
CREATED BY                                      SIZE
CMD ["python" "app.py"]                         0B
EXPOSE [5000/tcp]                               0B
ENV APP_ENV=production                          0B
COPY app.py . # buildkit                        12.3kB
RUN /bin/sh -c pip install --no-cache-dir -r…   16.9MB
COPY requirements.txt . # buildkit              12.3kB
WORKDIR /app                                    8.19kB
CMD ["python3"]                                 0B
RUN /bin/sh -c set -eux;  for src in idle3 p…   16.4kB
RUN /bin/sh -c set -eux;   savedAptMark="$(a…   42MB
ENV PYTHON_SHA256=c2215904f02b175596dc493515…   0B
```

Build it **again** without changing anything. Every step is `CACHED`:

<!-- test: contains=CACHED; output -->
```bash
docker build --progress=plain -f dockerfile-steps/05.Dockerfile -t simple-app:step5 . 2>&1 | grep -E '^#[0-9]+ (\[|CACHED)'
```

```text
#1 [internal] load build definition from 05.Dockerfile
#2 [internal] load metadata for docker.io/library/python:3.14-slim
#3 [internal] load .dockerignore
#4 [internal] load build context
#5 [1/5] FROM docker.io/library/python:3.14-slim@sha256:c3e521df8b2b498a7a682e7e18676771cb80c6b75b8699af886b2d554ce40151
#6 [3/5] COPY requirements.txt .
#6 CACHED
#7 [2/5] WORKDIR /app
#7 CACHED
#8 [4/5] RUN pip install --no-cache-dir -r requirements.txt
#8 CACHED
#9 [5/5] COPY app.py .
#9 CACHED
```

The full guided lab, with timings, is [labs/07-layers-and-cache](../labs/07-layers-and-cache/README.md).

## Expected Result

- `docker history` lists one row per instruction. The `RUN pip install` row has a size of a few MB,
  `COPY app.py` a few kB, the `ENV`/`EXPOSE`/`CMD` rows `0B`. Rows from the base image appear
  below ours.
- The repeated build shows `CACHED` for every step and finishes in about a second.

## Experiment

Now change the code and compare the two Dockerfile orders. Keep a backup of `app.py` first:

```bash
cp app.py app.py.bak
echo "# a small code change $(date +%s)" >> app.py
```

**Step 3 order** (`COPY . .` before `pip install`): the code change forces pip to run again.
`Collecting flask` in the output proves it:

<!-- test: timeout=600; contains=Collecting flask -->
```bash
docker build --progress=plain -f dockerfile-steps/03.Dockerfile -t simple-app:step3 . 2>&1 | grep -E 'CACHED|Collecting flask|RUN pip'
```

Change the code once more and rebuild with the **step 5 order**: pip is `CACHED`, only
`COPY app.py` runs:

<!-- test: timeout=600; absent=Collecting flask; contains=CACHED -->
```bash
echo "# another change $(date +%s)" >> app.py
docker build --progress=plain -f dockerfile-steps/05.Dockerfile -t simple-app:step5 . 2>&1 | grep -E 'CACHED|Collecting flask|COPY app.py'
```

Restore the original file:

```bash
mv app.py.bak app.py
```

## Break It

A layer cannot be undone by a later layer. Watch what happens when we create a big file in one
`RUN` and delete it in the next:

<!-- test: timeout=600 -->
```bash
printf 'FROM alpine:3.24\nRUN head -c 50000000 /dev/zero > /big.file\nRUN rm /big.file\n' | docker build -q -t layers-trap -
docker images layers-trap --format 'layers-trap: {{.Size}}'
```

## Troubleshoot It

- **Observe:** the image is about 50 MB bigger than `alpine:3.24`, although `/big.file` does not
  exist in it.
- **Investigate:** `docker history` shows where the size comes from:

<!-- test: contains=rm /big.file; output -->
```bash
docker history layers-trap --format 'table {{.CreatedBy}}\t{{.Size}}' | head -4
```

```text
CREATED BY                                      SIZE
RUN /bin/sh -c rm /big.file # buildkit          4.1kB
RUN /bin/sh -c head -c 50000000 /dev/zero > …   50MB
CMD ["/bin/sh"]                                 0B
```

- **Root cause:** the `head -c ...` layer contains the 50 MB file forever. The `rm` layer only
  adds a marker "this file is deleted" on top; the bytes are still shipped.
- **Fix:** create and delete in the **same** `RUN` (or never create it), so no layer ever contains it.
- **Verify:**

<!-- test: timeout=600; output -->
```bash
printf 'FROM alpine:3.24\nRUN head -c 50000000 /dev/zero > /big.file && rm /big.file\n' | docker build -q -t layers-fixed -
docker images --format 'table {{.Repository}}\t{{.Size}}' | grep -E 'REPOSITORY|layers-'
```

```text
sha256:98c74ac70f902fa1225d8408c928da912ce3abeeea3cf120d8f80a4cfbd6e83f
REPOSITORY                SIZE
layers-fixed              12.9MB
layers-trap               63MB
```

This is exactly why `apt-get update && apt-get install ... && rm -rf /var/lib/apt/lists/*` is
written as **one** `RUN`.

## Common Mistakes

- `COPY . .` at the top of the Dockerfile: every change reinstalls everything.
- Deleting files in a later `RUN` to "make the image smaller": it does not.
- Splitting `apt-get update` and `apt-get install` into two `RUN`s: the cached `update` layer
  becomes stale, and installs fail or install old versions.
- Putting secrets into a layer and deleting them later: they stay readable in the earlier layer.

## Best Practices

- Order instructions from least to most frequently changed.
- Copy the dependency list alone first (`requirements.txt`, `package.json`, `go.mod`), install,
  then copy the code.
- Combine commands that create and clean up temporary files into one `RUN`.
- Use `docker history` to find which instruction made an image big.

## Challenge

Using `docker history`, find out **which instruction** of `simple-app:step5` adds the most size
**on top of the base image**, and how big it is.

## Solution

<details><summary>Show the solution</summary>

`--no-trunc` shows the full instruction; sort by size isn't built in, so read the table:

<!-- test: contains=pip install -->
```bash
docker history simple-app:step5 --format '{{.Size}}\t{{.CreatedBy}}' | head -6
```

The `RUN pip install --no-cache-dir -r requirements.txt` row is the biggest of our own layers
(Flask and its dependencies). Everything below the `WORKDIR /app` row belongs to `python:3.14-slim`.

</details>

## Verification

- [ ] You can explain what a layer is and which instructions create one.
- [ ] You can predict which steps rebuild after a change.
- [ ] You can read `docker history`.
- [ ] You know why deleting a file in a later layer does not shrink the image.

Clean up (and return to the repository root):

```bash
docker rmi layers-trap layers-fixed
cd ../..
```

## Real-World Usage

- Build servers rebuild images many times a day; a cache-friendly Dockerfile saves minutes per
  build and a lot of bandwidth.
- When an image suddenly grows by hundreds of MB, `docker history` points to the instruction.
- Shared base images across a company mean most layers are already present on every server.

## Key Takeaways

- Images are stacks of read-only layers; containers add one writable layer.
- A changed layer invalidates every layer after it.
- Dependencies first, code last.
- Deleting in a later layer never removes bytes from an earlier one.
- Next: [11 · .dockerignore](11-dockerignore.md).
