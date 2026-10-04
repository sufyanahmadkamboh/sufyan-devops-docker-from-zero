# Lab 14 · Logs, inspect and resources

> Goal: investigate a running container like an engineer: read its logs, query its configuration with
> `docker inspect`, watch its CPU and memory, and limit what it may use. · Time: 45 minutes · You need: labs 01 to 11.

When something goes wrong in production, nobody guesses. You collect evidence: **what did the application say**
(logs), **how is the container configured** (inspect), and **what is it using right now** (stats, top). This lab gives
you all three tools, and then shows what happens when a container hits a resource limit.

## What you will learn

- `docker logs` with `--tail`, `--since`, `-t` and `-f`
- `docker inspect` and `--format` to answer precise questions: IP, ports, environment, mounts, networks
- `docker stats` and `docker top`: CPU, memory, network, disk I/O, processes
- `--memory` and `--cpus`, and how to recognise a container killed for using too much memory (exit code 137)

## Step 1 · Start a container with "a bit of everything"

From the repository root:

```bash
cd labs/14-logs-inspect-resources
```

We create a network and a volume, then one nginx container that uses a port, an environment variable, the volume and
the network. Then we have something to investigate.

```bash
docker network create lab14-net
docker volume create lab14-data
docker run -d --name web --network lab14-net -p 8080:80 -e APP_ENV=lab14 -v lab14-data:/data nginx:1.30-alpine
```

Generate some traffic: two normal requests and one for a page that does not exist.

<!-- test: retry=15 -->
```bash
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8080/
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8080/
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8080/does-not-exist
```

You see `200`, `200` and `404`.

## Step 2 · Logs

Docker collects everything the main process writes to **standard output** and **standard error**. The official nginx
image sends its access log to stdout and its error log to stderr, so `docker logs` shows both.

<!-- test: retry=15; output=tail:6; contains=GET -->
```bash
docker logs web
```

```text
...
2026/10/04 05:17:21 [notice] 1#1: start worker process 42
2026/10/04 05:17:21 [notice] 1#1: start worker process 43
172.18.0.1 - - [04/Oct/2026:05:17:21 +0000] "GET / HTTP/1.1" 200 896 "-" "curl/8.19.0" "-"
172.18.0.1 - - [04/Oct/2026:05:17:21 +0000] "GET / HTTP/1.1" 200 896 "-" "curl/8.19.0" "-"
2026/10/04 05:17:21 [error] 33#33: *3 open() "/usr/share/nginx/html/does-not-exist" failed (2: No such file or directory), client: 172.18.0.1, server: localhost, request: "GET /does-not-exist HTTP/1.1", host: "localhost:8080"
172.18.0.1 - - [04/Oct/2026:05:17:21 +0000] "GET /does-not-exist HTTP/1.1" 404 153 "-" "curl/8.19.0" "-"
```

At the top: nginx's start-up messages. At the bottom: one line per request, with the client address, the path and
the status code (`200`, `404`), and an error line explaining why `/does-not-exist` failed.

Real containers produce thousands of lines. Narrow it down:

<!-- test: retry=15; output; contains=does-not-exist -->
```bash
docker logs --tail 2 web
```

```text
2026/10/04 05:17:21 [error] 33#33: *3 open() "/usr/share/nginx/html/does-not-exist" failed (2: No such file or directory), client: 172.18.0.1, server: localhost, request: "GET /does-not-exist HTTP/1.1", host: "localhost:8080"
172.18.0.1 - - [04/Oct/2026:05:17:21 +0000] "GET /does-not-exist HTTP/1.1" 404 153 "-" "curl/8.19.0" "-"
```

<!-- test: output=tail:3 -->
```bash
docker logs --since 5m -t web
```

```text
...
2026-10-04T05:17:21.780941908Z 172.18.0.1 - - [04/Oct/2026:05:17:21 +0000] "GET / HTTP/1.1" 200 896 "-" "curl/8.19.0" "-"
2026-10-04T05:17:21.821888145Z 2026/10/04 05:17:21 [error] 33#33: *3 open() "/usr/share/nginx/html/does-not-exist" failed (2: No such file or directory), client: 172.18.0.1, server: localhost, request: "GET /does-not-exist HTTP/1.1", host: "localhost:8080"
2026-10-04T05:17:21.821932215Z 172.18.0.1 - - [04/Oct/2026:05:17:21 +0000] "GET /does-not-exist HTTP/1.1" 404 153 "-" "curl/8.19.0" "-"
```

