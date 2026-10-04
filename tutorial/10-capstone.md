# Chapter 10 · The capstone: build it, break it, fix it

> **Where you are:** you have practised every Docker building block on its own.
> **In this chapter:** you build and operate one complete application that uses all of them together, the way you
> would at work. Twenty steps, from `git clone` to a clean shutdown.
> **Time:** about 90 minutes.

```text
                         Browser  (http://localhost:8080)
                            |
                            | the only published port: 8080
                            v
          +-----------------+------------------+
          |  web            nginx, non-root    |  network: frontend
          |  docker-from-zero/web:1.0.0        |
          +-----------------+------------------+
                            | /api/  ->  http://api:5000
                            v
          +-----------------+------------------+
          |  api            Python, uid 10001  |  networks: frontend + backend
          |  read-only, 256 MiB, 0.5 CPU       |  password: /run/secrets/db_password
          +-----------------+------------------+
                            | db:5432
                            v
          +-----------------+------------------+
          |  db             postgres:18-alpine |  network: backend only
          +-----------------+------------------+
                            |
                            v
                  volume  capstone_db-data
```

Every box, line and label in this picture is something you learned. In this chapter you will check each of them with
your own commands.

## Step 1 · Clone the repository

If you have followed the course, you already have it. On a fresh machine:

<!-- test: skip -->
```bash
git clone https://github.com/sufyanahmadkamboh/sufyan-devops-docker-from-zero.git
cd sufyan-devops-docker-from-zero
```

## Step 2 · Enter the capstone directory

```bash
cd capstone
```

## Step 3 · Inspect the files

Never run something you have not looked at. Let's see what is here:

<!-- test: output; contains=docker-compose.yml; contains=verify.sh -->
```bash
ls
ls app/api app/web database secrets
```

```text
README.md
app
database
docker-compose.hub.yml
docker-compose.yml
secrets
verify.sh
app/api:
Dockerfile
app.py
requirements.txt

app/web:
Dockerfile
default.conf.template
html

database:
init.sql

secrets:
db_password.txt
db_password.txt.example
```

| File | Role |
|---|---|
| `app/web/` | the web image: nginx config template + the HTML page |
| `app/api/` | the API image: `app.py`, `requirements.txt`, multi-stage `Dockerfile` |
| `database/init.sql` | creates the `messages` table the first time the database starts |
| `secrets/db_password.txt.example` | an example password file; the real one is never committed |
| `.env.example` | settings you can change without editing the Compose file |
| `docker-compose.yml` | the whole application |
| `verify.sh` | an automatic check of everything this chapter checks by hand |

## Step 4 · Understand the Dockerfiles

Let's look at the important lines of the API's Dockerfile:

<!-- test: output; contains=AS builder; contains=USER app; contains=HEALTHCHECK -->
```bash
grep -nE "^(FROM|COPY|RUN|USER|HEALTHCHECK|CMD)" app/api/Dockerfile
```

```text
4:FROM python:3.14-slim AS builder
5:RUN python -m venv /opt/venv
6:COPY requirements.txt .
7:RUN /opt/venv/bin/pip install --no-cache-dir -r requirements.txt
10:FROM python:3.14-slim
11:COPY --from=builder /opt/venv /opt/venv
16:COPY app.py .
19:RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin app
20:USER app
25:HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
28:CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--preload", "--access-logfile", "-", "app:app"]
```

How to read it:

- **Two `FROM` lines = a multi-stage build.** The `builder` stage installs the Python packages into `/opt/venv`.
  The second stage starts clean and copies only that folder (`COPY --from=builder`). Nothing used for building ends up
  in the final image.
- **`COPY requirements.txt` before `COPY app.py`**: the slow `pip install` layer stays cached when only code changes.
- **`USER app`**: the process runs as uid 10001, not root.
- **`HEALTHCHECK`**: every 10 seconds Docker calls `/api/health` inside the container. The result shows up in
  `docker ps` as `healthy` or `unhealthy`, and Compose uses it to decide when the next service may start.
- **`CMD`**: gunicorn, a production web server for Python, with two worker processes.

The web image is short:

<!-- test: output; contains=nginx-unprivileged -->
```bash
cat app/web/Dockerfile
```

