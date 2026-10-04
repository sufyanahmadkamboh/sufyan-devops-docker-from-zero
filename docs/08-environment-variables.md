# Environment Variables

> Lesson 08 · about 30 minutes · you need: [07 · Ports](07-ports.md)

## What is it?

An **environment variable** is a named value (`APP_ENV=production`) that the operating system
hands to every program it starts. Docker lets you set environment variables for the main process
of a container with `-e NAME=value` (or a file with `--env-file`). Programs read them to decide how
to behave.

```text
   docker run -e APP_ENV=development -e GREETING="Hi" simple-app:1.0
                    |                        |
                    v                        v
           +--------------------------------------------+
           | container                                  |
           |   environment:  APP_ENV=development        |
           |                 GREETING=Hi                |
           |                 PATH=... (from the image)  |
           |   python app.py  -> os.environ["APP_ENV"]  |
           +--------------------------------------------+
```

## Why do we need it?

You want **one image** for every environment. The code is the same in development, test and
production; only the **configuration** differs: database host, log level, feature flags, a
greeting text. Environment variables carry that configuration **into** the container at start
time, so you never rebuild the image just to change a setting. This idea is part of the widely
used "twelve-factor app" guidelines.

## How does it work?

Values can come from three places. Later ones win:

```text
   1. ENV in the Dockerfile          ENV APP_ENV=production        (default, baked into the image)
   2. --env-file on docker run       APP_ENV=staging   (file)      (overrides 1)
   3. -e on docker run               -e APP_ENV=development        (overrides 1 and 2)
```

| Syntax | Meaning |
|---|---|
| `-e NAME=value` | set NAME to value |
| `-e NAME` | copy NAME's value from **your** terminal's environment |
| `--env-file app.env` | read many `NAME=value` lines from a file |

The program must actually **read** the variable. `examples/simple-app/app.py` does:

```python
APP_ENV = os.environ.get("APP_ENV", "development")
GREETING = os.environ.get("GREETING", "Hello from simple-app")
```

## Prerequisites

- Lessons 04–07. This lesson also builds `examples/simple-app` (a few seconds; lesson
  [09 · Dockerfile](09-dockerfile.md) explains how).

## Hands-on Lab

See a container's environment. `env` prints every variable of the process:

<!-- test: contains=APP_ENV=development; output -->
```bash
docker run --rm -e APP_ENV=development -e TEAM=platform alpine:3.24 env
```

```text
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
HOSTNAME=e1a60ee19fb5
APP_ENV=development
TEAM=platform
HOME=/root
```

Now with a real app. Build `simple-app` and run it twice with different configuration:

<!-- test: timeout=600 -->
```bash
docker build -q -t simple-app:1.0 examples/simple-app
```

```bash
docker run -d --name prod -p 5000:5000 simple-app:1.0
```

<!-- test: retry=15; contains=environment: production -->
```bash
curl -s http://localhost:5000
```

```bash
docker run -d --name dev -p 5001:5000 -e APP_ENV=development -e GREETING="Hi from the dev container" simple-app:1.0
```

<!-- test: retry=15; contains=Hi from the dev container; contains=environment: development -->
```bash
curl -s http://localhost:5001
```

Same image, two behaviours. The full lab is
[labs/05-environment-variables](../labs/05-environment-variables/README.md).

## Expected Result

- `env` lists `APP_ENV=development` and `TEAM=platform`, plus `PATH` and `HOSTNAME`, which Docker
  and the image always provide.
