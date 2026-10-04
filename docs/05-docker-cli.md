# Docker CLI

> Lesson 05 · about 45 minutes · you need: [04 · Containers](04-containers.md)

## What is it?

The Docker CLI is the `docker` command. It has one sub-command per job. You do not need to
memorize them all: about twenty cover 95% of daily work, and every one of them has `--help`.

```text
   docker  <object>  <action>  [options]  [arguments]
   docker  container ls        -a                        (long form)
   docker  ps                  -a                        (classic short form, same thing)
```

## Why do we need it?

Everything you do with Docker (starting, stopping, debugging, cleaning up) happens through
these commands. Knowing what each one is **for** lets you investigate problems instead of guessing.

## How does it work?

Every command is a request to the Docker Engine. The engine answers with data (lists, JSON, logs)
or performs an action.

### Command reference

| Command | What it does | Syntax · important options | Real-world use |
|---|---|---|---|
| `docker version` | Client and engine versions | `--format '{{.Server.Version}}'` | First check when something "does not work" |
| `docker info` | Engine-wide details: containers, images, storage, CPUs, memory | `--format` | Check resources and setup of a build machine |
| `docker images` | List local images | `-a`, `--filter dangling=true`, `--format` | See what takes disk space |
| `docker pull` | Download an image | `NAME:TAG`, `-q` quiet | Pre-fetch images before an offline demo |
| `docker run` | Create **and** start a container | `-d` background, `--name`, `-p` ports, `-e` env, `-v` volumes, `--rm` delete on exit, `-it` interactive | Start any service |
| `docker ps` | List running containers | `-a` all, `-q` IDs only, `--filter`, `--format` | "What is running right now?" |
| `docker stop` | Ask the main process to stop (stop signal, usually SIGTERM; SIGKILL after 10 s) | `-t` seconds | Graceful shutdown |
| `docker start` | Start a stopped container again | `-a` attach | Resume a stopped container with its data |
| `docker restart` | stop + start | `-t` | Reload after a configuration change |
| `docker rm` | Delete a stopped container | `-f` force (stop first), `-v` with anonymous volumes | Clean up |
| `docker rmi` | Delete an image | `-f` | Free disk space |
| `docker logs` | Show what the main process printed (stdout/stderr) | `-f` follow, `--tail N`, `--since 5m`, `-t` timestamps | **First step** of almost every investigation |
| `docker exec` | Run an extra command inside a **running** container | `-it` for a shell, `-u` user, `-e` env | Look around inside: files, processes, network |
| `docker inspect` | Every detail of a container/image/network/volume as JSON | `--format '{{...}}'` | Find IP, mounts, env, exit code, health |
| `docker stats` | Live CPU / memory / network / disk I/O per container | `--no-stream` one snapshot | Find the container that eats memory |
| `docker top` | Processes running inside a container | `docker top NAME` | See what is really running |
| `docker cp` | Copy files between host and container | `docker cp NAME:/path ./here` | Grab a log or config file |

Every command answers `--help`, for example `docker run --help`.

## Prerequisites

- Docker works; `nginx:1.30-alpine` can be pulled.

## Hands-on Lab

Start something to work with:

<!-- test: contains=web -->
```bash
docker run -d --name web -p 8080:80 nginx:1.30-alpine
docker ps --filter name=web
```

<!-- test-run: sleep 2 -->

**logs** — what did nginx print? Each line comes from the container's stdout/stderr:

<!-- test: retry=15; contains=start worker; output=tail:5 -->
```bash
docker logs web
```

```text
...
2026/10/04 05:02:20 [notice] 1#1: start worker process 39
2026/10/04 05:02:20 [notice] 1#1: start worker process 40
2026/10/04 05:02:20 [notice] 1#1: start worker process 41
2026/10/04 05:02:20 [notice] 1#1: start worker process 42
2026/10/04 05:02:20 [notice] 1#1: start worker process 43
```

**exec** — run a command inside the running container:

<!-- test: contains=nginx version; output -->
```bash
docker exec web nginx -v
docker exec web cat /etc/os-release
```

```text
nginx version: nginx/1.30.5
NAME="Alpine Linux"
ID=alpine
VERSION_ID=3.24.2
PRETTY_NAME="Alpine Linux v3.24"
HOME_URL="https://alpinelinux.org/"
BUG_REPORT_URL="https://gitlab.alpinelinux.org/alpine/aports/-/issues"
```

**inspect** — the container's details as JSON; `--format` picks one value:

<!-- test: contains=running; output -->
```bash
docker inspect web --format 'state={{.State.Status}} ip={{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}} started={{.State.StartedAt}}'
```

```text
state=running ip=172.17.0.2 started=2026-10-04T05:02:20.170081961Z
```

**stats** — one snapshot of resource use (without `--no-stream` it updates live until Ctrl+C):

<!-- test: contains=web; output -->
```bash
docker stats --no-stream web
```

```text
CONTAINER ID   NAME      CPU %     MEM USAGE / LIMIT     MEM %     NET I/O         BLOCK I/O     PIDS
c80c057b4b65   web       0.00%     11.64MiB / 15.35GiB   0.07%     1.17kB / 126B   0B / 8.19kB   15
```

**top** — the processes inside the container:

<!-- test: contains=nginx; output -->
```bash
docker top web
```

