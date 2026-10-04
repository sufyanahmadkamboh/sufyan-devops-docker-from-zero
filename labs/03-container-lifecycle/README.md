# Lab 03 · Container Lifecycle

> **Goal:** walk a container through every state with your own hands, and understand *why* containers stop.
> **Time:** about 40 minutes · **You need:** [Lab 02](../02-docker-cli/README.md)

## What you will learn

- The states of a container: **Created → Running → Exited → Removed**
- The difference between an **image**, a **container** and the **container's main process**
- `docker create`, `docker start`, `docker stop`, `docker kill` and what the exit codes mean
- Interactive containers with `docker run -it`
- The golden rule: **a container lives exactly as long as its main process**

```text
   IMAGE (read-only template)
     |
     |  docker create            docker run = create + start
     v
  [ Created ] --docker start--> [ Running ] --docker stop / process ends--> [ Exited ]
                                    ^                                          |
                                    +---------------- docker start -----------+
                                                                               |
                                                                          docker rm
                                                                               v
                                                                         [ Removed ]
```

Three different things, often confused:

| Thing | What it is | Example |
|---|---|---|
| **Image** | a read-only package of files plus "what to run" | `nginx:1.30-alpine` |
| **Container** | an isolated box created from an image, with its own writable layer, name, ID, network | `demo` |
| **Container process** | the program running inside the box. The first one is **PID 1**, the *main process* | `nginx: master process` |

## Step 1 · Created: a container that has never run

From the repository root:

```bash
cd labs/03-container-lifecycle
```

`docker create` prepares a container but does not start it:

```bash
docker create --name demo nginx:1.30-alpine
```

<!-- test: output; contains=Created -->
```bash
docker ps -a --filter name=demo --format '{{.Names}}: {{.Status}}'
```

```text
demo: Created
```

**What you see:** `Created`. The container exists (it has an ID, a name, a filesystem) but no process is running in it.

## Step 2 · Running

<!-- test: output; contains=Up -->
```bash
docker start demo
docker ps -a --filter name=demo --format '{{.Names}}: {{.Status}}'
```

```text
demo
demo: Up Less than a second
```

`docker start` started the main process. Status `Up ...` means running.

## Step 3 · Exited, the polite way: `docker stop`

<!-- test: retry=20; output; contains=Exited (0) -->
```bash
docker stop demo
docker ps -a --filter name=demo --format '{{.Names}}: {{.Status}}'
```

```text
demo
demo: Exited (0) Less than a second ago
```

`docker stop` sends the main process a **SIGTERM** signal: "please shut down". nginx finishes its work and exits with code **0** (success). If a process ignores SIGTERM, Docker waits 10 seconds and then kills it.

## Step 4 · Exited, the hard way: `docker kill`

<!-- test: retry=20; output; contains=Exited (137) -->
```bash
docker start demo
docker kill demo
docker ps -a --filter name=demo --format '{{.Names}}: {{.Status}}'
```

```text
demo
demo
demo: Exited (137) Less than a second ago
```

`docker kill` sends **SIGKILL**: the process is terminated immediately, no clean-up. The exit code **137** means "killed by signal 9" (128 + 9). Whenever you see `Exited (137)` later in your career, think: *something killed it*, often Docker itself because the container used too much memory (Lab 14).

| Exit code | Usual meaning |
|---|---|
| `0` | the program finished successfully |
| `1`, `2`, `3`... | the program reported an error (read the logs) |
| `137` | killed (SIGKILL): `docker kill`, or out of memory |
| `143` | terminated by SIGTERM and the program did not handle it gracefully |

## Step 5 · Removed

```bash
docker rm demo
```

<!-- test: absent=demo -->
```bash
docker ps -a --filter name=demo --format '{{.Names}}: {{.Status}}'
```

Nothing printed: the container is gone. The image `nginx:1.30-alpine` is untouched.

## Step 6 · Interactive containers

So far nginx ran in the background. Now we open a shell **inside** a brand-new Ubuntu container. `-i` keeps input open, `-t` gives you a terminal, `--rm` deletes the container when you leave:

<!-- test: skip -->
```bash
docker run -it --rm --name shell ubuntu:26.04 bash
```

Your prompt changes to something like `root@3f2a1b4c5d6e:/#`. You are now inside the container. Try:

<!-- test: skip -->
```bash
ls /
env
hostname
cat /etc/os-release
exit
```

- `ls /` shows a complete Linux filesystem: the container's own, not your computer's.
- `env` shows the container's environment variables (`HOSTNAME`, `PATH`, `HOME`...).
- `hostname` prints the short container ID: Docker uses it as the hostname.
- `cat /etc/os-release` says Ubuntu, whatever your computer runs.
- `exit` ends `bash`, the main process, so the container stops and `--rm` removes it.

The same checks without an interactive terminal (this is how scripts run commands in containers):

<!-- test: output; contains=Ubuntu -->
```bash
docker run --rm ubuntu:26.04 cat /etc/os-release
```

```text
PRETTY_NAME="Ubuntu 26.04.1 LTS"
NAME="Ubuntu"
VERSION_ID="26.04"
VERSION="26.04.1 LTS (Resolute Raccoon)"
VERSION_CODENAME=resolute
ID=ubuntu
ID_LIKE=debian
HOME_URL="https://www.ubuntu.com/"
SUPPORT_URL="https://help.ubuntu.com/"
BUG_REPORT_URL="https://bugs.launchpad.net/ubuntu/"
PRIVACY_POLICY_URL="https://www.ubuntu.com/legal/terms-and-policies/privacy-policy"
UBUNTU_CODENAME=resolute
LOGO=ubuntu-logo
```

