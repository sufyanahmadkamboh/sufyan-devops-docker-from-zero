# Chapter 9 · Troubleshooting like an engineer

> **Where you are:** you know every Docker building block in this course.
> **In this chapter:** we work through three real failures together, step by step, using the broken projects in
> [`troubleshooting/`](../troubleshooting/). Then you solve the other seven on your own.
> **Time:** about 60 minutes.

Beginners fix problems by guessing: change something, run again, change something else. Sometimes it works, and
nobody knows why. Engineers follow a loop, and the loop always starts with evidence:

```text
   What happened?            (the symptom, in one sentence)
         |
   What should we check?     (which layer: container state, logs, configuration, network, data)
         |
   Which command gives us evidence?
         |
   What does the output tell us?
         |
   Root cause                (the one thing that, if changed, explains every symptom)
         |
   Fix                       (change exactly that)
         |
   Verify                    (prove it works; never assume)
```

And these are the commands that give evidence, in the order I reach for them:

| Question | Command |
|---|---|
| Is it running? Did it exit? With which code? | `docker ps -a`, `docker compose ps -a` |
| What did the process say? | `docker logs <container>`, `docker compose logs <service>` |
| How is it configured (env, ports, mounts, networks)? | `docker inspect`, `docker compose config` |
| Can it reach the other container? | `docker exec` / `docker compose exec` + a connection test |
| What is in the image? | `docker history`, `docker run --rm <image> ls ...` |

Every scenario in `troubleshooting/` is broken **on purpose** and has a README with the full investigation. Here we do
three of them live.

## Scenario 1 · The container exits immediately

Let's go there and look at what we have.

```bash
cd troubleshooting/01-container-exits-immediately
ls
```

Build the image and start it, like any other app:

<!-- test: timeout=600; output=tail:2 -->
```bash
docker build -t ts01 .
```

```text
...

View build details: docker-desktop://dashboard/build/desktop-linux/desktop-linux/8w8vnmemhhxqfg5ukn6q2a4qf
```

<!-- test: output -->
```bash
docker run -d --name ts01 -p 5000:5000 ts01
```

```text
a16e2b103aa70ca020c16466bc3f9966c389c274358b8f51ddf0011ccdb5e6c5
```

Docker printed an ID. Everything fine? Let's check.

<!-- test-run: sleep 3 -->

<!-- test: output; absent=ts01 -->
```bash
docker ps --filter name=ts01
```

```text
CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES
```

**What happened?** The container is not in the list of running containers. Don't fix it yet. Don't start it again
either; that would just repeat the problem. Let's investigate.

**What should we check first?** Whether it exited, and how:

<!-- test: output; contains=Exited (2) -->
```bash
docker ps -a --filter name=ts01
```

```text
CONTAINER ID   IMAGE     COMMAND            CREATED         STATUS                     PORTS     NAMES
a16e2b103aa7   ts01      "python main.py"   4 seconds ago   Exited (2) 3 seconds ago             ts01
```

`Exited (2)`: the main process ended with exit code 2. A non-zero code means "error". Something in the process went
wrong, so the next question is: **what did the process say?**

<!-- test: output; contains=can't open file -->
```bash
docker logs ts01
```

```text
python: can't open file '/app/main.py': [Errno 2] No such file or directory
```

`python: can't open file '/app/main.py': [Errno 2] No such file or directory`. Now we have a precise claim to check:
Python was asked to run `/app/main.py`. **Which command gives evidence** about what is really inside `/app`? We can
run a different command in the same image (a throw-away container, `--rm`):

<!-- test: output; contains=app.py; absent=main.py -->
```bash
docker run --rm ts01 ls /app
```

```text
app.py
requirements.txt
```

There is `app.py` and `requirements.txt`, but no `main.py`. Where does `main.py` come from? From the `CMD` line:

<!-- test: output; contains=main.py -->
```bash
grep CMD Dockerfile
```

```text
CMD ["python", "main.py"]
```

**Root cause:** the `CMD` starts a file that does not exist. The container stops because its main process stopped
(remember: a container lives exactly as long as its main process).

