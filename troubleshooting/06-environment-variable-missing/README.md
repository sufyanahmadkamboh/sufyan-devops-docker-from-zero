# 06 · Environment variable missing

> The web page loads, but every API call fails with 502. Nothing in the Compose file looks wrong.
> Time: 20 minutes · You need: labs 05 and 13 (environment variables, Compose)

## Problem

The message board is configured with environment variables. Someone tidied up the Compose file and
removed a line they thought was not needed. The site is now half-broken.

Let's reproduce it. From the repository root:

```bash
cd troubleshooting/06-environment-variable-missing
```

<!-- test: timeout=900 -->
```bash
docker compose up -d --build
```

<!-- test-run: sleep 10 -->

## Symptoms

The web page itself is served:

<!-- test: retry=15; contains=Message Board -->
```bash
curl -s http://localhost:8080 | grep '<title>'
```

But the API behind it answers with an error status. `-w '%{http_code}'` makes curl print only the HTTP status code:

<!-- test: retry=15; contains=502 -->
```bash
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:8080/api/info
```

`502 Bad Gateway` comes from nginx. It means: *"I am fine, but the server behind me (the API) did not answer."*
In the browser, the page shows *"The web container could not reach the API"*.

## Investigation

The symptom points past nginx, at the API. Let's follow the request.

**Step 1: are all containers running?**

<!-- test: output; contains=Exited (3) -->
```bash
docker compose ps -a --format 'table {{.Service}}\t{{.Status}}'
```

```text
SERVICE   STATUS
api       Exited (3) 13 seconds ago
db        Up 14 seconds
web       Up 14 seconds
```

`web` and `db` are up, `api` exited with code **3**. nginx is reporting the truth: there is no API to talk to.

**Step 2: why did the API stop?**

<!-- test: output=tail:6; contains=required setting DB_PASSWORD is missing -->
```bash
docker compose logs api
```

```text
...
api-1  | ERROR: required setting DB_PASSWORD is missing. Set the environment variable DB_PASSWORD (or DB_PASSWORD_FILE).
api-1  | [2026-10-04 04:35:07 +0000] [7] [INFO] Worker exiting (pid: 7)
api-1  | [2026-10-04 04:35:07 +0000] [1] [ERROR] Worker (pid:8) exited with code 3.
api-1  | [2026-10-04 04:35:07 +0000] [1] [INFO] Worker (pid:7) was sent SIGTERM!
api-1  | [2026-10-04 04:35:07 +0000] [1] [ERROR] Shutting down: Master
api-1  | [2026-10-04 04:35:07 +0000] [1] [ERROR] Reason: Worker failed to boot.
```

Read from the bottom up. gunicorn (the Python web server) says `Worker failed to boot` and shuts down.
A few lines above, the application says exactly what it is missing:

```text
ERROR: required setting DB_PASSWORD is missing. Set the environment variable DB_PASSWORD (or DB_PASSWORD_FILE).
```

**Step 3: confirm what the container really received.** Logs tell you what the app *thinks*;
`docker inspect` tells you what Docker *gave* it:

<!-- test: output; contains=DB_HOST=db; absent=DB_PASSWORD -->
```bash
docker inspect ts06-api-1 --format '{{range .Config.Env}}{{println .}}{{end}}'
```

```text
DB_USER=board
DB_HOST=db
DB_NAME=board
PATH=/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
PYTHON_VERSION=3.14.8
PYTHON_SHA256=c2215904f02b175596dc49351585104f4bc20341e1c47378b26a2c274360ce73
```

`DB_HOST`, `DB_NAME` and `DB_USER` are there, plus a few variables from the Python base image.
`DB_PASSWORD` is not.

**Step 4: compare with the database.** The database was created with a password:

<!-- test: contains=POSTGRES_PASSWORD -->
```bash
docker compose config | grep -i password
```

`docker compose config` prints the final configuration Compose is using. Only `db` has a password setting.

## Commands

| Command | What it told us |
|---|---|
| `curl -w '%{http_code}'` | nginx answers 502: the backend is the problem |
| `docker compose ps -a` | `api` exited with code 3 |
| `docker compose logs api` | `required setting DB_PASSWORD is missing` |
| `docker inspect <container> --format '{{range .Config.Env}}{{println .}}{{end}}'` | the variable was never passed in |
| `docker compose config` | the merged configuration, as Compose sees it |

## Root Cause

The `api` service in `docker-compose.yml` has no `DB_PASSWORD`. The API needs it to log in to
PostgreSQL, so it refuses to start (exit code 3, our app's "a required setting is missing").
Without an API, nginx can only answer 502.

## Fix

Give the API the password, the same one the database was created with. The fixed file adds exactly one line:

<!-- test: contains=DB_PASSWORD -->
```bash
grep -n DB_PASSWORD docker-compose.fixed.yml
```

Stop the broken stack and start the fixed one. We stop first because nginx remembers the API's
address from its own start-up; a clean start avoids stale addresses:

```bash
docker compose down
```

<!-- test: timeout=900 -->
```bash
docker compose -f docker-compose.fixed.yml up -d --build
```

## Verification

<!-- test-run: sleep 8 -->
<!-- test: output; absent=Exited -->
```bash
docker compose -f docker-compose.fixed.yml ps -a --format 'table {{.Service}}\t{{.Status}}'
```

```text
SERVICE   STATUS
api       Up 8 seconds
db        Up 9 seconds
web       Up 8 seconds
```

<!-- test: retry=20; contains=200 -->
```bash
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:8080/api/info
```

<!-- test: retry=20; contains="database":"ok" -->
```bash
curl -s http://localhost:8080/api/health
```

The API can now log in to the database.

## Clean up

```bash
docker compose -f docker-compose.fixed.yml down -v
cd ../..
```

## Lesson Learned

- A `502` from a reverse proxy (nginx) means "the service behind me failed". Investigate the next hop.
- Good applications check their required settings at start-up and stop with a clear message.
  `docker logs` is where you read that message.
- `docker inspect ... .Config.Env` shows what the container really received; `docker compose config`
  shows what Compose intends to send.
- A password in a Compose file is fine for a local lab only. The capstone keeps it in a secret file instead.

Next: [07 · Running but not reachable](../07-running-but-not-reachable/README.md)
