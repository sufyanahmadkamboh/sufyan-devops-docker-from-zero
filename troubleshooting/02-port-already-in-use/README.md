# 02 · Port already in use

> You start a second web server and Docker refuses: the port is already allocated.
> Time: 10 minutes · You need: labs 01 and 04

## Problem

One host port can be used by **one** program at a time. Two containers can both listen on port 80
*inside* (each container has its own network space), but only one of them can be published on
port 8080 of *your computer*.

Let's reproduce it. From the repository root:

```bash
cd troubleshooting/02-port-already-in-use
```

A first web server, published on host port 8080:

```bash
docker run -d --name web -p 8080:80 nginx:1.30-alpine
```

Now a second one, on the same host port:

<!-- test: fail; contains=port is already allocated -->
```bash
docker run -d --name web2 -p 8080:80 nginx:1.30-alpine
```

## Symptoms

The second `docker run` ends with an error. The important part is near the end of it:

```text
Bind for 0.0.0.0:8080 failed: port is already allocated
```

`0.0.0.0:8080` means "port 8080 on every network interface of this computer".

A second, easy-to-miss symptom: the failed container **still exists**. Docker created it, then
could not start it:

<!-- test: output; contains=web2 -->
```bash
docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
```

```text
NAMES     STATUS        PORTS
web2      Created       
web       Up 1 second   0.0.0.0:8080->80/tcp, [::]:8080->80/tcp
```

`web2` has the status `Created`: it never ran. If you simply repeat the command, Docker now complains
that the **name** `web2` is already in use, a second error on top of the first one.

## Investigation

**Step 1: who holds port 8080?** Ask Docker which container publishes it:

<!-- test: output; contains=web -->
```bash
docker ps --filter publish=8080 --format 'table {{.Names}}\t{{.Ports}}'
```

```text
NAMES     PORTS
web       0.0.0.0:8080->80/tcp, [::]:8080->80/tcp
```

The container `web` owns `0.0.0.0:8080->80/tcp`.

**Step 2: confirm the mapping of a specific container.** `docker port` lists what a container publishes:

<!-- test: contains=8080 -->
```bash
docker port web
```

**Step 3: what if no container uses the port?** Then another program on your computer does
(a local web server, another tool). Docker cannot see those. Ask the operating system instead:

<!-- test: skip -->
```bash
# Linux / WSL
sudo ss -ltnp | grep ':8080'
# macOS
lsof -iTCP:8080 -sTCP:LISTEN
# Windows PowerShell
netstat -ano | findstr :8080
```

(These need extra rights or differ by system, so they are not part of the automatic tests.)

## Commands

| Command | What it tells you |
|---|---|
| `docker ps --filter publish=8080` | which container publishes host port 8080 |
| `docker port <name>` | all port mappings of one container |
| `docker ps -a` | the failed container is left behind in state `Created` |
| `ss -ltnp` / `lsof -i` / `netstat -ano` | non-Docker programs using the port |

## Root Cause

Container `web` already publishes host port 8080. A host port can only be bound once, so Docker
cannot start `web2` with `-p 8080:80`.

## Fix

You have two honest options. Pick the one that matches what you want:

1. You want **both** servers: give the second one a different **host** port. The container port stays 80.
2. You want to **replace** the first server: stop and remove it, then start the new one.

We want both. First remove the half-created `web2`, then start it on host port 8081:

```bash
docker rm web2
docker run -d --name web2 -p 8081:80 nginx:1.30-alpine
```

## Verification

Both servers answer, each on its own host port:

<!-- test: retry=15; contains=Welcome to nginx -->
```bash
curl -s http://localhost:8080 | grep '<title>'
```

<!-- test: retry=15; contains=Welcome to nginx -->
```bash
curl -s http://localhost:8081 | grep '<title>'
```

<!-- test: output; contains=8081 -->
```bash
docker ps --format 'table {{.Names}}\t{{.Ports}}'
```

```text
NAMES     PORTS
web2      0.0.0.0:8081->80/tcp, [::]:8081->80/tcp
web       0.0.0.0:8080->80/tcp, [::]:8080->80/tcp
```

## Clean up

```bash
docker rm -f web web2
cd ../..
```

## Lesson Learned

- `-p HOST:CONTAINER`: many containers can use the same **container** port, but each **host** port only once.
- `docker ps --filter publish=<port>` finds the container that holds a port in one command.
- A failed `docker run` can leave a container in state `Created`. Remove it (`docker rm`) before you try again.
- If no container holds the port, another program on your computer does: use `ss`, `lsof` or `netstat`.

Next: [03 · Containers cannot communicate](../03-containers-cannot-communicate/README.md)