**Fix:** `CMD ["python", "app.py"]`. The corrected file is next to the broken one, so you can compare them:

<!-- test: output; contains=app.py -->
```bash
diff Dockerfile Dockerfile.fixed || true
```

```text
1c1
< # Broken on purpose. Build it, run it, and find out why the container stops.
---
> # Fixed version: the CMD now points at the file that really exists in /app.
7c7
< CMD ["python", "main.py"]
---
> CMD ["python", "app.py"]
```

Build the fixed version and replace the broken container:

<!-- test: timeout=600 -->
```bash
docker build -f Dockerfile.fixed -t ts01:fixed .
docker rm ts01
docker run -d --name ts01 -p 5000:5000 ts01:fixed
```

**Verify:**

<!-- test: retry=15; output; contains=Hello from simple-app -->
```bash
curl -s http://localhost:5000/
```

```text
Hello from simple-app!
environment: development
container hostname: 48ed6aef9fc7
```

**Lesson learned:** "exits immediately" is never a mystery. `docker ps -a` gives you the exit code, `docker logs`
gives you the reason. Two commands, and you already know more than any guess could tell you.

```bash
docker rm -f ts01
```

## Scenario 3 · Containers cannot communicate

Next door, a Compose project where the web page never loads.

<!-- test: timeout=900; output=tail:4 -->
```bash
cd ../03-containers-cannot-communicate
docker compose up -d --build
```

```text
...
 Container ts03-api-1 Starting 
 Container ts03-api-1 Started 
 Container ts03-web-1 Starting 
 Container ts03-web-1 Started 
```

Compose says everything started. Let's try the application:

<!-- test-run: sleep 10 -->

<!-- test: fail -->
```bash
curl -s --max-time 5 http://localhost:8080/
```

Nothing comes back. **What happened?** The application is not reachable on port 8080. **What should we check?**
Start with the state of all containers of this project:

<!-- test: output; contains=Exited (1) -->
```bash
docker compose ps -a
```

```text
NAME         IMAGE                COMMAND                  SERVICE   CREATED          STATUS                     PORTS
ts03-api-1   ts03-api             "gunicorn --bind 0.0…"   api       14 seconds ago   Up 13 seconds              5000/tcp
ts03-db-1    postgres:18-alpine   "docker-entrypoint.s…"   db        14 seconds ago   Up 13 seconds              5432/tcp
ts03-web-1   ts03-web             "/docker-entrypoint.…"   web       14 seconds ago   Exited (1) 8 seconds ago   
```

`api` and `db` are up, `web` has `Exited (1)`. The web container is the one serving port 8080, so that explains the
symptom. Why did it exit? **Ask its logs:**

<!-- test: output=tail:3; contains=host not found in upstream -->
```bash
docker compose logs web
```

```text
...
web-1  | /docker-entrypoint.sh: Configuration complete; ready for start up
web-1  | 2026/10/04 04:24:43 [emerg] 1#1: host not found in upstream "api" in /etc/nginx/conf.d/default.conf:16
web-1  | nginx: [emerg] host not found in upstream "api" in /etc/nginx/conf.d/default.conf:16
```

`host not found in upstream "api"`. nginx forwards `/api/` requests to a host called `api`, and at start-up it could
not find any host with that name, so it refused to start. But there *is* a running container for the `api` service.
So the question becomes: **can web see api?** Containers find each other by name only when they share a network.
Let's ask each container which networks it is attached to:

<!-- test: output; contains=ts03_frontend -->
```bash
docker inspect ts03-web-1 --format '{{range $name, $net := .NetworkSettings.Networks}}{{$name}} {{end}}'
```

```text
ts03_frontend 
```

<!-- test: output; contains=ts03_backend -->
```bash
docker inspect ts03-api-1 --format '{{range $name, $net := .NetworkSettings.Networks}}{{$name}} {{end}}'
```

```text
ts03_backend 
```

There it is. `web` is only on `ts03_frontend`, `api` is only on `ts03_backend`. Two separate networks, so Docker's DNS
on the frontend network has never heard of `api`. Confirm it in the file:

