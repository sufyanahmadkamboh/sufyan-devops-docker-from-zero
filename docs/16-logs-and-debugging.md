# Logs and Debugging

## What is it?

Whatever the main process of a container writes to **standard output (stdout)** or **standard error (stderr)** is
captured by Docker. `docker logs` shows it. Logs are the first and most important evidence when something goes
wrong, together with `docker ps -a` (did it stop? with which exit code?) and `docker exec` (look inside).

```text
   container                         Docker Engine                    you
  ┌─────────────────┐   stdout   ┌──────────────────────┐   docker logs   ┌──────────┐
  │ main process    │ ─────────► │ log driver           │ ──────────────► │ terminal │
  │ (nginx, python) │   stderr   │ (json-file: a file   │   docker compose│          │
  │                 │ ─────────► │  per container)      │   logs SERVICE  │          │
  └─────────────────┘            └──────────────────────┘                 └──────────┘
   Files the app writes inside the container (e.g. /var/log/app.log) are NOT in docker logs.
```

## Why do we need it?

Containers are not machines you log into. When a container crashes it may already be gone, but its logs stay until
you remove it. A good debugging habit replaces guessing:

```text
Observe  →  Investigate  →  Identify root cause  →  Fix  →  Verify
docker ps -a    docker logs       read the error       change       check again
                docker inspect    message carefully    one thing
                docker exec
```

## How does it work?

| Command | What it shows |
|---|---|
| `docker logs NAME` | everything the container printed since it started |
| `docker logs --tail 20 NAME` | only the last 20 lines |
| `docker logs --since 5m NAME` | only the last 5 minutes |
| `docker logs -t NAME` | with timestamps |
| `docker logs -f NAME` | follow live (Ctrl+C to stop following; the container keeps running) |
| `docker compose logs SERVICE` | the same for a Compose service (`-f` to follow) |
| `docker ps -a` | stopped containers too, with `Exited (CODE)` |
| `docker exec -it NAME sh` | a shell inside a running container |

Exit codes worth knowing: `0` finished normally, `1`/`2`/`3` the program reported an error, `126`/`127` the command
could not be executed or was not found, `137` killed (by `docker kill` or because it ran out of memory), `143`
stopped with SIGTERM (`docker stop`).

## Prerequisites

- [05-docker-cli.md](05-docker-cli.md), [06-container-lifecycle.md](06-container-lifecycle.md)

## Hands-on Lab

Full lab: [labs/14-logs-inspect-resources](../labs/14-logs-inspect-resources/README.md). Short version:

```bash
docker run -d --name web -p 8080:80 nginx:1.30-alpine
```

<!-- test: retry=15; contains=Welcome to nginx -->
```bash
curl -s http://localhost:8080
```

<!-- test: retry=15; contains=GET / HTTP; output=tail:3 -->
```bash
docker logs --tail 3 web
```

```text
2026/10/04 05:18:59 [notice] 1#1: start worker process 43
2026/10/04 05:18:59 [notice] 1#1: start worker process 44
172.17.0.1 - - [04/Oct/2026:05:19:00 +0000] "GET / HTTP/1.1" 200 896 "-" "curl/8.19.0" "-"
```

Watching live is how you debug "what happens when I click this?". It never ends by itself, so it is not part of the
automatic tests; press **Ctrl+C** to stop following:

<!-- test: skip -->
```bash
docker logs -f web
```

## Expected Result

The last log lines include an **access log** line for your `curl`: client IP, time, `"GET / HTTP/1.1" 200`, and the
user agent `curl/...`. nginx writes access logs to stdout, which is why Docker can show them.

## Experiment

A container that crashes still has logs. Let's create one on purpose:

<!-- test: fail -->
```bash
docker run --name crasher alpine:3.24 sh -c "echo 'starting the job'; echo 'ERROR: config file /etc/job.conf not found' >&2; exit 3"
```

<!-- test: retry=20; contains=Exited (3) -->
```bash
docker ps -a --filter name=crasher --format '{{.Names}}  {{.Status}}'
```

<!-- test: retry=15; contains=ERROR: config file -->
```bash
docker logs crasher
```

The container is stopped, but `docker logs` still shows both lines, the one on stdout and the one on stderr.

## Break It

Run a container whose command does not exist:

<!-- test: fail; contains=executable file not found -->
```bash
docker run --name typo alpine:3.24 pyhton --version
```

## Troubleshoot It

<!-- test: contains=Created -->
```bash
docker ps -a --filter name=typo --format '{{.Names}}  {{.Status}}'
```

<!-- test: contains=127 -->
```bash
docker inspect typo --format 'exit code: {{.State.ExitCode}}  error: {{.State.Error}}'
```

The error is in the **state**, not in the logs: the program never started, so it could not print anything. Exit code
`127` means "command not found". Root cause: a typo (`pyhton`) and the alpine image has no Python anyway. Fix:
run a command that exists in the image, and verify:

<!-- test: contains=Hello -->
```bash
docker run --rm alpine:3.24 echo Hello
```

```bash
docker rm -f web crasher typo
```

More real investigations: [troubleshooting/01-container-exits-immediately](../troubleshooting/01-container-exits-immediately/README.md),
[troubleshooting/06-environment-variable-missing](../troubleshooting/06-environment-variable-missing/README.md).

## Common Mistakes

- Looking only at `docker ps` (running containers) and concluding "the container disappeared". Use `docker ps -a`.
- Removing a crashed container before reading its logs.
- Expecting logs from files inside the container. Only stdout/stderr reach `docker logs`.
- Changing three things at once. Change one, verify, then the next.

## Best Practices

- Make applications log to stdout/stderr (the official nginx and Python images already do).
- Fail fast with a clear message (the message board API prints exactly which setting is missing).
- Use `--tail` and `--since` on busy containers.
- Read the **first** error, not the last one; later errors are often consequences.

## Challenge

**Task:** start `busybox:1.37` with the command `sh -c 'i=0; while true; do i=$((i+1)); echo tick $i; sleep 1; done'`
in the background as `ticker`, wait a few seconds, then show **only the last 2 lines** of its logs, with timestamps.

## Solution

<details><summary>Solution</summary>

```bash
docker run -d --name ticker busybox:1.37 sh -c 'i=0; while true; do i=$((i+1)); echo tick $i; sleep 1; done'
```

<!-- test-run: sleep 4 -->

<!-- test: retry=15; contains=tick -->
```bash
docker logs -t --tail 2 ticker
docker rm -f ticker
```

`-t` adds the timestamp Docker recorded for each line; `--tail 2` limits the output.
</details>

## Verification

- [ ] I can read the logs of a running and of a stopped container.
- [ ] I can follow logs live and stop following.
- [ ] I know where to look when a program never started (exit code 127, `.State.Error`).
- [ ] I follow Observe → Investigate → Root cause → Fix → Verify.

## Real-World Usage

Logs are the first stop in every incident. In production, the same stdout/stderr streams are shipped by a log driver
or agent to a central log system, but the habit is identical: find the failing component, read its first error, form
one hypothesis, test it.

## Key Takeaways

- `docker logs` shows stdout and stderr of the main process, even after it stopped.
- `docker ps -a` + exit code tells you **that** it failed; logs tell you **why**.
- If the program never started, the reason is in `docker inspect` (`.State`), not in the logs.
- Investigate before you change anything.

Next: [17-docker-inspect.md](17-docker-inspect.md)
