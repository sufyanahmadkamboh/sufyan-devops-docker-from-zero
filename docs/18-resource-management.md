# Resource Management

## What is it?

Containers share your computer's CPU and memory. By default a container may use **as much as it wants**. Docker can
**measure** usage (`docker stats`, `docker top`) and **limit** it (`--memory`, `--cpus`), so one misbehaving
container cannot slow down or crash everything else.

```text
                       Your computer: e.g. 8 CPUs, 16 GB RAM
   ┌────────────────────────────────────────────────────────────────────────┐
   │  Linux kernel "cgroups" (control groups) enforce the limits            │
   │                                                                        │
   │  ┌───────────────────┐   ┌───────────────────┐   ┌──────────────────┐  │
   │  │ web               │   │ api               │   │ db               │  │
   │  │ no limit          │   │ --memory=256m     │   │ --memory=512m    │  │
   │  │ (can take all)    │   │ --cpus=0.5        │   │                  │  │
   │  └───────────────────┘   └───────────────────┘   └──────────────────┘  │
   │   over the memory limit -> the kernel kills the process (OOM, exit 137) │
   │   over the CPU limit    -> the process is slowed down, not killed       │
   └────────────────────────────────────────────────────────────────────────┘
```

## Why do we need it?

- A memory leak in one container should kill **that** container, not your whole machine.
- Limits make behaviour predictable: what you test locally behaves the same on a shared server.
- Measuring tells you what a service really needs before you set limits.

## How does it work?

| Command / flag | What it does |
|---|---|
| `docker stats` | live CPU %, memory usage / limit, network I/O, block I/O, process count (Ctrl+C to stop) |
| `docker stats --no-stream` | one snapshot, then exit (good for scripts) |
| `docker top NAME` | the processes running inside the container |
| `--memory=256m` | hard memory limit; above it the process is killed (**OOMKilled**, exit code 137) |
| `--cpus=0.5` | at most half of one CPU core; the process is throttled, never killed |
| Compose `deploy.resources.limits` | the same limits in a Compose file (the capstone uses them) |

Columns of `docker stats`: **CPU %** (100 % = one full core), **MEM USAGE / LIMIT** (limit = your machine's memory
if unset), **MEM %**, **NET I/O** (bytes received / sent), **BLOCK I/O** (disk read / written), **PIDS** (processes
and threads).

## Prerequisites

- [05-docker-cli.md](05-docker-cli.md), [17-docker-inspect.md](17-docker-inspect.md)

## Hands-on Lab

Full lab: [labs/14-logs-inspect-resources](../labs/14-logs-inspect-resources/README.md). Short version:

```bash
docker run -d --name limited --memory=256m --cpus=0.5 nginx:1.30-alpine
```

<!-- test: output -->
```bash
docker stats --no-stream limited
```

```text
CONTAINER ID   NAME      CPU %     MEM USAGE / LIMIT   MEM %     NET I/O      BLOCK I/O     PIDS
b14c5de1afc4   limited   0.00%     11.64MiB / 256MiB   4.55%     690B / 84B   0B / 8.19kB   15
```

<!-- test: contains=nginx -->
```bash
docker top limited
```

<!-- test: contains=268435456; contains=500000000 -->
```bash
docker inspect limited --format 'memory={{.HostConfig.Memory}} nanocpus={{.HostConfig.NanoCpus}}'
```

## Expected Result

- `stats` shows the `limited` container with a **MEM LIMIT of 256MiB** (instead of your machine's total memory) and a
  low CPU %. nginx is idle.
- `top` lists the nginx **master** process and its **worker** processes.
- `inspect` shows the limits in bytes and nano-CPUs: 268435456 bytes = 256 MiB, 500000000 = 0.5 CPU.

## Experiment

Live view (stop with Ctrl+C). Useful while you load the app in a browser:

<!-- test: skip -->
```bash
docker stats
```

## Break It

Give a Python program 64 MiB and ask it to allocate 256 MiB:

<!-- test: fail; timeout=600 -->
```bash
docker run --name oom --memory=64m --memory-swap=64m python:3.14-slim python -c "x = bytearray(256*1024*1024)"
```

> `--memory-swap=64m` (the same value as `--memory`) means "no swap on top". Without it, on a machine with swap
> the container may move memory to disk instead of being stopped, and the demo just runs slowly.

## Troubleshoot It

The command failed and printed nothing useful. Observe the exit code and the state:

<!-- test: contains=137; contains=OOMKilled=true -->
```bash
docker inspect oom --format 'exit={{.State.ExitCode}} OOMKilled={{.State.OOMKilled}}'
```

Exit code **137** plus **OOMKilled=true** is the fingerprint of "killed for using too much memory". Python had no
chance to log anything: the kernel killed it. Fix: give it enough memory (or fix the program), then verify:

<!-- test: contains=allocated -->
```bash
docker run --rm --memory=512m python:3.14-slim python -c "x = bytearray(256*1024*1024); print('allocated', len(x) // 1024 // 1024, 'MiB')"
```

```bash
docker rm -f limited oom
```

## Common Mistakes

- Setting limits without measuring first: a database with 64 MiB will be killed over and over.
- Confusing CPU and memory behaviour: too little CPU = slow; too little memory = killed.
- Forgetting that `docker stats` without `--no-stream` never ends (press Ctrl+C).
- Missing the OOM fingerprint and searching the application logs for an error that was never written.

## Best Practices

- Watch `docker stats` under realistic load, then set the memory limit with headroom (for example 1.5–2× normal use).
- Always limit memory for services that can grow (caches, workers, databases).
- Use CPU limits to keep noisy background jobs from slowing down interactive services.
- Put limits in the Compose file so everyone runs with the same values.

## Challenge

**Task:** run `busybox:1.37` with the command `sh -c 'while true; do :; done'` (a busy loop) as `burner` with
`--cpus=0.25`, and confirm with one `docker stats --no-stream` snapshot that it stays around 25 % CPU.

## Solution

<details><summary>Solution</summary>

```bash
docker run -d --name burner --cpus=0.25 busybox:1.37 sh -c 'while true; do :; done'
```

<!-- test-run: sleep 5 -->

<!-- test: contains=burner -->
```bash
docker stats --no-stream --format '{{.Name}} {{.CPUPerc}}' burner
docker rm -f burner
```

Without the limit, the loop would use 100 % of a core. With `--cpus=0.25` the kernel lets it run only a quarter of
the time. (The exact number varies a little between snapshots.)
</details>

## Verification

- [ ] I can read every column of `docker stats`.
- [ ] I can list the processes of a container.
- [ ] I can set and verify memory and CPU limits.
- [ ] I recognise an out-of-memory kill (137 + OOMKilled=true).

## Real-World Usage

Capacity planning and stability: on shared servers and container platforms, every service gets requests and limits
so that one bad deploy cannot take down its neighbours. "Exit 137 / OOMKilled" is one of the most common production
incidents you will investigate.

## Key Takeaways

- Measure with `docker stats` and `docker top`, then limit with `--memory` and `--cpus`.
- Memory limit exceeded → killed (137, OOMKilled). CPU limit → throttled.
- Limits belong in the Compose file, next to the service.

Next: [19-security-basics.md](19-security-basics.md)
