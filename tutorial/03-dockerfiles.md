# 03 · Dockerfiles

> Write your own image, one instruction at a time. Watch it fail, fix it, and understand every line. Then layers, the
> build cache, and `.dockerignore`.
> Time: about 90 minutes. You need: [02 · Ports and configuration](02-ports-and-config.md).

So far we used images other people built. Now we package **our own application**, `examples/simple-app`, into an image.

```text
  Dockerfile  ---- docker build ---->  Image  ---- docker run ---->  Container
  (recipe)                            (package)                     (running app)
```

A **Dockerfile** is a text file with instructions, read top to bottom. Let's go to the app:

<!-- test: contains=app.py; contains=requirements.txt -->
```bash
cd examples/simple-app
ls
```

Two files matter: `app.py` (the program) and `requirements.txt` (the one library it needs: Flask). The finished
`Dockerfile` is also here, but we will not peek. We will write it step by step; every version is in
`dockerfile-steps/`, so open each file in your editor as we go.

## Step 1 · `FROM`: a starting point

Open `dockerfile-steps/01.Dockerfile`. One line:

```dockerfile
FROM python:3.14-slim
```

Every image starts from a **base image**. `python:3.14-slim` is the official Python 3.14 image on a slimmed-down Debian.
Let's build it:

<!-- test: timeout=600; output=tail:6; contains=naming to -->
```bash
docker build -f dockerfile-steps/01.Dockerfile -t simple-app:step1 .
```

```text
...
#5 exporting manifest list sha256:21f9c18700c58361e10d75887522d7140762ef5542d7bb1faa64029194e747d8 0.0s done
#5 naming to docker.io/library/simple-app:step1 done
#5 unpacking to docker.io/library/simple-app:step1 done
#5 DONE 0.1s

View build details: docker-desktop://dashboard/build/desktop-linux/desktop-linux/t80gx2ovayxkbt16c2zquq8vg
```

Three parts of that command:

| Part | Meaning |
|---|---|
| `-f dockerfile-steps/01.Dockerfile` | which Dockerfile to use (default: a file called `Dockerfile` in the context) |
| `-t simple-app:step1` | the **tag**: name `simple-app`, version `step1` |
| `.` | the **build context**: the folder whose files the build may use. Remember this dot. |

Now run it:

<!-- test: contains=Exited (0) -->
```bash
docker run --name step1 simple-app:step1
docker ps -a --filter name=step1 --format '{{.Names}}: {{.Status}}'
```

It ran and stopped immediately, with exit code 0. You already know why from chapter 01: the default command of the
Python image is the interactive `python3` prompt, and without a terminal it ends at once. Our image contains Python,
but not our app and no instruction to start it.

```bash
docker rm step1
```

## Step 2 · `WORKDIR`, `COPY`, `CMD`: our code and how to start it

`dockerfile-steps/02.Dockerfile`:

```dockerfile
FROM python:3.14-slim
WORKDIR /app
COPY . .
CMD ["python", "app.py"]
```

- `WORKDIR /app`: create `/app` in the image and run the following instructions there.
- `COPY . .`: copy everything from the build context (the first `.`) into the current folder of the image (the
  second `.`, which is `/app`).
- `CMD ["python", "app.py"]`: the **default command**, the main process of the container.

<!-- test: timeout=600 -->
```bash
docker build -f dockerfile-steps/02.Dockerfile -t simple-app:step2 .
```

<!-- test: fail; output=tail:4; contains=ModuleNotFoundError: No module named 'flask' -->
```bash
docker run --rm simple-app:step2
```

```text
Traceback (most recent call last):
  File "/app/app.py", line 9, in <module>
    from flask import Flask
ModuleNotFoundError: No module named 'flask'
```

Don't fix it yet. We intentionally broke it. Read the last line: `ModuleNotFoundError: No module named 'flask'`.

- **What happened?** The container started our app and it crashed immediately.
- **Why?** `app.py` uses Flask. Our image has Python and our code, but nobody installed Flask in it.
- **Lesson:** an image contains **only** what you put into it. Your laptop may have Flask installed; the image does
  not know or care.

## Step 3 · `RUN`: install dependencies

`dockerfile-steps/03.Dockerfile` adds one line:

```dockerfile
RUN pip install --no-cache-dir -r requirements.txt
```

