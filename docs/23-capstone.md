# Capstone: Everything Together

## What is it?

The capstone is the message board application built **the way you would build it at work**, using every lesson of
this course in one place. It lives in [capstone/](../capstone/README.md); the guided walkthrough is
[tutorial/10-capstone.md](../tutorial/10-capstone.md).

```text
                              Developer
                                  │  docker compose up -d --build
                                  ▼
                              Docker CLI
                                  │  REST API
                                  ▼
                            Docker Engine
          ┌───────────────────────┼─────────────────────────┐
          ▼                       ▼                         ▼
   ┌──────────────┐       ┌──────────────┐          ┌──────────────┐
   │ web          │       │ api          │          │ db           │
   │ nginx        │──────►│ Python/Flask │─────────►│ PostgreSQL 18│
   │ unprivileged │ /api/ │ gunicorn     │  SQL     │              │
   │ :8080        │       │ :5000        │          │ :5432        │
   └──────┬───────┘       └──────────────┘          └──────┬───────┘
          │ capstone_frontend (web, api)                   │ capstone_backend (api, db)
          │                                                │
   Browser: http://localhost:8080                  Volume: capstone_db-data
   (the ONLY published port)                       (/var/lib/postgresql)
```

## Why do we need it?

Each lab teaches one idea in isolation. Real work means combining them and making them work **together**: the image
must be small and non-root, the containers must find each other on the right networks, the data must survive, the
password must not leak, the services must start in the right order, and you must be able to prove all of it.

## How does it work?

| File | What it does | Lessons it uses |
|---|---|---|
| `capstone/app/api/Dockerfile` | multi-stage build (venv in a builder stage), slim runtime, `USER app` (uid 10001), `HEALTHCHECK` | 09, 10, 19, 20 |
| `capstone/app/api/app.py` | the API; reads `DB_PASSWORD_FILE`, fails fast with a clear message if a setting is missing | 08, 16 |
| `capstone/app/web/Dockerfile` | `nginxinc/nginx-unprivileged`, listens on 8080, health check | 07, 19 |
| `capstone/app/web/default.conf.template` | forwards `/api/` to `http://${API_HOST}:5000` (a container name, resolved by Docker DNS) | 08, 14 |
| `capstone/database/init.sql` | creates the table and the first message, bind-mounted read-only into PostgreSQL | 13 |
| `capstone/docker-compose.yml` | 3 services, 2 networks, 1 volume, 1 secret, health-based start order, limits, read-only API | 12, 14, 15, 18, 19 |
| `capstone/app/*/.dockerignore` | keep junk and secrets out of the build context | 11 |
| `capstone/secrets/db_password.txt.example` | template for the secret file (the real file is never committed) | 19 |
| `capstone/.env.example` | settings you can change without editing the YAML (`WEB_PORT`, `APP_ENV`, `GREETING`) | 08, 15 |
| `capstone/verify.sh` | 18 automatic checks: health, ports, app, networks, security, volume; `--persistence` adds down + up | 16, 17 |

What Compose creates (project name `capstone`):

```text
containers  capstone-web-1   capstone-api-1   capstone-db-1
networks    capstone_frontend   capstone_backend
volume      capstone_db-data
images      docker-from-zero/web:1.0.0   docker-from-zero/api:1.0.0
```

## Prerequisites

All labs, or at least: [15-docker-compose.md](15-docker-compose.md), [14-networking.md](14-networking.md),
[12-volumes.md](12-volumes.md), [19-security-basics.md](19-security-basics.md).

## Hands-on Lab

```bash
cd capstone
cp secrets/db_password.txt.example secrets/db_password.txt
```

<!-- test: timeout=900; output=tail:8 -->
```bash
docker compose up -d --build
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

<!-- test: timeout=300; contains=All checks passed -->
```bash
./verify.sh
```

Open <http://localhost:8080>, write a message, and keep it in mind for the next step.

## Expected Result

- `up` builds two images and starts `db`, then `api` (once `db` is healthy), then `web` (once `api` is healthy).
- `./verify.sh` prints 17 `PASS` lines and `All checks passed.` (18 with `--persistence`).
- The page shows the greeting, the API container's hostname and the messages from the database.

## Experiment

Prove that the data lives on the volume, not in the container:

<!-- test: timeout=400; contains=All checks passed -->
```bash
./verify.sh --persistence
```

`--persistence` writes a message, runs `docker compose down` (containers and networks are deleted, the volume stays),
starts everything again and finds the message.

## Break It

Stop the database while the rest keeps running:

```bash
docker compose stop db
```

<!-- test: retry=20; contains=503 -->
```bash
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8080/api/health
```

## Troubleshoot It

<!-- test: contains=capstone-db-1 -->
```bash
docker compose ps -a
```

`db` is `Exited`, the API answers `503` on `/api/health`, and the web page shows an error for the messages. The
health endpoint tells you the database is the problem. Fix and verify:

```bash
docker compose start db
```

<!-- test: retry=40; contains="database":"ok" -->
```bash
curl -s http://localhost:8080/api/health
```

Clean up when you are done. `down` keeps your messages; add `-v` only if you want to delete them:

```bash
docker compose down -v
```

## Common Mistakes

- Forgetting to create `secrets/db_password.txt` (Compose stops with an error that names the missing file).
- Port 8080 already used by a container from an earlier lab (`docker ps`, or set `WEB_PORT=8081` in `.env`).
- Mounting PostgreSQL 18 data at `/var/lib/postgresql/data` (old tutorials). It must be `/var/lib/postgresql`.
- Running `docker compose down -v` and wondering where the messages went.
- Expecting to reach the API on `localhost:5000`: it is deliberately not published.

## Best Practices

The capstone shows them all in one file: pinned images, non-root users, multi-stage builds, health checks with
`depends_on: condition: service_healthy`, separate networks, a single published port, a named volume, secrets as files,
a read-only API filesystem, memory and CPU limits, and a script that verifies everything.

## Challenge

**Task:** change the greeting and the published port **without editing `docker-compose.yml`**: the page should be on
port 8081 and say `Hello from my capstone`.

**Hints:** look at `.env.example`.

## Solution

<details><summary>Solution</summary>

From the `capstone` folder:

```bash
printf 'WEB_PORT=8081\nGREETING=Hello from my capstone\n' > .env
docker compose up -d
```

<!-- test: retry=40; contains=Hello from my capstone -->
```bash
curl -s http://localhost:8081/api/info
```

```bash
docker compose down -v
rm .env
```

Compose reads `.env` automatically and substitutes `${WEB_PORT:-8080}` and `${GREETING:-...}`. Only the containers
whose configuration changed are recreated.
</details>

## Verification

- [ ] I can explain what every file in `capstone/` does and which lesson it comes from.
- [ ] I can start, verify, break, fix and stop the whole application.
- [ ] I can prove the data survives `docker compose down`.
- [ ] `./verify.sh` passes on my machine.

## Real-World Usage

This is a realistic local environment for a three-tier application, the kind of setup a team keeps in its repository
so every developer runs the same stack. The same images, health checks, limits and secret files carry over to the
platforms you will meet later in your DevOps career.

## Key Takeaways

- Every Docker concept in this course appears in the capstone.
- Health checks + `service_healthy` give a reliable start order.
- Two networks and one published port keep the database private.
- Verify with a script, not with a feeling.

Back to the start: [README](../README.md) · Knowledge check: [tutorial/11-knowledge-check.md](../tutorial/11-knowledge-check.md)
