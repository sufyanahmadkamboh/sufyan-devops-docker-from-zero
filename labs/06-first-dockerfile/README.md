# Lab 06 · Your First Dockerfile

> **Goal:** package a real application into your own image, one instruction at a time, and understand why each line is there.
> **Time:** about 60 minutes · **You need:** [Lab 05](../05-environment-variables/README.md)

## What you will learn

- What a **Dockerfile** is and how `docker build` turns it into an image
- The instructions `FROM`, `WORKDIR`, `COPY`, `RUN`, `ENV`, `EXPOSE`, `CMD`, `ENTRYPOINT`
- `docker build -t` (name and tag), `-f` (which Dockerfile) and the **build context** (the `.` at the end)
- Why an image needs its dependencies installed *inside* it
- The difference between `CMD` and `ENTRYPOINT`

```text
   Dockerfile  ---docker build--->  IMAGE  ---docker run--->  CONTAINER
   (recipe)                         (package)                 (running app)

   docker build -f dockerfile-steps/03.Dockerfile -t simple-app:step3 .
                |                                 |                  |
                which recipe                      name:tag           build context = this folder
```

## The application

We package `examples/simple-app`, a web app of about 30 lines. You do **not** need to know Python: the app reads two environment variables and answers with a greeting and the container's hostname. Have a look:

```bash
cd examples/simple-app
ls
cat app.py
cat requirements.txt
```

- `app.py`: the application. It listens on port `5000` and on every network interface (`0.0.0.0`).
- `requirements.txt`: one line, `flask==3.1.3`. Flask is the library the app needs.
- `dockerfile-steps/`: the Dockerfile we are going to grow, one step per file. Open each one before you build it.

## Step 1 · The smallest Dockerfile: `FROM`

```bash
cat dockerfile-steps/01.Dockerfile
```

`FROM python:3.14-slim` means: start from the official Python image, version 3.14, "slim" variant (Debian without extras). Every Dockerfile begins with `FROM`. Build it:

<!-- test: output=tail:6 -->
```bash
docker build -f dockerfile-steps/01.Dockerfile -t simple-app:step1 .
```

```text
...
#5 exporting manifest list sha256:f3b879a66ba56b45a3651eb0286e2286ce2a90402185a84a2a7107147cf8933f 0.0s done
#5 naming to docker.io/library/simple-app:step1 done
#5 unpacking to docker.io/library/simple-app:step1 done
#5 DONE 0.1s

View build details: docker-desktop://dashboard/build/desktop-linux/desktop-linux/odcexjpb0cyvt9anbp9emnaq1
```

**What you see:** BuildKit, Docker's builder, prints numbered steps (`#1`, `#2`...). It loads the Dockerfile, sends the **build context** (the files of this folder, minus what `.dockerignore` excludes, Lab 08), pulls the base image and finally names the result `simple-app:step1`.

Run it:

<!-- test: output; contains=Python 3.14 -->
```bash
docker run --rm simple-app:step1 python --version
```

```text
Python 3.14.8
```

We have our own image! But it only contains Python. Our app is not in it.

## Step 2 · Add the code: `WORKDIR`, `COPY`, `CMD`

```bash
cat dockerfile-steps/02.Dockerfile
```

| Instruction | Meaning |
|---|---|
| `WORKDIR /app` | create `/app` inside the image and use it as the current folder for everything that follows |
| `COPY . .` | copy the build context (first `.`) into the current folder of the image (second `.` = `/app`) |
| `CMD ["python", "app.py"]` | the default command when a container starts: the **main process** |

<!-- test: output=tail:4 -->
```bash
docker build -f dockerfile-steps/02.Dockerfile -t simple-app:step2 .
```

```text
...
#8 unpacking to docker.io/library/simple-app:step2 done
#8 DONE 0.1s

View build details: docker-desktop://dashboard/build/desktop-linux/desktop-linux/gjcwpte72l0x4ysd3tpqxzetl
```

Let's run it:

<!-- test: fail; contains=No module named 'flask' -->
```bash
docker run --rm simple-app:step2
```

It crashes. Look at the last line: `ModuleNotFoundError: No module named 'flask'`. Our code is in the image, but the library it needs is not. Your laptop may have Flask installed; **the image does not know your laptop**. Everything the app needs must be inside the image.

## Step 3 · Install dependencies: `RUN`

```bash
cat dockerfile-steps/03.Dockerfile
```

`RUN pip install --no-cache-dir -r requirements.txt` runs a command **while building** the image, and saves the result in the image. (`--no-cache-dir` tells pip not to keep its download cache, which would only waste space.)

> `RUN` happens at **build** time, once. `CMD` happens at **run** time, every time a container starts. Mixing them up is the most common Dockerfile mistake.

