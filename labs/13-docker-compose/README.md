# Lab 13 · Docker Compose

> Goal: start the whole message board (web + api + database + volume) with one command, and understand exactly what
> Compose creates for you. · Time: 45 minutes · You need: labs 09 (volumes), 11 (networking) and 12 (multi-container by hand).

In lab 12 you started three containers by hand: one network, one volume, and three long `docker run` commands that
had to be typed in the right order with the right flags. It worked, but imagine doing that every morning, or explaining
it to a new colleague.

Docker Compose solves exactly this. You describe the containers, networks and volumes **once**, in a file called
`docker-compose.yml`, and Compose turns that description into real Docker objects. Same Docker underneath: Compose
just types the `docker run` commands for you.

## What you will learn

- How to read a `docker-compose.yml` file, line by line
- `docker compose up`, `ps`, `logs`, `exec`, `restart`, `build`, `down`
- What Compose creates: containers, a network and a volume, and how it names them
- Why `docker compose down` keeps your data, and `docker compose down -v` deletes it
- How to investigate when one service of the stack is broken

## Step 1 · Go to the application and read the Compose file

From the repository root:

```bash
cd examples/multi-container-app
ls
```

You see three folders (`web`, `api`, `database`) and one file, `docker-compose.yml`. Let's read it:

<!-- test: output; contains=services -->
```bash
cat docker-compose.yml
```

```text
# The message board, described once and started with one command:
#   docker compose up -d --build
# Compose creates: 3 containers, 1 network (<project>_default), 1 volume (<project>_db-data).

services:
  web:
    build: ./web
    ports:
      - "8080:80"          # browser -> http://localhost:8080
    depends_on:
      - api

  api:
    build: ./api
    environment:
      APP_ENV: development
      GREETING: Hello from Docker Compose
      DB_HOST: db          # the service name below is also its DNS name
      DB_NAME: board
      DB_USER: board
      DB_PASSWORD: board-lab-password   # fine for a local lab; the capstone uses a secret file instead
    depends_on:
      - db

  db:
    image: postgres:18-alpine
    environment:
      POSTGRES_DB: board
      POSTGRES_USER: board
      POSTGRES_PASSWORD: board-lab-password
    volumes:
      - db-data:/var/lib/postgresql                          # named volume: the data survives "down"
      - ./database/init.sql:/docker-entrypoint-initdb.d/init.sql:ro   # bind mount: runs once on first start

volumes:
  db-data:
```

Here is every important line, from top to bottom:

| Line | What it means |
|---|---|
| `services:` | The list of containers this application needs. Each service becomes (at least) one container. |
| `web:` / `api:` / `db:` | The service names. They are also the **DNS names** the containers use to find each other. |
| `build: ./web` | Build an image from the Dockerfile in the `web` folder (like `docker build ./web`). |
| `ports: - "8080:80"` | Publish container port 80 on host port 8080 (like `-p 8080:80`). Only `web` has this. |
| `depends_on: - api` | Start `api` before `web`. It only controls the **start order**, not "wait until ready". |
| `environment:` | Environment variables for the container (like `-e DB_HOST=db`). |
| `DB_HOST: db` | The API finds the database by its service name `db`. No IP addresses anywhere. |
| `image: postgres:18-alpine` | `db` is not built, it uses an existing image from Docker Hub. |
| `db-data:/var/lib/postgresql` | Mount the **named volume** `db-data` where PostgreSQL 18 keeps its data. |
| `./database/init.sql:/docker-entrypoint-initdb.d/init.sql:ro` | A **bind mount** of one file from your computer, read-only. PostgreSQL runs it the first time it starts with an empty volume. |
| `volumes: db-data:` (bottom) | Declares the named volume, so Compose creates it. |

Notice what is **not** in the file: no network. Compose creates one network for every project automatically and
connects every service to it.

Want to see the file the way Compose understands it, after filling in defaults? Ask Compose:

<!-- test: contains=web; contains=api; contains=db -->
```bash
docker compose config --services
```

```text
(output appears here when the tests run)
```

`docker compose config` is a good habit: if the file has a typo or bad indentation, this command tells you before
anything starts.

