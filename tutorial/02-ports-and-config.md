# 02 · Ports and configuration

> Reach a container from your browser, understand `HOST:CONTAINER` port mapping, survive the two classic port
> failures, and change an application's behaviour with environment variables, without rebuilding anything.
> Time: about 60 minutes. You need: [01 · Your first container](01-first-container.md).

## Part 1 · Ports

### A web server you cannot reach

Let's start nginx again, exactly like in chapter 01:

<!-- test: contains=80/tcp -->
```bash
docker run -d --name web nginx:1.30-alpine
docker ps --filter name=web
```

nginx is running and the `PORTS` column says `80/tcp`. So let's open it:

<!-- test: fail -->
```bash
curl -s --max-time 3 http://localhost:80
```

Nothing (or "connection refused"). Don't fix it yet. Let's think about what we see. `80/tcp` without an arrow means:
"the container listens on port 80 **inside its own network namespace**". Your computer's port 80 is a different
thing. A container is isolated by default; nothing reaches it from outside unless you **publish** a port.

```text
  Your computer                          Container "web"
  +---------------------+                +----------------------+
  |  localhost:80  (?)  |      wall      |  nginx listening :80 |
  +---------------------+       ||       +----------------------+
```

### Publish a port

<!-- test: contains=0.0.0.0:8080->80/tcp -->
```bash
docker rm -f web
docker run -d --name web -p 8080:80 nginx:1.30-alpine
docker ps --filter name=web
```

`-p 8080:80` means **HOST PORT : CONTAINER PORT**. The `PORTS` column now shows the arrow:
`0.0.0.0:8080->80/tcp`. Traffic that arrives on port 8080 of your computer (on every network interface, that is what
`0.0.0.0` means) is forwarded to port 80 inside the container.

```text
  Your computer                          Container "web"
  +---------------------+                +----------------------+
  |  localhost:8080 ----+---- Docker ----+--> nginx :80         |
  +---------------------+                +----------------------+
```

<!-- test: retry=15; output=head:8; contains=Welcome to nginx -->
```bash
curl -s http://localhost:8080
```

```text
<!DOCTYPE html>
<html>
<head>
<title>Welcome to nginx!</title>
<style>
html { color-scheme: light dark; }
body { width: 35em; margin: 0 auto;
font-family: Tahoma, Verdana, Arial, sans-serif; }
...
```

There it is: nginx's welcome page. Open <http://localhost:8080> in your browser too.

Ask Docker which ports a container publishes:

<!-- test: contains=8080 -->
```bash
docker port web
```

### Experiment: one image, two ports

The host port is your choice. The container port is decided by the application inside. Let's run a second copy:

```bash
docker run -d --name web2 -p 8081:80 nginx:1.30-alpine
```

<!-- test: retry=15; contains=Welcome to nginx -->
```bash
curl -s http://localhost:8081 | grep title
```

Two containers, both listening on port 80 **inside** (no conflict: each has its own network namespace), published on
two **different host ports**.

### Failure 1 · "It's running, but I can't reach it"

Someone starts a third copy like this:

<!-- test: contains=0.0.0.0:8082->8080/tcp -->
```bash
docker run -d --name web3 -p 8082:8080 nginx:1.30-alpine
docker ps --filter name=web3
```

Running, port published. And yet:

<!-- test: fail -->
```bash
curl -s --max-time 3 http://localhost:8082
```

Don't fix it yet. Before changing anything, let's investigate.

- **What is the symptom?** The container is `Up`, the port is published, but the connection fails.
- **What should we check?** Which port the application really listens on inside the container.
- **Which command gives evidence?** The image tells us what it exposes:

<!-- test: contains=80/tcp -->
```bash
docker inspect nginx:1.30-alpine --format '{{json .Config.ExposedPorts}}'
```

- **What does it tell us?** nginx listens on `80/tcp`. We forwarded host port 8082 to container port **8080**, where
  nothing listens. Docker happily forwarded the traffic into the void.
- **Root cause:** the container port in `-p` was wrong.
- **Fix:** a container's published ports cannot be changed after creation, so recreate it:

```bash
docker rm -f web3
docker run -d --name web3 -p 8082:80 nginx:1.30-alpine
```

<!-- test: retry=15; contains=Welcome to nginx -->
```bash
curl -s http://localhost:8082 | grep title
```

- **Verify:** it answers. Lesson: **`-p` is HOST:CONTAINER, and the container side must match what the app listens on.**

### Failure 2 · "Port is already allocated"

Port 8080 is used by `web`. What if we try to use it again?

<!-- test: fail; contains=port is already allocated -->
```bash
docker run -d --name web4 -p 8080:80 nginx:1.30-alpine
```

Read the last part of the error: `Bind for 0.0.0.0:8080 failed: port is already allocated`. Only one program on your
computer can listen on a given port. Which container has it?

<!-- test: contains=web -->
```bash
docker ps --filter publish=8080 --format '{{.Names}} {{.Ports}}'
```

It is `web`. (If no container shows up, the port is used by a program outside Docker: on Linux and macOS
`sudo lsof -i :8080`, on Windows `netstat -ano | findstr :8080` tell you which one.)

Notice something sneaky:

<!-- test: contains=Created -->
```bash
docker ps -a --filter name=web4 --format '{{.Names}}: {{.Status}}'
```

The failed `docker run` still **created** the container `web4`; it just could not start it. Remove it, then pick a free
port:

```bash
docker rm web4
docker run -d --name web4 -p 8083:80 nginx:1.30-alpine
```

<!-- test: retry=15; contains=Welcome to nginx -->
```bash
curl -s http://localhost:8083 | grep title
```

Clean up the web servers:

```bash
docker rm -f web web2 web3 web4
```

### Where would I use this as a DevOps engineer?

