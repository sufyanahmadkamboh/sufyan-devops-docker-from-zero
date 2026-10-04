# Capstone · The Message Board, built the way you would build it at work

> Everything from the labs in one project · about 60 minutes · you need labs 01-18 (or the tutorial chapters 00-08)

This is the final project. There is nothing new to learn here. Instead, every Docker skill from this repository comes
together in one small application, and you prove that you can run it, check it, break it, fix it and clean it up.

The guided, step-by-step walkthrough is [tutorial/10-capstone.md](../tutorial/10-capstone.md). This page is the
reference: what is in the folder, why each line is there, and the commands to run it.

## Architecture

```text
                         You (browser / curl)
                                 |
                                 |  http://localhost:8080     (the ONLY published port)
                                 v
   +---------------------------- frontend network ----------------------------+
   |   web  (nginx, non-root, port 8080)  ---- /api/ ---->  api  (Python)      |
   +--------------------------------------------------------|----------------+
                                                            |
   +---------------------------- backend network -----------|----------------+
   |                                                        v                 |
   |                                  db  (PostgreSQL 18, port 5432)          |
   +--------------------------------------------------------|----------------+
                                                            |
                                                            v
                                            volume  capstone_db-data
                                            (the messages live here)
```

* The **web** container can talk to **api**, but not to **db**: they share no network.
* Only **web** is published on your computer. The API and the database are reachable only by other containers.
* The database password is a **secret file**, not an environment variable.

## What is in this folder

| Path | What it is | Lessons it uses |
|---|---|---|
| `app/web/Dockerfile` | nginx that runs as a normal user, with a `HEALTHCHECK` | Dockerfile, security, healthchecks |
| `app/web/default.conf.template` | nginx config; `${API_HOST}` is filled from an environment variable | environment variables, networking |
| `app/web/html/` | the page: plain HTML, CSS and a little JavaScript | |
| `app/api/Dockerfile` | multi-stage build, `USER app`, `HEALTHCHECK` | layers, cache, optimization, security |
| `app/api/app.py` | the API (about 100 lines); reads its settings from environment variables or secret files | environment variables |
| `database/init.sql` | creates the `messages` table the first time the database starts | bind mounts, volumes |
| `docker-compose.yml` | the whole system: 3 services, 2 networks, 1 volume, 1 secret | Compose, networking, volumes, resources |
| `secrets/db_password.txt.example` | an example password; copy it to `secrets/db_password.txt` | security |
| `.env.example` | settings you can change without editing the Compose file | environment variables |
| `verify.sh` | 18 automatic checks of the running system | inspect, logs, troubleshooting |

## The Compose file, line by line

Open [docker-compose.yml](docker-compose.yml) next to this table.

| Line | Why it is there |
|---|---|
| `name: capstone` | Fixes the project name, so containers are always `capstone-web-1`, `capstone-api-1`, `capstone-db-1` and the volume is always `capstone_db-data`, whatever the folder is called. |
| `build:` + `image:` | Compose builds the image from the folder and tags it `docker-from-zero/web:1.0.0`, a name you can push to a registry later. |
| `ports: "${WEB_PORT:-8080}:8080"` | Publishes only the web container. `${WEB_PORT:-8080}` means "use WEB_PORT from `.env`, or 8080". |
| `networks: [frontend]` / `[frontend, backend]` / `[backend]` | Two networks: the web container and the database never share one. |
| `depends_on: ... condition: service_healthy` | Start the API only after the database is healthy, and the web only after the API is healthy. |
| `secrets: [db_password]` | The password file appears inside the container as `/run/secrets/db_password`. It is not visible in `docker inspect`. |
| `DB_PASSWORD_FILE` / `POSTGRES_PASSWORD_FILE` | Tell the API and PostgreSQL to read the password from that file. |
| `read_only: true` + `tmpfs: [/tmp]` | The API cannot change its own files. Only a small in-memory `/tmp` is writable. |
| `deploy.resources.limits` | The API may use at most 256 MiB of memory and half a CPU; the database at most 512 MiB. |
| `healthcheck` (db) | Docker runs `pg_isready` every 5 seconds; `docker compose ps` shows `(healthy)`. |
| `restart: unless-stopped` | If a container crashes, Docker starts it again (unless you stopped it yourself). |
| `volumes: db-data:/var/lib/postgresql` | The database files live on a named volume, so they survive `docker compose down`. PostgreSQL 18 needs the parent folder, not `/var/lib/postgresql/data` (see [troubleshooting/10](../troubleshooting/10-database-data-disappears/README.md)). |
| `./database/init.sql:/docker-entrypoint-initdb.d/init.sql:ro` | A read-only bind mount: PostgreSQL runs this file once, when the volume is still empty. |

## Run it

All commands run from the repository root.

Step 1. Go to the capstone folder and create the secret file from the example (only once):

```bash
cd capstone
cp secrets/db_password.txt.example secrets/db_password.txt
```

`secrets/db_password.txt` is listed in `.gitignore`, so your real password is never committed. In a real project you
would put a long random value in it.

Step 2. Build the images and start everything in the background:

<!-- test: timeout=600; contains=capstone-web-1 -->
```bash
docker compose up -d --build
```

The first build downloads the base images and takes a minute or two. Compose then creates the networks, the volume and
the three containers, and waits for each health check before starting the next service.

Step 3. Look at what is running:

<!-- test: retry=30; contains=(healthy); output -->
```bash
docker compose ps --format 'table {{.Name}}\t{{.Status}}\t{{.Ports}}'
docker compose ps | grep -q 'capstone-web-1.*(healthy)'
```