- `--tail 2`: only the last 2 lines
- `--since 5m`: only what was written in the last 5 minutes (also `--since 2026-10-04T10:00:00`)
- `-t`: prefix every line with the time Docker received it, very useful when the app itself prints no time

Follow the log live, like `tail -f`. Open <http://localhost:8080> in your browser and watch new lines arrive. Stop
following with `Ctrl+C` (the container keeps running):

<!-- test: skip -->
```bash
docker logs -f web
```

> If `docker logs` shows nothing, the application writes its logs to a **file inside the container** instead of
> stdout/stderr. Docker cannot see those. Fix it in the application or the image (the official nginx image links
> `/var/log/nginx/access.log` to `/dev/stdout` for exactly this reason).

## Step 3 · docker inspect: the full configuration

`docker inspect` prints everything Docker knows about a container as JSON. It is long:

<!-- test: output=head:20; contains=lab14 -->
```bash
docker inspect web
```

```text
[
    {
        "Id": "5588460359f0eb31454845a4f2591312dfc8807202d0b8463311247b2ecfea4f",
        "Created": "2026-10-04T05:17:21.224843442Z",
        "Path": "/docker-entrypoint.sh",
        "Args": [
            "nginx",
            "-g",
            "daemon off;"
        ],
        "State": {
            "Status": "running",
            "Running": true,
            "Paused": false,
            "Restarting": false,
            "OOMKilled": false,
            "Dead": false,
            "Pid": 1713482,
            "ExitCode": 0,
            "Error": "",
...
```

Scrolling through hundreds of lines is slow. `--format` (a Go template) picks exactly the field you want. Let's answer
the classic investigation questions.

**What is the container's IP address?**

<!-- test: output -->
```bash
docker inspect --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' web
```

```text
172.18.0.2
```

**Which networks is it connected to?**

<!-- test: output; contains=lab14-net -->
```bash
docker inspect --format '{{range $name, $net := .NetworkSettings.Networks}}{{$name}} {{end}}' web
```

```text
lab14-net 
```

**Which ports are mapped?** There is a shortcut for this one:

<!-- test: output; contains=8080 -->
```bash
docker port web
```

```text
80/tcp -> 0.0.0.0:8080
80/tcp -> [::]:8080
```

and the same from inspect, as JSON:

<!-- test: output; contains=8080 -->
```bash
docker inspect --format '{{json .NetworkSettings.Ports}}' web
```

```text
{"80/tcp":[{"HostIp":"0.0.0.0","HostPort":"8080"},{"HostIp":"::","HostPort":"8080"}]}
```

**Which environment variables does it have?** (yours, plus the ones the image defines)

<!-- test: output; contains=APP_ENV=lab14 -->
```bash
docker inspect --format '{{range .Config.Env}}{{println .}}{{end}}' web
```

```text
APP_ENV=lab14
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
NGINX_VERSION=1.30.5
PKG_RELEASE=1
DYNPKG_RELEASE=1
NJS_VERSION=1.0.1
NJS_RELEASE=1
ACME_VERSION=0.4.1
```

**What is mounted, and where?**

<!-- test: output; contains=lab14-data -->
```bash
docker inspect --format '{{range .Mounts}}{{.Type}} {{.Name}} -> {{.Destination}}{{println}}{{end}}' web
```

```text
volume lab14-data -> /data
```

**Is it running, since when, and how often did it restart?**

<!-- test: output; contains=running -->
```bash
docker inspect --format 'status={{.State.Status}} started={{.State.StartedAt}} restarts={{.RestartCount}}' web
```

```text
status=running started=2026-10-04T05:17:21.361715297Z restarts=0
```

> PowerShell users: the single quotes work the same way there. In Windows `cmd.exe`, use double quotes around the
> template instead.

`docker inspect` works on everything, not only containers: `docker inspect lab14-net`, `docker volume inspect
lab14-data`, `docker image inspect nginx:1.30-alpine`.

## Step 4 · What is it using? docker stats and docker top

<!-- test: output; contains=web -->
```bash
docker stats --no-stream
```

```text
CONTAINER ID   NAME      CPU %     MEM USAGE / LIMIT     MEM %     NET I/O           BLOCK I/O     PIDS
5588460359f0   web       0.00%     11.63MiB / 15.35GiB   0.07%     3.39kB / 3.69kB   0B / 8.19kB   15
```