```text
# Capstone web image: nginx that runs as a normal user (uid 101), listening on 8080.
FROM nginxinc/nginx-unprivileged:1.30-alpine
ENV API_HOST=api
COPY default.conf.template /etc/nginx/templates/default.conf.template
COPY html/ /usr/share/nginx/html/
EXPOSE 8080
HEALTHCHECK --interval=10s --timeout=3s --retries=3 \
  CMD wget -q -O /dev/null http://127.0.0.1:8080/ || exit 1
```

`nginx-unprivileged` is the official nginx image variant that runs as a normal user. A normal user may not open ports
below 1024, which is why it listens on **8080** instead of 80.

## Step 5 · Understand the Compose file

Open `docker-compose.yml` in your editor and read it with this table next to it:

| Setting | Where | What it does | Chapter |
|---|---|---|---|
| `ports: "${WEB_PORT:-8080}:8080"` | web | the only port published to your computer (8080 unless `.env` says otherwise) | 2 |
| `networks: [frontend]` / `[frontend, backend]` / `[backend]` | all | web↔api and api↔db can talk; web cannot reach db at all | 5 |
| `depends_on: condition: service_healthy` | web, api | start only after the dependency's health check passes | 6, 7 |
| `secrets: [db_password]` + `*_PASSWORD_FILE` | api, db | the password arrives as a file in `/run/secrets/`, not as an env variable | 8 |
| `read_only: true` + `tmpfs: [/tmp]` | api | the container cannot modify its own files, except a small in-memory `/tmp` | 8 |
| `deploy.resources.limits` | api, db | at most 256 MiB / 0.5 CPU for the API, 512 MiB for the database | 7 |
| `volumes: db-data:/var/lib/postgresql` | db | the database files live on a named volume | 4 |
| `./database/init.sql:...:ro` | db | a read-only bind mount of the init script | 4 |
| `healthcheck: pg_isready` | db | the database's own readiness check | 7 |
| `restart: unless-stopped` | all | restart crashed containers automatically, unless you stopped them | 7 |

Let Compose check the file and list the services:

<!-- test: output; contains=web; contains=api; contains=db -->
```bash
docker compose config --services
```

```text
db
api
web
```

If you forget the next step, `docker compose config` will tell you: the secret file does not exist yet.

## Step 6 · Create the secret, then build the images

The password file is ignored by Git (see `.gitignore`), so every person creates their own:

```bash
cp secrets/db_password.txt.example secrets/db_password.txt
```

> In real life, put a long random value into that file. For this lab, the example value is fine.

Now build both images:

<!-- test: timeout=1200; output=tail:4 -->
```bash
docker compose build
```

```text
...
#24 [api] resolving provenance for metadata file
#24 DONE 0.0s
 Image docker-from-zero/web:1.0.0 Built 
 Image docker-from-zero/api:1.0.0 Built 
```

<!-- test: output; contains=docker-from-zero/api; contains=docker-from-zero/web -->
```bash
docker images --filter "reference=docker-from-zero/*"
```

```text
IMAGE                        ID             DISK USAGE   CONTENT SIZE   EXTRA
docker-from-zero/api:1.0.0   861de5936573        247MB         58.8MB        
docker-from-zero/web:1.0.0   b976402ef15f       81.5MB         23.1MB        
```

Two images with proper names and versions (`1.0.0`), because the Compose file sets `image:` next to `build:`.

## Step 7 · Start the containers

<!-- test: timeout=600; output=tail:8 -->
```bash
docker compose up -d
```

```text
...
 Container capstone-db-1 Waiting 
 Container capstone-db-1 Healthy 
 Container capstone-api-1 Starting 
 Container capstone-api-1 Started 
 Container capstone-api-1 Waiting 
 Container capstone-api-1 Healthy 
 Container capstone-web-1 Starting 
 Container capstone-web-1 Started 
```

Read the output from top to bottom: networks, volume, then `db` starts and becomes **Healthy**, only then `api` starts
and becomes **Healthy**, only then `web` starts. That is `depends_on: condition: service_healthy` at work.

## Step 8 · Verify the containers

<!-- test: retry=30; output; contains=(healthy) -->
```bash
docker compose ps
```

