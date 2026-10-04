# Security Basics

## What is it?

Beginner-level Docker security is a handful of habits that remove the most common risks:

1. **Do not run as root** inside the container (`USER` in the Dockerfile).
2. **Use small, trusted, pinned images** (official images, a specific tag like `python:3.14-slim`).
3. **Scan images** for known vulnerabilities.
4. **Keep secrets out of environment variables and images** (use files / Docker secrets).
5. **Least privilege**: read-only filesystem, no extra Linux capabilities, publish only needed ports.

This lesson is deliberately basic. It gives you the right instincts, not an advanced security course.

## Why do we need it?

A container is isolated, but not a security boundary as strong as a virtual machine: it shares the host's kernel.
If an attacker breaks into your application, what they can do next depends on these settings. Root user + writable
filesystem + all capabilities + a password in an environment variable is the attacker's best case. Every habit above
takes something away from them.

## How does it work?

```text
   Dockerfile / docker run             What it takes away from an attacker
  ┌─────────────────────────────┐
  │ FROM python:3.14-slim       │  fewer packages = fewer vulnerabilities, no compilers
  │ RUN useradd ... appuser     │
  │ USER appuser                │  not root: cannot change system files or install tools
  │ --read-only                 │  cannot modify the app or drop malware on disk
  │ --cap-drop ALL              │  root (if any) loses special kernel powers (chown, raw sockets, ...)
  │ secrets as files            │  passwords are not visible in docker inspect / child processes
  │ publish only the web port   │  database and API are not reachable from outside
  └─────────────────────────────┘
```

**Root vs non-root.** By default, the process in most images runs as **root (uid 0)**. `USER appuser` in the
Dockerfile (or `--user` at run time) changes that. The simple-app and capstone images already do it.

**Secrets vs environment variables.** Environment variables are easy, but anyone who can run `docker inspect` (and
every child process) can read them. Docker Compose `secrets:` mounts the value as a **file** in `/run/secrets/`
instead. The official PostgreSQL image reads `POSTGRES_PASSWORD_FILE`; the message board API reads `DB_PASSWORD_FILE`.

**Image scanning.** A scanner compares the packages inside an image with public vulnerability databases. Docker
Desktop includes Docker Scout; the free open-source scanner Trivy runs as a container. Scanning is a concept to know
here; it is optional in this course.

## Prerequisites

- [09-dockerfile.md](09-dockerfile.md), [08-environment-variables.md](08-environment-variables.md)

## Hands-on Lab

Full lab: [labs/15-security](../labs/15-security/README.md). Who am I in a default container?

<!-- test: contains=root -->
```bash
docker run --rm alpine:3.24 whoami
```

Now the simple-app image, which has `USER appuser` in its Dockerfile:

```bash
cd examples/simple-app
docker build -t simple-app:1.0 .
```

<!-- test: contains=uid=10001 -->
```bash
docker run --rm simple-app:1.0 id
```

## Expected Result

- `alpine` answers `root`.
- simple-app answers `uid=10001(appuser) gid=10001(appuser) ...`: the application runs as an ordinary user.

## Experiment

**Read-only filesystem:** the container cannot write anywhere (except mounted volumes or tmpfs).

<!-- test: fail; contains=Read-only file system -->
```bash
docker run --rm --read-only alpine:3.24 touch /hacked
```

**Dropping capabilities:** even root loses special powers such as changing file owners.

<!-- test: fail; contains=Operation not permitted -->
```bash
docker run --rm --cap-drop ALL alpine:3.24 chown nobody /tmp
```

**Optional: scan an image** with Trivy (downloads a vulnerability database; takes a minute the first time):

<!-- test: skip -->
```bash
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy:0.75.0 image --severity HIGH,CRITICAL simple-app:1.0
```

## Break It

Pass a password the "easy" way:

```bash
docker run -d --name leaky -e DB_PASSWORD=super-secret-123 nginx:1.30-alpine
```

<!-- test: contains=super-secret-123 -->
```bash
docker inspect leaky --format '{{json .Config.Env}}'
```

Anyone with access to the Docker engine can read it, and it often ends up in logs and screenshots.

## Troubleshoot It

The fix is to pass the secret as a **file**, mounted read-only, and let the program read the file. A simple version
with a bind mount (Compose `secrets:` does the same thing for you):

```bash
docker rm -f leaky
printf 'super-secret-123' > db_password.txt
docker run -d --name safer -v "$(pwd)/db_password.txt":/run/secrets/db_password:ro -e DB_PASSWORD_FILE=/run/secrets/db_password nginx:1.30-alpine
```

<!-- test: absent=super-secret-123 -->
```bash
docker inspect safer --format '{{json .Config.Env}}'
```

<!-- test: retry=5; contains=super-secret-123 -->
```bash
docker exec safer cat /run/secrets/db_password
```

Verified: `inspect` only shows the **path** of the secret, while the file is still available to the process that
needs it. Clean up (and never commit secret files: list them in `.gitignore`):

```bash
docker rm -f safer
rm db_password.txt
```

## Common Mistakes

- `FROM something:latest` from an unknown publisher.
- Copying `.env` or private keys into the image with `COPY . .` (use `.dockerignore`, see [11-dockerignore.md](11-dockerignore.md)).
- Putting passwords in `ENV` inside the Dockerfile: they are stored in the image forever (`docker history` shows them).
- Running as root "because it is easier", or adding `--privileged` to make an error go away.
- Publishing the database port to the whole network.

## Best Practices

- Official or verified images, pinned to a version tag.
- `USER` with a fixed numeric uid in every Dockerfile you write.
- `--read-only` (+ `tmpfs` for `/tmp`) and `--cap-drop ALL` where the app allows it; the capstone API runs read-only.
- Secrets as files, never in images, never in Git.
- Scan images regularly and rebuild them to pick up security updates.

## Challenge

**Task:** run `nginx:1.30-alpine` so that its filesystem is read-only, yet it still starts and serves the welcome
page on port 8081.

**Hints:** nginx writes temporary files to `/var/cache/nginx` and its PID file to `/run`. `--tmpfs PATH` gives a container a small
writable in-memory folder.

## Solution

<details><summary>Solution</summary>

```bash
docker run -d --name ro-web -p 8081:80 --read-only --tmpfs /var/cache/nginx --tmpfs /run nginx:1.30-alpine
```

<!-- test: retry=15; contains=Welcome to nginx -->
```bash
curl -s http://localhost:8081
```

<!-- test: fail; contains=Read-only file system -->
```bash
docker exec ro-web touch /usr/share/nginx/html/hacked
```

```bash
docker rm -f ro-web
```

Without the two `--tmpfs` folders nginx exits at start-up because it cannot create its cache and PID files. Try it:
`docker logs` will tell you exactly which path it needed.
</details>

## Verification

- [ ] I can check which user a container runs as, and change it with `USER` / `--user`.
- [ ] I can run a container with a read-only filesystem and without capabilities.
- [ ] I know why passwords do not belong in environment variables or images.
- [ ] I know what an image scanner does.

## Real-World Usage

Security reviews and platform policies check exactly these points: non-root, pinned base images, no secrets in images,
scanned images, minimal privileges. Getting them right from your first Dockerfile saves painful rework later.

## Key Takeaways

- Containers run as root by default; change it with `USER`.
- Small, official, pinned images; scan them.
- Secrets as files, not environment variables, never in images.
- Read-only filesystem and dropped capabilities limit the damage of a break-in.

Next: [20-image-optimization.md](20-image-optimization.md)
