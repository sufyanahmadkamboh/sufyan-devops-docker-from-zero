# Docker Compose

## What is it?

**Docker Compose** lets you describe a whole application (several containers, their networks, volumes, ports and
environment variables) in **one YAML file**, and start or stop all of it with one command.

```text
   docker-compose.yml                       docker compose up -d
  ┌─────────────────────────┐            ┌─────────────────────────────────────────────┐
  │ services:               │            │ network  multi-container-app_default        │
  │   web:  build, ports    │ ─────────► │   ├── container multi-container-app-web-1   │
  │   api:  build, env      │            │   ├── container multi-container-app-api-1   │
  │   db:   image, volume   │            │   └── container multi-container-app-db-1    │
  │ volumes:                │            │ volume   multi-container-app_db-data        │
  │   db-data:              │            │ images   multi-container-app-web / -api     │
  └─────────────────────────┘            └─────────────────────────────────────────────┘
```

## Why do we need it?

In [labs/12-multi-container](../labs/12-multi-container/README.md) you start the message board by hand: create a
network, create a volume, then three long `docker run` commands in the right order with the right flags. It works,
but it is easy to get wrong and impossible to remember. A Compose file is that same knowledge, written down once,
versioned in Git, and repeatable for everyone on the team.

## How does it work?

The `docker compose` command reads `docker-compose.yml` (or `compose.yaml`) in the current folder. Each entry under
`services:` becomes one or more containers. Compose also creates:

- a **project name**: the folder name (or `name:` in the file). Everything it creates is prefixed with it.
- a **default network** `<project>_default`, joined by every service, so services reach each other **by service name**.
- **named volumes** listed under `volumes:` as `<project>_<name>`.
- **images** for services with `build:`.

| Command | What it does |
|---|---|
| `docker compose up -d` | create everything that is missing and start it in the background |
| `docker compose up -d --build` | rebuild images first |
| `docker compose ps` | the containers of **this** project |
| `docker compose logs api` | logs of one service (`-f` to follow) |
| `docker compose exec db psql -U board` | run a command in a running service container |
| `docker compose build` | only build the images |
| `docker compose restart api` | restart one service |
| `docker compose down` | remove containers and networks (**volumes are kept**) |
| `docker compose down -v` | ...and the named volumes too (**data is deleted**) |

## Prerequisites

- [09-dockerfile.md](09-dockerfile.md), [12-volumes.md](12-volumes.md), [14-networking.md](14-networking.md)
- [labs/12-multi-container](../labs/12-multi-container/README.md) (doing it by hand first makes Compose obvious)

## Hands-on Lab

Full lab: [labs/13-docker-compose](../labs/13-docker-compose/README.md). Short version:

```bash
cd examples/multi-container-app
```

<!-- test: timeout=900; output=tail:8 -->
```bash
docker compose up -d --build
```

```text
...
 Container multi-container-app-web-1 Creating 
 Container multi-container-app-web-1 Created 
 Container multi-container-app-db-1 Starting 
 Container multi-container-app-db-1 Started 
 Container multi-container-app-api-1 Starting 
 Container multi-container-app-api-1 Started 
 Container multi-container-app-web-1 Starting 
 Container multi-container-app-web-1 Started 
```

<!-- test: output -->
```bash
docker compose ps
```

```text
NAME                        IMAGE                     COMMAND                  SERVICE   CREATED        STATUS                  PORTS
multi-container-app-api-1   multi-container-app-api   "gunicorn --bind 0.0…"   api       1 second ago   Up Less than a second   5000/tcp
multi-container-app-db-1    postgres:18-alpine        "docker-entrypoint.s…"   db        1 second ago   Up 1 second             5432/tcp
multi-container-app-web-1   multi-container-app-web   "/docker-entrypoint.…"   web       1 second ago   Up Less than a second   0.0.0.0:8080->80/tcp, [::]:8080->80/tcp
```

<!-- test: retry=30; contains="database":"ok" -->
```bash
curl -s http://localhost:8080/api/health
```

## Expected Result

- `up` builds the `web` and `api` images, creates the network and the volume, and starts `db`, `api`, `web` in that
  order (because of `depends_on`).
- `ps` shows three containers, all `Up`, and only `web` with a published port (`0.0.0.0:8080->80/tcp`).
- The health endpoint answers `{"database":"ok","status":"ok"}`: browser → web → api → db works.
- Open <http://localhost:8080> in your browser to see the message board.

## Experiment

See exactly what Compose created:

<!-- test: contains=multi-container-app_default -->
```bash
docker network ls --filter name=multi-container-app
```

