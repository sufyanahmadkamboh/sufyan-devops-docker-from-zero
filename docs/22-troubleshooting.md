# Troubleshooting

## What is it?

Troubleshooting is a **method**, not a list of fixes to memorise. You collect evidence until the cause is obvious,
change one thing, and prove the fix worked. This lesson gives you the method and a map of the ten hands-on scenarios
in [troubleshooting/](../troubleshooting/).

## Why do we need it?

Things break all the time: a typo in a Dockerfile, a port already taken, a missing environment variable, a wrong
volume name. Beginners guess and change random settings until something works, often making it worse. Engineers ask
the system what is wrong. Docker gives you excellent evidence: states, exit codes, logs, inspect output, networks and
volumes.

## How does it work?

```text
                      Something does not work
                                │
                                ▼
             docker ps -a  ── is the container running?
                │                              │
            NO (Exited / Created)          YES (Up)
                │                              │
                ▼                              ▼
     docker logs NAME                 Can you reach it?
     docker inspect NAME               curl http://localhost:PORT
       (.State.ExitCode,                 │                  │
        .State.Error,                  NO                 YES, but wrong result
        .State.OOMKilled)                │                  │
                │                        ▼                  ▼
    read the FIRST error      docker ps (PORTS column)   docker logs NAME
    exit 127: command missing  docker inspect (Ports)     docker exec NAME ...
    exit 137: killed / OOM     docker logs: which address (env? config? data?)
    exit 1-3: app error        does the app listen on?    docker inspect (.Config.Env,
                               0.0.0.0 vs 127.0.0.1        .Mounts, networks)
                                │
                                ▼
   Container-to-container problem?  docker network inspect / docker inspect (.NetworkSettings.Networks)
   Data problem?                    docker volume ls / docker inspect (.Mounts)
   Build problem?                   read the failing step (#N) in the build output, check .dockerignore
                                │
                                ▼
          Root cause → change ONE thing → verify with the same command that showed the problem
```

Every scenario in this repository is written with the same eight parts:

```text
Problem → Symptoms → Investigation → Commands → Root Cause → Fix → Verification → Lesson Learned
```

## Prerequisites

- [16-logs-and-debugging.md](16-logs-and-debugging.md), [17-docker-inspect.md](17-docker-inspect.md)

## Hands-on Lab

The ten scenarios. Each folder contains the broken files and a README that walks you through it:

| # | Scenario | First command that shows the problem |
|---|---|---|
| 01 | [Container exits immediately](../troubleshooting/01-container-exits-immediately/README.md) | `docker ps -a`, `docker logs` |
| 02 | [Port already in use](../troubleshooting/02-port-already-in-use/README.md) | the `docker run` error, `docker ps --filter publish=8080` |
| 03 | [Containers cannot communicate](../troubleshooting/03-containers-cannot-communicate/README.md) | `docker compose ps -a`, `docker compose logs web` |
| 04 | [Volume data appears missing](../troubleshooting/04-volume-data-missing/README.md) | `docker volume ls`, `docker inspect --format '{{json .Mounts}}'` |
| 05 | [Dockerfile build fails](../troubleshooting/05-dockerfile-build-fails/README.md) | the failing build step, `.dockerignore` |
| 06 | [Environment variable missing](../troubleshooting/06-environment-variable-missing/README.md) | `docker compose ps -a`, `docker compose logs api` |
| 07 | [Running but not reachable](../troubleshooting/07-running-but-not-reachable/README.md) | `curl`, `docker logs`, `docker exec` |
| 08 | [Image too large](../troubleshooting/08-image-too-large/README.md) | `docker images`, `docker history` |
| 09 | [Host changes not reflected](../troubleshooting/09-host-changes-not-reflected/README.md) | `docker inspect --format '{{json .Mounts}}'` |
| 10 | [Database data disappears](../troubleshooting/10-database-data-disappears/README.md) | `docker volume ls`, `docker compose logs db` |

Let's practise the method once here, on a small example. A job container that should print a report:

