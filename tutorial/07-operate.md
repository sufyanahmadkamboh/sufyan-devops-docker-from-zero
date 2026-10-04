# Chapter 7 · Operating containers: logs, inspect and resources

> **Where you are:** you can build images and run a whole application with Compose.
> **In this chapter:** you learn to look *inside* running containers: what they say (logs), how they are configured
> (inspect) and what they consume (stats, top, limits).
> **Time:** about 40 minutes.

Here is a habit that separates engineers from guessers: when something is wrong, you do not change things until the
evidence tells you what is wrong. The evidence comes from three places, and this chapter is about all three.

```text
   Observe  ->  Investigate  ->  Identify root cause  ->  Fix  ->  Verify
      |              |
      |              +-- docker logs     what did the process say?
      |              +-- docker inspect  how is the container configured?
      |              +-- docker stats    what does it consume right now?
      +-- docker ps -a                   is it running at all? what was its exit code?
```

## 7.1 Logs: what did the container say?

Let's start a web server we can talk to:

<!-- test: output -->
```bash
docker run -d --name web -p 8080:80 nginx:1.30-alpine
```

```text
6906e2f045aebddd3b510c45d01f75b5f865822acb88999372b3a8b429743eaa
```

Now make a few requests, so nginx has something to log:

<!-- test: retry=15 -->
```bash
curl -s -o /dev/null http://localhost:8080/
curl -s -o /dev/null http://localhost:8080/
curl -s -o /dev/null http://localhost:8080/this-page-does-not-exist
```

Docker collects everything a container's main process writes to its standard output and standard error. That is
all `docker logs` shows:

<!-- test: retry=15; output=tail:8; contains=GET / HTTP; contains=404 -->
```bash
docker logs web
```

```text
...
2026/10/04 05:12:40 [notice] 1#1: start worker process 41
2026/10/04 05:12:40 [notice] 1#1: start worker process 42
2026/10/04 05:12:40 [notice] 1#1: start worker process 43
2026/10/04 05:12:40 [notice] 1#1: start worker process 44
172.17.0.1 - - [04/Oct/2026:05:12:41 +0000] "GET / HTTP/1.1" 200 896 "-" "curl/8.19.0" "-"
172.17.0.1 - - [04/Oct/2026:05:12:41 +0000] "GET / HTTP/1.1" 200 896 "-" "curl/8.19.0" "-"
2026/10/04 05:12:41 [error] 33#33: *3 open() "/usr/share/nginx/html/this-page-does-not-exist" failed (2: No such file or directory), client: 172.17.0.1, server: localhost, request: "GET /this-page-does-not-exist HTTP/1.1", host: "localhost:8080"
172.17.0.1 - - [04/Oct/2026:05:12:41 +0000] "GET /this-page-does-not-exist HTTP/1.1" 404 153 "-" "curl/8.19.0" "-"
```

At the top you see nginx starting up, at the bottom one line per request. Find the line for
`/this-page-does-not-exist`: the number after the request is `404`, "not found". That is a real investigation already:
the logs tell you which requests failed and why.

Logs can get long. These options keep you sane:

<!-- test: output -->
```bash
docker logs --tail 2 web
```

```text
2026/10/04 05:12:41 [error] 33#33: *3 open() "/usr/share/nginx/html/this-page-does-not-exist" failed (2: No such file or directory), client: 172.17.0.1, server: localhost, request: "GET /this-page-does-not-exist HTTP/1.1", host: "localhost:8080"
172.17.0.1 - - [04/Oct/2026:05:12:41 +0000] "GET /this-page-does-not-exist HTTP/1.1" 404 153 "-" "curl/8.19.0" "-"
```

<!-- test: output=head:4 -->
```bash
docker logs --since 5m --timestamps web
```

```text
2026-10-04T05:12:40.873130322Z /docker-entrypoint.sh: /docker-entrypoint.d/ is not empty, will attempt to perform configuration
2026-10-04T05:12:40.873166794Z /docker-entrypoint.sh: Looking for shell scripts in /docker-entrypoint.d/
2026-10-04T05:12:40.874107914Z /docker-entrypoint.sh: Launching /docker-entrypoint.d/10-listen-on-ipv6-by-default.sh
2026-10-04T05:12:40.883270848Z 10-listen-on-ipv6-by-default.sh: info: Getting the checksum of /etc/nginx/conf.d/default.conf
...
```

`--tail 2` shows the last two lines, `--since 5m` only the last five minutes, `--timestamps` adds Docker's own time to
each line. To watch logs live (and stop with `Ctrl+C`), add `-f`:

