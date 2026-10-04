# Chapter 6 · Docker Compose: the whole app with one command

> **Where you are:** you started three containers by hand in [Chapter 5](05-networking.md): a network, a volume,
> three long `docker run` commands, in the right order. It worked, but it was a lot of typing.
> **In this chapter:** you describe the same application once, in a file, and start it with one command.
> **Time:** about 45 minutes.

Let me be honest with you: nobody at work starts a three-container application with three `docker run` commands.
They write a `docker-compose.yml` file. Compose does not add new magic. Everything it does, you already did by hand:
it creates a network, a volume and containers. It just does it for you, from a file you can read, review and keep in Git.

```text
            docker-compose.yml                        what Compose creates
   +-------------------------------+          +-----------------------------------+
   | services:                     |          |  network  multi-container-app_default
   |   web:  build ./web, 8080:80  |  ----->  |  volume   multi-container-app_db-data
   |   api:  build ./api, env ...  |  up -d   |  container multi-container-app-web-1
   |   db:   postgres:18-alpine    |          |  container multi-container-app-api-1
   | volumes:                      |          |  container multi-container-app-db-1
   |   db-data:                    |          +-----------------------------------+
   +-------------------------------+
```

## 6.1 Read the file before you run it

Let's go to the example application. This is the same message board you built by hand in Chapter 5.

```bash
cd examples/multi-container-app
ls
```

Now look at the Compose file. Read it slowly, top to bottom.

<!-- test: output; contains=services:; contains=db-data -->
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

Here is how to read it:

| In the file | What it means | What you did by hand in Chapter 5 |
|---|---|---|
| `services:` | the containers of this application | three `docker run` commands |
| `build: ./web` | build an image from the Dockerfile in `./web` | `docker build -t ... ./web` |
| `image: postgres:18-alpine` | use a ready-made image | `docker run postgres:18-alpine` |
| `ports: "8080:80"` | publish a port to your computer | `-p 8080:80` |
| `environment:` | environment variables | `-e DB_HOST=db ...` |
| `volumes: db-data:/var/lib/postgresql` | a named volume for the database files | `-v db-data:/var/lib/postgresql` |
| `depends_on:` | start order: db, then api, then web | you typed them in that order |
| (nothing about networks) | Compose creates one network and puts every service on it | `docker network create` + `--network` |

Notice the last row. You did not write a network, and still the `api` service can reach `db` by name. Keep that in mind.

Let's ask Compose itself to check the file. If there is a typo, this is where you find out, not halfway through a start.

<!-- test: output; contains=web; contains=api; contains=db -->
```bash
docker compose config --services
```

```text
db
api
web
```

`docker compose config` reads the file, fills in defaults and checks it. `--services` just lists the service names.

## 6.2 Start everything

Let's run this. `-d` means "in the background" (like `docker run -d`), `--build` means "build the images first".

<!-- test: timeout=900; output=tail:10 -->
```bash
docker compose up -d --build
```