<!-- test: output=tail:8 -->
```bash
docker build -f dockerfile-steps/03.Dockerfile -t simple-app:step3 .
```

```text
...
#9 exporting config sha256:94850611b5c8634806a53f5888308c6be6f80c16a6ee401533936893f148a890 done
#9 exporting attestation manifest sha256:14bffa5c8c98a31f8c38878cf0f54ff30c97154d1c90b7e47ad1021858971b93 0.0s done
#9 exporting manifest list sha256:67c42d9bdc4deb7ce6df78d7a99803d74ea1d785443d2b4b608d6d97586bb636 0.0s done
#9 naming to docker.io/library/simple-app:step3 done
#9 unpacking to docker.io/library/simple-app:step3 done
#9 DONE 0.1s

View build details: docker-desktop://dashboard/build/desktop-linux/desktop-linux/lh79ah8tmqd9p3hah7xpmn3is
```

Run it in the background, with a port mapping (Lab 04):

```bash
docker run -d --name simple -p 5000:5000 simple-app:step3
```

<!-- test: retry=15; output; contains=Hello from simple-app -->
```bash
curl -s http://localhost:5000
```

```text
Hello from simple-app!
environment: development
container hostname: cce90fa05cb5
```

**What you see:** the greeting, `environment: development` (the app's default) and the container hostname. Open http://localhost:5000 in your browser too. Then look at the logs:

<!-- test: retry=15; output=head:4; contains=simple-app starting on 0.0.0.0:5000 -->
```bash
docker logs simple
```

```text
simple-app starting on 0.0.0.0:5000 (APP_ENV=development)
 * Serving Flask app 'app'
 * Debug mode: off
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
...
```

The first line is printed by `app.py`. The warning *"This is a development server"* comes from Flask: fine for learning; the multi-container app later uses a production server (gunicorn).

## Step 4 · Configuration and documentation: `ENV`, `EXPOSE`

```bash
cat dockerfile-steps/04.Dockerfile
```

- `ENV APP_ENV=production` sets a **default** environment variable inside the image.
- `EXPOSE 5000` **documents** that the app listens on 5000. It does *not* publish anything: you still need `-p`.

<!-- test: output=tail:3 -->
```bash
docker build -f dockerfile-steps/04.Dockerfile -t simple-app:step4 .
```

```text
...
#9 DONE 0.1s

View build details: docker-desktop://dashboard/build/desktop-linux/desktop-linux/cwhfr47d6tscws9ltnqwdhjwd
```

<!-- test: retry=15; contains=environment: production -->
```bash
docker rm -f simple
docker run -d --name simple -p 5000:5000 simple-app:step4
curl -s http://localhost:5000
```

Now the app says `environment: production`, the default from the image. Override it at run time (Lab 05):

<!-- test: retry=15; contains=environment: testing -->
```bash
docker rm -f simple
docker run -d --name simple -p 5000:5000 -e APP_ENV=testing simple-app:step4
curl -s http://localhost:5000
```

`EXPOSE` is stored in the image's metadata:

<!-- test: output; contains=5000/tcp -->
```bash
docker image inspect simple-app:step4 --format '{{json .Config.ExposedPorts}}'
```

```text
{"5000/tcp":{}}
```

## Step 5 · `CMD` versus `ENTRYPOINT`

```bash
cat dockerfile-steps/entrypoint-vs-cmd.Dockerfile
```

- `ENTRYPOINT ["echo", "Hello,"]` is the program that always runs.
- `CMD ["world"]` is the **default argument**, replaced by whatever you type after the image name.

<!-- test: output; contains=Hello, world; contains=Hello, Docker -->
```bash
docker build -q -f dockerfile-steps/entrypoint-vs-cmd.Dockerfile -t greeter .
docker run --rm greeter
docker run --rm greeter Docker
```

```text
sha256:15597981addb6a5cc4e00ccf9750b249a4237e01842c9c1aa2198874b4a89061
Hello, world
Hello, Docker
```

(`-q` = quiet build, only the image ID is printed.) With only `CMD`, as in our simple-app, anything after the image name *replaces* the whole command. That is why `docker run --rm simple-app:step1 python --version` worked in Step 1. `--entrypoint` replaces the entrypoint itself:

<!-- test: contains=Bye -->
```bash
docker run --rm --entrypoint echo greeter Bye
```

| | `CMD` | `ENTRYPOINT` |
|---|---|---|
| Purpose | default command or default arguments | the fixed program |
| `docker run image something` | `something` replaces CMD | `something` is appended as arguments |
| Typical use | most application images | tool-like images (`greeter`, CLI tools) |

## Step 6 · The finished Dockerfile

Steps 5 and 6 (cache-friendly order and a non-root user) are explained in Labs 07 and 15. The finished result is `examples/simple-app/Dockerfile`, read it now: every line has a comment. When the file is called `Dockerfile`, you do not need `-f`:

<!-- test: output=tail:3 -->
```bash
docker build -t simple-app:1.0 .
```

```text
...
#11 DONE 0.1s

View build details: docker-desktop://dashboard/build/desktop-linux/desktop-linux/r892zcixd374197ualsr2d92f
```

<!-- test: output; contains=simple-app -->
```bash
docker images simple-app
```

```text
IMAGE                   ID             DISK USAGE   CONTENT SIZE   EXTRA
simple-app:1.0          3f6962c3154a        212MB         51.9MB        
simple-app:clean        614749901fce        189MB         46.5MB        
simple-app:fat          f29822dcd7e5       1.75GB          454MB        
simple-app:leaky        06809757035e        239MB         46.5MB        
simple-app:multistage   2bcbfd28cfde        108MB         26.1MB        
simple-app:root         939d3ab86401        212MB         51.9MB        
simple-app:step1        f3b879a66ba5        189MB         46.5MB        
simple-app:step2        0709c7207019        189MB         46.5MB        
simple-app:step3        67c42d9bdc4d        212MB         51.9MB        
simple-app:step4        ead82f948cbf        212MB         51.9MB   U    
simple-app:step5        667a8d95bf73        212MB         51.9MB        
```

**What you see:** one repository `simple-app` with several tags. Some tags may share the same IMAGE ID when their content is identical.

## Break it · The wrong build context

The `.` at the end of `docker build` is not decoration. Let's point it at the wrong folder:

<!-- test: fail; contains=requirements.txt -->
```bash
docker build -f dockerfile-steps/03.Dockerfile -t simple-app:broken dockerfile-steps
```

## Troubleshoot it

**Observe.** The build fails at the `RUN pip install` step. pip says it cannot open `requirements.txt`.

**Investigate.** What did `COPY . .` copy? The build context is the last argument: `dockerfile-steps`. What is in that folder?

<!-- test: output; absent=requirements.txt -->
```bash
ls dockerfile-steps
```

```text
01.Dockerfile
02.Dockerfile
03.Dockerfile
04.Dockerfile
05.Dockerfile
06.Dockerfile
entrypoint-vs-cmd.Dockerfile
```

Only Dockerfiles. No `app.py`, no `requirements.txt`.

**Root cause.** `-f` says *which recipe*, the last argument says *which ingredients*. Docker can only `COPY` files from the build context. Anything outside it does not exist for the build.

**Fix.** Use the app folder as the context:

<!-- test: output=tail:2 -->
```bash
docker build -f dockerfile-steps/03.Dockerfile -t simple-app:fixed .
```

```text
...

View build details: docker-desktop://dashboard/build/desktop-linux/desktop-linux/qao6iydxsilgxv199ycqobctx
```

**Verify.** The build ends with `naming to ...simple-app:fixed`.

## Challenge

**Task:** make the app greet with `Hi from my first image` **without editing `app.py`**.

**Requirements:** run it as a container named `mine` on host port `5002`, using the image `simple-app:1.0`.

**Hints:** look at how `app.py` builds its first line. Which environment variable does it read? (Bonus: what would you add to a Dockerfile to make it the default?)

**Expected result:** `curl -s http://localhost:5002` starts with `Hi from my first image!`.

<details>
<summary>Solution</summary>

```bash
docker run -d --name mine -p 5002:5000 -e GREETING="Hi from my first image" simple-app:1.0
```

<!-- test: retry=15; output; contains=Hi from my first image! -->
```bash
curl -s http://localhost:5002
```

```text
Hi from my first image!
environment: production
container hostname: b9940bf2b969
```

**Explanation:** `app.py` reads `GREETING` from the environment. `-e` sets it for this container. To make it the default for everyone, add `ENV GREETING="Hi from my first image"` to a Dockerfile and rebuild.

</details>

## Verify

You can now:

- [ ] write a Dockerfile with `FROM`, `WORKDIR`, `COPY`, `RUN`, `ENV`, `EXPOSE` and `CMD`
- [ ] explain the difference between build time (`RUN`) and run time (`CMD`)
- [ ] build with `docker build -t name:tag`, choose a file with `-f`, and explain the build context
- [ ] explain why "it works on my laptop" does not mean "it works in the image"
- [ ] explain `CMD` versus `ENTRYPOINT`

## Clean up

```bash
docker rm -f simple mine
cd ../..
```

We keep the `simple-app` images: Lab 07 uses them to show the build cache.

## Next

➡️ [Lab 07 · Layers and cache](../07-layers-and-cache/README.md) · 📖 Concepts: [docs/09-dockerfile.md](../../docs/09-dockerfile.md)
