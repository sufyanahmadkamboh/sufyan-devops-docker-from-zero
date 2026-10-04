# Docker Networking

## What is it?

Every container gets its own network stack: its own IP address, its own `localhost`, its own ports. A **Docker
network** is a virtual switch that containers plug into. Containers on the **same** network can talk to each other;
containers on **different** networks cannot.

## Why do we need it?

Real applications are several programs: a web server talks to an API, the API talks to a database. Each runs in its
own container, so they need a safe, predictable way to find each other. Docker networks give you:

- **Communication** between containers, without publishing ports to your computer.
- **Names instead of IP addresses**: the API connects to `db`, not to `172.18.0.3` (IPs change every restart).
- **Isolation**: the web container does not even need to see the database.

## How does it work?

When you install Docker you get a network called `bridge` (the default). Containers started without `--network`
join it. On the default bridge, containers get IP addresses but **no name resolution**.

When you create your **own** network (`docker network create`), Docker also runs a small **DNS server** for it:
every container on that network can be reached by its **container name** (and in Compose, by its **service name**).

```text
          user-defined bridge network "demo-net"  (Docker DNS: name -> IP)
   ┌─────────────────────────────────────────────────────────────┐
   │                                                             │
   │   ┌──────────────┐   "http://web"   ┌──────────────┐        │
   │   │  container   │ ───────────────► │  container   │        │
   │   │  client      │   DNS answers    │  web (nginx) │        │
   │   │ 172.20.0.3   │   172.20.0.2     │ 172.20.0.2   │        │
   │   └──────────────┘                  └──────────────┘        │
   └─────────────────────────────────────────────────────────────┘
                 Containers outside "demo-net" cannot reach "web" at all.
```

The capstone uses **two** networks so the web server can never touch the database:

```text
                Browser
                   │  localhost:8080 (the only published port)
                   ▼
   ┌───────── capstone_frontend ─────────┐
   │   web (nginx)  ───────►  api        │
   └─────────────────────────│───────────┘
                             │  api is on BOTH networks
   ┌───────── capstone_backend ─┼────────┐
   │                        api ───────► db (PostgreSQL)
   └─────────────────────────────────────┘
        web ──X──► db   "bad address 'db'": web is not on capstone_backend
```

Useful commands:

```text
docker network ls                         list networks
docker network create NAME                create a user-defined bridge network
docker network inspect NAME               which containers are attached, their IPs, the subnet
docker network connect NAME CONTAINER     plug a running container into another network
docker network disconnect NAME CONTAINER  unplug it
docker network rm NAME                    remove a network (no containers may be attached)
```

## Prerequisites

- [04-containers.md](04-containers.md), [07-ports.md](07-ports.md)

## Hands-on Lab

Full lab: [labs/11-networking](../labs/11-networking/README.md). The short version: create a network, start nginx
on it, and reach it **by name** from a second container.

```bash
docker network create demo-net
docker run -d --name web --network demo-net nginx:1.30-alpine
```

<!-- test: retry=15; contains=Welcome to nginx -->
```bash
docker run --rm --network demo-net busybox:1.37 wget -qO- http://web
```

<!-- test: output=head:12 -->
```bash
docker network inspect demo-net --format '{{range .Containers}}{{.Name}} {{.IPv4Address}}{{"\n"}}{{end}}'
```

```text
web 172.18.0.2/16
```

## Expected Result

- `wget` prints the HTML of the nginx welcome page: the busybox container found `web` by its name.
- `docker network inspect` lists `web` with an IP address in the network's subnet. (The busybox container is
  already gone, because `--rm` removed it when `wget` finished.)

## Experiment

Do the same on the **default** bridge network, without `--network`:

```bash
docker run -d --name web2 nginx:1.30-alpine
```

<!-- test: fail; contains=bad address -->
```bash
docker run --rm busybox:1.37 wget -qO- -T 3 http://web2
```

