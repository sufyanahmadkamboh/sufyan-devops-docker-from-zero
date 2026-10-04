# Ports

> Lesson 07 · about 30 minutes · you need: [04 · Containers](04-containers.md)

## What is it?

A container has its **own network interface** with a private IP address. A program listening on
port 80 inside the container is **not** reachable from your browser automatically. **Port
publishing** (`-p`) tells Docker: "forward traffic that arrives on this port of my computer to
that port of the container".

```text
   -p 8080:80
      HOST : CONTAINER

   Browser  ->  localhost:8080  ->  Docker  ->  container 172.17.0.2:80  ->  nginx
                (your computer)     (forward)    (private, inside Docker)
```

## Why do we need it?

Containers are isolated on purpose. Publishing is how you deliberately open exactly the ports you
want: the web server, yes; the database, usually no. It also lets you run several containers that
all listen on port 80 inside, by giving each a different port on the host.

## How does it work?

| Option | Meaning |
|---|---|
| `-p 8080:80` | host port 8080 → container port 80, on all host interfaces |
| `-p 127.0.0.1:8080:80` | only reachable from your own computer, not from the network |
| `-p 80` | container port 80 → a **random** free host port (see it with `docker port`) |
| `-P` | publish every port the image `EXPOSE`s, to random host ports |
| `EXPOSE 80` (in a Dockerfile) | **documentation only**: says which port the app uses, publishes nothing |

```text
   Your computer (host)
   +-------------------------------------------------------------+
   |  port 8080  ----------+                                     |
   |  port 8081  -------+  |                                     |
   |                    |  |   Docker network (172.17.0.0/16)    |
   |                    |  +-> web   172.17.0.2:80  (nginx)      |
   |                    +----> web2  172.17.0.3:80  (nginx)      |
   |  (nothing published) ---> db    172.17.0.4:5432 (private)   |
   +-------------------------------------------------------------+
```

Two rules decide whether a request arrives:

1. the **host port** must be free (only one program per port on your computer);
2. the **container port** must be the port the app really listens on.

## Prerequisites

- `curl` in your terminal (WSL, Linux, macOS, Git Bash; PowerShell has `curl.exe`).

## Hands-on Lab

Publish nginx's port 80 on port 8080 of your computer:

<!-- test: contains=0.0.0.0:8080->80/tcp; output -->
```bash
docker run -d --name web -p 8080:80 nginx:1.30-alpine
docker ps --filter name=web --format 'table {{.Names}}\t{{.Ports}}'
```

```text
5b5a5cfc3512c76f4988c41c4495b42f211814e2eb6142f3d33fb24397aaec9f
NAMES     PORTS
web       0.0.0.0:8080->80/tcp, [::]:8080->80/tcp
```

Open <http://localhost:8080> in your browser, or ask with curl:

<!-- test: retry=15; contains=Welcome to nginx -->
```bash
curl -s http://localhost:8080 | grep -o '<title>.*</title>'
```

`docker port` lists the mappings of one container:

<!-- test: contains=80/tcp; output -->
```bash
docker port web
```

```text
80/tcp -> 0.0.0.0:8080
80/tcp -> [::]:8080
```

The full lab, with port conflicts and a "running but unreachable" case, is
[labs/04-port-mapping](../labs/04-port-mapping/README.md).

## Expected Result

- The PORTS column shows `0.0.0.0:8080->80/tcp` (and often `[::]:8080->80/tcp` for IPv6).
- curl prints `<title>Welcome to nginx!</title>`.
- `docker port web` prints `80/tcp -> 0.0.0.0:8080`.

## Experiment

Run a second nginx on a **different host port**. Inside, both listen on 80, and that is fine:

```bash
docker run -d --name web2 -p 8081:80 nginx:1.30-alpine
```

<!-- test: retry=15; contains=Welcome to nginx -->
```bash
curl -s http://localhost:8081 | grep -o '<title>.*</title>'
```

Let Docker choose a free host port with `-p 80`:

<!-- test: contains=80/tcp; output -->
```bash
docker run -d --name web3 -p 80 nginx:1.30-alpine
docker port web3
```

```text
f8c6e5277ec18645a87fca266eeff682a450c31cc02a9314dccf774e00e57f53
80/tcp -> 0.0.0.0:51162
80/tcp -> [::]:51162
```

## Break It

**Break 1 · the host port is already taken.** Port 8080 belongs to `web`:

<!-- test: fail; contains=port is already allocated -->
```bash
docker run -d --name web4 -p 8080:80 nginx:1.30-alpine
```

**Break 2 · wrong container port.** nginx listens on 80, but we forward to 8080 inside:

<!-- test: contains=wrong -->
```bash
docker run -d --name wrong -p 8082:8080 nginx:1.30-alpine
docker ps --filter name=wrong --format '{{.Names}} {{.Status}} {{.Ports}}'
```

