# Lab 12 · A Multi-Container App, the Hard Way

> **Goal:** run a real three-container application (web, API, database) by hand, using everything from the previous labs.
> **Time:** about 35 minutes · **You need:** Labs [05](../05-environment-variables/README.md) (environment variables),
> [06](../06-first-dockerfile/README.md) (build), [09](../09-volumes/README.md) (volumes),
> [10](../10-bind-mounts/README.md) (bind mounts) and [11](../11-networking/README.md) (networks)

## What you will learn

- How images, containers, ports, environment variables, a network, a volume and a bind mount work **together**.
- Why the **order** in which containers start matters.
- How data survives when every container is replaced.
- Why typing all of this by hand gets painful, which is exactly the problem Docker Compose solves in [Lab 13](../13-docker-compose/README.md).

```text
                     your browser / curl
                            │  http://localhost:8080
                            ▼   -p 8080:80
┌──────────────────────── network "board-net" ────────────────────────┐
│  ┌────────────┐  /api/ → http://api:5000  ┌────────────┐  db:5432   ┌────────────┐ │
│  │    web     │ ─────────────────────────►│    api     │ ──────────►│     db     │ │
│  │ nginx      │                           │ Python     │            │ PostgreSQL │ │
│  │ board-web  │                           │ board-api  │            │ 18-alpine  │ │
│  └────────────┘                           └────────────┘            └─────┬──────┘ │
└───────────────────────────────────────────────────────────────────────────┼────────┘
                                                                            │ -v board-data:/var/lib/postgresql
                                                                     ┌──────▼───────┐
                                                                     │ volume       │
                                                                     │ "board-data" │
                                                                     └──────────────┘
```

The app is a tiny message board. You do **not** need to understand its code; it only exists so you can practise Docker.
The files are in `examples/multi-container-app/`:

| Folder | What it is |
|---|---|
| `web/` | nginx serving a web page; forwards everything under `/api/` to the container named in `API_HOST` (default `api`) |
| `api/` | a small Python API; reads `DB_HOST`, `DB_PASSWORD` and friends from environment variables |
| `database/init.sql` | creates the `messages` table and a first message, the first time the database starts |

> **Windows users:** use WSL2, or in Git Bash run `export MSYS_NO_PATHCONV=1` first (we bind mount a file with `$(pwd)`).

## Step 1 · Build the two images

```bash
cd examples/multi-container-app
docker build -t board-api:1.0 ./api
docker build -t board-web:1.0 ./web
```

Note the build context: `./api` and `./web`, each folder with its own Dockerfile. The database needs no build: we use
the official `postgres:18-alpine` image as it is.

<!-- test: contains=board-api; contains=board-web -->
```bash
docker images --filter reference='board-*'
```

## Step 2 · Create the network and the volume

```bash
docker network create board-net
docker volume create board-data
```

## Step 3 · Start the database

```bash
docker run -d --name db --network board-net \
  -e POSTGRES_DB=board \
  -e POSTGRES_USER=board \
  -e POSTGRES_PASSWORD=board-lab-password \
  -v board-data:/var/lib/postgresql \
  -v "$(pwd)/database/init.sql:/docker-entrypoint-initdb.d/init.sql:ro" \
  postgres:18-alpine
```

Read it line by line:

| Part | Why |
|---|---|
| `--network board-net` | the API will find this container under the name `db` |
| `-e POSTGRES_...` | the official image creates this database, user and password on first start |
| `-v board-data:/var/lib/postgresql` | a **volume**: the data survives the container |
| `-v .../init.sql:...:ro` | a **bind mount** of one file, read-only: SQL files in `/docker-entrypoint-initdb.d/` run once, on the first start |
| no `-p` | nothing outside Docker needs to reach the database directly. Fewer open doors |

Watch the database start (the first start takes a few seconds; it runs `init.sql`):

<!-- test: retry=30; contains=ready to accept connections -->
```bash
docker logs db 2>&1 | tail -n 5
```

## Step 4 · Start the API

```bash
docker run -d --name api --network board-net \
  -e DB_HOST=db \
  -e DB_PASSWORD=board-lab-password \
  -e APP_ENV=development \
  -e GREETING="Hello from the hard way" \
  board-api:1.0
```

`DB_HOST=db` is the database container's **name**: Docker's DNS on `board-net` turns it into an IP address.
`DB_NAME` and `DB_USER` default to `board`, so we can leave them out.

<!-- test: retry=10; contains=Listening at -->
```bash
docker logs api
```

`Listening at: http://0.0.0.0:5000` means the API is up (gunicorn is the Python web server inside the image).

## Step 5 · Start the web container

```bash
docker run -d --name web --network board-net -p 8080:80 board-web:1.0
```

Only `web` publishes a port: it is the single entrance from your computer into the app.

<!-- test: output; contains=web; contains=api; contains=db -->
```bash
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"
```

```text
NAMES     IMAGE                STATUS                  PORTS
web       board-web:1.0        Up Less than a second   0.0.0.0:8080->80/tcp, [::]:8080->80/tcp
api       board-api:1.0        Up 2 seconds            5000/tcp
db        postgres:18-alpine   Up 5 seconds            5432/tcp
```

Three containers `Up`. Only `web` shows a mapping like `0.0.0.0:8080->80/tcp`; `api` and `db` show their ports
without an arrow (reachable inside the network only).

## Step 6 · Use the application

Open <http://localhost:8080> in your browser. Then check each layer from the command line:

<!-- test: retry=30; contains=database":"ok -->
```bash
curl -s http://localhost:8080/api/health
```

`{"database":"ok","status":"ok"}`: the browser → web → api → db chain works.