`bad address 'web2'`: the default bridge has **no DNS for container names**. This is why you should always create
your own network (or let Compose create one).

Now plug `web2` into `demo-net` while it is running, and try again from `demo-net`:

```bash
docker network connect demo-net web2
```

<!-- test: retry=10; contains=Welcome to nginx -->
```bash
docker run --rm --network demo-net busybox:1.37 wget -qO- -T 3 http://web2
```

`web2` is now on two networks at the same time, exactly like the capstone's `api` container.

## Break It

Unplug `web` from `demo-net` and try to reach it:

```bash
docker network disconnect demo-net web
```

<!-- test: fail; contains=bad address -->
```bash
docker run --rm --network demo-net busybox:1.37 wget -qO- -T 3 http://web
```

## Troubleshoot It

When two containers cannot talk, do not guess. Check **which networks each one is on**:

<!-- test: contains=demo-net -->
```bash
docker inspect web --format '{{range $name, $net := .NetworkSettings.Networks}}{{$name}} {{end}}'
docker inspect web2 --format '{{range $name, $net := .NetworkSettings.Networks}}{{$name}} {{end}}'
```

`web` is only on `bridge`; `web2` is on `bridge` and `demo-net`. They do not share a user-defined network, so there is
no name resolution between them. Fix and verify:

```bash
docker network connect demo-net web
```

<!-- test: retry=10; contains=Welcome to nginx -->
```bash
docker run --rm --network demo-net busybox:1.37 wget -qO- -T 3 http://web
```

The Compose version of this problem (`host not found in upstream "api"`) is in
[troubleshooting/03-containers-cannot-communicate](../troubleshooting/03-containers-cannot-communicate/README.md).

```bash
docker rm -f web web2
docker network rm demo-net
```

## Common Mistakes

- Using container IP addresses in configuration. They change; use names.
- Expecting names to work on the default `bridge` network.
- Using `localhost` to reach **another** container. Inside a container, `localhost` is the container itself.
- Publishing database ports (`-p 5432:5432`) just so another container can reach it. Containers on the same network
  do not need published ports at all.
- Removing a network that still has containers attached (Docker refuses; stop or disconnect them first).

## Best Practices

- One user-defined network per application (Compose does this automatically).
- Split networks by trust: the database only on a backend network.
- Publish only the ports humans need (usually just the web port).
- Refer to services by name everywhere (`DB_HOST=db`).

## Challenge

**Task:** create a network `shop-net`, run nginx named `shop` on it, and prove that a busybox container on
`shop-net` can reach it while a busybox container on the default bridge cannot.

**Hints:** `docker network create`, `--network`, `wget -qO- -T 3`.

## Solution

<details><summary>Solution</summary>

```bash
docker network create shop-net
docker run -d --name shop --network shop-net nginx:1.30-alpine
```

<!-- test: retry=15; contains=Welcome to nginx -->
```bash
docker run --rm --network shop-net busybox:1.37 wget -qO- -T 3 http://shop
```

<!-- test: fail; contains=bad address -->
```bash
docker run --rm busybox:1.37 wget -qO- -T 3 http://shop
```

```bash
docker rm -f shop
docker network rm shop-net
```

Same network → Docker DNS answers `shop`. Default bridge → no name resolution.
</details>

## Verification

- [ ] I can create a network and attach containers to it.
- [ ] I can reach a container by its name from another container.
- [ ] I know why names do not work on the default bridge.
- [ ] I can find out which networks a container is on.

## Real-World Usage

Service-to-service communication is everyday DevOps work: a web tier calls an API, the API calls a database, a cache
or a message queue. Network segmentation (frontend/backend) is a basic security control in every environment, from
Docker Compose on a laptop to large container platforms later in your career.

## Key Takeaways

- Containers on the same user-defined network reach each other **by name**.
- The default `bridge` network has no name resolution.
- `localhost` inside a container means that container.
- Separate networks = separate trust zones.

Next: [15-docker-compose.md](15-docker-compose.md)