```text
(output appears here when the tests run)
```

All three containers should be `Up` and `(healthy)`. Only `capstone-web-1` shows a published port
(`0.0.0.0:8080->8080/tcp`). The other two only have container ports.

Step 4. Open <http://localhost:8080> in your browser, or ask with curl:

<!-- test: retry=15; contains="database":"ok"; output -->
```bash
curl -s http://localhost:8080/api/health
```

```text
(output appears here when the tests run)
```

<!-- test: contains=Hello from the capstone; output -->
```bash
curl -s http://localhost:8080/api/info
```

```text
(output appears here when the tests run)
```

Step 5. Add a message and read the list back:

<!-- test: contains=written by the capstone README -->
```bash
curl -s -X POST -H 'Content-Type: application/json' -d '{"text":"written by the capstone README"}' http://localhost:8080/api/messages
curl -s http://localhost:8080/api/messages
```

Step 6. Let the checks prove the rest (networks, non-root users, read-only filesystem, secrets, limits, and that the
data survives `docker compose down`):

<!-- test: timeout=300; contains=All checks passed.; output -->
```bash
./verify.sh --persistence
```

```text
(output appears here when the tests run)
```

On Windows, run `verify.sh` from WSL2 or Git Bash (it is a bash script).

## Investigate it

These are the commands from the labs, pointed at the capstone.

<!-- test: contains=capstone_frontend; contains=capstone_backend -->
```bash
docker network ls --filter name=capstone
docker volume ls --filter name=capstone
```

Which containers are on which network?

<!-- test: contains=capstone-web-1; output -->
```bash
docker network inspect capstone_frontend --format '{{range .Containers}}{{.Name}} {{end}}'
docker network inspect capstone_backend --format '{{range .Containers}}{{.Name}} {{end}}'
```

```text
(output appears here when the tests run)
```

The frontend network holds web and api; the backend network holds api and db.

Who is the API running as, and what are its limits?

<!-- test: contains=10001; output -->
```bash
docker compose exec api id
docker inspect capstone-api-1 --format 'memory limit: {{.HostConfig.Memory}} bytes, read-only: {{.HostConfig.ReadonlyRootfs}}'
```

```text
(output appears here when the tests run)
```

How much are they using right now?

<!-- test: output -->
```bash
docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}'
```

```text
(output appears here when the tests run)
```

The last lines the API wrote:

<!-- test: output=tail:5 -->
```bash
docker compose logs --tail 5 api
```

```text
(output appears here when the tests run)
```

## Break it, then fix it

Stop the database. Do not restart it yet.

```bash
docker compose stop db
```

Before changing anything, let's investigate. What does a user see?

<!-- test: retry=10; contains="status":"error" -->
```bash
curl -s http://localhost:8080/api/health
```

The API answers, but with `"status":"error"` and HTTP 503. So the web container and the API are fine. The problem is
behind the API. Ask Docker what it thinks:

<!-- test: contains=Exited -->
```bash
docker compose ps -a --format 'table {{.Name}}\t{{.Status}}'
```

`capstone-db-1` is `Exited`. Within half a minute the API's health check also turns `(unhealthy)`, because
`/api/health` checks the database. Root cause: the database container is not running. Fix it and verify:

<!-- test: timeout=120 -->
```bash
docker compose start db
```

<!-- test: retry=40; contains="database":"ok" -->
```bash
curl -s http://localhost:8080/api/health
```

The message you wrote earlier is still there, because it lives on the volume, not in the container:

<!-- test: contains=written by the capstone README -->
```bash
curl -s http://localhost:8080/api/messages
```

More scenarios to practise on this exact stack are in [troubleshooting/](../troubleshooting/README.md) (03, 06 and 10
use the same application).

## Clean up

`down` removes the containers and the networks. The volume (your messages) stays:

```bash
docker compose down
docker volume ls --filter name=capstone
```

To delete the data as well, add `-v`. Only do this when you really want an empty database next time:

```bash
docker compose down -v
```

## Use the published images instead of building

The images of this capstone are published on Docker Hub as `sufibaba6629/docker-from-zero-web:1.0.0` and
`sufibaba6629/docker-from-zero-api:1.0.0`, for Intel/AMD and ARM (Apple Silicon) computers.
[docker-compose.hub.yml](docker-compose.hub.yml) runs the same system from those images, without building anything:

<!-- test: timeout=300; contains=capstone-web-1 -->
```bash
docker compose -f docker-compose.hub.yml up -d
```

<!-- test: retry=40; contains="database":"ok" -->
```bash
curl -s http://localhost:8080/api/health
```

```bash
docker compose -f docker-compose.hub.yml down -v
```

## What this capstone proves you can do

- [ ] write Dockerfiles with a good layer order, a multi-stage build, a non-root user and a health check
- [ ] describe a multi-container system in one Compose file and start it with one command
- [ ] connect containers with networks, and keep containers that should not talk apart
- [ ] keep data on a named volume and prove that it survives
- [ ] configure containers with environment variables, a `.env` file and secret files
- [ ] limit memory and CPU, and check usage with `docker stats`
- [ ] investigate with `docker compose ps`, `logs`, `exec`, `inspect` and `network inspect`
- [ ] break a running system on purpose, find the root cause from evidence, fix it and verify

Next: [tutorial/11-knowledge-check.md](../tutorial/11-knowledge-check.md)