```text
NAME             IMAGE                        COMMAND                  SERVICE   CREATED          STATUS                                     PORTS
capstone-api-1   docker-from-zero/api:1.0.0   "gunicorn --bind 0.0…"   api       13 seconds ago   Up 6 seconds (healthy)                     5000/tcp
capstone-db-1    postgres:18-alpine           "docker-entrypoint.s…"   db        13 seconds ago   Up 12 seconds (healthy)                    5432/tcp
capstone-web-1   docker-from-zero/web:1.0.0   "/docker-entrypoint.…"   web       13 seconds ago   Up Less than a second (health: starting)   0.0.0.0:8080->8080/tcp, [::]:8080->8080/tcp
```

All three should say `Up ... (healthy)` (`web` may show `health: starting` for a few seconds; run it again). Look at the
`PORTS` column: only `web` has a `0.0.0.0:8080->8080/tcp` mapping. `api` and `db` are not reachable from your computer.
Let's prove that, not just believe it:

<!-- test: fail -->
```bash
curl -s --max-time 3 http://localhost:5000/
```

Nothing listens on port 5000 of your computer. Good.

## Step 9 · Verify the networking

Compose created two networks:

<!-- test: output; contains=capstone_frontend; contains=capstone_backend -->
```bash
docker network ls --filter name=capstone
```

```text
NETWORK ID     NAME                DRIVER    SCOPE
005d2cac127c   capstone_backend    bridge    local
ff4d682895db   capstone_frontend   bridge    local
```

The API is on both, so it can reach the database by name:

<!-- test: retry=10; output; contains=api reaches db -->
```bash
docker compose exec -T api python -c "import socket; socket.create_connection(('db', 5432), 2); print('api reaches db:5432')"
```

```text
api reaches db:5432
```

The web container is only on `frontend`. It cannot even find the name `db`:

<!-- test: fail; contains=bad address -->
```bash
docker compose exec -T web wget -q -T 2 -O /dev/null http://db:5432/
```

`bad address 'db:5432'`: Docker's DNS on the frontend network has never heard of `db`. That is network isolation:
even if someone broke into the web container, the database is not reachable from there.

## Step 10 · Verify the application

Through the only public door, port 8080:

<!-- test: retry=20; output; contains="database":"ok" -->
```bash
curl -s http://localhost:8080/api/health
```

```text
{"database":"ok","status":"ok"}
```

<!-- test: output; contains=Hello from the capstone -->
```bash
curl -s http://localhost:8080/api/info
```

```text
{"app_env":"production","container_hostname":"80ca3e7d8d9c","database_host":"db","greeting":"Hello from the capstone"}
```

`container_hostname` is the short ID of the API container that answered. Now open <http://localhost:8080> in your
browser and add a message, or do it with curl:

<!-- test: output; contains="id" -->
```bash
curl -s -X POST -H "Content-Type: application/json" -d '{"text":"capstone persistence check"}' http://localhost:8080/api/messages
```

```text
{"id":2,"text":"capstone persistence check"}
```

## Step 11 · Verify database persistence

The real test of a volume: throw away every container and network, and see if the data is still there.

<!-- test: timeout=300; output=tail:6 -->
```bash
docker compose down
docker volume ls --filter name=capstone
```

```text
...
 Network capstone_frontend Removing 
 Network capstone_backend Removing 
 Network capstone_backend Removed 
 Network capstone_frontend Removed 
DRIVER    VOLUME NAME
local     capstone_db-data
```

Containers and networks are gone; `capstone_db-data` is still there. Start again:

<!-- test: timeout=600 -->
```bash
docker compose up -d
```

<!-- test: retry=30; output; contains=capstone persistence check -->
```bash
curl -s http://localhost:8080/api/messages
```

```text
[{"created_at":"2026-10-04T05:14:09.549015+00:00","id":1,"text":"Hello! This first message was created by database/init.sql."},{"created_at":"2026-10-04T05:14:31.186611+00:00","id":2,"text":"capstone persistence check"}]
```

New containers, same data. Note what did **not** happen: `init.sql` did not run again (there is still only one
"Hello!" row). The database image only runs init scripts when the volume is empty.

## Step 12 · Check the logs

<!-- test: output=tail:6 -->
```bash
docker compose logs api --tail 5
```