## Step 2 · Start everything

<!-- test: timeout=900; output=tail:12; contains=Started -->
```bash
docker compose up -d --build
```

```text
...
 Container multi-container-app-db-1 Creating 
 Container multi-container-app-db-1 Created 
 Container multi-container-app-api-1 Creating 
 Container multi-container-app-api-1 Created 
 Container multi-container-app-web-1 Creating 
 Container multi-container-app-web-1 Created 
 Container multi-container-app-db-1 Starting 
 Container multi-container-app-db-1 Started 
 Container multi-container-app-api-1 Starting 
 Container multi-container-app-api-1 Started 
 Container multi-container-app-web-1 Starting 
 Container multi-container-app-web-1 Started 
```

What happened, in order:

1. `--build` built the `web` and `api` images from their Dockerfiles (the first time this takes a minute).
2. Compose created a **network** and a **volume**.
3. Compose created and started the containers: `db` first, then `api`, then `web` (because of `depends_on`).
4. `-d` (detached) gave you your terminal back. Without `-d`, the logs of all three containers stream into your
   terminal and `Ctrl+C` stops everything.

## Step 3 · See what Compose created

<!-- test: retry=10; output; contains=multi-container-app-web-1; contains=multi-container-app-api-1; contains=multi-container-app-db-1 -->
```bash
docker compose ps
```

```text
NAME                        IMAGE                     COMMAND                  SERVICE   CREATED         STATUS                  PORTS
multi-container-app-api-1   multi-container-app-api   "gunicorn --bind 0.0…"   api       2 seconds ago   Up Less than a second   5000/tcp
multi-container-app-db-1    postgres:18-alpine        "docker-entrypoint.s…"   db        2 seconds ago   Up 1 second             5432/tcp
multi-container-app-web-1   multi-container-app-web   "/docker-entrypoint.…"   web       2 seconds ago   Up Less than a second   0.0.0.0:8080->80/tcp, [::]:8080->80/tcp
```

Look at the `NAME` column. Compose names every container `<project>-<service>-<number>`:

- The **project** name is the folder name: `multi-container-app`.
- The **service** is the name in the file: `web`, `api`, `db`.
- The **number** is `1` because there is one container per service.

The `PORTS` column shows that only `web` is published (`0.0.0.0:8080->80/tcp`). `api` and `db` show their port without
an arrow: reachable by the other containers, but not from your computer.

Now the network and the volume. These are normal Docker objects, so the normal commands show them:

<!-- test: output; contains=multi-container-app_default -->
```bash
docker network ls --filter name=multi-container-app
```

```text
NETWORK ID     NAME                          DRIVER    SCOPE
3871c31348df   multi-container-app_default   bridge    local
```

<!-- test: output; contains=multi-container-app_db-data -->
```bash
docker volume ls --filter name=multi-container-app
```

```text
DRIVER    VOLUME NAME
local     multi-container-app_db-data
```

The network is `<project>_default` and the volume is `<project>_<volume name>`. Compose puts the project name in front
of everything, so two projects can both have a volume called `db-data` without clashing.

## Step 4 · Use the application

The database needs a few seconds to initialise the first time. The health endpoint answers only when the API can talk
to the database:

<!-- test: retry=30; output; contains=ok -->
```bash
curl -fs http://localhost:8080/api/health
```

```text
{"database":"ok","status":"ok"}
```

`-f` makes curl fail on an HTTP error, so if you see `{"database":"ok","status":"ok"}` the whole chain works:
**your computer → web → api → db**.

Ask the API who it is:

<!-- test: retry=10; output; contains=Hello from Docker Compose -->
```bash
curl -s http://localhost:8080/api/info
```

```text
{"app_env":"development","container_hostname":"54908cbbc7d2","database_host":"db","greeting":"Hello from Docker Compose"}
```

The `greeting` and `app_env` come from the `environment:` section of the Compose file. `container_hostname` is the
short ID of the API container.

Add a message, then list all messages:

<!-- test: contains=written with compose -->
```bash
curl -s -X POST -H "Content-Type: application/json" -d '{"text":"written with compose"}' http://localhost:8080/api/messages
```