`RUN` executes a command **at build time**, and the result (here: Flask installed in the image) becomes part of the
image. Compare with `CMD`, which runs at **container start**.

<!-- test: timeout=600 -->
```bash
docker build --progress=plain -f dockerfile-steps/03.Dockerfile -t simple-app:step3 .
```

`--progress=plain` prints every build step in full, so you can see pip downloading and installing Flask (if you built
this before, you see `CACHED` instead: Docker reused the earlier result, more on that soon). Now run it,
publishing the app's port:

```bash
docker run -d --name step3 -p 5000:5000 simple-app:step3
```

<!-- test: retry=15; output; contains=Hello from simple-app! -->
```bash
curl -s http://localhost:5000
```

```text
Hello from simple-app!
environment: development
container hostname: ed88c1d93152
```

It works! Your first application image. Notice `environment: development`: the app's built-in default, because nobody
set `APP_ENV`.

```bash
docker rm -f step3
```

## Step 4 · `ENV` and `EXPOSE`: defaults and documentation

`dockerfile-steps/04.Dockerfile` adds:

```dockerfile
ENV APP_ENV=production
EXPOSE 5000
```

- `ENV` sets a **default** environment variable inside the image. `docker run -e` can still override it.
- `EXPOSE 5000` **documents** that the app listens on 5000. It does **not** publish anything. You still need `-p`.

<!-- test: timeout=600 -->
```bash
docker build -f dockerfile-steps/04.Dockerfile -t simple-app:step4 .
docker run -d --name step4 -p 5000:5000 simple-app:step4
```

<!-- test: retry=15; contains=environment: production -->
```bash
curl -s http://localhost:5000
```

`environment: production`, the image's new default. And `EXPOSE` is visible to anyone who inspects the image:

<!-- test: contains=5000/tcp -->
```bash
docker inspect simple-app:step4 --format '{{json .Config.ExposedPorts}}'
docker rm -f step4
```

## Side quest · `ENTRYPOINT` vs `CMD`

Both define what runs when the container starts. The difference shows when you add arguments to `docker run`. Look at
`dockerfile-steps/entrypoint-vs-cmd.Dockerfile`:

```dockerfile
FROM alpine:3.24
ENTRYPOINT ["echo", "Hello,"]
CMD ["world"]
```

<!-- test: contains=Hello, world -->
```bash
docker build -q -f dockerfile-steps/entrypoint-vs-cmd.Dockerfile -t greeter .
docker run --rm greeter
```

<!-- test: contains=Hello, Docker -->
```bash
docker run --rm greeter Docker
```

- `ENTRYPOINT` is the fixed program (`echo Hello,`).
- `CMD` is the **default argument** (`world`), replaced by whatever you type after the image name.

Use `CMD` alone (like our app) when the whole command may be replaced, for example `docker run simple-app:step4 python
--version`. Use `ENTRYPOINT` when the image is "a tool" that always runs the same program.

## Part 2 · Layers and the build cache

Every instruction in a Dockerfile creates a **layer**. The image is the stack of them:

```text
 Dockerfile                                    Image
 FROM python:3.14-slim          ---->  +------------------------------+
 WORKDIR /app                   ---->  | layers of python:3.14-slim   |
 COPY . .                       ---->  +------------------------------+
 RUN pip install ...            ---->  | WORKDIR /app        (0 B)    |
 ENV / EXPOSE / CMD             ---->  | COPY . .            (KB)     |
                                       | RUN pip install     (MB)     |
                                       | ENV/EXPOSE/CMD      (0 B)    |
                                       +------------------------------+
```

Let's see the real layers:

<!-- test: output=head:10; contains=pip install -->
```bash
docker history simple-app:step4
```