The columns:

| Column | Meaning |
|---|---|
| `CPU %` | Share of **one** CPU core in use right now (can be more than 100 % with several cores) |
| `MEM USAGE / LIMIT` | Memory in use / the most it may use. Without a limit, the limit is all the memory Docker has. |
| `MEM %` | Usage divided by the limit |
| `NET I/O` | Data received / sent over the network since the container started |
| `BLOCK I/O` | Data read from / written to disk |
| `PIDS` | Number of processes and threads |

Without `--no-stream`, `docker stats` refreshes every second until you press `Ctrl+C`:

<!-- test: skip -->
```bash
docker stats
```

Which processes run inside the container?

<!-- test: output; contains=nginx -->
```bash
docker top web
```

```text
UID                 PID                 PPID                C                   STIME               TTY                 TIME                CMD
root                1713482             1713459             0                   05:17               ?                   00:00:00            nginx: master process nginx -g daemon off;
statd               1713536             1713482             0                   05:17               ?                   00:00:00            nginx: worker process
statd               1713537             1713482             0                   05:17               ?                   00:00:00            nginx: worker process
statd               1713538             1713482             0                   05:17               ?                   00:00:00            nginx: worker process
statd               1713539             1713482             0                   05:17               ?                   00:00:00            nginx: worker process
statd               1713540             1713482             0                   05:17               ?                   00:00:00            nginx: worker process
statd               1713541             1713482             0                   05:17               ?                   00:00:00            nginx: worker process
statd               1713542             1713482             0                   05:17               ?                   00:00:00            nginx: worker process
statd               1713543             1713482             0                   05:17               ?                   00:00:00            nginx: worker process
statd               1713544             1713482             0                   05:17               ?                   00:00:00            nginx: worker process
statd               1713545             1713482             0                   05:17               ?                   00:00:00            nginx: worker process
statd               1713546             1713482             0                   05:17               ?                   00:00:00            nginx: worker process
statd               1713547             1713482             0                   05:17               ?                   00:00:00            nginx: worker process
statd               1713548             1713482             0                   05:17               ?                   00:00:00            nginx: worker process
statd               1713549             1713482             0                   05:17               ?                   00:00:00            nginx: worker process
```

One nginx **master** process (PID 1 inside the container, the main process) and its **worker** processes. The PIDs
shown here are the ones on the Docker host, which is why they are large numbers.

## Step 5 · Limit memory and CPU

By default a container may use all the CPU and memory of the machine. One buggy container can slow down everything
else. Set limits:

```bash
docker run -d --name limited --memory=256m --cpus=0.5 nginx:1.30-alpine
```

<!-- test: output; contains=256MiB -->
```bash
docker stats --no-stream limited
```

```text
CONTAINER ID   NAME      CPU %     MEM USAGE / LIMIT   MEM %     NET I/O      BLOCK I/O     PIDS
ad56d89dcee8   limited   0.00%     11.52MiB / 256MiB   4.50%     690B / 84B   0B / 8.19kB   15
```

The `LIMIT` column now says `256MiB` instead of the whole machine. Docker stores the limits in the container's
configuration, in bytes and in billionths of a CPU:

<!-- test: output; contains=268435456; contains=500000000 -->
```bash
docker inspect --format 'memory={{.HostConfig.Memory}} nanocpus={{.HostConfig.NanoCpus}}' limited
```

```text
memory=268435456 nanocpus=500000000
```

`268435456` bytes = 256 MiB, and `500000000` nano-CPUs = half a CPU.

Now watch a CPU limit work. This container runs an endless loop, which would normally use a full CPU core:

```bash
docker run -d --name busy --cpus=0.5 busybox:1.37 sh -c "while true; do :; done"
```

<!-- test-run: sleep 3 -->

<!-- test: output; contains=busy -->
```bash
docker stats --no-stream busy
```

```text
CONTAINER ID   NAME      CPU %     MEM USAGE / LIMIT   MEM %     NET I/O       BLOCK I/O   PIDS
958e3fe2d3fa   busy      49.54%    444KiB / 15.35GiB   0.00%     914B / 126B   0B / 0B     1
```

The `CPU %` column stays around 50 %: the loop wants more, Docker does not give it more. Stop it, it is just burning
CPU:

```bash
docker rm -f busy
```

## Break it

