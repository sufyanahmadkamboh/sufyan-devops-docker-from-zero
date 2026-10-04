# Container Lifecycle

> Lesson 06 · about 40 minutes · you need: [05 · Docker CLI](05-docker-cli.md)

## What is it?

Every container moves through a small set of **states**. Knowing them tells you what you can do
with a container right now, and why it is (or is not) running.

```text
                    docker create                 docker start
      IMAGE  ---------------------->  CREATED  ------------------->  RUNNING (Up)
                                                                     |   ^     |
                       docker run = create + start ------------------+   |     | docker pause
                                                                         |     v
                            main process ends by itself,          docker start  PAUSED
                            docker stop (SIGTERM),                       |     | docker unpause
                            docker kill (SIGKILL)                        |     v
                                     |                                   |  RUNNING
                                     v                                   |
                              EXITED (exit code)  ------------------------+
                                     |
                                     | docker rm
                                     v
                                  REMOVED (gone, together with its writable layer)
```

## Why do we need it?

"My container is not running" is the most common Docker problem. The state and the **exit code**
tell you why:

| STATUS in `docker ps -a` | Meaning |
|---|---|
| `Created` | created, never started |
| `Up 3 minutes` | the main process is running |
| `Up 3 minutes (healthy)` | running, and its health check passes |
| `Exited (0)` | the main process finished normally |
| `Exited (1)`, `(2)`, `(3)` ... | the process failed; the number comes from the app itself |
| `Exited (137)` | killed with SIGKILL: `docker kill`, or out of memory (137 = 128 + 9) |
| `Exited (143)` | ended by SIGTERM and the app reported it (143 = 128 + 15) |
| `Restarting` | crashed and a restart policy is starting it again |

## How does it work?

### Image, container, process

```text
   IMAGE  (read-only template, on disk)
     |
     | docker run
     v
   CONTAINER  (writable layer + settings + network)
     |
     | runs
     v
   MAIN PROCESS  (PID 1 inside the container, e.g. nginx, python app.py, sleep 30)
```

The container **is not** the process, but it is **tied** to it. When PID 1 exits, the container
stops. Docker does not keep an "empty" container running.

### How docker stop works

`docker stop` sends a stop signal ("please shut down") to PID 1, waits up to 10 seconds, then
sends **SIGKILL** ("die now"). The stop signal is **SIGTERM** unless the image chooses another one:
the nginx image uses SIGQUIT, nginx's own "graceful shutdown" signal (you can see it with
`docker image inspect nginx:1.30-alpine --format '{{.Config.StopSignal}}'`). `docker kill` sends
SIGKILL immediately. Well-behaved apps (nginx, PostgreSQL) handle their stop signal and shut down
cleanly with exit code 0.

### Why containers stop

A container stops when its main process ends. Common reasons:

1. the job is done (`echo hello` prints and exits);
2. the program is a shell with no input (`docker run ubuntu:26.04` runs `bash`, which has no
   terminal attached, reads end-of-input, and exits immediately);
3. the program crashed (wrong command, missing file, missing setting);
4. someone stopped or killed it, or it ran out of memory.

## Prerequisites

- Images `nginx:1.30-alpine`, `alpine:3.24` and `ubuntu:26.04` (Docker pulls them when needed).

## Hands-on Lab

Walk through every state by hand. **Create** without starting:

<!-- test: contains=Created; output -->
```bash
docker create --name demo nginx:1.30-alpine
docker ps -a --filter name=demo --format 'table {{.Names}}\t{{.Status}}'
```

```text
606fa2f5bcdbb989a7c9a7a89cf9c7ff935f966182c3313ac9c5206782ac70fa
NAMES     STATUS
demo      Created
```

**Start** it:

<!-- test: contains=Up; output -->
```bash
docker start demo
docker ps -a --filter name=demo --format 'table {{.Names}}\t{{.Status}}'
```

```text
demo
NAMES     STATUS
demo      Up Less than a second
```

**Stop** it gracefully (stop signal, then SIGKILL only if needed):

<!-- test: contains=Exited (0); output -->
```bash
docker stop demo
docker ps -a --filter name=demo --format 'table {{.Names}}\t{{.Status}}'
```

```text
demo
NAMES     STATUS
demo      Exited (0) Less than a second ago
```

**Start** it again, then **kill** it (SIGKILL):

<!-- test: contains=Exited (137); output -->
```bash
docker start demo
docker kill demo
docker ps -a --filter name=demo --format 'table {{.Names}}\t{{.Status}}'
```

```text
demo
demo
NAMES     STATUS
demo      Exited (137) Less than a second ago
```

**Remove** it:

```bash
docker rm demo
```

<!-- test: absent=demo -->
```bash
docker ps -a --format '{{.Names}}'
```

### Interactive containers

`-i` keeps input open, `-t` gives you a terminal. Together they let you work inside a container
like on a remote machine. Type `exit` (or Ctrl+D) to leave; leaving ends `bash`, so the container stops:

<!-- test: skip -->
```bash
docker run -it --name shell ubuntu:26.04 bash
```

Inside, try `ls /`, `ps`, `env`, `hostname`, `cat /etc/os-release`. You can run the same
commands without a terminal, which is how they are tested here:

