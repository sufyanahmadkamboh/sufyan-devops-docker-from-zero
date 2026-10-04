# Dockerfile

> Lesson 09 · about 60 minutes · you need: [08 · Environment Variables](08-environment-variables.md)

## What is it?

A **Dockerfile** is a text file with step-by-step instructions to build an image. Each line is
one instruction: start from this base image, copy these files, run this command, use this port,
start this program. `docker build` reads it and produces an image.

```text
   Dockerfile  --(docker build)-->  Image  --(docker run)-->  Container
   (recipe)                         (package)                  (running app)
```

## Why do we need it?

Images like `nginx` or `python` are generic. Your application needs **its own** image: Python
plus your code plus your dependencies. Writing that down as a Dockerfile makes the build:

- **repeatable:** anyone runs `docker build` and gets the same result;
- **reviewable:** it is a text file in git, changes are visible in pull requests;
- **automatable:** a build server can build it without a human clicking anything.

## How does it work?

### The instructions you need

| Instruction | What it does | Example |
|---|---|---|
| `FROM` | the base image to start from (always first) | `FROM python:3.14-slim` |
| `WORKDIR` | the working directory for the next instructions (created if missing) | `WORKDIR /app` |
| `COPY` | copy files from the **build context** into the image | `COPY app.py .` |
| `RUN` | run a command **while building** (installs, setup); the result is saved in the image | `RUN pip install -r requirements.txt` |
| `ENV` | set default environment variables | `ENV APP_ENV=production` |
| `EXPOSE` | document the port the app listens on (does not publish it) | `EXPOSE 5000` |
| `USER` | which user runs the following instructions and the container | `USER appuser` |
| `CMD` | the default command when a container starts (easy to override) | `CMD ["python", "app.py"]` |
| `ENTRYPOINT` | the fixed program; `CMD` then supplies its default arguments | `ENTRYPOINT ["echo", "Hello,"]` |

Other useful ones you will meet later: `ARG` (build-time variable), `LABEL` (metadata),
`HEALTHCHECK` (how Docker checks the app is healthy), `COPY --from=` (multi-stage builds,
lesson [20 · Image Optimization](20-image-optimization.md)).

### RUN versus CMD

```text
   RUN  pip install flask      -> happens ONCE, during docker build, result stored in the image
   CMD  python app.py          -> happens EVERY time a container starts, during docker run
```

### ENTRYPOINT versus CMD

```text
   ENTRYPOINT ["echo", "Hello,"]     CMD ["world"]

   docker run greeter            ->  echo Hello, world
   docker run greeter Docker     ->  echo Hello, Docker      (arguments replace CMD only)
```

### The build context

`docker build -t name .` — the final `.` is the **build context**: the folder whose files Docker
may `COPY`. Docker sends that folder (minus what `.dockerignore` excludes) to the engine before
building. `COPY` can only see files inside it.

### Exec form versus shell form

Write `CMD ["python", "app.py"]` (JSON "exec form"), not `CMD python app.py` ("shell form").
The exec form starts Python directly as PID 1, so it receives the stop signal from `docker stop`
and shuts down cleanly.

## Prerequisites

- `examples/simple-app/` from this repository: `app.py` (a 30-line Flask app),
  `requirements.txt` (`flask==3.1.3`) and the step files in `dockerfile-steps/`.

## Hands-on Lab

We build the image in steps, adding only what the previous step proved we need. Go to the app:

```bash
cd examples/simple-app
```

**Step 1 · only a base image.** `dockerfile-steps/01.Dockerfile` contains just `FROM python:3.14-slim`.

<!-- test: timeout=600; contains=simple-app:step1 -->
```bash
docker build -f dockerfile-steps/01.Dockerfile -t simple-app:step1 .
```

It runs Python, but there is no app in it yet:

<!-- test: contains=Python 3.14 -->
```bash
docker run --rm simple-app:step1 python --version
```

**Step 2 · add the code and a start command** (`WORKDIR /app`, `COPY . .`, `CMD ["python", "app.py"]`):

<!-- test: timeout=600 -->
```bash
docker build -f dockerfile-steps/02.Dockerfile -t simple-app:step2 .
```

<!-- test: fail; contains=No module named 'flask' -->
```bash
docker run --rm simple-app:step2
```

The image builds, but the app crashes: `ModuleNotFoundError: No module named 'flask'`. The base
image has Python, not our dependency. We need `RUN`.

**Step 3 · install the dependency** (`RUN pip install --no-cache-dir -r requirements.txt`):

<!-- test: timeout=600 -->
```bash
docker build -f dockerfile-steps/03.Dockerfile -t simple-app:step3 .
docker run -d --name step3 -p 5000:5000 simple-app:step3
```

<!-- test: retry=15; contains=Hello from simple-app -->
```bash
curl -s http://localhost:5000
```

**Step 4 · configuration and documentation** (`ENV APP_ENV=production`, `EXPOSE 5000`):

<!-- test: timeout=600; contains=APP_ENV=production; contains=5000/tcp; output -->
```bash
docker build -q -f dockerfile-steps/04.Dockerfile -t simple-app:step4 .
docker image inspect simple-app:step4 --format 'env: {{.Config.Env}}
ports: {{.Config.ExposedPorts}}
cmd: {{.Config.Cmd}}'
```

```text
sha256:753c5e1653cd669655f850cc43f34564d3224b666fdfaa4454757476c13e7128
env: [PATH=/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin PYTHON_VERSION=3.14.8 PYTHON_SHA256=c2215904f02b175596dc49351585104f4bc20341e1c47378b26a2c274360ce73 APP_ENV=production]
ports: map[5000/tcp:{}]
cmd: [python app.py]
```

