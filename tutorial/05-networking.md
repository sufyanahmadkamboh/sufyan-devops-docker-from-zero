# 05 · Networking

> How containers find and talk to each other, why names work on some networks and not on others, how to isolate
> containers, and then the big one: the three-container message board, wired together by hand.
> Time: about 75 minutes. You need: [04 · Data](04-data.md).

## Part 1 · The default network

Every container gets a network connection. Let's see which networks exist:

<!-- test: output; contains=bridge -->
```bash
docker network ls
```

```text
NETWORK ID     NAME      DRIVER    SCOPE
9c28fbb933f7   bridge    bridge    local
6278dc274ea1   host      host      local
3d5e01f105cb   none      null      local
```

Three networks are always there:

| Network | What it is |
|---|---|
| `bridge` | the **default** network; every container joins it unless told otherwise |
| `host` | no isolation: the container uses your machine's network directly (Linux only) |
| `none` | no network at all |

Start a web server and try to reach it **by name** from a second container:

```bash
docker run -d --name web1 nginx:1.30-alpine
```

<!-- test: fail; contains=bad address -->
```bash
docker run --rm busybox:1.37 wget -qO- -T 3 http://web1
```

`bad address 'web1'`. Don't fix it yet. Both containers are on the same default `bridge` network, so why does the name not
work? Let's try the IP address instead. `docker inspect` knows it:

<!-- test: contains=. -->
```bash
docker inspect web1 --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'
```

<!-- test: retry=10; contains=Welcome to nginx -->
```bash
WEB_IP=$(docker inspect web1 --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}')
docker run --rm busybox:1.37 wget -qO- -T 3 "http://$WEB_IP" | grep title
```

By IP it works. So the network connection is fine; only **name resolution** is missing. That is a property of the
default `bridge` network: for historical reasons it has **no built-in DNS**. And IP addresses change every time a
container is recreated, so using them is fragile.

## Part 2 · User-defined networks: names just work

Create your own network:

```bash
docker network create labnet
docker run -d --name web2 --network labnet nginx:1.30-alpine
```

<!-- test: retry=10; contains=Welcome to nginx -->
```bash
docker run --rm --network labnet busybox:1.37 wget -qO- -T 3 http://web2 | grep title
```

The name works. Every **user-defined** network has Docker's built-in DNS server: a container can reach any other container
on the same network by its **name**.

```text
  network "labnet"   (Docker DNS: web2 -> 172.x.x.x)
  +-------------------------------------------------------+
  |   [ busybox ]  --- http://web2 --->   [ web2: nginx ]  |
  +-------------------------------------------------------+
```

Who is on the network, with which address?

<!-- test: contains=web2 -->
```bash
docker network inspect labnet --format '{{range .Containers}}{{.Name}} {{.IPv4Address}}{{println}}{{end}}'
```

> The busybox container is not listed: it already finished and was removed (`--rm`).

## Part 3 · Isolation, connect and disconnect

Containers on **different** networks cannot see each other. Let's prove it with a long-running "client" container on a
second network:

```bash
docker network create othernet
docker run -d --name client --network othernet busybox:1.37 sleep 3600
```

<!-- test: fail; contains=bad address -->
```bash
docker exec client wget -qO- -T 3 http://web2
```

Isolated: `client` cannot even resolve `web2`. Isolation is a feature: your database should not be reachable from
everything.

Now connect `client` to `labnet` as well. A container can be on several networks at the same time:

```bash
docker network connect labnet client
```

<!-- test: retry=10; contains=Welcome to nginx -->
```bash
docker exec client wget -qO- -T 3 http://web2 | grep title
```

<!-- test: contains=labnet; contains=othernet -->
```bash
docker inspect client --format '{{range $name, $settings := .NetworkSettings.Networks}}{{$name}} {{end}}'
```

`client` is now on both networks. Disconnect it again:

<!-- test: fail; contains=bad address -->
```bash
docker network disconnect labnet client
docker exec client wget -qO- -T 3 http://web2
```

Isolated again. And one more safety net: you cannot delete a network that containers are using:

<!-- test: fail; contains=active endpoints -->
```bash
docker network rm labnet
```