```text
...
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

The first time, this takes a while: Compose builds two images and pulls PostgreSQL. Look at the last lines. You can
see the order: the network is created, the volume is created, then `db`, then `api`, then `web`. That order comes
from `depends_on`.

Now check what is running. This is the Compose version of `docker ps`: it only shows the containers of this project.

<!-- test: output; contains=multi-container-app-web-1; contains=0.0.0.0:8080 -->
```bash
docker compose ps
```

```text
NAME                        IMAGE                     COMMAND                  SERVICE   CREATED         STATUS                  PORTS
multi-container-app-api-1   multi-container-app-api   "gunicorn --bind 0.0…"   api       2 seconds ago   Up Less than a second   5000/tcp
multi-container-app-db-1    postgres:18-alpine        "docker-entrypoint.s…"   db        2 seconds ago   Up 1 second             5432/tcp
multi-container-app-web-1   multi-container-app-web   "/docker-entrypoint.…"   web       2 seconds ago   Up Less than a second   0.0.0.0:8080->80/tcp, [::]:8080->80/tcp
```

Three rows. Look at the `NAME` column: Compose names containers `<project>-<service>-<number>`. The project name is
the folder name, `multi-container-app`. Only `web` has something in `PORTS` that starts with `0.0.0.0:8080`. The `api`
and `db` ports are only reachable inside the Docker network, which is exactly what we want.

Let's see if the application answers. If you are fast, the database may still be starting; just run it again after a
few seconds.

<!-- test: retry=20; output; contains="database":"ok" -->
```bash
curl -s http://localhost:8080/api/health
```

```text
{"database":"ok","status":"ok"}
```

`"database":"ok"`: the request went browser → web → api → db and back. Open <http://localhost:8080> in your browser
too. You should see the message board with the first message from `database/init.sql`.

## 6.3 What did Compose create?

Don't trust me; let's look. Compose created a network:

<!-- test: output; contains=multi-container-app_default -->
```bash
docker network ls --filter name=multi-container-app
```

```text
NETWORK ID     NAME                          DRIVER    SCOPE
1269798b7625   multi-container-app_default   bridge    local
```

And a volume:

<!-- test: output; contains=multi-container-app_db-data -->
```bash
docker volume ls --filter name=multi-container-app
```

```text
DRIVER    VOLUME NAME
local     multi-container-app_db-data
```

The names are `<project>_<name>`. That prefix matters later: if you rename the folder, the project name changes, and
Compose will create a **new, empty** volume. (That exact surprise is
[troubleshooting scenario 04](../troubleshooting/04-volume-data-missing/README.md).)

Let's prove that `api` finds `db` by name on that network. We run a one-line Python check inside the `api` container:

<!-- test: retry=10; output; contains=db is reachable -->
```bash
docker compose exec -T api python -c "import socket; socket.create_connection(('db', 5432), 2); print('db is reachable from api')"
```

```text
db is reachable from api
```

> **What is `-T`?** `docker compose exec` normally connects your terminal to the container (like `docker exec -it`).
> `-T` turns that off. You do not need it when you type commands yourself, but it makes the command work inside scripts
> too, so I use it in this tutorial.

## 6.4 Logs, exec and the database

Every container writes logs. With Compose you can read them per service:

<!-- test: output=tail:6 -->
```bash
docker compose logs api --tail 5
```

```text
api-1  | [2026-10-04 05:12:21 +0000] [8] [INFO] Booting worker with pid: 8
api-1  | [2026-10-04 05:12:21 +0000] [9] [INFO] Booting worker with pid: 9
api-1  | [2026-10-04 05:12:21 +0000] [1] [INFO] Control socket listening at /root/.gunicorn/gunicorn.ctl
api-1  | 172.18.0.4 - - [04/Oct/2026:05:12:22 +0000] "GET /api/health HTTP/1.1" 503 200 "-" "curl/8.19.0"
api-1  | 172.18.0.4 - - [04/Oct/2026:05:12:23 +0000] "GET /api/health HTTP/1.1" 200 32 "-" "curl/8.19.0"
```

You see gunicorn starting its workers, and one access log line per request (including our `/api/health` call).
Each line is prefixed with the container name, so when you run `docker compose logs` without a service name, you can
still tell who said what.

To follow logs live, you would add `-f` and stop with `Ctrl+C`:

<!-- test: skip -->
```bash
docker compose logs -f
```

Let's add a message through the API, exactly like the web page does:

<!-- test: output; contains="id" -->
```bash
curl -s -X POST -H "Content-Type: application/json" -d '{"text":"Written in chapter 6"}' http://localhost:8080/api/messages
```

```text
{"id":2,"text":"Written in chapter 6"}
```

> **Windows PowerShell:** the quotes in this command behave differently in PowerShell. Use WSL2 or Git Bash for this
> tutorial, or simply type the message on the web page.

Now ask the database directly. `docker compose exec` runs a command in a running service container; here the
PostgreSQL client `psql` inside the `db` container:

<!-- test: retry=10; output; contains=Written in chapter 6 -->
```bash
docker compose exec -T db psql -U board -d board -c "SELECT id, text FROM messages;"
```

```text
 id |                            text                             
----+-------------------------------------------------------------
  1 | Hello! This first message was created by database/init.sql.
  2 | Written in chapter 6
(2 rows)
```

Two rows: the one from `init.sql` and yours.

## 6.5 Restart, stop, start

Restart one service (for example after you changed its configuration):

<!-- test: output -->
```bash
docker compose restart api
```

```text
 Container multi-container-app-api-1 Restarting 
 Container multi-container-app-api-1 Started 
```

If you change code, `restart` is not enough: the old image is still used. You need to rebuild:

<!-- test: timeout=900; output=tail:4 -->
```bash
docker compose build api
docker compose up -d
```

```text
...
 Container multi-container-app-api-1 Recreated 
 Container multi-container-app-web-1 Running 
 Container multi-container-app-api-1 Starting 
 Container multi-container-app-api-1 Started 
```

`up -d` is clever: it only recreates containers whose image or configuration changed. Nothing changed here, so
everything stays as it is.

## 6.6 Break it: the database goes away

Don't fix it yet. We are going to break it on purpose. Stop only the database:

<!-- test: output -->
```bash
docker compose stop db
```

```text
 Container multi-container-app-db-1 Stopping 
 Container multi-container-app-db-1 Stopped 