<!-- test: fail -->
```bash
docker run --name report -e REPORT_NAME= alpine:3.24 sh -c 'test -n "$REPORT_NAME" || { echo "ERROR: REPORT_NAME is empty" >&2; exit 2; }; echo "report $REPORT_NAME done"'
```

## Expected Result

The command returns an error and prints `ERROR: REPORT_NAME is empty`. Do not fix it yet. Let's investigate as if you
had not seen the message (in real life the container usually runs in the background).

## Experiment

**Observe:**

<!-- test: contains=Exited (2) -->
```bash
docker ps -a --filter name=report --format '{{.Names}}  {{.Status}}'
```

**Investigate:** the logs and the configuration the container really received:

<!-- test: contains=REPORT_NAME is empty -->
```bash
docker logs report
```

<!-- test: contains=REPORT_NAME= -->
```bash
docker inspect report --format '{{range .Config.Env}}{{println .}}{{end}}'
```

**Root cause:** the variable exists but is empty (`REPORT_NAME=`), and the program checks for that.
**Fix** (one change) and **verify** with the same evidence:

```bash
docker rm report
docker run --name report -e REPORT_NAME=weekly alpine:3.24 sh -c 'test -n "$REPORT_NAME" || { echo "ERROR: REPORT_NAME is empty" >&2; exit 2; }; echo "report $REPORT_NAME done"'
```

<!-- test: contains=Exited (0) -->
```bash
docker ps -a --filter name=report --format '{{.Names}}  {{.Status}}'
```

<!-- test: contains=report weekly done -->
```bash
docker logs report
docker rm report
```

## Break It

Every scenario in [troubleshooting/](../troubleshooting/) is a "break it" exercise with a real broken file. Start with
[01](../troubleshooting/01-container-exits-immediately/README.md); it takes ten minutes.

## Troubleshoot It

A checklist to keep next to your terminal:

1. `docker ps -a`: running? exit code?
2. `docker logs NAME` (or `docker compose logs SERVICE`): first error message?
3. `docker inspect NAME`: state, env, mounts, ports, networks as Docker sees them.
4. `docker exec NAME ...`: test from **inside** the container (does the app answer on its own port?).
5. `docker network inspect` / `docker volume ls`: are the containers where you think they are?
6. Form one hypothesis, change one thing, re-run the command that showed the problem.

## Common Mistakes

- Restarting or recreating before reading the logs (evidence lost).
- Fixing the second error instead of the first.
- Changing several things at once, so you never learn what the cause was.
- Using `--privileged`, root, or `docker system prune -a --volumes` to "make it work".
- Not verifying: "it should work now" is not a test.

## Best Practices

- Write down what you checked and what you saw; it becomes the incident note or the pull request description.
- Reproduce the problem before fixing it, and keep the reproduction (that is what this repository's scenarios are).
- Make applications fail fast with clear messages (the message board API does).

## Challenge

**Task:** pick any **three** scenarios from the table, and solve them **without opening the Root Cause section**
first. Write down the command that gave you the decisive evidence for each.

## Solution

<details><summary>Solution</summary>

There is no single answer: each scenario's README has its own Investigation, Root Cause and Verification sections to
compare your notes with. A good answer names one command per scenario, for example: 01 `docker logs`, 03
`docker compose logs web` + `docker inspect` networks, 07 `docker exec` (it works inside, not outside).
</details>

## Verification

- [ ] I follow Observe → Investigate → Root cause → Fix → Verify without skipping steps.
- [ ] I know which command answers which question (state, logs, config, network, data).
- [ ] I have solved at least three scenarios from `troubleshooting/`.

## Real-World Usage

On-call engineers follow exactly this loop during incidents, and the habit of verifying with the same evidence that
showed the problem is what separates a fix from a guess. Teams turn solved problems into runbooks, like the scenario
READMEs in this repository.

## Key Takeaways

- Evidence first: state, logs, inspect, exec, networks, volumes.
- Read the first error; know your exit codes (127, 137, 1–3).
- One change at a time, and always verify.

Next: [23-capstone.md](23-capstone.md)