<!-- test: retry=10; contains=Hello from the hard way -->
```bash
curl -s http://localhost:8080/api/info
```

The greeting is the one **you** passed with `-e`, and `container_hostname` is the API container's ID.

<!-- test: contains=init.sql -->
```bash
curl -s http://localhost:8080/api/messages
```

The first message was created by `init.sql`. Add one of your own:

<!-- test: contains=id -->
```bash
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"text":"Hello from the hard way"}' \
  http://localhost:8080/api/messages
```

<!-- test: contains=Hello from the hard way -->
```bash
curl -s http://localhost:8080/api/messages
```

Refresh the browser: your message is in the list.

## Step 7 · Replace every container, keep the data

Remove all three containers. The volume and the network stay:

```bash
docker rm -f web api db
```

Start them again, in the same order, with exactly the same commands:

```bash
docker run -d --name db --network board-net \
  -e POSTGRES_DB=board \
  -e POSTGRES_USER=board \
  -e POSTGRES_PASSWORD=board-lab-password \
  -v board-data:/var/lib/postgresql \
  -v "$(pwd)/database/init.sql:/docker-entrypoint-initdb.d/init.sql:ro" \
  postgres:18-alpine
docker run -d --name api --network board-net \
  -e DB_HOST=db \
  -e DB_PASSWORD=board-lab-password \
  -e APP_ENV=development \
  -e GREETING="Hello from the hard way" \
  board-api:1.0
docker run -d --name web --network board-net -p 8080:80 board-web:1.0
```

<!-- test: retry=30; contains=Hello from the hard way -->
```bash
curl -s http://localhost:8080/api/messages
```

Your message is still there. Every container is new, but the database files lived in the `board-data` volume.
`init.sql` did **not** run again: the database was not empty, so PostgreSQL skipped initialisation.

Notice how long those commands are. Three containers, a network, a volume, a bind mount, nine environment variables,
and a start order to remember. Imagine ten services. That is why the next lab introduces Docker Compose.

## Break it

Don't fix it yet; we break it on purpose. Remove `api` and `web`, then start **web first**:

```bash
docker rm -f web api
docker run -d --name web --network board-net -p 8080:80 board-web:1.0
```

<!-- test-run: sleep 3 -->

<!-- test: fail; retry=5 -->
```bash
curl -s -f http://localhost:8080
```

The browser cannot connect. `docker run` printed a container ID, so it started... didn't it?

## Troubleshoot it

1. **Observe:** is `web` running?

   <!-- test: retry=5; contains=Exited -->
   ```bash
   docker ps -a --filter name=web --format "{{.Names}}: {{.Status}}"
   ```

   `Exited (1)`. It started and stopped immediately.
2. **Investigate:** a stopped container still has its logs:

   <!-- test: contains=host not found in upstream -->
   ```bash
   docker logs web
   ```

   `nginx: [emerg] host not found in upstream "api"`.
3. **Root cause:** nginx looks up the name `api` **once, when it starts**. There was no container called `api` on the
   network, so nginx refused to start. Order matters: dependencies must exist before the services that use them.
4. **Fix:** start the API, then start the existing `web` container again:

   ```bash
   docker run -d --name api --network board-net \
     -e DB_HOST=db \
     -e DB_PASSWORD=board-lab-password \
     -e APP_ENV=development \
     -e GREETING="Hello from the hard way" \
     board-api:1.0
   docker start web
   ```

5. **Verify:**

   <!-- test: retry=30; contains=database":"ok -->
   ```bash
   curl -s http://localhost:8080/api/health
   ```

The same symptom, caused by networks instead of order, is [troubleshooting/03](../../troubleshooting/03-containers-cannot-communicate/README.md).

## Challenge

**Task:** change the API's greeting without rebuilding any image.

**Requirements:**
- `/api/info` must return the greeting `Configured at run time`.
- Do not run `docker build`. Do not touch the database.

**Hints:** environment variables are set when a container is **created**, so you need a new `api` container.
nginx remembers the API's IP address from the moment it started; what does that mean for `web` after you replace `api`?

**Expected result:** `curl -s http://localhost:8080/api/info` contains `Configured at run time`.

<details><summary>Solution</summary>

```bash
docker rm -f api
docker run -d --name api --network board-net \
  -e DB_HOST=db \
  -e DB_PASSWORD=board-lab-password \
  -e APP_ENV=development \
  -e GREETING="Configured at run time" \
  board-api:1.0
docker restart web
```

<!-- test: retry=30; contains=Configured at run time -->
```bash
curl -s http://localhost:8080/api/info
```

**Explanation:** the image is the same; only the configuration changed. That is the point of environment variables:
one image, many configurations. `docker restart web` makes nginx look up the name `api` again, because the new
container may have a different IP address than the old one.

</details>

## Verify

- [ ] I started three containers that talk to each other by name on one network.
- [ ] I can explain which container publishes a port and why only that one.
- [ ] I can explain the job of the volume and of the `init.sql` bind mount.
- [ ] I replaced every container and the data survived.
- [ ] I can diagnose a container that exits at start-up with `docker ps -a` and `docker logs`.

## Clean up

Removing the volume deletes the database. Do it only when you are done with this lab:

```bash
docker rm -f web api db
docker network rm board-net
docker volume rm board-data
```

Keep the images if you want; Lab 13 builds its own.

## Next

- Next lab: [Lab 13 · Docker Compose](../13-docker-compose/README.md)
- Concept lessons: [docs/14-networking.md](../../docs/14-networking.md), [docs/15-docker-compose.md](../../docs/15-docker-compose.md)
