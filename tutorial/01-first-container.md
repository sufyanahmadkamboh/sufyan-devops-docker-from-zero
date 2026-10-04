# 01 · Your first container

> Pull an image, run a container, list it, stop it, start it, enter it, remove it. Then the container lifecycle, and
> the most important rule in Docker: **a container lives exactly as long as its main process**.
> Time: about 60 minutes. You need: [00 · Start here](00-start-here.md).

We start in the repository root, with no containers. Let's make sure:

<!-- test: output -->
```bash
docker ps -a
```

```text
CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES
```

Only the column headers (or perhaps the `hello-world` containers from chapter 00, if you did not clean up). That is fine.

## Part 1 · Images

### Pull an image

An **image** is a packaged filesystem plus a default command. Let's download the official nginx web server image:

<!-- test: output=head:12; contains=nginx:1.30-alpine -->
```bash
docker pull nginx:1.30-alpine
```

```text
1.30-alpine: Pulling from library/nginx
Digest: sha256:0985e772fb9f729e6fa0980da05fca5d9c468e870eed43071545afa9d2e27d94
Status: Image is up to date for nginx:1.30-alpine
docker.io/library/nginx:1.30-alpine
```

Look at the output:

- `1.30-alpine` is the **tag**: nginx version 1.30, built on the small Alpine Linux base.
- Each line with an ID like `a1b2c3...` is a **layer**. An image is a stack of layers; Docker downloads them in parallel
  and reuses layers it already has.
- `Digest: sha256:...` is the unique fingerprint of exactly this image content.

Where did it come from? From **Docker Hub**, the default registry. `nginx:1.30-alpine` is short for
`docker.io/library/nginx:1.30-alpine`.

### List your images

<!-- test: output; contains=nginx -->
```bash
docker images
```

```text
IMAGE                            ID             DISK USAGE   CONTENT SIZE   EXTRA
alpine:3.24                      294b683cb724         13MB         3.94MB        
board-api:1.0                    9d6da54368f6        243MB         58.5MB        
board-web:1.0                    37b4d6321a8d       92.8MB         26.1MB        
busybox:1.37                     bdf57e528e45       6.77MB         2.22MB        
docker-from-zero/api:1.0.0       7cfd494a3172        247MB         58.8MB        
docker-from-zero/web:1.0.0       c80c81a9e7f5       81.5MB         23.1MB        
greeter:latest                   acc561ba6f7e       12.9MB         3.85MB        
hello-world:latest               5e2309035332       25.9kB         9.49kB        
jitesoft/tesseract-ocr:latest    23fbc1f29a6d        401MB          129MB        
linuxserver/ffmpeg:latest        a7182d4fe498       1.09GB          268MB        
multi-container-app-api:latest   6bac428db361        243MB         58.5MB        
multi-container-app-web:latest   bc959e0bc319       92.8MB         26.1MB        
nginx:1.30-alpine                0985e772fb9f       93.6MB           27MB        
postgres:18-alpine               77f585114c32        433MB          121MB        
python:3.14-slim                 c3e521df8b2b        192MB         48.7MB        
registry:3                       ddf754342cfc       86.9MB         20.7MB        
simple-app:1.0                   a0d6cae60a15        212MB         51.9MB        
simple-app:fat                   c2619eff3ce5       1.75GB          454MB        
simple-app:fat-nocache           40b870a8fffa       1.74GB          453MB        
simple-app:fixed                 18b09356d161        212MB         51.9MB        
simple-app:mine                  99343326e3bc        212MB         51.9MB        
simple-app:multistage            cb8c8c901b29        108MB         26.1MB        
simple-app:slim                  929c66f80e88        212MB         51.9MB        
simple-app:step1                 c64b54e3f2b6        189MB         46.5MB        
simple-app:step2                 ec6dbcfb69aa        189MB         46.5MB        
simple-app:step3                 bd079254e6f9        212MB         51.9MB        
simple-app:step4                 a80b707a17ee        212MB         51.9MB        
simple-app:step5                 2b87150db06c        212MB         51.9MB        
ts01:latest                      86f535124674        212MB         51.9MB        
ts03-api:latest                  b44d462d7e19        243MB         58.5MB        
ts03-web:latest                  e8b8fc8f7e1c       92.8MB         26.1MB        
ts06-api:latest                  0a194b6f7ab0        243MB         58.5MB        
ts06-web:latest                  7fb452dc3a2a       92.8MB         26.1MB        
typo:latest                      812ef2b3da18        189MB         46.5MB        
ubuntu:26.04                     f144425ff09b        162MB         45.6MB        
```