<!-- test: contains=multi-container-app_db-data -->
```bash
docker volume ls --filter name=multi-container-app
```

Run a command inside a service container (here: ask PostgreSQL how many messages it stores):

<!-- test: retry=10; contains=1 row -->
```bash
docker compose exec -T db psql -U board -d board -c "SELECT count(*) FROM messages"
```

(`-T` turns off the interactive terminal; you only need it in scripts. Typing it by hand works with or without.)

## Break It

`down` removes containers and the network but **keeps** the volume. `down -v` deletes the volume as well. Let's prove
the first one keeps your data:

<!-- test: contains=201 -->
```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST -H "Content-Type: application/json" -d '{"text":"survive me"}' http://localhost:8080/api/messages
docker compose down
docker compose up -d
```

<!-- test: retry=30; contains=survive me -->
```bash
curl -s http://localhost:8080/api/messages
```

## Troubleshoot It

When a Compose application misbehaves, check in this order:

```bash
docker compose ps -a
```

<!-- test: output=tail:5 -->
```bash
docker compose logs api
```

```text
...
api-1  | [2026-10-04 04:17:59 +0000] [1] [INFO] Using worker: sync
api-1  | [2026-10-04 04:17:59 +0000] [7] [INFO] Booting worker with pid: 7
api-1  | [2026-10-04 04:17:59 +0000] [8] [INFO] Booting worker with pid: 8
api-1  | [2026-10-04 04:17:59 +0000] [1] [INFO] Control socket listening at /root/.gunicorn/gunicorn.ctl
api-1  | 172.18.0.4 - - [04/Oct/2026:04:18:00 +0000] "GET /api/messages HTTP/1.1" 200 205 "-" "curl/8.19.0"
```

`ps -a` shows stopped containers too (look for `Exited (N)`), and `logs <service>` shows why. Real examples:
[troubleshooting/06-environment-variable-missing](../troubleshooting/06-environment-variable-missing/README.md) and
[troubleshooting/03-containers-cannot-communicate](../troubleshooting/03-containers-cannot-communicate/README.md).

Clean up. `-v` deletes the database volume, so only use it when you really want the data gone:

```bash
docker compose down -v
```

## Common Mistakes

- Running `docker compose` from the wrong folder ("no configuration file provided").
- Forgetting `--build` after changing code: Compose reuses the old image.
- Using `down -v` out of habit and losing database data.
- Thinking `depends_on` waits until a service is **ready**. By default it only waits until it is **started**. The
  capstone uses `condition: service_healthy` with health checks for that.
- Indentation errors in YAML (use spaces, never tabs).

## Best Practices

- Keep the Compose file in Git next to the code.
- Publish only the ports people need.
- Use named volumes for data, health checks for readiness, and `.env` files for settings that change per machine.
- Keep secrets out of the YAML (the capstone uses `secrets:` with a file that is not committed).

## Challenge

**Task:** change the greeting the API returns to `Hello from my own Compose file` **without editing the YAML**,
using an override on the command line.

**Hints:** `docker compose run` does not help here. Look at how `GREETING` is set and remember that Compose
can read another file with `-f`.

## Solution

<details><summary>Solution</summary>

In `examples/multi-container-app`, create an override file next to the original (Compose merges files given with
`-f`, later files win):

```bash
printf 'services:\n  api:\n    environment:\n      GREETING: Hello from my own Compose file\n' > greeting.override.yml
docker compose -f docker-compose.yml -f greeting.override.yml up -d --build
```

<!-- test: retry=30; contains=Hello from my own Compose file -->
```bash
curl -s http://localhost:8080/api/info
```

```bash
docker compose -f docker-compose.yml -f greeting.override.yml down -v
rm greeting.override.yml
```

Override files are how teams keep one base file and small per-environment differences.
</details>

## Verification

- [ ] I can start, inspect and stop a multi-container app with Compose.
- [ ] I can name everything `docker compose up` created.
- [ ] I know the difference between `down` and `down -v`.
- [ ] I can read the logs of one service and run a command inside it.

## Real-World Usage

Compose is the standard tool for **local development environments**: a new team member clones the repo, runs
`docker compose up`, and has the app plus its database running in minutes. It is also used for demos, integration
tests and small single-server deployments.

## Key Takeaways

- One YAML file describes containers, networks, volumes and configuration.
- Services find each other by **service name** on the project network.
- `down` keeps volumes; `down -v` deletes them.
- `ps -a` + `logs <service>` is the first step of every Compose investigation.

Next: [16-logs-and-debugging.md](16-logs-and-debugging.md)