<!-- test: contains=Ubuntu; output=head:6 -->
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
...
```

The full lab is [labs/03-container-lifecycle](../labs/03-container-lifecycle/README.md).

## Expected Result

- `Created` after `docker create`, `Up ...` after `docker start`.
- `Exited (0)` after `docker stop`: nginx shut down cleanly on its stop signal.
- `Exited (137)` after `docker kill`: 128 + 9 (SIGKILL).
- After `docker rm`, the container is gone from `docker ps -a`.

## Experiment

A container that only lives as long as its job:

<!-- test: contains=Up -->
```bash
docker run -d --name sleeper alpine:3.24 sleep 5
docker ps --filter name=sleeper --format '{{.Names}}: {{.Status}}'
```

Wait more than 5 seconds, then look again: `sleep` finished, so the container exited with 0.

<!-- test-run: sleep 7 -->

<!-- test: contains=Exited (0) -->
```bash
docker ps -a --filter name=sleeper --format '{{.Names}}: {{.Status}}'
```

And the classic beginner surprise: Ubuntu "does not start".

<!-- test: contains=Exited (0) -->
```bash
docker run --name ubuntu-test ubuntu:26.04
docker ps -a --filter name=ubuntu-test --format '{{.Names}}: {{.Status}}'
```

It **did** start. Its main process is `bash`, without a terminal it has nothing to read, so it
exits at once. To keep a container busy, give it a long-running process (a server, or
`sleep infinity` for experiments).

## Break It

Run a container whose main process fails:

<!-- test: fail -->
```bash
docker run --name broken alpine:3.24 sh -c 'echo "starting..."; ls /does-not-exist'
```

## Troubleshoot It

- **Observe:** the command printed `starting...` and an `ls` error, and returned to the prompt.
- **Investigate:** the state and the exit code, then the logs:

<!-- test: contains=Exited (1); contains=No such file -->
```bash
docker ps -a --filter name=broken --format '{{.Names}}: {{.Status}}'
docker inspect broken --format 'exit code: {{.State.ExitCode}}'
docker logs broken
```

- **Root cause:** `ls` failed (exit code 1), PID 1 ended, the container stopped.
- **Fix:** run a command that works (in a real app: fix the command, file or setting the logs name).
- **Verify:**

<!-- test: contains=Exited (0) -->
```bash
docker rm broken
docker run --name fixed alpine:3.24 sh -c 'echo "starting..."; ls /'
docker ps -a --filter name=fixed --format '{{.Names}}: {{.Status}}'
```

## Common Mistakes

- Thinking `Exited (0)` means "crashed". It means "finished normally": often the command simply
  had nothing long-running to do.
- Looking only at `docker ps`: stopped containers are only in `docker ps -a`.
- Using `docker kill` by habit: it skips the clean shutdown (databases may need recovery afterwards).
- Expecting `docker start` to apply new options. Options (ports, env, volumes) are fixed at
  `docker create`/`run` time; to change them, remove the container and run a new one.

## Best Practices

- Read the exit code first, then the logs: together they explain almost every stopped container.
- Use `docker stop` (graceful) rather than `docker kill`.
- Keep the main process in the foreground (nginx uses `daemon off;` for exactly this reason).
- Use `--rm` for one-off experiments so stopped containers do not pile up.

## Challenge

Start an `alpine:3.24` container named `timer` that stays running for exactly 20 seconds. While
it runs, use `docker exec` to print its hostname. Then prove it stopped by itself with exit code 0.

## Solution

<details><summary>Show the solution</summary>

<!-- test: contains=Up -->
```bash
docker run -d --name timer alpine:3.24 sleep 20
docker exec timer hostname
docker ps --filter name=timer --format '{{.Names}}: {{.Status}}'
```

<!-- test-run: sleep 21 -->

After 20 seconds:

<!-- test: contains=exit code 0 -->
```bash
docker inspect timer --format 'state={{.State.Status}} exit code {{.State.ExitCode}}'
```

</details>

## Verification

- [ ] You can name every state and the command that leads to it.
- [ ] You can explain Exited (0), (1) and (137).
- [ ] You can explain why `docker run ubuntu:26.04` exits immediately.
- [ ] You know the difference between `docker stop` and `docker kill`.

Clean up:

```bash
docker rm -f sleeper ubuntu-test fixed timer
```

## Real-World Usage

- `Exited (137)` with `OOMKilled: true` is how you recognise a service that needs more memory
  (lesson [18 · Resource Management](18-resource-management.md)).
- Restart policies (`--restart unless-stopped`) bring crashed services back; the restart count in
  `docker inspect` tells you how often it happened.
- Graceful SIGTERM handling is what makes zero-downtime deployments possible on any container platform.

## Key Takeaways

- States: Created → Up → Exited → removed (plus Paused, Restarting).
- A container lives exactly as long as its main process (PID 1).
- Exit codes tell the story: 0 normal, 1–127 app errors, 137 killed, 143 terminated.
- `stop` = stop signal (SIGTERM by default) then SIGKILL; `kill` = SIGKILL now.
- Next: [07 · Ports](07-ports.md).