The columns:

| Column | Meaning |
|---|---|
| `IMAGE` | the image name and tag (`nginx:1.30-alpine`). Official images on Docker Hub have no user name in front |
| `ID` | a short form of the image's unique ID. Two tags can point to the same ID |
| `DISK USAGE` | how much disk space the unpacked image uses (layers shared with other images are counted in each) |
| `CONTENT SIZE` | how much was downloaded (the compressed layers) |
| `EXTRA` | `U` means the image is **in use** by a container (running or stopped) |

This is the layout of Docker 29 and newer. Older versions (and `docker images --format table`) show the classic
columns `REPOSITORY`, `TAG`, `IMAGE ID`, `CREATED` (when the publisher **built** the image, not when you downloaded
it) and `SIZE`. The information is the same.

## Part 2 · Containers

### Run a container

<!-- test: contains=web -->
```bash
docker run -d --name web nginx:1.30-alpine
docker ps
```

Two new options:

- `-d` (**detached**): run in the background and give me my terminal back.
- `--name web`: call the container `web`. Without it, Docker invents a funny name like `quirky_hopper`.

`docker run` printed a long hexadecimal string: the **container ID**. Now look at the `docker ps` output:

| Column | Meaning |
|---|---|
| `CONTAINER ID` | the first 12 characters of the container ID |
| `IMAGE` | which image it was created from |
| `COMMAND` | the main process running inside (nginx's start script) |
| `CREATED` | when the container was created |
| `STATUS` | `Up 3 seconds`: it is running |
| `PORTS` | `80/tcp`: nginx listens on port 80 **inside** the container (we cannot reach it yet, that is chapter 02) |
| `NAMES` | `web` |

The image ID and the container ID are **different things**. One image (`nginx:1.30-alpine`) can be the source of many
containers, each with its own ID.

### Read its logs

Whatever the main process writes to its output is collected by Docker:

<!-- test: output=tail:6; contains=start worker -->
```bash
docker logs web
```

```text
...
2026/10/04 04:21:33 [notice] 1#1: start worker process 38
2026/10/04 04:21:33 [notice] 1#1: start worker process 39
2026/10/04 04:21:33 [notice] 1#1: start worker process 40
2026/10/04 04:21:33 [notice] 1#1: start worker process 41
2026/10/04 04:21:33 [notice] 1#1: start worker process 42
2026/10/04 04:21:33 [notice] 1#1: start worker process 43
```

These are nginx's start-up messages. When something goes wrong, `docker logs` is the first command you run.

### Stop, start, restart

<!-- test: contains=Exited -->
```bash
docker stop web
docker ps -a --filter name=web
```

`docker ps` would now show nothing, because it only lists **running** containers. `docker ps -a` (all) shows the stopped
one: `STATUS` is `Exited (0) ...`. The `0` is the exit code of the main process: 0 means it ended cleanly.

The container still exists. Its filesystem is still there. Let's start it again:

<!-- test: contains=Up -->
```bash
docker start web
docker ps --filter name=web
```

And restart it (stop + start in one command):

<!-- test: contains=Up -->
```bash
docker restart web
docker ps --filter name=web --format '{{.Names}}: {{.Status}}'
```

`--format` picks only the columns you want. `Up 1 second` tells you it really restarted.

### Go inside a running container

`docker exec` runs an **extra** command inside a container that is already running:

<!-- test: output; contains=nginx -->
```bash
docker exec web ps
```

```text
PID   USER     TIME  COMMAND
    1 root      0:00 nginx: master process nginx -g daemon off;
   22 nginx     0:00 nginx: worker process
   23 nginx     0:00 nginx: worker process
   24 nginx     0:00 nginx: worker process
   25 nginx     0:00 nginx: worker process
   26 nginx     0:00 nginx: worker process
   27 nginx     0:00 nginx: worker process
   28 nginx     0:00 nginx: worker process
   29 nginx     0:00 nginx: worker process
   30 nginx     0:00 nginx: worker process
   31 nginx     0:00 nginx: worker process
   32 nginx     0:00 nginx: worker process
   33 nginx     0:00 nginx: worker process
   34 nginx     0:00 nginx: worker process
   35 nginx     0:00 nginx: worker process
   36 root      0:00 ps
```

Look at the first line: PID 1 is `nginx: master process`. Inside a container, the main process **is** PID 1. The
other `nginx: worker process` lines are its children, and the last line is `ps` itself, which we just added with exec.

<!-- test: output -->
```bash
docker exec web hostname
docker exec web cat /etc/os-release
```

```text
a46b1ce979b0
NAME="Alpine Linux"
ID=alpine
VERSION_ID=3.24.2
PRETTY_NAME="Alpine Linux v3.24"
HOME_URL="https://alpinelinux.org/"
BUG_REPORT_URL="https://gitlab.alpinelinux.org/alpine/aports/-/issues"
```

The hostname is the short container ID, and the operating system is Alpine Linux, even if your computer runs Windows,
macOS or Ubuntu. The container has its own filesystem, its own process list and its own hostname, but it shares the
**kernel** of the machine (or the Linux VM inside Docker Desktop). That is the difference between a container and a
virtual machine.

### Remove it

<!-- test: fail; contains=container is running -->
```bash
docker rm web
```

Don't panic, this failure is on purpose. Read the error: you cannot remove a **running** container. Either stop it first
or force it:

```bash
docker stop web
docker rm web
```

Both commands print the name of the container they acted on. Now list all containers, including stopped ones:

<!-- test: absent=web -->
```bash
docker ps -a --format '{{.Names}}'
```

The container is gone. The **image** is still there (`docker images`), ready for the next `docker run`.

## Part 3 · The container lifecycle

```text
  Image
    |
    |  docker create            (or docker run = create + start)
    v
 Created
    |
    |  docker start
    v
 Running   <---- docker restart ----+
    |                                |
    |  docker stop / docker kill / the main process ends
    v                                |
 Exited ----- docker start ----------+
    |
    |  docker rm
    v
 Removed
```

Let's walk through every state by hand.

<!-- test: contains=Created -->
```bash
docker create --name demo nginx:1.30-alpine
docker ps -a --filter name=demo --format '{{.Names}}: {{.Status}}'
```

`Created`: the container exists (its filesystem and settings are prepared), but no process runs yet. `docker run` is
simply `docker create` followed by `docker start`.

<!-- test: contains=Up -->
```bash
docker start demo
docker ps -a --filter name=demo --format '{{.Names}}: {{.Status}}'
```

Now stop it in two different ways. First, politely:

<!-- test: contains=Exited -->
```bash
docker stop demo
docker ps -a --filter name=demo --format '{{.Names}}: {{.Status}}'
```

`docker stop` sends a signal asking the process to shut down cleanly, waits up to 10 seconds, and only then kills it.
Now start it again and kill it without asking:

<!-- test: contains=Exited (137) -->
```bash
docker start demo
docker kill demo
docker ps -a --filter name=demo --format '{{.Names}}: {{.Status}}'
```

`Exited (137)`. Remember this number: **137 = 128 + 9**, meaning "killed by signal 9 (SIGKILL)". You will see 137 again
when a container is killed for using too much memory (chapter 07).

```bash
docker rm demo
```

<!-- test: absent=demo -->
```bash
docker ps -a --format '{{.Names}}'
```

## Part 4 · Interactive containers and the main process

### A shell inside Ubuntu

Run this on your machine:

<!-- test: skip -->
```bash
docker run -it --name shell ubuntu:26.04 bash
```

- `-i` keeps input open, `-t` gives you a terminal. Together: an interactive shell.
- Your prompt changes to something like `root@3f2a1b4c5d6e:/#`. You are inside the container.

Try these commands inside it, then type `exit`:

```text
ls /
ps
env
hostname
cat /etc/os-release
exit
```

You will notice: `ps` shows only two processes (`bash` and `ps`), `hostname` is the container ID, `env` shows a short,
clean list of variables, and `/etc/os-release` says Ubuntu.

Now, the important question: after `exit`, is the container still running?

<!-- test-run: docker run --name shell ubuntu:26.04 bash -c "exit 0" -->
<!-- test: contains=Exited -->
```bash
docker ps -a --filter name=shell --format '{{.Names}}: {{.Status}}'
```

It is `Exited`. You did not stop it. You ended `bash`, and `bash` was the **main process**. When the main process
ends, the container stops. That is the rule.

The same commands work without an interactive session (this is how scripts do it):

<!-- test: output; contains=Ubuntu -->
```bash
docker run --rm ubuntu:26.04 cat /etc/os-release
```

```text
(output appears here when the tests run)
```

`--rm` removes the container automatically when it stops, so you do not collect dead containers.

### Make a container stop on purpose

Let's run a container whose main process is `sleep 5`:

```bash
docker run -d --name sleeper alpine:3.24 sleep 5
docker ps --filter name=sleeper --format '{{.Names}}: {{.Status}}'
```

It is `Up`. Wait a few seconds, then look again:

<!-- test-run: sleep 7 -->
<!-- test: contains=Exited (0) -->
```bash
docker ps -a --filter name=sleeper --format '{{.Names}}: {{.Status}}'
```

`Exited (0)`. Nobody stopped it. The main process (`sleep 5`) finished its job after 5 seconds, so the container
finished too.

Now the classic beginner surprise:

<!-- test: contains=Exited -->
```bash
docker run --name quick ubuntu:26.04
docker ps -a --filter name=quick --format '{{.Names}}: {{.Status}}'
```

"I ran Ubuntu and it stopped immediately! Docker is broken!" Let's investigate instead of guessing. What is the main
process of this image?

<!-- test: contains=bash -->
```bash
docker inspect ubuntu:26.04 --format '{{json .Config.Cmd}}'
```

It is `bash`. Without `-it`, `bash` has no terminal to read commands from, so it reads "end of input" and exits
immediately. The container did exactly what it was told. **A container is not a virtual machine that boots and waits;
it is a process.** nginx stays up because nginx is a server that runs forever; `bash` without a terminal ends at once.

Clean up the stopped containers:

```bash
docker rm shell sleeper quick
```

## Where would I use this as a DevOps engineer?

- `docker ps -a` and the `STATUS` column are your first look at any broken server: "is it running, restarting, or
  exited, and with which code?"
- Exit codes tell stories: `0` finished normally, `1` the app failed, `137` killed (by you, or by the out-of-memory
  killer), `143` stopped with SIGTERM.
- `docker exec` is how you look inside a running service without restarting it.
- Every container runs a single main process. When a production container "keeps restarting", the question is always
  **why did its main process end?**

## What you learned

- `pull`, `images`, `run -d --name`, `ps`, `ps -a`, `logs`, `stop`, `start`, `restart`, `exec`, `rm`, `create`, `kill`.
- Image ID vs container ID vs container name.
- The lifecycle: Created → Running → Exited → Removed.
- A container stops when its main process stops, and the exit code tells you how it ended.

## Try it yourself

- Labs: [01-first-container](../labs/01-first-container/README.md), [02-docker-cli](../labs/02-docker-cli/README.md),
  [03-container-lifecycle](../labs/03-container-lifecycle/README.md)
- Challenges: the "First steps" section of [challenges/README.md](../challenges/README.md)
- Deeper: [docs/03-images.md](../docs/03-images.md), [docs/04-containers.md](../docs/04-containers.md),
  [docs/06-container-lifecycle.md](../docs/06-container-lifecycle.md)

## Next

[02 · Ports and configuration](02-ports-and-config.md)