```text
api-1  | [2026-10-04 05:14:42 +0000] [7] [INFO] Booting worker with pid: 7
api-1  | [2026-10-04 05:14:42 +0000] [8] [INFO] Booting worker with pid: 8
api-1  | [2026-10-04 05:14:42 +0000] [1] [ERROR] Control server error: [Errno 30] Read-only file system: '/home/app'
api-1  | 127.0.0.1 - - [04/Oct/2026:05:14:47 +0000] "GET /api/health HTTP/1.1" 200 32 "-" "Python-urllib/3.14"
api-1  | 172.18.0.3 - - [04/Oct/2026:05:14:47 +0000] "GET /api/messages HTTP/1.1" 200 221 "-" "curl/8.19.0"
```

You see gunicorn starting and one line per request, including the health checks Docker runs every 10 seconds.

<!-- test: output=tail:5 -->
```bash
docker compose logs db --tail 4
```

```text
db-1  | 2026-10-04 05:14:35.978 UTC [1] LOG:  listening on IPv6 address "::", port 5432
db-1  | 2026-10-04 05:14:35.982 UTC [1] LOG:  listening on Unix socket "/var/run/postgresql/.s.PGSQL.5432"
db-1  | 2026-10-04 05:14:35.990 UTC [32] LOG:  database system was shut down at 2026-10-04 05:14:34 UTC
db-1  | 2026-10-04 05:14:35.996 UTC [1] LOG:  database system is ready to accept connections
```

The database says it is ready to accept connections. Run `docker compose logs db` without `--tail` and look near the
top of the latest start: "Database directory appears to contain a database; Skipping initialization". The volume
already had data, so `init.sql` was not run again.

## Step 13 · Inspect the containers

Let's confirm the security settings with evidence:

<!-- test: output; contains=user=app; contains=readonly=true; contains=memory=268435456 -->
```bash
docker inspect capstone-api-1 --format 'user={{.Config.User}} readonly={{.HostConfig.ReadonlyRootfs}} memory={{.HostConfig.Memory}} cpus={{.HostConfig.NanoCpus}}'
```

```text
user=app readonly=true memory=268435456 cpus=500000000
```

The health status Docker keeps for the API:

<!-- test: retry=20; output; contains=healthy -->
```bash
docker inspect capstone-api-1 --format '{{.State.Health.Status}}'
```

```text
healthy
```

And the proof that the password is not an environment variable:

<!-- test: output; absent=DB_PASSWORD= -->
```bash
docker inspect capstone-api-1 --format '{{range .Config.Env}}{{println .}}{{end}}' | grep DB_
```

```text
DB_HOST=db
DB_NAME=board
DB_USER=board
DB_PASSWORD_FILE=/run/secrets/db_password
```

Only `DB_PASSWORD_FILE=/run/secrets/db_password`, a path, not the password itself.

## Step 14 · Check resources

<!-- test: output; contains=capstone-api-1 -->
```bash
docker stats --no-stream capstone-web-1 capstone-api-1 capstone-db-1
```

```text
CONTAINER ID   NAME             CPU %     MEM USAGE / LIMIT     MEM %     NET I/O           BLOCK I/O     PIDS
aa8a7ad34c98   capstone-web-1   0.00%     11.19MiB / 15.35GiB   0.07%     2.2kB / 1.46kB    0B / 8.19kB   15
a34f2d326bd5   capstone-api-1   0.02%     63.21MiB / 256MiB     24.69%    6.39kB / 3.45kB   0B / 0B       3
5fc12a971921   capstone-db-1    0.08%     23.03MiB / 512MiB     4.50%     4.3kB / 3.14kB    0B / 28.7kB   9
```

The `LIMIT` column shows `256MiB` for the API and `512MiB` for the database, the limits from the Compose file.
The web container has no limit, so its limit is all the memory Docker has. (Adding one is a good exercise.)

## Step 15 · Break something

Don't fix it yet. We break it on purpose. A database server goes down:

<!-- test: output -->
```bash
docker compose stop db
```

```text
 Container capstone-db-1 Stopping 
 Container capstone-db-1 Stopped 
```

Look at the application from the user's side:

<!-- test: retry=15; output; contains="status":"error" -->
```bash
curl -s http://localhost:8080/api/health
```