Clean up Parts 1-3:

```bash
docker rm -f web1 web2 client
docker network rm labnet othernet
```

### Where would I use this as a DevOps engineer?

Every multi-service application runs on user-defined networks, and services address each other by name
(`DB_HOST=db`), never by IP. Splitting services across networks (web can reach the API, only the API can reach the
database) is a simple, effective security layer. You will see exactly that in the capstone.

## Part 4 · The message board, by hand

Now everything comes together: images, ports, environment variables, a volume, a bind mount and a network. We will run
the message board from `examples/multi-container-app` with plain `docker` commands. It is a lot of typing. That is on
purpose: in chapter 06 you will appreciate Compose.

```text
                       Browser  http://localhost:8080
                          |
   network "board-net"    v
  +-----------------------------------------------------------------------+
  |   [ web: nginx ] --- http://api:5000 ---> [ api: python ]             |
  |                                                |                      |
  |                                     db:5432    v                      |
  |                                         [ db: postgres ]              |
  +-----------------------------------------------|-----------------------+
                                                  v
                                        volume "board-data"
```

### Build the two images

<!-- test: timeout=900; contains=board-api; contains=board-web -->
```bash
docker build -q -t board-api examples/multi-container-app/api
docker build -q -t board-web examples/multi-container-app/web
docker images --format '{{.Repository}}:{{.Tag}}' | grep board
```

(`-q` means quiet: print only the image ID. Look at `examples/multi-container-app/api/Dockerfile` and
`web/Dockerfile`; you know every instruction in them.)

### Network and volume

```bash
docker network create board-net
docker volume create board-data
```

### 1. The database

```bash
docker run -d --name db --network board-net \
  -e POSTGRES_DB=board -e POSTGRES_USER=board -e POSTGRES_PASSWORD=board-lab-password \
  -v board-data:/var/lib/postgresql \
  -v "$(pwd)/examples/multi-container-app/database/init.sql:/docker-entrypoint-initdb.d/init.sql:ro" \
  postgres:18-alpine
```

Two mounts: the **volume** for the data, and a **bind mount** of one file, `init.sql`. The PostgreSQL image runs every
`.sql` file in `/docker-entrypoint-initdb.d/` the first time it starts with an empty data folder; ours creates the
`messages` table. Notice what is missing: **no `-p`**. The database is not published to your computer. Only containers
on `board-net` can reach it.

<!-- test: retry=30; contains=accepting connections -->
```bash
docker exec db pg_isready -U board -d board
```

### 2. The API

```bash
docker run -d --name api --network board-net \
  -e DB_HOST=db -e DB_PASSWORD=board-lab-password \
  -e APP_ENV=development -e GREETING="Hello from a container I started by hand" \
  board-api
```

`DB_HOST=db`: the API finds the database **by its container name**, thanks to the network's DNS. No `-p` here either.

### 3. The web front end

```bash
docker run -d --name web --network board-net -p 8080:80 board-web
```

The only published port. Now the moment of truth:

<!-- test: retry=30; output; contains="database":"ok" -->
```bash
curl -s http://localhost:8080/api/health
```

```text
{"database":"ok","status":"ok"}
```

The request went: your terminal → port 8080 → `web` (nginx) → `/api/` forwarded to `api:5000` → the API asked `db:5432`
→ "ok". Three containers, one network, all by name.

<!-- test: retry=10; output; contains=Hello from a container I started by hand -->
```bash
curl -s http://localhost:8080/api/info
```

```text
{"app_env":"development","container_hostname":"d7b72582d107","database_host":"db","greeting":"Hello from a container I started by hand"}
```

Add a message and read them all:

<!-- test: contains=written by hand -->
```bash
curl -s -X POST -H 'Content-Type: application/json' -d '{"text":"written by hand"}' http://localhost:8080/api/messages
```

<!-- test: retry=10; output; contains=init.sql; contains=written by hand -->
```bash
curl -s http://localhost:8080/api/messages
```

```text
[{"created_at":"2026-10-04T05:12:03.754757+00:00","id":1,"text":"Hello! This first message was created by database/init.sql."},{"created_at":"2026-10-04T05:12:06.704740+00:00","id":2,"text":"written by hand"}]
```

