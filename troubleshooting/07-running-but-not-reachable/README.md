# 07 · Running but not reachable

> `docker ps` says Up, the port is mapped, the logs look happy. And still: connection reset.
> Time: 20 minutes · You need: labs 04 and 06 (ports, Dockerfile)

## Problem

This one confuses experienced people too, because every quick check looks green.
The container runs, the port mapping is there, but the application cannot be reached from your computer.

Let's reproduce it. From the repository root:

```bash
cd troubleshooting/07-running-but-not-reachable
```

We need the `simple-app` image. Build it from `examples/simple-app` (fast if you did lab 06):

```bash
docker build -t simple-app:1.0 ../../examples/simple-app
```

Now start it the way a colleague did after "making it more secure":

```bash
docker run -d --name simple -p 5000:5000 -e HOST=127.0.0.1 simple-app:1.0
```

<!-- test-run: sleep 3 -->

## Symptoms

<!-- test: fail -->
```bash
curl -s --max-time 5 http://localhost:5000
```

curl fails (exit code 56 or 52: *connection reset* or *empty reply*). Not "connection refused",
not a timeout: something accepts the connection and then drops it.

Symptom in one sentence: *"The container is Up and the port is mapped, but every request is reset."*

## Investigation

Check the layers one by one, from the outside in.

**Step 1: is the container running, and is the port published?**

<!-- test: output; contains=0.0.0.0:5000->5000/tcp -->
```bash
docker ps --filter name=simple --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
```

```text
NAMES     STATUS         PORTS
simple    Up 3 seconds   0.0.0.0:5000->5000/tcp, [::]:5000->5000/tcp
```

Up, and `0.0.0.0:5000->5000/tcp`: the host side is fine. Docker forwards port 5000 into the container.

**Step 2: does the app work *inside* the container?** We run a request from inside, with the Python
that is already in the image (the slim image has no curl):

<!-- test: contains=Hello from simple-app -->
```bash
docker exec simple python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:5000').read().decode())"
```

It answers. So the app itself works. The problem is **between** Docker's port forwarding and the app.

**Step 3: on which address does the app listen?** The app prints it at start-up:

<!-- test: retry=15; contains=starting on 127.0.0.1:5000 -->
```bash
docker logs simple
```

`127.0.0.1` is the *loopback* address: "only accept connections that come from inside this same
container". Docker's port forwarding arrives from **outside** the container, on the container's own
network address (something like `172.17.0.2`).

**Step 4: prove it from a neighbour container.** Find the container's IP address, then ask from a
throw-away `busybox` container on the same (default) network:

<!-- test: output; contains=. -->
```bash
docker inspect simple --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'
```

```text
172.17.0.2
```

<!-- test: fail; contains=Connection refused -->
```bash
docker run --rm busybox:1.37 wget -q -O- -T 3 "http://$(docker inspect simple --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'):5000"
```

`Connection refused`: on its network address, nothing listens on 5000. Only on loopback.

```text
  your computer                 container "simple"
  curl localhost:5000  --->  docker port forward  --->  172.17.0.x:5000   nobody listens here
                                                         127.0.0.1:5000   the app listens here only
```

## Commands

| Command | What it told us |
|---|---|
| `docker ps` | Up, and `0.0.0.0:5000->5000/tcp` is published |
| `docker exec simple python -c "...urlopen('http://127.0.0.1:5000')..."` | the app works inside the container |
| `docker logs simple` | `starting on 127.0.0.1:5000` |
| `docker inspect simple --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'` | the container's own address |
| `docker run --rm busybox:1.37 wget ... http://<ip>:5000` | refused on the container address |

## Root Cause

The app was started with `HOST=127.0.0.1`, so it only listens on the container's loopback interface.
Docker's port forwarding delivers traffic to the container's network interface, where nothing listens.
Inside a container, a server must listen on `0.0.0.0` (all interfaces) to be reachable through `-p`.

(The same bug appears without any environment variable: Flask's `app.run()` and many other development
servers listen on `127.0.0.1` by default. That is why `simple-app` sets `0.0.0.0` explicitly.)

## Fix

Start the container without the wrong override; the app's default is `0.0.0.0`:

```bash
docker rm -f simple
docker run -d --name simple -p 5000:5000 simple-app:1.0
```

## Verification

<!-- test: retry=15; contains=Hello from simple-app -->
```bash
curl -s http://localhost:5000
```

<!-- test: retry=15; contains=starting on 0.0.0.0:5000 -->
```bash
docker logs simple
```

## Clean up

```bash
docker rm -f simple
cd ../..
```

## Lesson Learned

- "Up" and a published port do not prove the app is reachable. Test from outside **and** from inside.
- A server in a container must listen on `0.0.0.0`. `127.0.0.1` inside a container means *this container only*.
- Work from the outside in: port mapping (`docker ps`) → app inside (`docker exec`) → listen address (`docker logs`).
- "Connection reset" through a published port often means "Docker forwarded it, but nothing listened on the
  container's address".

Next: [08 · Image too large](../08-image-too-large/README.md)