```text
{"database":"failed to resolve host 'db': [Errno -2] Name or service not known","status":"error"}
```

The page still loads, but the API reports an error, and the browser shows no messages.

## Step 16 · Troubleshoot it

Before changing anything, let's investigate. **What is the symptom?** The API answers, but cannot use the database.
**What should we check first?** The state of every service:

<!-- test: retry=20; output; contains=Exited -->
```bash
docker compose ps -a
```

```text
NAME             IMAGE                        COMMAND                  SERVICE   CREATED          STATUS                            PORTS
capstone-api-1   docker-from-zero/api:1.0.0   "gunicorn --bind 0.0…"   api       20 seconds ago   Up 14 seconds (healthy)           5000/tcp
capstone-db-1    postgres:18-alpine           "docker-entrypoint.s…"   db        20 seconds ago   Exited (0) 4 seconds ago          
capstone-web-1   docker-from-zero/web:1.0.0   "/docker-entrypoint.…"   web       20 seconds ago   Up 8 seconds (health: starting)   0.0.0.0:8080->8080/tcp, [::]:8080->8080/tcp
```

`db` has exited. Wait 30 seconds and look again: after three failed health checks the API is also marked `unhealthy`,
because its health check calls `/api/health`, which needs the database. Docker's health status tells you which part
is broken; the logs tell you why:

<!-- test: output=tail:4 -->
```bash
docker compose logs db --tail 3
```

```text
db-1  | 2026-10-04 05:14:51.109 UTC [30] LOG:  checkpoint starting: shutdown immediate
db-1  | 2026-10-04 05:14:51.124 UTC [30] LOG:  checkpoint complete: wrote 1 buffers (0.0%), wrote 3 SLRU buffers; 0 WAL file(s) added, 0 removed, 0 recycled; write=0.004 s, sync=0.004 s, total=0.018 s; sync files=3, longest=0.002 s, average=0.002 s; distance=0 kB, estimate=0 kB; lsn=0/1BFAFE8, redo lsn=0/1BFAFE8
db-1  | 2026-10-04 05:14:51.133 UTC [1] LOG:  database system is shut down
```

The database log ends with a normal, clean shutdown ("database system is shut down"). It did not crash; someone
stopped it. **Root cause:** the `db` container is stopped. (Remember `restart: unless-stopped`: Docker restarts crashed
containers, but not containers you stopped on purpose.)

## Step 17 · Fix it

<!-- test: output -->
```bash
docker compose start db
```

```text
 Container capstone-db-1 Starting 
 Container capstone-db-1 Started 
```

## Step 18 · Restart everything

After an incident it is good practice to restart cleanly and watch everything come back:

<!-- test: timeout=300; output -->
```bash
docker compose restart
```

```text
 Container capstone-web-1 Restarting 
 Container capstone-db-1 Restarting 
 Container capstone-api-1 Restarting 
 Container capstone-db-1 Started 
 Container capstone-web-1 Started 
 Container capstone-api-1 Started 
```

<!-- test: retry=30; contains="database":"ok" -->
```bash
curl -s http://localhost:8080/api/health
```

## Step 19 · Verify everything

You have checked everything by hand. `verify.sh` runs the same checks automatically, including a full `down` + `up`
persistence test. Read the script once; every check is one line you could type yourself.

<!-- test: timeout=600; output; contains=All checks passed -->
```bash
./verify.sh --persistence
```

```text
1. Containers (docker compose ps, docker inspect)
  PASS  capstone-web-1 is running and healthy
  PASS  capstone-api-1 is running and healthy
  PASS  capstone-db-1 is running and healthy
2. Ports (only the web container is published)
  PASS  web page answers on http://localhost:8080
  PASS  API is NOT published on localhost:5000
  PASS  database is NOT published on localhost:5432
3. Application (browser -> web -> api -> db)
  PASS  GET /api/health says the database is ok
  PASS  POST /api/messages stores a message
  PASS  GET /api/messages returns it
4. Networks (frontend: web+api, backend: api+db)
  PASS  api can reach db (same backend network)
  PASS  web can NOT even resolve db (different network)
5. Security basics
  PASS  api runs as a normal user (uid 10001, not root)
  PASS  web runs as a normal user (not root)
  PASS  api filesystem is read-only
  PASS  password is not in the api's environment variables
  PASS  api memory limit is 256 MiB
6. Data on a volume (docker volume inspect capstone_db-data)
  PASS  volume capstone_db-data exists
   docker compose down  (containers and networks are removed, the volume is kept)
  PASS  after down + up, the message verify-1791090914 is still there

All checks passed.
```