<!-- test: skip -->
```bash
docker logs -f web
```

> **Why does my app show no logs?** Docker only sees what the main process writes to stdout/stderr. If an application
> writes to a log *file* inside the container, `docker logs` stays empty. That is why official images (like nginx)
> redirect their log files to stdout.

## 7.2 Break it: a container that stops right after starting

Don't fix it yet. Start a database without the configuration it needs:

<!-- test: output -->
```bash
docker run -d --name db postgres:18-alpine
```

```text
a8105a16ac9e56ddf53df977d96c6e71c5703663c20f1486a14db76dcf13554c
```

Docker printed a container ID. That only means "the container was created and started". It does **not** mean
"the application works". Let's check:

<!-- test-run: sleep 5 -->

<!-- test: output; absent=postgres -->
```bash
docker ps --filter name=db
```

```text
CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES
```

Nothing. Before changing anything, let's investigate. Where did it go? `-a` shows stopped containers too:

<!-- test: retry=20; output; contains=Exited (1) -->
```bash
docker ps -a --filter name=db
```

```text
CONTAINER ID   IMAGE                COMMAND                  CREATED         STATUS                     PORTS     NAMES
a8105a16ac9e   postgres:18-alpine   "docker-entrypoint.s…"   6 seconds ago   Exited (1) 5 seconds ago             db
```

`Exited (1)`: the main process ended with exit code 1, which by convention means "error". Now the most important
command in this chapter:

<!-- test: retry=15; output; contains=superuser password is not specified -->
```bash
docker logs db
```

```text
Error: Database is uninitialized and superuser password is not specified.
       You must specify POSTGRES_PASSWORD to a non-empty value for the
       superuser. For example, "-e POSTGRES_PASSWORD=password" on "docker run".

       You may also use "POSTGRES_HOST_AUTH_METHOD=trust" to allow all
       connections without a password. This is *not* recommended.

       See PostgreSQL documentation about "trust":
       https://www.postgresql.org/docs/current/auth-trust.html
```

The image tells you exactly what is wrong: the database is uninitialised and no superuser password was given.
**Root cause:** a required environment variable is missing. **Fix:** remove the broken container and start it with
the variable:

```bash
docker rm db
docker run -d --name db -e POSTGRES_PASSWORD=lab-only-password postgres:18-alpine
```

**Verify:**

<!-- test: retry=15; output=tail:2; contains=ready to accept connections -->
```bash
docker logs db
```

```text
...
2026-10-04 05:12:49.910 UTC [50] LOG:  checkpoint complete: wrote 0 buffers (0.0%), wrote 3 SLRU buffers; 0 WAL file(s) added, 0 removed, 0 recycled; write=0.004 s, sync=0.002 s, total=0.016 s; sync files=2, longest=0.001 s, average=0.001 s; distance=0 kB, estimate=0 kB; lsn=0/1765F90, redo lsn=0/1765F90
2026-10-04 05:12:49.920 UTC [46] LOG:  database system is shut down
```

"database system is ready to accept connections". Observe → investigate → root cause → fix → verify. You will use this
loop for the rest of your career.

## 7.3 docker inspect: everything Docker knows about a container

`docker inspect` prints the full configuration and state of a container as JSON. It is long, so let's just look at
how long:

<!-- test: output -->
```bash
docker inspect web | wc -l
```

```text
239
```

Hundreds of lines. Nobody reads that top to bottom. Instead you ask for exactly the field you need with `--format`.
Let's answer real questions.

**Is it running, and since when?**

<!-- test: output; contains=running -->
```bash
docker inspect web --format '{{.State.Status}} since {{.State.StartedAt}}'
```

```text
running since 2026-10-04T05:12:40.700137805Z
```

**What is the container's IP address?**

<!-- test: output; contains=172. -->
```bash
docker inspect web --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'
```

```text
172.17.0.2
```

This is the address on Docker's internal network. Your browser does not use it; you reach the container through the
published port instead.

**Which port is mapped to my computer?**

<!-- test: output; contains=8080 -->
```bash
docker inspect web --format '{{json .NetworkSettings.Ports}}'
```

```text
{"80/tcp":[{"HostIp":"0.0.0.0","HostPort":"8080"},{"HostIp":"::","HostPort":"8080"}]}
```

Container port `80/tcp` → host port `8080`. The short version of the same question:

<!-- test: output; contains=8080 -->
```bash
docker port web
```

```text
80/tcp -> 0.0.0.0:8080
80/tcp -> [::]:8080
```

**Which environment variables does the database container have?**