```text
UID                 PID                 PPID                C                   STIME               TTY                 TIME                CMD
root                1685514             1685490             0                   05:02               ?                   00:00:00            nginx: master process nginx -g daemon off;
statd               1685558             1685514             0                   05:02               ?                   00:00:00            nginx: worker process
statd               1685559             1685514             0                   05:02               ?                   00:00:00            nginx: worker process
statd               1685560             1685514             0                   05:02               ?                   00:00:00            nginx: worker process
statd               1685561             1685514             0                   05:02               ?                   00:00:00            nginx: worker process
statd               1685562             1685514             0                   05:02               ?                   00:00:00            nginx: worker process
statd               1685563             1685514             0                   05:02               ?                   00:00:00            nginx: worker process
statd               1685564             1685514             0                   05:02               ?                   00:00:00            nginx: worker process
statd               1685565             1685514             0                   05:02               ?                   00:00:00            nginx: worker process
statd               1685566             1685514             0                   05:02               ?                   00:00:00            nginx: worker process
statd               1685567             1685514             0                   05:02               ?                   00:00:00            nginx: worker process
statd               1685568             1685514             0                   05:02               ?                   00:00:00            nginx: worker process
statd               1685569             1685514             0                   05:02               ?                   00:00:00            nginx: worker process
statd               1685570             1685514             0                   05:02               ?                   00:00:00            nginx: worker process
statd               1685571             1685514             0                   05:02               ?                   00:00:00            nginx: worker process
```

**cp** — copy nginx's default page out of the container to your computer:

<!-- test: contains=Welcome to nginx -->
```bash
docker cp web:/usr/share/nginx/html/index.html ./nginx-default.html
grep -o '<title>.*</title>' nginx-default.html
rm nginx-default.html
```

The full guided lab is [labs/02-docker-cli](../labs/02-docker-cli/README.md).

## Expected Result

- `docker logs web` ends with nginx's start-up lines (`start worker process ...`).
- `docker exec web nginx -v` prints the nginx version; `/etc/os-release` says **Alpine Linux**:
  the container has its own userland, whatever your host runs.
- `docker inspect --format` prints `state=running` and an IP address (typically `172.17.0.x`).
- `docker stats --no-stream` shows CPU %, MEM USAGE / LIMIT, NET I/O, BLOCK I/O and PIDS.
- `docker top web` shows the nginx master process and its worker processes.

## Experiment

Make a request, then look at the logs again: nginx writes an access-log line for every request.

<!-- test: retry=10; contains=GET / HTTP -->
```bash
curl -s -o /dev/null http://localhost:8080
docker logs --tail 1 web
```

`--tail 1` shows only the last line; `--since 1m` would show the last minute; `-f` would keep
following new lines until you press Ctrl+C:

<!-- test: skip -->
```bash
docker logs -f web
```

## Break It

`exec` only works on **running** containers. Stop `web` and try:

<!-- test: fail; contains=is not running -->
```bash
docker stop web
docker exec web nginx -v
```

## Troubleshoot It

- **Observe:** `Error response from daemon: container ... is not running`.
- **Investigate:** `docker ps -a --filter name=web` shows `Exited (0)`: we stopped it. Logs are
  still readable on stopped containers: `docker logs web`.
- **Root cause:** `exec` starts an extra process inside the container; a stopped container has no
  running environment to start it in.
- **Fix:** `docker start web`.
- **Verify:**

<!-- test: contains=nginx version -->
```bash
docker start web
docker exec web nginx -v
```

## Common Mistakes

- Confusing `docker run` (creates a **new** container) with `docker start` (restarts an
  **existing** one). Running `docker run` again and again leaves many stopped containers behind.
- Confusing `docker rm` (containers) with `docker rmi` (images).
- Using `docker exec -it ... bash` on Alpine images: they have `sh`, not `bash`.
- Reading `docker stats` without `--no-stream` in a script: it never returns.

## Best Practices

- Start every investigation with `docker ps -a` and `docker logs <name>`.
- Use `--format` to get exactly the field you need instead of scrolling through JSON.
- Use `--rm` for one-off containers (`docker run --rm alpine:3.24 echo hi`) so they delete themselves.
- Use `docker <command> --help` instead of guessing options.

## Challenge

Using only the CLI: find out **how many worker processes** nginx started inside `web`, and copy
nginx's main configuration file `/etc/nginx/nginx.conf` to your current folder.

## Solution

<details><summary>Show the solution</summary>

<!-- test: contains=worker process -->
```bash
docker top web | grep -c 'worker process'
docker top web
```

<!-- test: contains=worker_processes -->
```bash
docker cp web:/etc/nginx/nginx.conf ./nginx.conf
grep worker_processes nginx.conf
rm nginx.conf
```

`worker_processes auto;` means one worker per CPU the container can see, so the count depends
on your machine.

</details>

## Verification

- [ ] You can read logs (`docker logs`, `--tail`, `-f`).
- [ ] You can run a command inside a container (`docker exec`).
- [ ] You can pick one value out of `docker inspect` with `--format`.
- [ ] You can see resource usage and processes (`docker stats --no-stream`, `docker top`).
- [ ] You can copy a file out of a container (`docker cp`).

Clean up:

```bash
docker rm -f web
```

## Real-World Usage

- On-call engineers start incidents with `docker ps -a`, `docker logs --since 10m` and
  `docker inspect` to see exit codes and restart counts.
- `docker exec` is how you check, from inside, whether a service can reach its database.
- `docker cp` grabs a crash dump or a generated report out of a container.

## Key Takeaways

- `run` = new container; `start` = existing one; `rm` = containers; `rmi` = images.
- `logs`, `exec`, `inspect`, `stats`, `top`, `cp` are your investigation tools.
- `--format` and `--filter` turn long outputs into exact answers.
- Next: [06 · Container Lifecycle](06-container-lifecycle.md).
