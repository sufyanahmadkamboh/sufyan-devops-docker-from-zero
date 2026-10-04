# 01 · Container exits immediately

> You run a container with `-d`, Docker prints an ID, everything looks fine. But the container is not there.
> Time: 15 minutes · You need: labs 01–06

## Problem

A colleague wrote a Dockerfile for `simple-app`. The image builds without errors and `docker run -d`
does not complain. But nobody can reach the app, and `docker ps` shows nothing.

This is the most common Docker problem there is. It has nothing to do with Docker being broken:
**a container lives exactly as long as its main process.** When the main process ends, the container stops.

Let's reproduce it. From the repository root:

```bash
cd troubleshooting/01-container-exits-immediately
```

Build the image and start it the same way your colleague did:

```bash
docker build -t exits-demo .
```

```bash
docker run -d --name exits -p 5000:5000 exits-demo
```

Docker printed a long ID. That only means: *the container was created and its process was started*.
It says nothing about whether the process is still alive.

<!-- test-run: sleep 3 -->

## Symptoms

Let's look at the running containers:

<!-- test: absent=exits-demo -->
```bash
docker ps
```

Only the header line, no `exits` container. And the app does not answer:

<!-- test: fail -->
```bash
curl -s --max-time 3 http://localhost:5000
```

Symptom in one sentence: *"The container starts and disappears from `docker ps` within a second."*

## Investigation

Don't rebuild anything yet. A stopped container is not deleted: it is still there, with its
logs and its configuration. That is our evidence.

**Step 1: is it really gone, or only stopped?** `docker ps` shows only running containers. `-a` shows all of them:

<!-- test: output; contains=Exited (2) -->
```bash
docker ps -a --filter name=exits --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}'
```

```text
NAMES     IMAGE        STATUS
exits     exits-demo   Exited (2) 5 seconds ago
```

The STATUS column says `Exited (2)`. Two facts: it stopped, and it stopped with **exit code 2**.
Exit code 0 means "finished normally"; anything else means "something went wrong".

**Step 2: what did the process say before it died?** Everything the main process writes is kept in the logs:

<!-- test: output; contains=can't open file '/app/main.py' -->
```bash
docker logs exits
```

```text
python: can't open file '/app/main.py': [Errno 2] No such file or directory
```

Python says it cannot open `/app/main.py`. Now we have a precise clue.

**Step 3: which command does the image run?** Every image stores its default command (`CMD`):

<!-- test: contains=main.py -->
```bash
docker inspect exits-demo --format '{{json .Config.Cmd}}'
```

The image runs `python main.py`.

**Step 4: which files are really in `/app`?** We cannot `docker exec` into a stopped container.
But we can start a new, throw-away container from the same image and **replace the command**
with something that only lists files:

<!-- test: output; contains=app.py; absent=main.py -->
```bash
docker run --rm exits-demo ls -la /app
```

```text
total 16
drwxr-xr-x 1 root root 4096 Oct  4 04:08 .
drwxr-xr-x 1 root root 4096 Oct  4 04:34 ..
-rwxr-xr-x 1 root root 1087 Oct  4 03:44 app.py
-rwxr-xr-x 1 root root   13 Oct  4 03:44 requirements.txt
```

`--rm` removes this helper container as soon as `ls` finishes. In `/app` there is `app.py`, but no `main.py`.

## Commands

The commands that gave us the evidence, in the order you should reach for them:

| Command | What it told us |
|---|---|
| `docker ps -a` | the container exists, but `Exited (2)` |
| `docker logs exits` | `can't open file '/app/main.py'` |
| `docker inspect exits-demo --format '{{json .Config.Cmd}}'` | the image runs `python main.py` |
| `docker run --rm exits-demo ls -la /app` | the file is called `app.py` |

## Root Cause

The last line of the Dockerfile is `CMD ["python", "main.py"]`, but the application file
copied into the image is `app.py`. Python cannot find the file and exits with code 2.
No main process means no container.

## Fix

Change **one** thing: the `CMD`. The corrected file is next to the broken one as `Dockerfile.fixed`
(the broken `Dockerfile` stays, so you can repeat the exercise):

<!-- test: contains=app.py -->
```bash
grep CMD Dockerfile Dockerfile.fixed
```

Build the fixed image with `-f`, which picks a different Dockerfile:

```bash
docker build -f Dockerfile.fixed -t exits-demo:fixed .
```

Remove the dead container and start the fixed one. We reuse the port, so the old container has to go first:

```bash
docker rm exits
docker run -d --name exits-fixed -p 5000:5000 exits-demo:fixed
```

## Verification

The container is still up a few seconds later:

<!-- test-run: sleep 3 -->
<!-- test: contains=Up -->
```bash
docker ps --filter name=exits-fixed --format '{{.Names}} {{.Status}}'
```

And the app answers:

<!-- test: retry=15; contains=Hello from simple-app -->
```bash
curl -s http://localhost:5000
```

### One more cause of the same symptom

A container also stops when its main process finishes **successfully**. The `ubuntu` image runs
`bash` by default. Without a terminal attached (`-it`), bash has nothing to read, so it ends at once:

```bash
docker run --name idle ubuntu:26.04
```

<!-- test: contains=Exited (0) -->
```bash
docker ps -a --filter name=idle --format '{{.Names}} {{.Status}}'
```

`Exited (0)`: nothing went wrong, the program simply had no more work. A container is not a small
virtual machine that stays on: it needs a long-running main process (a web server, a database, ...).

## Clean up

```bash
docker rm -f exits-fixed idle
docker rmi exits-demo exits-demo:fixed
cd ../..
```

## Lesson Learned

- `docker run -d` printing an ID only means *started*, not *still running*.
- A container lives as long as its main process. `Exited (0)`: the process finished. `Exited (non-zero)`: it failed.
- Your first two commands are always `docker ps -a` (status and exit code) and `docker logs` (the reason).
- To look inside an image whose container will not stay up, run a throw-away container with a different
  command: `docker run --rm <image> ls -la /app`.

Next: [02 · Port already in use](../02-port-already-in-use/README.md)