<!-- test: output; contains=POSTGRES_PASSWORD=lab-only-password -->
```bash
docker inspect db --format '{{json .Config.Env}}'
```

```text
["POSTGRES_PASSWORD=lab-only-password","PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin","GOSU_VERSION=1.19","LANG=en_US.utf8","PG_MAJOR=18","PG_VERSION=18.6","PG_SHA256=555610c24d53e4316da5b7d3fc25c279d96856d5e0e23ee308c328c5fa881d9f","DOCKER_PG_LLVM_DEPS=llvm21-dev \t\tclang21","PGDATA=/var/lib/postgresql/18/docker"]
```

Look closely: the password is right there, readable by anyone who can run `docker inspect`. Remember this; it is the
reason the capstone passes passwords as files ([Chapter 8](08-secure-optimize-share.md)).

**Where is the data stored?** The postgres image declares a volume, so Docker created one automatically:

<!-- test: output; contains=volume -->
```bash
docker inspect db --format '{{range .Mounts}}{{.Type}} {{.Name}} -> {{.Destination}}{{end}}'
```

```text
volume e744fd3ddffbf3d4023dec0b6405bc874a6edd7e34fd2160e2666c3ca8dbdb76 -> /var/lib/postgresql
```

An anonymous volume (a long random name) mounted at `/var/lib/postgresql`. We did not ask for it; the image did.

> **Practice:** answer these yourself with `docker inspect --format`:
> the image `web` was created from (`.Config.Image`), its restart policy (`.HostConfig.RestartPolicy.Name`),
> and the command it runs (`.Config.Cmd`).

## 7.4 Resources: stats and top

`docker stats` is like the task manager for containers. Without options it refreshes forever (stop with `Ctrl+C`);
`--no-stream` prints one snapshot:

<!-- test: output; contains=CPU %; contains=MEM USAGE -->
```bash
docker stats --no-stream
```

```text
CONTAINER ID   NAME      CPU %     MEM USAGE / LIMIT     MEM %     NET I/O           BLOCK I/O     PIDS
7b0ffad33a7f   db        0.07%     32.79MiB / 15.35GiB   0.21%     872B / 126B       0B / 40.9MB   9
6906e2f045ae   web       0.00%     11.56MiB / 15.35GiB   0.07%     3.07kB / 3.73kB   0B / 12.3kB   15
```

How to read the columns:

| Column | Meaning |
|---|---|
| `CPU %` | share of one CPU core used right now (can be above 100% on multi-core machines) |
| `MEM USAGE / LIMIT` | memory used / maximum allowed. Without a limit, the limit is all memory Docker has |
| `MEM %` | usage as a percentage of the limit |
| `NET I/O` | bytes received / sent over the network |
| `BLOCK I/O` | bytes read / written on disk |
| `PIDS` | number of processes inside the container |

And which processes are those? `docker top` lists them, as seen from the host:

<!-- test: output; contains=nginx -->
```bash
docker top web
```

```text
UID                 PID                 PPID                C                   STIME               TTY                 TIME                CMD
root                1703572             1703550             0                   05:12               ?                   00:00:00            nginx: master process nginx -g daemon off;
statd               1703617             1703572             0                   05:12               ?                   00:00:00            nginx: worker process
statd               1703618             1703572             0                   05:12               ?                   00:00:00            nginx: worker process
statd               1703619             1703572             0                   05:12               ?                   00:00:00            nginx: worker process
statd               1703620             1703572             0                   05:12               ?                   00:00:00            nginx: worker process
statd               1703621             1703572             0                   05:12               ?                   00:00:00            nginx: worker process
statd               1703622             1703572             0                   05:12               ?                   00:00:00            nginx: worker process
statd               1703623             1703572             0                   05:12               ?                   00:00:00            nginx: worker process
statd               1703624             1703572             0                   05:12               ?                   00:00:00            nginx: worker process
statd               1703625             1703572             0                   05:12               ?                   00:00:00            nginx: worker process
statd               1703626             1703572             0                   05:12               ?                   00:00:00            nginx: worker process
statd               1703627             1703572             0                   05:12               ?                   00:00:00            nginx: worker process
statd               1703628             1703572             0                   05:12               ?                   00:00:00            nginx: worker process
statd               1703629             1703572             0                   05:12               ?                   00:00:00            nginx: worker process
statd               1703630             1703572             0                   05:12               ?                   00:00:00            nginx: worker process
```

One nginx master process and its worker processes. A container is not a virtual machine: it is a group of ordinary
processes with their own view of the system.

## 7.5 Limits: one container must not take the whole machine