And who is PID 1? Let's ask `ps` inside a small Alpine container:

<!-- test: output; contains=PID -->
```bash
docker run --rm alpine:3.24 ps
```

```text
PID   USER     TIME  COMMAND
    1 root      0:00 ps
```

**What you see:** exactly one process, `ps` itself, with **PID 1**. A container does not boot a whole operating system with dozens of services. It runs *your* process, and that process is number 1.

## Step 7 · Why containers stop

Here is the rule again: **a container runs as long as its main process runs.** Let's prove it three ways.

**Experiment 1: a process that ends by itself.** `sleep 15` runs for 15 seconds, then exits:

<!-- test: output; contains=Up -->
```bash
docker run -d --name sleeper alpine:3.24 sleep 15
docker ps --filter name=sleeper --format '{{.Names}}: {{.Status}}'
```

```text
803f265508e65a18ffa1fdc2d0d8446850320902ba5bd04d50017f260027cdca
sleeper: Up Less than a second
```

Wait 15 seconds, then look again:

<!-- test-run: sleep 16 -->
<!-- test: retry=20; output; contains=Exited (0) -->
```bash
docker ps -a --filter name=sleeper --format '{{.Names}}: {{.Status}}'
```

```text
sleeper: Exited (0) 1 second ago
```

Nobody stopped it. `sleep` finished, so the container finished.

**Experiment 2: a shell with nobody to talk to.**

<!-- test: retry=20; output; contains=Exited (0) -->
```bash
docker run --name quick ubuntu:26.04
docker ps -a --filter name=quick --format '{{.Names}}: {{.Status}}'
```

```text
quick: Exited (0) Less than a second ago
```

The default command of the Ubuntu image is `bash`. Without `-it` there is no terminal, `bash` reads "end of input" immediately and exits. This is why people say "my Ubuntu container stops right away". It did exactly what it was told.

**Experiment 3: stop the main process from inside.**

```bash
docker run -d --name web nginx:1.30-alpine
```

`nginx -s quit` asks nginx to shut down. We send it with `docker exec`:

```bash
docker exec web nginx -s quit
```

<!-- test-run: sleep 2 -->
<!-- test: retry=20; output; contains=Exited (0) -->
```bash
docker ps -a --filter name=web --format '{{.Names}}: {{.Status}}'
```

```text
web: Exited (0) 2 seconds ago
```

We never typed `docker stop`. The main process ended, so the container stopped.

## Break it

The `sleeper` container has exited. Let's try to run a command in it:

<!-- test: fail; contains=is not running -->
```bash
docker exec sleeper echo hello
```

## Troubleshoot it

**Observe.** `Error response from daemon: container ... is not running`.

**Investigate.** Check the state and the exit code:

<!-- test: output; contains=exited -->
```bash
docker inspect sleeper --format 'status={{.State.Status}} exit code={{.State.ExitCode}} finished={{.State.FinishedAt}}'
```

```text
status=exited exit code=0 finished=2026-10-04T04:52:14.745890497Z
```

**Root cause.** The container is `exited` with exit code 0: its main process (`sleep 15`) completed normally. `docker exec` needs a running main process to attach to.

**Fix.** `docker start sleeper` brings it back for another 15 seconds. That is enough to run our command:

<!-- test: contains=hello -->
```bash
docker start sleeper
docker exec sleeper echo hello
```

**Verify.** The command printed `hello`. Lesson: if a container keeps stopping, do not ask "how do I keep it alive?" but "what is its main process, and why did it end?" `docker logs` and `docker inspect` tell you.

## Challenge

**Task:** predict and then prove the status of a container whose main process fails.

**Requirements:**
- Run an `alpine:3.24` container named `failing` whose main process prints `about to fail` and then exits with code `3`.
- Find the exit code **only** with `docker ps -a` and `docker inspect`.
- Read the message with `docker logs`.

**Hints:** `sh -c '...; exit 3'` runs a small shell script as the main process.

**Expected result:** status `Exited (3)`, `ExitCode` 3, and `about to fail` in the logs.

<details>
<summary>Solution</summary>

<!-- test: fail -->
```bash
docker run --name failing alpine:3.24 sh -c 'echo about to fail; exit 3'
```

`docker run` (without `-d`) returns the container's exit code, so your shell sees a failure too.

<!-- test: retry=20; output; contains=Exited (3); contains=3; contains=about to fail -->
```bash
docker ps -a --filter name=failing --format '{{.Names}}: {{.Status}}'
docker inspect failing --format '{{.State.ExitCode}}'
docker logs failing
```

```text
failing: Exited (3) Less than a second ago
3
about to fail
```

**Explanation:** the exit code of the main process becomes the exit code of the container. Non-zero means "something went wrong": your first move is always `docker logs`.

</details>

## Verify

You can now:

- [ ] name the states of a container and the command that moves it between them
- [ ] explain the difference between an image, a container and the main process
- [ ] read exit codes 0, 1-3, 137 and know where to look next
- [ ] open an interactive shell with `docker run -it` and leave it again
- [ ] explain why an Ubuntu container without `-it` stops immediately

## Clean up

```bash
docker rm -f sleeper quick web failing
```

## Next

➡️ [Lab 04 · Port mapping](../04-port-mapping/README.md) · 📖 Concepts: [docs/06-container-lifecycle.md](../../docs/06-container-lifecycle.md)