Memory works differently from CPU. A container that wants more CPU just gets slower. A container that needs more
memory than its limit is **killed**. Let's see that happen: this Python one-liner tries to reserve 256 MiB while the
container may only use 64 MiB. Don't fix it yet, we broke it on purpose.

<!-- test: fail; timeout=600 -->
```bash
docker run --name oom --memory=64m --memory-swap=64m python:3.14-slim python -c "x = bytearray(256*1024*1024)"
```

> `--memory-swap=64m` (the same value as `--memory`) means "no swap on top". Without it, on a machine with swap
> the container may move memory to disk instead of being stopped, and the demo just runs slowly.

The command ends without any Python error message. Check the exit status your shell received:

<!-- test: skip -->
```bash
echo $?
```

It prints `137`.

## Troubleshoot it

**Observe.** The container stopped, no error in the output. Before changing anything, let's investigate.

**Investigate.** First, the status Docker recorded:

<!-- test: output; contains=137 -->
```bash
docker ps -a --filter name=oom
```

```text
CONTAINER ID   IMAGE              COMMAND                  CREATED        STATUS                                PORTS     NAMES
e1032bf46e06   python:3.14-slim   "python -c 'x = byte…"   1 second ago   Exited (137) Less than a second ago             oom
```

`Exited (137)`. Exit codes above 128 mean "killed by a signal": 137 − 128 = 9, which is `SIGKILL`, a kill that the
program cannot catch. Who killed it? Ask Docker:

<!-- test: output; contains=OOMKilled=true -->
```bash
docker inspect --format 'OOMKilled={{.State.OOMKilled}} exit={{.State.ExitCode}} limit={{.HostConfig.Memory}}' oom
```

```text
OOMKilled=true exit=137 limit=67108864
```

`OOMKilled=true`: the Linux kernel's **Out Of Memory killer** stopped the process because it went over the memory
limit. And the logs are empty, because the program never had a chance to write anything:

<!-- test: output -->
```bash
docker logs oom
```

```text
```

**Root cause.** The program needs more memory than the container is allowed to use.

**Fix.** Either the program uses less memory, or the limit goes up. Here we raise the limit:

<!-- test: timeout=300; contains=allocated 256 MiB -->
```bash
docker run --rm --memory=512m python:3.14-slim python -c "x = bytearray(256*1024*1024); print('allocated 256 MiB without problems')"
```

**Verify.** The program prints its message and exits with status 0.

Remember the pattern: **exit code 137 + `OOMKilled=true` = memory limit too small (or a memory leak)**. On a real
server, if a container restarts again and again with 137, this is the first thing to check.

## Challenge

**Task:** From **another container**, fetch the nginx welcome page of `web` using its name, then using its IP address.

**Requirements:**
- Do not use the published port 8080.
- Find the IP address with `docker inspect`, not by guessing.

**Hints:**
- The helper container must be on the same network as `web` (`--network ...`).
- `busybox:1.37` has `wget`: `wget -qO- http://<name-or-ip>`.

<details><summary>Solution</summary>

By name (Docker's DNS on a user-defined network):

<!-- test: contains=Welcome to nginx -->
```bash
docker run --rm --network lab14-net busybox:1.37 wget -qO- http://web
```

By IP address:

<!-- test: contains=Welcome to nginx -->
```bash
WEB_IP=$(docker inspect --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' web)
echo "web has IP $WEB_IP"
docker run --rm --network lab14-net busybox:1.37 wget -qO- "http://$WEB_IP"
```

Both work. In practice you use names: IP addresses change every time a container is recreated, names do not.

</details>

## Verify

- [ ] I can show the last lines, recent lines and timestamps of a container's logs
- [ ] I can find a container's IP, ports, environment variables, mounts and networks with `docker inspect --format`
- [ ] I can read the columns of `docker stats` and `docker top`
- [ ] I can start a container with `--memory` and `--cpus` and check the limits
- [ ] I can recognise a container killed for memory: exit code 137 and `OOMKilled=true`

## Clean up

```bash
docker rm -f web limited oom
docker network rm lab14-net
docker volume rm lab14-data
cd ../..
```

## Next

- Concept lessons: [docs/16-logs-and-debugging.md](../../docs/16-logs-and-debugging.md),
  [docs/17-docker-inspect.md](../../docs/17-docker-inspect.md),
  [docs/18-resource-management.md](../../docs/18-resource-management.md)
- Next lab: [Lab 15 · Security basics](../15-security/README.md)
