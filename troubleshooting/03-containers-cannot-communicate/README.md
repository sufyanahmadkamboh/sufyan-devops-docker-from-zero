# 03 · Containers cannot communicate

> The message board starts, but the web container keeps stopping and the site is down.
> Time: 20 minutes · You need: labs 11–13 (networking and Compose)

## Problem

Someone "improved" the message board by putting the database on its own network, so that the
web container cannot reach it. Good idea. But now the whole site is down.

Let's reproduce it. From the repository root:

```bash
cd troubleshooting/03-containers-cannot-communicate
```

Have a quick look at the Compose file first. Notice the `networks:` line under each service:

<!-- test: contains=networks -->
```bash
cat docker-compose.yml
```

Start it:

<!-- test: timeout=900 -->
```bash
docker compose up -d --build
```

Compose reports every container as `Started`. Wait a few seconds, then look again.

<!-- test-run: sleep 10 -->

## Symptoms

The browser (or curl) gets no answer at all on port 8080:

<!-- test: fail -->
```bash
curl -s --max-time 3 http://localhost:8080
```

Symptom in one sentence: *"Compose said Started, but nothing listens on port 8080."*

## Investigation

**Step 1: which containers are still running?**

<!-- test: retry=20; output; contains=Exited (1) -->
```bash
docker compose ps -a --format 'table {{.Service}}\t{{.Status}}'
```

```text
SERVICE   STATUS
api       Up 13 seconds
db        Up 13 seconds
web       Exited (1) 7 seconds ago
```

`api` and `db` are up. `web` has exited with code 1. So our question becomes: *why did nginx stop?*

**Step 2: read the web container's logs.**

<!-- test: retry=15; output=tail:3; contains=host not found in upstream "api" -->
```bash
docker compose logs web
```

```text
...
web-1  | /docker-entrypoint.sh: Configuration complete; ready for start up
web-1  | 2026/10/04 04:57:28 [emerg] 1#1: host not found in upstream "api" in /etc/nginx/conf.d/default.conf:16
web-1  | nginx: [emerg] host not found in upstream "api" in /etc/nginx/conf.d/default.conf:16
```

The key line:

```text
nginx: [emerg] host not found in upstream "api" in /etc/nginx/conf.d/default.conf:16
```

nginx forwards `/api/` requests to a host called `api` (line 16 of its configuration).
When nginx starts, it looks that name up. The lookup failed, so nginx refused to start.

**Step 3: but the `api` container is running. Why can't web find it?** Docker's built-in DNS only
answers for containers **on the same network**. Let's see which networks each container joined:

<!-- test: contains=ts03_frontend -->
```bash
docker inspect ts03-web-1 --format '{{range $name, $net := .NetworkSettings.Networks}}{{$name}} {{end}}'
```

<!-- test: contains=ts03_backend; absent=ts03_frontend -->
```bash
docker inspect ts03-api-1 --format '{{range $name, $net := .NetworkSettings.Networks}}{{$name}} {{end}}'
```

`web` is only on `ts03_frontend`. `api` is only on `ts03_backend`. They share no network.

**Step 4: prove it with a test container.** We start a tiny throw-away `busybox` container on each
network and ask it to reach `api`. On the frontend network:

<!-- test: fail; contains=bad address -->
```bash
docker run --rm --network ts03_frontend busybox:1.37 ping -c 1 api
```

`bad address 'api'`: the name does not exist on this network. On the backend network:

<!-- test: contains=1 packets received -->
```bash
docker run --rm --network ts03_backend busybox:1.37 ping -c 1 api
```

There it works. The evidence is complete.

## Commands

| Command | What it told us |
|---|---|
| `docker compose ps -a` | `web` exited with code 1, the others run |
| `docker compose logs web` | `host not found in upstream "api"` |
| `docker inspect <container> --format '{{range $name, $net := .NetworkSettings.Networks}}{{$name}} {{end}}'` | web: frontend only, api: backend only |
| `docker run --rm --network <net> busybox:1.37 ping -c 1 api` | `api` resolves on backend, not on frontend |

## Root Cause

In `docker-compose.yml` the `api` service is attached only to the `backend` network,
while `web` is attached only to `frontend`. Containers can only resolve and reach each other by
name when they share at least one network. nginx cannot resolve `api`, so it exits.

## Fix

The api is the bridge between the two worlds: it must be on **both** networks. The database stays on
`backend` only, so the original goal (web cannot reach the database) is kept.

The fixed file is `docker-compose.fixed.yml`. The only difference is one line:

<!-- test: contains=networks: [frontend, backend] -->
```bash
grep -n 'networks: \[' docker-compose.yml docker-compose.fixed.yml
```

Stop the broken stack first. This matters: nginx looks up `api` only once, at start-up, so we want
a completely fresh start:

```bash
docker compose down
```

Start the fixed version. `-f` tells Compose which file to use (the project name `ts03` is set inside the file):

<!-- test: timeout=900 -->
```bash
docker compose -f docker-compose.fixed.yml up -d --build
```

## Verification

All three containers stay up:

<!-- test-run: sleep 8 -->
<!-- test: output; absent=Exited -->
```bash
docker compose -f docker-compose.fixed.yml ps -a --format 'table {{.Service}}\t{{.Status}}'
```

```text
SERVICE   STATUS
api       Up 9 seconds
db        Up 9 seconds
web       Up 8 seconds
```

The web page and the API answer through nginx:

<!-- test: retry=20; contains=greeting -->
```bash
curl -s http://localhost:8080/api/info
```

<!-- test: retry=20; contains="database":"ok" -->
```bash
curl -s http://localhost:8080/api/health
```

And the isolation still works: from the frontend network, the database name does not exist:

<!-- test: fail; contains=bad address -->
```bash
docker run --rm --network ts03_frontend busybox:1.37 ping -c 1 db
```

## Clean up

```bash
docker compose -f docker-compose.fixed.yml down -v
cd ../..
```

## Lesson Learned

- Containers find each other **by name** only when they share a network.
- "Host not found" or "bad address" errors are network problems, not application bugs.
- `docker inspect ... .NetworkSettings.Networks` shows which networks a container joined; a throw-away
  `busybox` container on a network is the quickest way to test name resolution.
- Separate networks are a good security idea, but the service in the middle must join both sides.

Next: [04 · Volume data appears missing](../04-volume-data-missing/README.md)