The container is **running**, yet:

<!-- test: fail -->
```bash
curl -sS --max-time 5 http://localhost:8082
```

## Troubleshoot It

**Break 1:** the error ends with `Bind for 0.0.0.0:8080 failed: port is already allocated`.
Investigate who owns the port:

<!-- test: contains=web -->
```bash
docker ps --filter publish=8080 --format '{{.Names}} uses {{.Ports}}'
```

Root cause: two containers cannot share one **host** port. Fix: choose another host port
(`-p 8083:80`) or stop the other container. Note that Docker already **created** `web4` before
the port failed; remove the leftover with `docker rm web4`.

```bash
docker rm web4
docker run -d --name web4 -p 8083:80 nginx:1.30-alpine
```

<!-- test: retry=15; contains=Welcome to nginx -->
```bash
curl -s http://localhost:8083 | grep -o '<title>.*</title>'
```

If the port is used by a program **outside** Docker, `docker ps` will not show it. On Linux/WSL
use `sudo ss -ltnp | grep 8080`, on Windows `netstat -ano | findstr :8080`, on macOS
`lsof -i :8080`.

**Break 2:** curl fails (connection reset, empty reply, or refused, depending on your system).
Do not guess, collect evidence:

1. Is the container running? `docker ps` says **Up**. So it is not a crash.
2. What is published? `8082->8080/tcp`.
3. What does the app listen on? Ask the image and the process:

<!-- test: contains=80/tcp -->
```bash
docker image inspect nginx:1.30-alpine --format 'image exposes: {{.Config.ExposedPorts}}'
docker exec wrong grep -m1 listen /etc/nginx/conf.d/default.conf
```

Root cause: we forward to container port 8080, but nginx listens on 80. Fix: recreate the
container with the right container port (options cannot be changed on an existing container):

```bash
docker rm -f wrong
docker run -d --name wrong -p 8082:80 nginx:1.30-alpine
```

<!-- test: retry=15; contains=Welcome to nginx -->
```bash
curl -s http://localhost:8082 | grep -o '<title>.*</title>'
```

## Common Mistakes

- Writing the ports the wrong way round. It is always `HOST:CONTAINER`.
- Thinking `EXPOSE` publishes a port. It does not; only `-p`/`-P` (or Compose `ports:`) do.
- Using `-p 80:80` on Linux/WSL where port 80 may be used by another web server, or needs root.
- An app inside the container listening on `127.0.0.1` only: it then refuses traffic coming from
  Docker's port forwarding. Apps in containers must listen on `0.0.0.0`
  (scenario [07 · running but not reachable](../troubleshooting/07-running-but-not-reachable/README.md)).

## Best Practices

- Publish only what users must reach (web front end); keep databases and internal APIs unpublished.
- Use `-p 127.0.0.1:8080:80` for services that only you should reach on a shared network.
- Pick high host ports (8080, 8081, ...) for local development to avoid conflicts.
- Document the app's port with `EXPOSE` in your Dockerfile.

## Challenge

Run two nginx containers, `blue` on host port 8091 and `green` on host port 8092, and prove with
curl that both answer. Then find, with a Docker command, which container owns port 8092.

## Solution

<details><summary>Show the solution</summary>

```bash
docker run -d --name blue -p 8091:80 nginx:1.30-alpine
docker run -d --name green -p 8092:80 nginx:1.30-alpine
```

<!-- test: retry=15; contains=Welcome to nginx -->
```bash
curl -s http://localhost:8091 | grep -o '<title>.*</title>'
curl -s http://localhost:8092 | grep -o '<title>.*</title>'
```

<!-- test: contains=green -->
```bash
docker ps --filter publish=8092 --format '{{.Names}}'
```

</details>

## Verification

- [ ] You can explain `HOST:CONTAINER`.
- [ ] You know `EXPOSE` is documentation and `-p` is publishing.
- [ ] You can find which container uses a port.
- [ ] You can diagnose "running but unreachable" with evidence, not guesses.

Clean up:

```bash
docker rm -f web web2 web3 web4 wrong blue green
```

## Real-World Usage

- Locally, every developer runs the app on a published port (8080) and the database unpublished.
- On servers, usually only a reverse proxy or load balancer publishes 80/443; everything else
  talks over internal networks.
- "Port already allocated" is a daily message when several projects run on one laptop.

## Key Takeaways

- `-p HOST:CONTAINER` forwards a host port to a container port.
- `EXPOSE` documents, `-p` publishes.
- One host port = one container; the container port must match what the app listens on.
- Investigate with `docker ps`, `docker port`, `docker ps --filter publish=`, `docker inspect`.
- Next: [08 · Environment Variables](08-environment-variables.md).