```

Now ask the health endpoint again:

<!-- test: retry=10; output; contains="status":"error" -->
```bash
curl -s http://localhost:8080/api/health
```

```text
{"database":"failed to resolve host 'db': [Errno -2] Name or service not known","status":"error"}
```

The web page still loads, but the API reports `"status":"error"` and a database error message. Before changing anything,
let's investigate like an engineer:

1. **What is the symptom?** The API answers, but says the database is not reachable.
2. **What should we check?** Is every container running?

<!-- test: retry=20; output; contains=Exited -->
```bash
docker compose ps -a
```

```text
NAME                        IMAGE                     COMMAND                  SERVICE   CREATED          STATUS                     PORTS
multi-container-app-api-1   multi-container-app-api   "gunicorn --bind 0.0…"   api       6 seconds ago    Up 5 seconds               5000/tcp
multi-container-app-db-1    postgres:18-alpine        "docker-entrypoint.s…"   db        13 seconds ago   Exited (0) 4 seconds ago   
multi-container-app-web-1   multi-container-app-web   "/docker-entrypoint.…"   web       13 seconds ago   Up 12 seconds              0.0.0.0:8080->80/tcp, [::]:8080->80/tcp
```

3. **What does the output tell us?** `db` shows `Exited`. `-a` was important: without it, stopped containers are hidden,
   and you would only see two healthy-looking containers.
4. **Root cause:** the database container is not running.
5. **Fix:**

<!-- test: output -->
```bash
docker compose start db
```

```text
 Container multi-container-app-db-1 Starting 
 Container multi-container-app-db-1 Started 
```

6. **Verify:** never skip this step.

<!-- test: retry=20; contains="database":"ok" -->
```bash
curl -s http://localhost:8080/api/health
```

## 6.7 down: what goes away, and what stays

`docker compose down` removes the containers and the network. Watch carefully what it does **not** remove.

<!-- test: output -->
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

<!-- test: output; contains=multi-container-app_db-data -->
```bash
docker volume ls --filter name=multi-container-app
```

```text
DRIVER    VOLUME NAME
local     multi-container-app_db-data
```

The volume is still there. Let's start again and see if our message survived:

<!-- test: timeout=300 -->
```bash
docker compose up -d
```

<!-- test: retry=20; output; contains=Written in chapter 6 -->
```bash
curl -s http://localhost:8080/api/messages
```

```text
[{"created_at":"2026-10-04T05:12:22.781535+00:00","id":1,"text":"Hello! This first message was created by database/init.sql."},{"created_at":"2026-10-04T05:12:24.664247+00:00","id":2,"text":"Written in chapter 6"}]
```

It did. The containers are new, but the data lives in the volume. This is the single most important idea about data
in Docker: **containers are disposable, volumes are not**.

Now the dangerous one. `-v` also removes the volumes of the project:

<!-- test: output; contains=Removed -->
```bash
docker compose down -v
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
 Volume multi-container-app_db-data Removing 
 Volume multi-container-app_db-data Removed 
 Network multi-container-app_default Removed 
```

> **Warning:** `docker compose down -v` deletes the database. On your laptop that is a clean reset. Next to real data
> it is the command you double-check before pressing Enter.

<!-- test: absent=multi-container-app_db-data -->
```bash
docker volume ls --filter name=multi-container-app
```

Empty. The data is gone for good.

## 6.8 Command summary

| Command | What it does |
|---|---|
| `docker compose config` | check the file and show the final configuration |
| `docker compose up -d --build` | build images, create network + volumes + containers, start in the background |
| `docker compose ps` / `ps -a` | containers of this project (`-a` includes stopped ones) |
| `docker compose logs <service>` | logs of one service (`-f` to follow, `--tail N` for the last lines) |
| `docker compose exec <service> <cmd>` | run a command in a running service container |
| `docker compose restart <service>` | restart containers (does not pick up new code) |
| `docker compose build <service>` | rebuild an image after code changes |
| `docker compose stop` / `start` | stop/start containers without removing them |
| `docker compose down` | remove containers and network, **keep** volumes |
| `docker compose down -v` | also remove volumes: **deletes data** |

## Where would I use this as a DevOps engineer?

Compose is the standard way to run an application on a developer laptop: "clone the repository, run
`docker compose up -d`, start coding". It is also used for small servers, demo environments and for running the
dependencies (a database, a cache) of an application during tests. When an application grows to many servers,
teams usually move to Kubernetes, but the ideas you just practised (services, networks, volumes, configuration in a
file) carry over directly.

## What you learned

- A `docker-compose.yml` describes services, volumes and (optionally) networks in one readable file.
- `docker compose up -d --build` creates a network, volumes and containers in dependency order.
- Compose names things `<project>_<name>` and `<project>-<service>-1`; the project name is the folder name.
- Services find each other by service name on the network Compose creates.
- `down` keeps volumes, `down -v` deletes them.
- When something fails: `docker compose ps -a`, then `docker compose logs <service>`.

## Try it yourself

1. Change `GREETING` in `docker-compose.yml`, run `docker compose up -d` and check `curl -s http://localhost:8080/api/info`.
   Which container was recreated? (Watch the output of `up -d`.)
2. Change the published port to `8081:80`. What do you need to run, and which URL works now?
3. Run `docker compose up -d` from a copy of the folder with a different name. How many volumes do you have now, and why?

## Next

Your application runs. Now you need to see inside it while it runs: logs, configuration, resource usage.
Continue with [Chapter 7 · Operating containers](07-operate.md).