- `prod` answers with `environment: production` (the Dockerfile's `ENV` default).
- `dev` answers with `Hi from the dev container!` and `environment: development` (`-e` overrides).

## Experiment

Read a running container's configuration from the outside, without entering it:

<!-- test: contains=APP_ENV=development; output -->
```bash
docker inspect dev --format '{{range .Config.Env}}{{println .}}{{end}}'
```

```text
APP_ENV=development
GREETING=Hi from the dev container
PATH=/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
PYTHON_VERSION=3.14.8
PYTHON_SHA256=c2215904f02b175596dc49351585104f4bc20341e1c47378b26a2c274360ce73
```

…or from the inside:

<!-- test: contains=development -->
```bash
docker exec dev printenv APP_ENV
```

Use an env file for many values:

```bash
printf 'APP_ENV=staging\nGREETING=From a file\n' > staging.env
docker run -d --name staging -p 5002:5000 --env-file staging.env simple-app:1.0
rm staging.env
```

<!-- test: retry=15; contains=From a file; contains=environment: staging -->
```bash
curl -s http://localhost:5002
```

Note: in an env file, quotes are taken literally, so write `GREETING=From a file` without quotes.

## Break It

Some images **require** a setting. PostgreSQL refuses to create a database without a password:

<!-- test: fail -->
```bash
docker run --name pg postgres:18-alpine
```

## Troubleshoot It

- **Observe:** the command returns immediately; the message starts with
  `Error: Database is uninitialized and superuser password is not specified.`
- **Investigate:**

<!-- test: retry=20; contains=Exited (1); contains=POSTGRES_PASSWORD -->
```bash
docker ps -a --filter name=pg --format '{{.Names}}: {{.Status}}'
docker logs pg
```

- **Root cause:** the required variable `POSTGRES_PASSWORD` was not set. The image's documentation
  on Docker Hub lists the variables it understands.
- **Fix:** start a new container with the variable (options cannot be added to an existing container):

```bash
docker rm pg
docker run -d --name pg -e POSTGRES_PASSWORD=lab-only-password postgres:18-alpine
```

- **Verify:** after a few seconds, `docker ps` shows `pg` as **Up**, and the logs end with
  `database system is ready to accept connections`:

<!-- test: retry=20; contains=ready to accept connections -->
```bash
docker ps --filter name=pg --format '{{.Names}}: {{.Status}}'
docker logs pg 2>&1 | tail -3
```

The same pattern for our own API is scenario
[06 · environment variable missing](../troubleshooting/06-environment-variable-missing/README.md).

## Common Mistakes

- Setting a variable with `-e` that the app never reads (check the app's docs or code).
- Forgetting that `-e` goes **before** the image name: `docker run -e A=1 image`, not `docker run image -e A=1`
  (after the image name it becomes an argument for the container's command).
- Expecting `docker restart` to pick up new values. Environment is fixed at creation; recreate the container.
- Putting real passwords in `-e`: anyone who can run `docker inspect` can read them
  (lesson [19 · Security Basics](19-security-basics.md) shows secret files instead).
- Quoting values inside `--env-file`: the quotes become part of the value.
- (macOS) "port is already allocated" on 5000: the AirPlay Receiver uses port 5000. Use another
  host port (`-p 5050:5000`) or switch AirPlay Receiver off in System Settings.

## Best Practices

- Give every setting a sensible default in the Dockerfile (`ENV APP_ENV=production`) or in code.
- Let the app **fail fast** with a clear message when a required setting is missing.
- Keep env files out of git when they contain secrets (`.gitignore`, `.dockerignore`).
- Use Docker secrets/secret files for passwords in anything shared or deployed.

## Challenge

Run `simple-app:1.0` on host port 5005 so that it answers `Welcome to the challenge!` and
`environment: challenge`, using exactly two `-e` options. Prove it with curl and with `docker inspect`.

## Solution

<details><summary>Show the solution</summary>

`app.py` adds the `!` itself, so the greeting is `Welcome to the challenge`:

```bash
docker run -d --name challenge -p 5005:5000 -e APP_ENV=challenge -e GREETING="Welcome to the challenge" simple-app:1.0
```

<!-- test: retry=15; contains=Welcome to the challenge!; contains=environment: challenge -->
```bash
curl -s http://localhost:5005
```

<!-- test: contains=APP_ENV=challenge -->
```bash
docker inspect challenge --format '{{range .Config.Env}}{{println .}}{{end}}' | grep -E 'APP_ENV|GREETING'
```

</details>

## Verification

- [ ] You can set variables with `-e` and `--env-file`.
- [ ] You know the order of precedence (Dockerfile ENV < env file < -e).
- [ ] You can read a container's environment with `docker inspect` and `docker exec printenv`.
- [ ] You can diagnose a container that exits because a variable is missing.

Clean up:

```bash
docker rm -f prod dev staging pg challenge
```

## Real-World Usage

- Every 12-factor style service is configured through environment variables: database URLs,
  log levels, feature flags.
- The same image moves from test to production; only the variables change.
- Platforms (Compose, and later orchestrators) inject environment variables per environment.

## Key Takeaways

- Environment variables configure a container at start time; the image stays the same.
- Precedence: Dockerfile `ENV` < `--env-file` < `-e`.
- Read them with `docker inspect` or `docker exec ... printenv`.
- Passwords in env vars are visible to anyone with Docker access: use secrets for real systems.
- Next: [09 · Dockerfile](09-dockerfile.md).
