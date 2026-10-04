# 05 · Dockerfile build fails

> `docker build` stops with "not found", but the file is right there in the folder.
> Time: 15 minutes · You need: labs 06–08 (Dockerfile, layers, .dockerignore)

## Problem

The Dockerfile here is the same one that worked yesterday. Since then, someone added a `.dockerignore`
"to keep log files and notes out of the image". Now the build fails.

Let's reproduce it. From the repository root:

```bash
cd troubleshooting/05-dockerfile-build-fails
```

<!-- test: fail; contains="/requirements.txt": not found -->
```bash
docker build -t build-demo .
```

## Symptoms

The build stops at the `COPY requirements.txt .` step. Among the long error text:

```text
ERROR: failed to build: failed to solve: failed to compute cache key: failed to calculate checksum of ref ...: "/requirements.txt": not found
```

Symptom in one sentence: *"docker build says requirements.txt is not found, but `ls` shows it."*

## Investigation

**Step 1: is the file really there?** Don't trust memory, check:

<!-- test: contains=requirements.txt -->
```bash
ls -la
```

It is. So the problem is not the folder on your disk. It is what Docker **receives**.

**Step 2: remember how a build works.** `docker build .` first packs the folder (the *build context*)
and sends it to the Docker engine. The engine never reads your disk directly. `COPY` can only copy
files that are inside that package. And one file decides what is left out of the package:

<!-- test: contains=*.txt -->
```bash
cat .dockerignore
```

`*.txt` matches every text file, so also `requirements.txt`.

**Step 3: prove it.** Let's build a throw-away image that copies the whole build context and lists it.
The Dockerfile comes from standard input (`-f -`), and `--progress=plain` shows the output of `RUN`:

<!-- test: contains=/ctx/app.py; absent=/ctx/requirements.txt -->
```bash
docker build --no-cache --progress=plain -t context-check -f - . <<'EOF'
FROM busybox:1.37
COPY . /ctx
RUN find /ctx -type f
EOF
```

In the output you see `/ctx/app.py`, `/ctx/Dockerfile` and more, but no `/ctx/requirements.txt`.
(You do see `/ctx/fixed/requirements.txt`: a pattern like `*.txt` only matches files in the top folder of
the context. To match in every subfolder you would write `**/*.txt`.)
This trick works for any project: whenever a `COPY` "cannot find" something, list what Docker really got.

## Commands

| Command | What it told us |
|---|---|
| `docker build ...` (read the full error) | `COPY requirements.txt` fails: `not found` |
| `ls -la` | the file exists on disk |
| `cat .dockerignore` | the pattern `*.txt` excludes it |
| `docker build -f - . <<'EOF' ... COPY . /ctx ... RUN find /ctx` | the build context really lacks the file |

## Root Cause

`.dockerignore` contains `*.txt`. That pattern removes `requirements.txt` from the build context,
so the `COPY requirements.txt .` instruction has nothing to copy. The Dockerfile is fine.

## Fix

Make the ignore rule match only what should stay out. The folder `fixed/` contains the same
Dockerfile and app, with a corrected `.dockerignore` (the broken files stay as they are, so you can
practise again):

<!-- test: contains=*.log; absent=*.txt -->
```bash
cat fixed/.dockerignore
```

Build the fixed version. The last argument is the build context, now the `fixed/` folder:

```bash
docker build -t build-demo:fixed fixed
```

In your own project you would simply edit the `.dockerignore` line, or add an exception with `!`:

```text
*.txt
!requirements.txt
```

## Verification

The image builds, and Flask really got installed from `requirements.txt`:

<!-- test: contains=Name: Flask -->
```bash
docker run --rm build-demo:fixed pip show flask
```

And the app starts:

```bash
docker run -d --name build-ok -p 5000:5000 build-demo:fixed
```

<!-- test: retry=15; contains=Hello from simple-app -->
```bash
curl -s http://localhost:5000
```

## Clean up

```bash
docker rm -f build-ok
docker rmi build-demo:fixed context-check
cd ../..
```

## Lesson Learned

- `docker build` copies from the **build context**, not from your disk. `.dockerignore` decides what is in it.
- "not found" during `COPY` means: the file is not in the context. Check the path, the build context
  argument (the `.` at the end), and `.dockerignore`.
- Wide patterns like `*.txt` are dangerous. Use exceptions (`!requirements.txt`) or narrower patterns.
- To see the real build context, build a throw-away image that runs `find` on `COPY . /ctx`.

Next: [06 · Environment variable missing](../06-environment-variable-missing/README.md)