Every line should say `PASS`. If one says `FAIL`, you know the drill: `docker compose ps -a`, then
`docker compose logs <service>`.

> **Windows:** run `verify.sh` in WSL2 or Git Bash, not in PowerShell.

## Step 20 · Clean up

Stop and remove the containers and networks, but keep the data:

<!-- test: output -->
```bash
docker compose down
```

```text
 Container capstone-web-1 Stopping 
 Container capstone-web-1 Stopped 
 Container capstone-web-1 Removing 
 Container capstone-web-1 Removed 
 Container capstone-api-1 Stopping 
 Container capstone-api-1 Stopped 
 Container capstone-api-1 Removing 
 Container capstone-api-1 Removed 
 Container capstone-db-1 Stopping 
 Container capstone-db-1 Stopped 
 Container capstone-db-1 Removing 
 Container capstone-db-1 Removed 
 Network capstone_frontend Removing 
 Network capstone_backend Removing 
 Network capstone_backend Removed 
 Network capstone_frontend Removed 
```

The next `docker compose up -d` starts exactly where you left off. When you want a completely fresh start, remove the
volume too, and with it every message:

<!-- test: output -->
```bash
docker compose down -v
```

```text
 Volume capstone_db-data Removing 
 Volume capstone_db-data Removed 
```

> **Warning:** `down -v` deletes the database volume `capstone_db-data`. On a real system, this is the moment you stop
> and ask yourself whether there is a backup.

The images stay on your machine (`docker images --filter "reference=docker-from-zero/*"`). Remove them with
`docker rmi docker-from-zero/web:1.0.0 docker-from-zero/api:1.0.0` when you no longer need them.

## What you built

| You used | Where in the capstone |
|---|---|
| Dockerfile, custom image, tags | `app/api/Dockerfile`, `app/web/Dockerfile`, `docker-from-zero/*:1.0.0` |
| Layers and build cache | `requirements.txt` copied before the code |
| `.dockerignore` | `app/api/.dockerignore`, `app/web/.dockerignore` |
| Multi-stage build, small base images | `builder` stage, `python:3.14-slim`, `nginx-unprivileged:1.30-alpine` |
| Containers, ports | three services, one published port |
| Environment variables | `APP_ENV`, `GREETING`, `DB_HOST`, `.env.example` |
| Networking and DNS | `frontend` / `backend`, names `api` and `db` |
| Volumes and bind mounts | `capstone_db-data`, `init.sql:ro` |
| Docker Compose | `docker-compose.yml` |
| Logs, exec, inspect, stats | steps 8 to 16 |
| Security basics | non-root users, read-only API, secrets as files, isolation, limits |
| Troubleshooting | steps 15 to 18 |

## Where would I use this as a DevOps engineer?

This is the shape of most web applications you will meet: a front end, an API and a database, packaged as images,
wired together by configuration, with data on volumes and secrets kept out of images. The tools change with scale
(Kubernetes, cloud services), the questions you asked in this chapter do not: which ports are open, who can talk to
whom, where is the data, which user runs the process, what happens when one part fails.

## What you learned

- How every concept in this course fits into one real application.
- How to verify a running system with evidence instead of assumptions.
- How health checks, dependencies and restart policies behave when a part fails.
- How to shut down safely without losing data, and how to reset on purpose.

## Try it yourself

1. Create a `.env` file from `.env.example`, change `WEB_PORT` to `8090` and `GREETING` to your name. Run
   `docker compose up -d`. Which containers were recreated, and why only those?
2. Add a memory limit to the `web` service and confirm it with `docker stats --no-stream`.
3. Change the text in `app/web/html/index.html`. What do you need to run to see it in the browser?
4. Start the stack with a different password in `secrets/db_password.txt` **after** the database was already
   initialised. What happens, and why? (Hint: init only runs on an empty volume.)

## Next

Check what you know: [Chapter 11 · Knowledge check](11-knowledge-check.md).