<!-- test: output; contains=init.sql; contains=written with compose -->
```bash
curl -s http://localhost:8080/api/messages
```

```text
[{"created_at":"2026-10-04T04:05:17.690148+00:00","id":1,"text":"Hello! This first message was created by database/init.sql."},{"created_at":"2026-10-04T04:05:18.932558+00:00","id":2,"text":"written with compose"}]
```

You see two messages: the first one was created by `database/init.sql`, the second one is yours.

Open <http://localhost:8080> in your browser too. It is the same data, shown as a page.

## Step 5 · Logs of the whole stack, or of one service

<!-- test: output=tail:8 -->
```bash
docker compose logs --tail 5
```

```text
...
db-1   | 2026-10-04 04:05:18.034 UTC [1] LOG:  listening on Unix socket "/var/run/postgresql/.s.PGSQL.5432"
db-1   | 2026-10-04 04:05:18.041 UTC [70] LOG:  database system was shut down at 2026-10-04 04:05:17 UTC
db-1   | 2026-10-04 04:05:18.047 UTC [1] LOG:  database system is ready to accept connections
web-1  | 172.18.0.1 - - [04/Oct/2026:04:05:17 +0000] "GET /api/health HTTP/1.1" 503 200 "-" "curl/8.19.0" "-"
web-1  | 172.18.0.1 - - [04/Oct/2026:04:05:18 +0000] "GET /api/health HTTP/1.1" 200 32 "-" "curl/8.19.0" "-"
web-1  | 172.18.0.1 - - [04/Oct/2026:04:05:18 +0000] "GET /api/info HTTP/1.1" 200 122 "-" "curl/8.19.0" "-"
web-1  | 172.18.0.1 - - [04/Oct/2026:04:05:18 +0000] "POST /api/messages HTTP/1.1" 201 39 "-" "curl/8.19.0" "-"
web-1  | 172.18.0.1 - - [04/Oct/2026:04:05:19 +0000] "GET /api/messages HTTP/1.1" 200 215 "-" "curl/8.19.0" "-"
```

Every line starts with the container name, so you can tell who said what. Usually you only care about one service:

<!-- test: output; contains=GET -->
```bash
docker compose logs api --tail 5
```

```text
api-1  | 172.18.0.4 - - [04/Oct/2026:04:05:17 +0000] "GET /api/health HTTP/1.1" 503 200 "-" "curl/8.19.0"
api-1  | 172.18.0.4 - - [04/Oct/2026:04:05:18 +0000] "GET /api/health HTTP/1.1" 200 32 "-" "curl/8.19.0"
api-1  | 172.18.0.4 - - [04/Oct/2026:04:05:18 +0000] "GET /api/info HTTP/1.1" 200 122 "-" "curl/8.19.0"
api-1  | 172.18.0.4 - - [04/Oct/2026:04:05:18 +0000] "POST /api/messages HTTP/1.1" 201 39 "-" "curl/8.19.0"
api-1  | 172.18.0.4 - - [04/Oct/2026:04:05:19 +0000] "GET /api/messages HTTP/1.1" 200 215 "-" "curl/8.19.0"
```

These are gunicorn's access log lines: one line per request the API answered, with the HTTP status code.

To follow the logs live (stop with `Ctrl+C`):

<!-- test: skip -->
```bash
docker compose logs -f api
```

## Step 6 · Run a command inside a service

`docker compose exec <service> <command>` is `docker exec` that uses the **service name** instead of the container name.
Let's ask PostgreSQL directly what is stored:

<!-- test: output; contains=written with compose -->
```bash
docker compose exec -T db psql -U board -d board -c "SELECT id, text FROM messages;"
```

```text
 id |                            text                             
----+-------------------------------------------------------------
  1 | Hello! This first message was created by database/init.sql.
  2 | written with compose
(2 rows)
```

`-T` means "do not allocate a terminal". You can leave it out when you type the command yourself; it matters in
scripts (and in the automated tests of this repository).

Now prove that the containers find each other **by name**: from inside the API container, resolve the name `db`.