Steps 5 (cache-friendly order) and 6 (non-root user) follow in lessons
[10 · Image Layers](10-image-layers.md) and [19 · Security Basics](19-security-basics.md).
The finished result is `examples/simple-app/Dockerfile`. The full guided lab is
[labs/06-first-dockerfile](../labs/06-first-dockerfile/README.md).

## Expected Result

- Each `docker build` ends with a line that names the image (`naming to ...simple-app:stepN`).
- Step 1 prints `Python 3.14.x`; step 2 fails with `No module named 'flask'`; step 3 answers
  `Hello from simple-app!`.
- The step 4 image carries `APP_ENV=production` and documents `5000/tcp`.
- `docker images simple-app` lists one image per tag.

## Experiment

ENTRYPOINT and CMD together, with `dockerfile-steps/entrypoint-vs-cmd.Dockerfile`:

<!-- test: contains=Hello, world; contains=Hello, Docker -->
```bash
docker build -q -f dockerfile-steps/entrypoint-vs-cmd.Dockerfile -t greeter .
docker run --rm greeter
docker run --rm greeter Docker
```

Override the CMD of our app at run time: the image stays the same, only this container runs
something else:

<!-- test: contains=Flask -->
```bash
docker run --rm simple-app:step3 pip show flask
```

## Break It

Build a Dockerfile with a typo in an instruction (here we pipe a two-line Dockerfile straight
into `docker build` with `-`; such a build has no context, which is fine without `COPY`):

<!-- test: fail; contains=unknown instruction -->
```bash
printf 'FROM python:3.14-slim\nRUNN echo hello\n' | docker build -t typo -
```

## Troubleshoot It

- **Observe:** the build stops before doing anything: `dockerfile parse error ... unknown
  instruction: RUNN` (BuildKit even suggests `did you mean RUN?`).
- **Investigate:** the error names the line number and the word it did not understand.
- **Root cause:** `RUNN` is not an instruction.
- **Fix and verify:**

<!-- test: contains=hello -->
```bash
printf 'FROM python:3.14-slim\nRUN echo hello > /greeting.txt\nCMD ["cat", "/greeting.txt"]\n' | docker build -q -t typo -
docker run --rm typo
```

A different build failure, a `COPY` of a file that is not in the build context, is scenario
[05 · Dockerfile build fails](../troubleshooting/05-dockerfile-build-fails/README.md).

## Common Mistakes

- `COPY . .` before installing dependencies: every code change re-installs everything
  (lesson [10 · Image Layers](10-image-layers.md)).
- Using `RUN python app.py` to "start" the app: `RUN` executes at build time and the build then
  hangs (a server never finishes). Starting is `CMD`'s job.
- Shell-form `CMD python app.py`: signals go to a shell, not your app; shutdowns become slow.
- `FROM python` without a tag: you silently get whatever `latest` is today.
- Copying secrets (`.env`, keys) into the image because `.dockerignore` is missing
  (lesson [11 · .dockerignore](11-dockerignore.md)).

## Best Practices

- Pin the base image tag (`python:3.14-slim`).
- Order instructions from "rarely changes" to "often changes": base, system packages,
  dependencies, then your code.
- Use exec-form `CMD`/`ENTRYPOINT`.
- Add a `.dockerignore`, and run as a non-root `USER`.
- Keep one Dockerfile per image, next to the code it builds.

## Challenge

Write your own Dockerfile (call it `my.Dockerfile`, in `examples/simple-app/`) that builds a
working simple-app image whose **default greeting** is `Built by me`, without changing `app.py`.
Run it on port 5050 and prove it with curl.

## Solution

<details><summary>Show the solution</summary>

The greeting comes from the `GREETING` environment variable, so an `ENV` default is all it takes:

<!-- test: timeout=600; retry=15; contains=Built by me! -->
```bash
cat > my.Dockerfile <<'EOF'
FROM python:3.14-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
ENV GREETING="Built by me"
EXPOSE 5000
CMD ["python", "app.py"]
EOF
docker build -q -f my.Dockerfile -t simple-app:mine .
docker rm -f mine 2>/dev/null; docker run -d --name mine -p 5050:5000 simple-app:mine
sleep 2
curl -s http://localhost:5050
```

<!-- test-run: rm -f my.Dockerfile -->

</details>

## Verification

- [ ] You can explain what each of FROM, WORKDIR, COPY, RUN, ENV, EXPOSE, CMD, ENTRYPOINT does.
- [ ] You know the difference between build time (`RUN`) and run time (`CMD`).
- [ ] You can build with `-t` (name) and `-f` (which Dockerfile).
- [ ] You understand what the build context is.

Clean up (and go back to the repository root):

```bash
docker rm -f step3 mine
rm -f my.Dockerfile
cd ../..
```

## Real-World Usage

- Every service a team owns has a Dockerfile in its repository; build servers build it on every change.
- Code review of a Dockerfile catches problems early: unpinned bases, root users, secrets copied in.
- `ENTRYPOINT` + `CMD` is the standard pattern for CLI tools packaged as images.

## Key Takeaways

- A Dockerfile is a reproducible recipe for an image.
- `RUN` = build time, `CMD`/`ENTRYPOINT` = run time.
- The build context is the folder you pass to `docker build`; `COPY` sees only that.
- Build up a Dockerfile in small, tested steps.
- Next: [10 · Image Layers](10-image-layers.md).