<!-- test: output; contains=networks -->
```bash
grep -n "networks" docker-compose.yml
```

```text
9:    networks: [frontend]
17:    networks: [backend]
28:    networks: [backend]
30:networks:
```

**Root cause:** the API is not on the network the web container uses. **Fix:** the API must be on *both* networks:
`frontend` (to be reached by web) and `backend` (to reach the database). That is exactly the design of the capstone.
Compare with the fixed file:

<!-- test: output -->
```bash
diff docker-compose.yml docker-compose.fixed.yml || true
```

```text
1c1,4
< # Broken on purpose: the web container keeps stopping. Why?
---
> # Fixed: the api joins BOTH networks.
> #   frontend: web <-> api   (so nginx can find "api")
> #   backend:  api <-> db    (so the api can find "db")
> # The database stays on backend only: web still cannot reach it.
17c20
<     networks: [backend]
---
>     networks: [frontend, backend]
```

Stop the broken project and start the fixed one:

<!-- test: timeout=900 -->
```bash
docker compose down
docker compose -f docker-compose.fixed.yml up -d --build
```

**Verify:**

<!-- test: retry=30; output; contains="database":"ok" -->
```bash
curl -s http://localhost:8080/api/health
```

```text
{"database":"ok","status":"ok"}
```

**Lesson learned:** "cannot communicate" almost always means "not on the same network" or "wrong name". `docker inspect`
shows the networks of each container; compare them before touching anything else.

```bash
docker compose -f docker-compose.fixed.yml down -v
```

## Scenario 6 · A missing environment variable

The last one we do together. The Compose file looks fine at first sight.

<!-- test: timeout=900; output=tail:4 -->
```bash
cd ../06-environment-variable-missing
docker compose up -d --build
```

```text
...
 Container ts06-api-1 Starting 
 Container ts06-api-1 Started 
 Container ts06-web-1 Starting 
 Container ts06-web-1 Started 
```

<!-- test-run: sleep 10 -->

Try the API through the web container:

<!-- test: output; contains=502 -->
```bash
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost:8080/api/info
```

```text
HTTP 502
```

**What happened?** HTTP `502 Bad Gateway`. That code is precise: the web server (nginx) is running, but the server
*behind* it did not answer. So web is fine, the problem is behind it. **What should we check?** The state of the
services:

<!-- test: output; contains=Exited (3) -->
```bash
docker compose ps -a
```

```text
NAME         IMAGE                COMMAND                  SERVICE   CREATED          STATUS                      PORTS
ts06-api-1   ts06-api             "gunicorn --bind 0.0…"   api       14 seconds ago   Exited (3) 13 seconds ago   
ts06-db-1    postgres:18-alpine   "docker-entrypoint.s…"   db        14 seconds ago   Up 14 seconds               5432/tcp
ts06-web-1   ts06-web             "/docker-entrypoint.…"   web       14 seconds ago   Up 13 seconds               0.0.0.0:8080->80/tcp, [::]:8080->80/tcp
```

`api` has `Exited (3)`. **What did it say?**

<!-- test: output=tail:6; contains=required setting DB_PASSWORD is missing -->
```bash
docker compose logs api
```

```text
...
api-1  | [2026-10-04 04:25:07 +0000] [7] [INFO] Worker exiting (pid: 7)
api-1  | [2026-10-04 04:25:07 +0000] [8] [INFO] Worker exiting (pid: 8)
api-1  | [2026-10-04 04:25:07 +0000] [1] [ERROR] Worker (pid:8) exited with code 3.
api-1  | [2026-10-04 04:25:07 +0000] [1] [INFO] Worker (pid:7) was sent SIGTERM!
api-1  | [2026-10-04 04:25:07 +0000] [1] [ERROR] Shutting down: Master
api-1  | [2026-10-04 04:25:07 +0000] [1] [ERROR] Reason: Worker failed to boot.
```