<!-- test: output; contains=db -->
```bash
docker compose exec -T api python -c "import socket; print('db is', socket.gethostbyname('db'))"
```

```text
db is 172.18.0.2
```

That IP address belongs to the database container on the `multi-container-app_default` network. You never had to
know it: Docker's built-in DNS translated the name for you.

## Step 7 · Restart and rebuild

Restart one service (the container is stopped and started again, same container, same data):

<!-- test: contains=Started -->
```bash
docker compose restart api
```

<!-- test: retry=15; contains=ok -->
```bash
curl -fs http://localhost:8080/api/health
```

If you change the code of a service, rebuild its image and recreate only that container:

<!-- test: timeout=600; output=tail:6 -->
```bash
docker compose build api
docker compose up -d api
```

```text
...
 Image multi-container-app-api Built 
 Container multi-container-app-db-1 Running 
 Container multi-container-app-api-1 Recreate 
 Container multi-container-app-api-1 Recreated 
 Container multi-container-app-api-1 Starting 
 Container multi-container-app-api-1 Started 
```

Because nothing changed in the API code, every build step shows `CACHED` and Compose sees the container is already
up to date. Change `GREETING` in `docker-compose.yml`, run `docker compose up -d` again, and Compose recreates only
the `api` container, because only its configuration changed.

## Step 8 · down keeps the data, down -v deletes it

Stop and remove everything:

<!-- test: output; contains=Removed -->
```bash
docker compose down
```

```text
 Container multi-container-app-web-1 Stopping 
 Container multi-container-app-web-1 Stopped 
 Container multi-container-app-web-1 Removing 
 Container multi-container-app-web-1 Removed 
 Container multi-container-app-api-1 Stopping 
 Container multi-container-app-api-1 Stopped 
 Container multi-container-app-api-1 Removing 
 Container multi-container-app-api-1 Removed 
 Container multi-container-app-db-1 Stopping 
 Container multi-container-app-db-1 Stopped 
 Container multi-container-app-db-1 Removing 
 Container multi-container-app-db-1 Removed 
 Network multi-container-app_default Removing 
 Network multi-container-app_default Removed 
```

Read the output carefully: containers **removed**, network **removed**. The volume is not in the list. Check:

<!-- test: contains=multi-container-app_db-data -->
```bash
docker volume ls --filter name=multi-container-app
```

Start the stack again. There is no `--build` this time: the images already exist.

<!-- test: timeout=300; contains=Started -->
```bash
docker compose up -d
```

<!-- test: retry=30; contains=written with compose -->
```bash
curl -s http://localhost:8080/api/messages
```

Your message is still there. The containers are brand new, but they mounted the same volume, so the database found
its old files. **Containers are disposable, volumes are not.**

Now the dangerous one. `-v` means "also remove the volumes declared in this file":

<!-- test: contains=Removed -->
```bash
docker compose down -v
```

<!-- test: absent=multi-container-app_db-data -->
```bash
docker volume ls --filter name=multi-container-app
```

The volume is gone, and with it every message. Next time you run `up`, `init.sql` runs again and you start from one
message. Use `down -v` when you **want** a fresh database; never as a habit.

## Break it

Let's start the stack again and then take the database away while the application is running.

<!-- test: timeout=300; contains=Started -->
```bash
docker compose up -d
```

<!-- test: retry=30; contains=ok -->
```bash
curl -fs http://localhost:8080/api/health
```

<!-- test: contains=Stopped -->
```bash
docker compose stop db
```

Now call the health endpoint again. Don't fix anything yet, we broke it on purpose.

<!-- test: fail -->
```bash
curl -fs http://localhost:8080/api/health
```