By default a container may use all CPU and memory Docker has. On a shared machine, one runaway container can slow
down or crash everything else. Let's start a container with limits:

<!-- test: output -->
```bash
docker run -d --name limited --memory=256m --cpus=0.5 nginx:1.30-alpine
```

```text
79b9dd9b5a71166dceca0352d93a2002a81c1f99515b26d9f928dc457384a8d8
```

`--memory=256m`: at most 256 MiB of memory. `--cpus=0.5`: at most half a CPU core. Check the limit in `docker stats`:

<!-- test: output; contains=256MiB -->
```bash
docker stats --no-stream limited
```

```text
CONTAINER ID   NAME      CPU %     MEM USAGE / LIMIT   MEM %     NET I/O      BLOCK I/O     PIDS
79b9dd9b5a71   limited   0.00%     11.52MiB / 256MiB   4.50%     390B / 84B   0B / 8.19kB   15
```

The `LIMIT` column now says `256MiB` instead of all your memory. And in `inspect` (in bytes and in billionths of a CPU):

<!-- test: output; contains=268435456; contains=500000000 -->
```bash
docker inspect limited --format 'memory={{.HostConfig.Memory}} cpus={{.HostConfig.NanoCpus}}'
```

```text
memory=268435456 cpus=500000000
```

## 7.6 Break it: what happens when a container needs more?

Let's run a tiny Python program that tries to use 256 MiB, inside a container that may only use 64 MiB. Don't fix it
yet. Watch what happens:

<!-- test: fail; timeout=300 -->
```bash
docker run --name oom --memory=64m --memory-swap=64m python:3.14-slim python -c "x = bytearray(256*1024*1024)"
```

> `--memory-swap=64m` (the same value as `--memory`) means "no swap on top". Without it, on a machine with swap
> the container may move memory to disk instead of being stopped, and the demo just runs slowly.

No Python error message at all; the command just ends. Investigate. What was the exit code?

<!-- test: retry=20; output; contains=Exited (137) -->
```bash
docker ps -a --filter name=oom
```

```text
CONTAINER ID   IMAGE              COMMAND                  CREATED        STATUS                                PORTS     NAMES
5d7f39f114d5   python:3.14-slim   "python -c 'x = byte…"   1 second ago   Exited (137) Less than a second ago             oom
```

`137` = 128 + 9: the process was killed with signal 9 (`SIGKILL`). Who killed it? `inspect` knows:

<!-- test: output; contains=OOMKilled=true -->
```bash
docker inspect oom --format 'OOMKilled={{.State.OOMKilled}} exit={{.State.ExitCode}}'
```

```text
OOMKilled=true exit=137
```

**Root cause:** the kernel's "out of memory killer" stopped the process because it went over the container's memory
limit. The program never got the chance to print an error, which is why `docker logs oom` is empty. **Fix:** either
give the container more memory (`--memory=512m`) or make the program use less. **Lesson:** exit code `137` together
with `OOMKilled=true` means "memory limit". You will see this exact pair in real incidents.

## 7.7 Clean up

```bash
docker rm -f web db limited oom
```

## Where would I use this as a DevOps engineer?

- **Logs** are the first thing you check in every incident: "what did the application say right before it failed?"
- **Inspect** answers configuration questions with evidence: which image, which environment, which ports, which volume.
- **Stats and top** tell you whether a slow service is busy, out of memory, or stuck.
- **Limits** protect neighbours on shared machines. Every production platform (Compose, Kubernetes, cloud container
  services) has the same two knobs: memory and CPU.

## What you learned

- `docker logs` shows stdout/stderr of the main process; `--tail`, `--since`, `--timestamps`, `-f` keep it readable.
- `docker run -d` printing an ID only means "started". Always check `docker ps -a` and `docker logs`.
- `docker inspect --format` answers precise questions: state, IP, ports, environment, mounts.
- `docker stats --no-stream` and `docker top` show resource use and processes.
- `--memory` and `--cpus` limit a container; exit `137` + `OOMKilled=true` = killed for using too much memory.

## Try it yourself

1. Start `nginx:1.30-alpine` with `--memory=32m`. Does nginx still start? Check with `docker stats --no-stream`.
2. Find the full container ID, the creation time and the image ID of a running container using only `docker inspect --format`.
3. Run `docker run -d --name counter alpine:3.24 sh -c 'i=0; while true; do i=$((i+1)); echo tick $i; sleep 1; done'`,
   then show only the lines of the last 5 seconds.

## Next

You can run, configure and observe containers. Now let's make them safer, smaller and shareable.
Continue with [Chapter 8 · Secure, optimise and share](08-secure-optimize-share.md).