```text
IMAGE          CREATED             CREATED BY                                      SIZE      COMMENT
1273cbf408e4   13 minutes ago      CMD ["python" "app.py"]                         0B        buildkit.dockerfile.v0
<missing>      13 minutes ago      EXPOSE [5000/tcp]                               0B        buildkit.dockerfile.v0
<missing>      13 minutes ago      ENV APP_ENV=production                          0B        buildkit.dockerfile.v0
<missing>      13 minutes ago      RUN /bin/sh -c pip install --no-cache-dir -r…   16.9MB    buildkit.dockerfile.v0
<missing>      15 minutes ago      COPY . . # buildkit                             16.4kB    buildkit.dockerfile.v0
<missing>      About an hour ago   WORKDIR /app                                    8.19kB    buildkit.dockerfile.v0
<missing>      2 days ago          CMD ["python3"]                                 0B        buildkit.dockerfile.v0
<missing>      2 days ago          RUN /bin/sh -c set -eux;  for src in idle3 p…   16.4kB    buildkit.dockerfile.v0
<missing>      2 days ago          RUN /bin/sh -c set -eux;   savedAptMark="$(a…   42MB      buildkit.dockerfile.v0
...
```

Read it bottom to top (oldest first): the base image layers, then ours. `CREATED BY` shows the instruction, `SIZE` how
much it added. `ENV`, `EXPOSE`, `CMD` and `WORKDIR` add 0 B: they only change metadata. `RUN pip install` adds the
megabytes of Flask.

### The cache

When you build again, Docker reuses a layer if its instruction and its inputs did not change. That is the **build
cache**, and it makes rebuilds fast. Let's prove it. Make a tiny change to the app (we add a comment with the current time, so the file is really different every time you
try this):

```bash
echo "# a tiny change made at $(date)" >> app.py
```

Now rebuild step 3 and look only at the interesting lines:

<!-- test: timeout=600; output; contains=Successfully installed -->
```bash
docker build --progress=plain -f dockerfile-steps/03.Dockerfile -t simple-app:step3 . 2>&1 | grep -E '\[[0-9]/[0-9]\]|CACHED|Successfully installed'
```

```text
#4 [1/4] FROM docker.io/library/python:3.14-slim@sha256:c3e521df8b2b498a7a682e7e18676771cb80c6b75b8699af886b2d554ce40151
#6 [2/4] WORKDIR /app
#6 CACHED
#7 [3/4] COPY . .
#8 [4/4] RUN pip install --no-cache-dir -r requirements.txt
#8 2.141 Successfully installed blinker-1.9.0 click-8.5.0 flask-3.1.3 itsdangerous-2.2.0 jinja2-3.1.6 markupsafe-3.0.4 werkzeug-3.1.9
```

We changed **one comment line** in `app.py` and pip installed Flask **again**. Why? In step 3, `COPY . .` comes
**before** `RUN pip install`. The copied files changed, so the `COPY` layer changed, and **every layer after a
changed layer is rebuilt**. The cache is a chain; break one link and everything below it is rebuilt.

Step 5 fixes this. Open `dockerfile-steps/05.Dockerfile`:

```dockerfile
FROM python:3.14-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
...
```

Dependencies first (they change rarely), code last (it changes all the time). Build it once, then change the app again
and rebuild:

<!-- test: timeout=600 -->
```bash
docker build -q -f dockerfile-steps/05.Dockerfile -t simple-app:step5 .
echo "# another tiny change made at $(date)" >> app.py
```

<!-- test: timeout=600; output; contains=CACHED; absent=Successfully installed -->
```bash
docker build --progress=plain -f dockerfile-steps/05.Dockerfile -t simple-app:step5 . 2>&1 | grep -E '\[[0-9]/[0-9]\]|CACHED|Successfully installed'
```

```text
#5 [1/5] FROM docker.io/library/python:3.14-slim@sha256:c3e521df8b2b498a7a682e7e18676771cb80c6b75b8699af886b2d554ce40151
#6 [2/5] WORKDIR /app
#6 CACHED
#7 [3/5] COPY requirements.txt .
#7 CACHED
#8 [4/5] RUN pip install --no-cache-dir -r requirements.txt
#8 CACHED
#9 [5/5] COPY app.py .
```

Now look at the output: the `RUN pip install` step is `CACHED`. Only `COPY app.py` was redone. On a real project with
hundreds of dependencies this is the difference between a 3-second and a 3-minute build.

Undo our test edits (this restores `app.py` from git):

```bash
git checkout -- app.py
```

## Part 3 · `.dockerignore`: what goes into the build context

Remember the `.` at the end of `docker build`? Docker sends **the whole folder** to the engine before building. That is
the **build context**. What if the folder contains things that should never be in an image?

Let's simulate a real project folder: a big file nobody needs, and a `.env` file with a secret:

