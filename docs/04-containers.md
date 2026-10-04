# Containers

> Lesson 04 · about 30 minutes · you need: [03 · Images](03-images.md)

## What is it?

A **container** is a running (or stopped) instance of an image. Technically it is one or more
ordinary Linux processes that the kernel isolates:

- it sees **its own filesystem**: the image's read-only layers plus one thin **writable layer**
  that belongs only to this container;
- it sees **its own processes**: inside, the main process is PID 1;
- it has **its own hostname and network interface** (and IP address);
- it can be given **limits** for CPU and memory.

```text
   container "web"                      container "web2"
   +------------------------+           +------------------------+
   | writable layer (own)   |           | writable layer (own)   |
   +------------------------+           +------------------------+
   |                                                              |
   |       nginx:1.30-alpine image layers (read-only, SHARED)     |
   +--------------------------------------------------------------+
```

## Why do we need it?

The image is the package; the container is where the work happens. Containers give you:

- **isolation:** an app in one container cannot see or break files of another;
- **speed:** starting a container takes about a second;
- **disposability:** you can delete a container and create a fresh one from the same image at
  any time. Nothing lingers on your computer.

## How does it work?

`docker run` is a shortcut for four steps:

```text
  docker run -d --name web nginx:1.30-alpine
        |
        +-- 1. image present? if not: docker pull nginx:1.30-alpine
        +-- 2. docker create  (writable layer, network, settings)  -> state: Created
        +-- 3. docker start   (start the main process)               -> state: Up / running
        +-- 4. -d: return immediately and print the container ID
           (without -d: attach your terminal to the container's output)
```

Each container gets:

| Property | Example | Where you see it |
|---|---|---|
| **Container ID** | 64 hex characters, shown short as 12 | `docker ps` (CONTAINER ID) |
| **Name** | `web` (yours) or a random one like `eager_turing` | `docker ps` (NAMES) |
| **Main process** | `nginx -g 'daemon off;'` | `docker ps` (COMMAND) |
| **State** | Up, Exited (0), Exited (137) ... | `docker ps -a` (STATUS) |

**The golden rule:** a container lives exactly as long as its **main process**. When that
process ends, the container stops. Lesson [06 · Container Lifecycle](06-container-lifecycle.md)
is built around this rule.

## Prerequisites

- `nginx:1.30-alpine` pulled, or an internet connection (Docker pulls it automatically).

## Hands-on Lab

Start nginx in the background (`-d` = detached) with a name you choose:

<!-- test: output -->
```bash
docker run -d --name web nginx:1.30-alpine
```

```text
5399d05fd2508042084387b4c6dffa33de4649d1f50c8697c42ded16e3a78f57
```

The long hexadecimal string is the full **container ID**. List running containers:

<!-- test: contains=web; output -->
```bash
docker ps
```

```text
CONTAINER ID   IMAGE               COMMAND                  CREATED                  STATUS                  PORTS     NAMES
5399d05fd250   nginx:1.30-alpine   "/docker-entrypoint.…"   Less than a second ago   Up Less than a second   80/tcp    web
```

Start a second container from the **same** image. It is completely independent:

<!-- test: contains=web2 -->
```bash
docker run -d --name web2 nginx:1.30-alpine
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}'
```

Prove the isolation: create a file in `web` and look for it in `web2`:

<!-- test: contains=only-in-web -->
```bash
docker exec web sh -c 'echo hello > /tmp/only-in-web.txt'
docker exec web ls /tmp
```

<!-- test: absent=only-in-web -->
```bash
docker exec web2 ls /tmp
```

The full hands-on lab is [labs/01-first-container](../labs/01-first-container/README.md).

## Expected Result

`docker ps` prints one row per running container with these columns:

| Column | Meaning |
|---|---|
| CONTAINER ID | the short ID (first 12 characters) |
| IMAGE | the image it was started from |
| COMMAND | the main process (shortened) |
| CREATED | when the container was created |
| STATUS | `Up 5 seconds`, `Exited (0) 2 minutes ago`, ... |
| PORTS | published ports (empty here: we published none) |
| NAMES | the name you gave with `--name` |

`web` has `/tmp/only-in-web.txt`; `web2` does not. Same image, separate writable layers.

## Experiment

Each container has its own hostname. By default it is the short container ID:

<!-- test: output -->
```bash
docker exec web hostname
docker exec web2 hostname
```

```text
5399d05fd250
76666314f6a6
```

Compare with the CONTAINER ID column of `docker ps`: they match.

## Break It

Try to create another container named `web`:

<!-- test: fail; contains=already in use -->
```bash
docker run -d --name web nginx:1.30-alpine
```

## Troubleshoot It

- **Observe:** `Conflict. The container name "/web" is already in use by container "<id>".`
- **Investigate:** `docker ps -a --filter name=web` shows the existing container with that name
  (it might even be stopped, which is why `docker ps` alone sometimes hides it).
- **Root cause:** container names are unique on one Docker engine.
- **Fix:** choose another name, or remove the old container first (`docker rm -f web`).
- **Verify:**

<!-- test: contains=web -->
```bash
docker rm -f web
docker run -d --name web nginx:1.30-alpine
docker ps --filter name=web
```

## Common Mistakes

- Expecting changes inside a container to appear in other containers or in the image. They live
  only in that container's writable layer, and they are deleted with the container.
- Forgetting `-d` and wondering why the terminal "hangs": without `-d`, your terminal shows the
  container's output until you press Ctrl+C (which also stops nginx).
- Using `docker ps` to look for a stopped container. Use `docker ps -a`.
- Giving names with one character: Docker rejects them; use at least two.

## Best Practices

- Always give containers you work with a **name** (`--name web`); typing `web` beats copying IDs.
- Treat containers as **disposable**: never store important data only in a container's writable
  layer (lesson [12 · Volumes](12-volumes.md)).
- One main concern per container (a web server, a database, an API), not everything in one.

## Challenge

Start three nginx containers called `site1`, `site2`, `site3`, show only their names and
statuses in a table, then remove all three with **one** command.

## Solution

<details><summary>Show the solution</summary>

<!-- test: contains=site3 -->
```bash
docker run -d --name site1 nginx:1.30-alpine
docker run -d --name site2 nginx:1.30-alpine
docker run -d --name site3 nginx:1.30-alpine
docker ps --filter name=site --format 'table {{.Names}}\t{{.Status}}'
```

`docker rm -f` accepts several names at once (`-f` stops running containers before removing):

```bash
docker rm -f site1 site2 site3
```

<!-- test: absent=site -->
```bash
docker ps --format '{{.Names}}'
```

</details>

## Verification

- [ ] You can start a named container in the background.
- [ ] You can read every column of `docker ps`.
- [ ] You can explain why a file created in one container is not in another.
- [ ] You know that a container stops when its main process stops.

Clean up:

```bash
docker rm -f web web2
```

## Real-World Usage

- In production, each service (web server, API, worker, database) runs as one or more containers
  started from versioned images.
- Scaling out means "start more containers from the same image".
- Because containers are disposable, a broken one is often simply replaced by a fresh one.

## Key Takeaways

- A container = image layers (shared, read-only) + its own writable layer + isolated processes.
- `docker run` = pull (if needed) + create + start.
- Names must be unique; IDs are generated.
- A container lives as long as its main process.
- Next: [05 · Docker CLI](05-docker-cli.md).