Every time you run a service locally (a database for development, an API to test against), you publish its port.
"Port already allocated" and "running but not reachable" are two of the most common support questions you will
answer. Now you know: check `docker ps` for the arrow, check which port the app really listens on, check who owns
the host port.

## Part 2 · Environment variables

Applications need configuration: which environment they run in, where the database is, which greeting to show. The
standard way to give a container its configuration is **environment variables**.

### Set one

<!-- test: contains=APP_ENV=development -->
```bash
docker run --rm -e APP_ENV=development alpine:3.24 env
```

`-e NAME=value` sets a variable inside the container. `env` lists all of them: a few that Docker always sets
(`PATH`, `HOSTNAME`, `HOME`) plus yours.

Several at once, or from a file:

<!-- test: contains=APP_ENV=staging; contains=GREETING=Hi there -->
```bash
printf 'APP_ENV=staging\nGREETING=Hi there\n' > demo.env
docker run --rm --env-file demo.env alpine:3.24 env
rm demo.env
```

`--env-file` reads one `NAME=value` per line. That is handy when there are many settings.

### Configuration that changes behaviour

A real application reads those variables. The PostgreSQL image is a great example. Let's start a database without any
configuration:

<!-- test: fail; contains=superuser password is not specified -->
```bash
docker run --name db postgres:18-alpine
```

It stopped immediately (and gave us the terminal back). Before changing anything, let's investigate:

<!-- test: retry=20; contains=Exited (1) -->
```bash
docker ps -a --filter name=db --format '{{.Names}}: {{.Status}}'
```

<!-- test: retry=15; output; contains=POSTGRES_PASSWORD -->
```bash
docker logs db
```

```text
Error: Database is uninitialized and superuser password is not specified.
       You must specify POSTGRES_PASSWORD to a non-empty value for the
       superuser. For example, "-e POSTGRES_PASSWORD=password" on "docker run".

       You may also use "POSTGRES_HOST_AUTH_METHOD=trust" to allow all
       connections without a password. This is *not* recommended.

       See PostgreSQL documentation about "trust":
       https://www.postgresql.org/docs/current/auth-trust.html
```

- **Symptom:** the container exits with code 1.
- **Evidence:** the logs say `Database is uninitialized and superuser password is not specified` and even tell us the
  fix: `-e POSTGRES_PASSWORD=password`.
- **Root cause:** a required environment variable is missing. The image refuses to create a database without a
  password, on purpose.

Fix and verify:

```bash
docker rm db
docker run -d --name db -e POSTGRES_PASSWORD=lab-only-password postgres:18-alpine
```

<!-- test: retry=20; contains=accepting connections -->
```bash
docker exec db pg_isready
```

`pg_isready` answers `accepting connections` once the database is up (the test retries for a few seconds; on your
machine just run it again if it says "no response").

### Inspect a container's environment

Where can you check what a container was started with? `docker inspect`:

<!-- test: contains=POSTGRES_PASSWORD=lab-only-password -->
```bash
docker inspect db --format '{{json .Config.Env}}'
```

There is our password, in plain text. Anyone who can run `docker inspect` on this machine can read it. For a local lab
that is fine. For real secrets it is not, and in chapter 08 we will pass the password as a **file** instead.

```bash
docker rm -f db
```

### Experiment: our own app, configured from outside

`examples/simple-app/app.py` reads `APP_ENV` and `GREETING`. Let's build it (you will learn exactly what `docker build`
does in the next chapter; for now, trust it):

<!-- test: timeout=600; contains=simple-app:1.0 -->
```bash
docker build -t simple-app:1.0 examples/simple-app
docker images simple-app
```

Run it twice with different configuration:

```bash
docker run -d --name simple -p 5000:5000 simple-app:1.0
```

<!-- test: retry=15; output; contains=environment: production -->
```bash
curl -s http://localhost:5000
```

```text
Hello from simple-app!
environment: production
container hostname: b0c31ba226d1
```

```bash
docker run -d --name simple2 -p 5001:5000 -e APP_ENV=development -e GREETING="Good morning from Docker" simple-app:1.0
```

<!-- test: retry=15; output; contains=Good morning from Docker!; contains=environment: development -->
```bash
curl -s http://localhost:5001
```

```text
Good morning from Docker!
environment: development
container hostname: e35975d7f688
```

Same image, byte for byte. Different behaviour, decided at run time. This is one of the most important ideas in
containers: **build the image once, configure it per environment** (development, test, production) with environment
variables.

Notice also the third line: each answer comes from a different container hostname.

```bash
docker rm -f simple simple2
```

### Where would I use this as a DevOps engineer?

The same image is promoted from test to production; only the environment variables change: database host, log level,
feature flags. When an app behaves differently in two places, `docker inspect --format '{{json .Config.Env}}'` is how
you compare the two configurations in seconds.

## What you learned

- `-p HOST:CONTAINER` publishes a port; without it, nothing outside reaches the container.
- How to investigate "running but not reachable" and "port is already allocated".
- `-e` and `--env-file` set environment variables; `docker inspect` shows them.
- Missing configuration makes good images fail fast, with a message in `docker logs`.
- One image, many configurations.

## Try it yourself

- Labs: [04-port-mapping](../labs/04-port-mapping/README.md), [05-environment-variables](../labs/05-environment-variables/README.md)
- Troubleshooting: [02-port-already-in-use](../troubleshooting/02-port-already-in-use/README.md)
- Challenges: the "Ports and configuration" section of [challenges/README.md](../challenges/README.md)
- Deeper: [docs/07-ports.md](../docs/07-ports.md), [docs/08-environment-variables.md](../docs/08-environment-variables.md)

## Next

[03 · Dockerfiles](03-dockerfiles.md)