`ERROR: required setting DB_PASSWORD is missing. Set the environment variable DB_PASSWORD (or DB_PASSWORD_FILE).`
A well-written application tells you exactly what it needs. Let's get evidence from the configuration side too: which
environment variables did the container actually receive?

<!-- test: output; contains=DB_HOST=db; absent=DB_PASSWORD -->
```bash
docker inspect ts06-api-1 --format '{{range .Config.Env}}{{println .}}{{end}}' | grep DB_
```

```text
DB_NAME=board
DB_USER=board
DB_HOST=db
```

`DB_HOST`, `DB_NAME`, `DB_USER`, but no `DB_PASSWORD`.

**Root cause:** the API needs the database password and the Compose file never gives it one. (The database service
does have `POSTGRES_PASSWORD`, but that variable belongs to a different container. Each container only sees its own
environment.)

**Fix:** add `DB_PASSWORD` to the `api` service:

<!-- test: output; contains=DB_PASSWORD -->
```bash
diff docker-compose.yml docker-compose.fixed.yml || true
```

```text
1c1
< # Broken on purpose: the app does not work. Nothing in this file looks obviously wrong...
---
> # Fixed: the api gets the DB_PASSWORD it needs (the same value the database was created with).
16a17
>       DB_PASSWORD: board-lab-password
```

<!-- test: timeout=600 -->
```bash
docker compose down
docker compose -f docker-compose.fixed.yml up -d
```

**Verify:**

<!-- test: retry=30; output; contains=greeting -->
```bash
curl -s http://localhost:8080/api/info
```

```text
{"app_env":"development","container_hostname":"26b479d23bc4","database_host":"db","greeting":"Hello from the API"}
```

**Lesson learned:** a `502` from a proxy points *behind* the proxy. Exit codes, logs and the environment in
`docker inspect` together show what the container received versus what it needed.

```bash
docker compose -f docker-compose.fixed.yml down -v
```

## Your turn: the other seven

Each folder has a README with the same structure (Problem, Symptoms, Investigation, Commands, Root Cause, Fix,
Verification, Lesson Learned). Try to find the root cause **before** you scroll down to it.

| # | Scenario | The first command I would run |
|---|---|---|
| 02 | [Port already in use](../troubleshooting/02-port-already-in-use/README.md) | read the error of `docker run`, then `docker ps --filter publish=8080` |
| 04 | [Volume data appears missing](../troubleshooting/04-volume-data-missing/README.md) | `docker volume ls` |
| 05 | [Dockerfile build fails](../troubleshooting/05-dockerfile-build-fails/README.md) | read the first `ERROR` line of the build, then `cat .dockerignore` |
| 07 | [Running but not reachable](../troubleshooting/07-running-but-not-reachable/README.md) | `docker logs` (which address does the app listen on?) |
| 08 | [Image too large](../troubleshooting/08-image-too-large/README.md) | `docker history <image>` |
| 09 | [Host changes not reflected](../troubleshooting/09-host-changes-not-reflected/README.md) | `docker inspect --format '{{json .Mounts}}'` |
| 10 | [Database data disappears](../troubleshooting/10-database-data-disappears/README.md) | `docker volume ls` before and after `down` + `up` |

## Where would I use this as a DevOps engineer?

Every day. "The container keeps restarting", "the service can't reach the database", "it works on my machine" are the
everyday tickets of a DevOps team. The people who solve them fastest are not the ones who know the most commands; they
are the ones who collect evidence before they change anything.

## What you learned

- Start from the symptom, collect evidence, find the one root cause, fix it, verify.
- `ps -a` (exit code) and `logs` (reason) solve most "container stopped" problems.
- `502` from nginx means the problem is behind nginx.
- `docker inspect` shows what a container really received: networks, environment, mounts.
- Containers communicate only on shared networks; each container sees only its own environment variables.

## Try it yourself

Solve scenarios 02, 04, 05, 07, 08, 09 and 10. For each one, write down the symptom and the evidence command
*before* you read the root cause.

## Next

Time to put everything together.
Continue with [Chapter 10 · The capstone](10-capstone.md).