Open <http://localhost:8080> in your browser: the same data, with a page around it. Add a message there too.

### Failure · the web container won't stay up

A colleague recreates the web container and forgets one option:

```bash
docker rm -f web
docker run -d --name web -p 8080:80 board-web
```

<!-- test-run: sleep 4 -->

<!-- test: fail -->
```bash
curl -s --max-time 3 http://localhost:8080/api/health
```

Don't fix it yet. Before changing anything, let's investigate.

**What is the symptom?** Nothing answers on 8080. **What should we check first?** Whether the container is running:

<!-- test: retry=20; contains=Exited (1) -->
```bash
docker ps -a --filter name=web --format '{{.Names}}: {{.Status}}'
```

It exited with code 1. **Which command tells us why?** The logs:

<!-- test: retry=15; output=tail:2; contains=host not found in upstream "api" -->
```bash
docker logs web
```

```text
...
2026/10/04 05:12:07 [emerg] 1#1: host not found in upstream "api" in /etc/nginx/conf.d/default.conf:16
nginx: [emerg] host not found in upstream "api" in /etc/nginx/conf.d/default.conf:16
```

**What does it tell us?** nginx could not resolve the host `api` at start-up, and nginx refuses to start with an unknown
upstream. **Why can't it resolve `api`?** Let's check which network the new `web` container is on:

<!-- test: contains=bridge; absent=board-net -->
```bash
docker inspect web --format '{{range $name, $settings := .NetworkSettings.Networks}}{{$name}} {{end}}'
```

**Root cause:** `--network board-net` was forgotten, so `web` landed on the default `bridge` network, where there is no
DNS and no `api` container. **Fix:**

```bash
docker rm -f web
docker run -d --name web --network board-net -p 8080:80 board-web
```

<!-- test: retry=20; contains="database":"ok" -->
```bash
curl -s http://localhost:8080/api/health
```

**Verify:** healthy again. This exact failure (in Compose form) is
[troubleshooting/03](../troubleshooting/03-containers-cannot-communicate/README.md).

### Experiment · replace the database container, keep the data

```bash
docker rm -f db
docker run -d --name db --network board-net \
  -e POSTGRES_DB=board -e POSTGRES_USER=board -e POSTGRES_PASSWORD=board-lab-password \
  -v board-data:/var/lib/postgresql \
  -v "$(pwd)/examples/multi-container-app/database/init.sql:/docker-entrypoint-initdb.d/init.sql:ro" \
  postgres:18-alpine
```

<!-- test: retry=30; contains=accepting connections -->
```bash
docker exec db pg_isready -U board -d board
```

<!-- test: retry=20; contains=written by hand -->
```bash
curl -s http://localhost:8080/api/messages
```

A brand-new database container, and our message is still there, because the data lives on the `board-data` volume. The
API did not even need a restart: it connects to `db` by name, and the name now points to the new container.

### Clean up

```bash
docker rm -f web api db
docker network rm board-net
docker volume rm board-data
```

## Where would I use this as a DevOps engineer?

What you just did by hand (network, volume, three `docker run` commands with the right options in the right order) is
exactly what tools like Docker Compose and Kubernetes automate. When an automated deployment breaks, you debug it with the
same questions you asked here: is it running? what do the logs say? which network is it on? can it resolve the name?

## What you learned

- `docker network ls | create | inspect | connect | disconnect | rm`.
- The default `bridge` network has no DNS; user-defined networks resolve container names.
- Containers on different networks are isolated; one container can join several networks.
- A three-tier application needs: a network, a volume, environment variables, and exactly one published port.
- "Host not found" means: check the network.

## Try it yourself

- Labs: [11-networking](../labs/11-networking/README.md), [12-multi-container](../labs/12-multi-container/README.md)
- Troubleshooting: [03-containers-cannot-communicate](../troubleshooting/03-containers-cannot-communicate/README.md)
- Challenges: the "Networking" section of [challenges/README.md](../challenges/README.md)
- Deeper: [docs/14-networking.md](../docs/14-networking.md)

## Next

[06 · Docker Compose](06-compose.md)