curl fails. The website itself still loads (try <http://localhost:8080>), but the messages do not.

## Troubleshoot it

**Observe.** Something behind the web page is broken. Before changing anything, let's investigate.

**Investigate.** Which containers are actually running? `-a` also shows stopped ones:

<!-- test: output; contains=Exited -->
```bash
docker compose ps -a
```

```text
NAME                        IMAGE                     COMMAND                  SERVICE   CREATED         STATUS                     PORTS
multi-container-app-api-1   multi-container-app-api   "gunicorn --bind 0.0…"   api       8 seconds ago   Up 7 seconds               5000/tcp
multi-container-app-db-1    postgres:18-alpine        "docker-entrypoint.s…"   db        8 seconds ago   Exited (0) 4 seconds ago   
multi-container-app-web-1   multi-container-app-web   "/docker-entrypoint.…"   web       8 seconds ago   Up 7 seconds               0.0.0.0:8080->80/tcp, [::]:8080->80/tcp
```

`web` and `api` are `Up`, `db` is `Exited`. Ask the API what it thinks; without `-f`, curl shows the error body:

<!-- test: contains=error -->
```bash
curl -s http://localhost:8080/api/health
```

The API answers with `"status":"error"` and the database error message: it cannot connect to `db`. And the
database's own logs end with a clean shutdown, so nobody crashed: it was stopped.

<!-- test: output=tail:4 -->
```bash
docker compose logs db --tail 4
```

```text
db-1  | 2026-10-04 04:05:33.040 UTC [68] LOG:  shutting down
db-1  | 2026-10-04 04:05:33.042 UTC [68] LOG:  checkpoint starting: shutdown immediate
db-1  | 2026-10-04 04:05:33.055 UTC [68] LOG:  checkpoint complete: wrote 0 buffers (0.0%), wrote 3 SLRU buffers; 0 WAL file(s) added, 0 removed, 0 recycled; write=0.004 s, sync=0.002 s, total=0.015 s; sync files=2, longest=0.001 s, average=0.001 s; distance=0 kB, estimate=0 kB; lsn=0/1BACEB8, redo lsn=0/1BACEB8
db-1  | 2026-10-04 04:05:33.065 UTC [1] LOG:  database system is shut down
```

**Root cause.** The `db` service is stopped. The API is fine; it just has nothing to talk to.

**Fix.**

<!-- test: contains=Started -->
```bash
docker compose start db
```

**Verify.**

<!-- test: retry=30; contains=ok -->
```bash
curl -fs http://localhost:8080/api/health
```

Notice the order of the investigation: **status (`ps -a`) → symptom from the user's side (`curl`) → logs of the
suspicious service → fix → verify**. That order works for every Compose problem.

## Challenge

**Task:** Run the message board on host port **8081** instead of 8080, **without editing `docker-compose.yml`**.

**Requirements:**
- `docker-compose.yml` stays unchanged.
- `curl http://localhost:8081/api/health` reports the database as ok.

**Hints:**
- Compose automatically reads a second file called `docker-compose.override.yml` if it exists in the same folder.
- Values in the override file are merged with the main file.

<details><summary>Solution</summary>

Create the override file (bash, WSL, Git Bash or macOS; in PowerShell create the file with your editor):

```bash
cat > docker-compose.override.yml <<'EOF'
services:
  web:
    ports: !override
      - "8081:80"
EOF
docker compose up -d
```

<!-- test: retry=30; contains=ok -->
```bash
curl -fs http://localhost:8081/api/health
```

Without `!override`, Compose would **add** 8081 to the list and keep 8080 too: lists are merged, not replaced.
`!override` replaces the whole `ports` list.

Remove the override file afterwards so the next labs use port 8080 again:

```bash
rm docker-compose.override.yml
docker compose up -d
```

</details>

## Verify

- [ ] I can explain every line of `examples/multi-container-app/docker-compose.yml`
- [ ] I can start a stack with `docker compose up -d --build` and check it with `docker compose ps`
- [ ] I know which network and volume Compose created, and how it named them
- [ ] I can read the logs of one service and run commands in it with `docker compose exec`
- [ ] I know that `down` keeps volumes and `down -v` deletes them
- [ ] I investigated a broken service with `ps -a`, `curl` and `logs` before fixing it

## Clean up

<!-- test: contains=Removed -->
```bash
docker compose down -v
cd ../..
```

## Next

- Concept lesson: [docs/15-docker-compose.md](../../docs/15-docker-compose.md)
- Next lab: [Lab 14 · Logs, inspect and resources](../14-logs-inspect-resources/README.md)