```bash
mkdir -p junk
head -c 50000000 /dev/zero > junk/big.bin
printf 'DB_PASSWORD=super-secret-do-not-ship\n' > .env
```

(`head -c` creates a 50 MB file. In PowerShell, create any large file instead, or use WSL.)

### Without `.dockerignore`

This folder already has a `.dockerignore` (you will see it in a moment). Let's switch it off and build step 2, which uses
`COPY . .`:

<!-- test: timeout=600; output; contains=transferring context -->
```bash
mv .dockerignore .dockerignore.off
docker build --progress=plain -f dockerfile-steps/02.Dockerfile -t simple-app:leaky . 2>&1 | grep 'transferring context'
```

```text
#3 transferring context: 2B done
#4 transferring context: 50.02MB 1.9s done
```

Tens of megabytes sent to the engine for a 40-line app. Slow, and worse:

<!-- test: contains=super-secret-do-not-ship -->
```bash
docker run --rm simple-app:leaky cat .env
```

**The secret is inside the image.** Anyone who pulls this image can read it. This happens in real companies.

### With `.dockerignore`

<!-- test: contains=junk/ -->
```bash
mv .dockerignore.off .dockerignore
cat .dockerignore
```

It lists files and folders that are never sent to the build: `.git`, `.env`, logs, `junk/`, and the Dockerfiles
themselves. Build again:

<!-- test: timeout=600; output; contains=transferring context -->
```bash
docker build --progress=plain -f dockerfile-steps/02.Dockerfile -t simple-app:clean . 2>&1 | grep 'transferring context'
```

```text
#3 transferring context: 295B done
#4 transferring context: 63B done
```

A few kilobytes. And the secret?

<!-- test: absent=.env; contains=app.py -->
```bash
docker run --rm simple-app:clean ls -a
```

Not there. Clean up the junk we created:

```bash
rm -rf junk .env
```

## Step 6 · The finished Dockerfile

Now open `examples/simple-app/Dockerfile`. You know every line in it. The only new thing is at the end:

```dockerfile
RUN useradd --create-home --uid 10001 appuser
USER appuser
```

By default, processes in a container run as **root**. `USER` switches to an ordinary user, so a bug in the app cannot
do root things. We will dig into this in chapter 08. Build the final image (this is the one other chapters use):

<!-- test: timeout=600; contains=appuser -->
```bash
docker build -t simple-app:1.0 .
docker run --rm simple-app:1.0 whoami
```

`appuser`, not `root`. Back to the repository root for the next chapter:

```bash
cd ../..
```

## Where would I use this as a DevOps engineer?

- Every application you deploy ships as an image built from a Dockerfile, usually by a build server. Reading and fixing
  Dockerfiles is a daily task.
- "Why is our build so slow?" is very often instruction order: dependencies copied together with the code.
- "Why is there a password in our image?" is a missing `.dockerignore` (or a `COPY . .` too many).
- `docker history` is how you find out which instruction made an image huge.

## What you learned

- `FROM`, `WORKDIR`, `COPY`, `RUN`, `ENV`, `EXPOSE`, `CMD`, `ENTRYPOINT`, `USER`.
- `docker build -f ... -t name:tag <context>`.
- `RUN` happens at build time; `CMD` at container start.
- Each instruction is a layer; a changed layer rebuilds every layer after it. Put rarely changing things first.
- The build context is everything in the folder, unless `.dockerignore` excludes it.

## Try it yourself

- Labs: [06-first-dockerfile](../labs/06-first-dockerfile/README.md), [07-layers-and-cache](../labs/07-layers-and-cache/README.md),
  [08-dockerignore](../labs/08-dockerignore/README.md)
- Troubleshooting: [01-container-exits-immediately](../troubleshooting/01-container-exits-immediately/README.md),
  [05-dockerfile-build-fails](../troubleshooting/05-dockerfile-build-fails/README.md)
- Challenges: the "Dockerfiles" section of [challenges/README.md](../challenges/README.md)
- Deeper: [docs/09-dockerfile.md](../docs/09-dockerfile.md), [docs/10-image-layers.md](../docs/10-image-layers.md),
  [docs/11-dockerignore.md](../docs/11-dockerignore.md)

## Next

[04 · Data](04-data.md)
