# Bind Mounts

## What is it?

A **bind mount** connects a folder (or a single file) **on your computer** to a path **inside a container**.
It is not a copy. Both sides look at the same files: change a file on your computer and the container sees the
change immediately, and the other way round.

```text
   Your computer (the "host")                    Container
  ┌──────────────────────────────┐             ┌───────────────────────────────┐
  │ examples/nginx/site/         │   bind      │ /usr/share/nginx/html/        │
  │   index.html  ◄──────────────┼── mount ───►│   index.html                  │
  │   (you edit it in VS Code)   │  same files │   (nginx serves it)           │
  └──────────────────────────────┘             └───────────────────────────────┘
```

## Why do we need it?

Rebuilding an image every time you change one line of HTML or code is slow. During **local development** you want
to edit files with your normal editor and see the result in the running container at once. Bind mounts give you
exactly that. They are also how you hand a container a single configuration file (the capstone mounts
`database/init.sql` into the PostgreSQL container this way).

## How does it work?

Docker asks the Linux kernel to make a host path visible at a container path. There are two ways to write it:

```text
-v   HOST_PATH:CONTAINER_PATH[:ro]                                  short, older syntax
--mount type=bind,src=HOST_PATH,dst=CONTAINER_PATH[,readonly]       long, explicit syntax
```

| | `-v` | `--mount` |
|---|---|---|
| Host path does not exist | Docker **creates an empty folder** for you (often hiding a typo) | Native Linux **refuses**: `bind source path does not exist`. Docker Desktop (Windows/Mac) may create it instead |
| Readability | short | every part is named |
| Read-only | `:ro` at the end | `,readonly` |

**Volume vs bind mount** (see [12-volumes.md](12-volumes.md)):

| | Named volume | Bind mount |
|---|---|---|
| Where the data lives | managed by Docker (`docker volume inspect`) | a folder **you** chose on your computer |
| Created with | `-v mydata:/path` (a name) | `-v "$(pwd)/folder":/path` (a path) |
| Best for | database data, anything the app owns | source code, config files during development |
| Survives `docker rm` | yes | yes (it is your folder) |
| Portable between machines | yes | depends on your folder layout |

The rule of thumb: **if the value before the `:` is a path, it is a bind mount; if it is a plain name, it is a volume.**

> **Windows users:** use WSL2 (recommended) or PowerShell. In PowerShell write `${PWD}` instead of `$(pwd)`.
> In Git Bash run `export MSYS_NO_PATHCONV=1` first, otherwise Git Bash rewrites `/usr/share/...` into a Windows path.

## Prerequisites

- [12-volumes.md](12-volumes.md) (what a volume is)
- [07-ports.md](07-ports.md) (`-p 8080:80`)

## Hands-on Lab

The full lab is [labs/10-bind-mounts](../labs/10-bind-mounts/README.md). The short version:

```bash
cd examples/nginx
docker run -d --name web -p 8080:80 -v "$(pwd)/site":/usr/share/nginx/html:ro nginx:1.30-alpine
```

<!-- test: retry=15; contains=Hello from my container -->
```bash
curl -s http://localhost:8080
```

nginx now serves the files from `examples/nginx/site/`, not the default nginx page. Let's add a new file **on the
host** and ask the container for it, without restarting anything:

<!-- test: retry=5; contains=Added on the host -->
```bash
echo "<h1>Added on the host, seen by the container</h1>" > site/live.html
curl -s http://localhost:8080/live.html
```

## Expected Result

- The first `curl` returns the page from `site/index.html` ("Hello from my container!").
- The second `curl` returns the file you just created on your computer. No rebuild, no restart.

## Experiment

The mount is `:ro` (read-only) for the container. Your computer can still write, but the container cannot:

<!-- test: fail; contains=Read-only file system -->
```bash
docker exec web sh -c "echo hacked > /usr/share/nginx/html/index.html"
```

That is a good default for anything a container only needs to **read**.

Clean up the experiment file:

```bash
rm site/live.html
docker rm -f web
```

## Break It

A typo in the host path is one of the most common real mistakes. With `-v`, Docker silently creates the missing
folder, so the container starts happily and serves... an empty folder:

```bash
docker run -d --name web -p 8080:80 -v "$(pwd)/sitee":/usr/share/nginx/html nginx:1.30-alpine
```

<!-- test: retry=15; contains=403 -->
```bash
curl -s http://localhost:8080
```

nginx answers **403 Forbidden**: there is no `index.html` in an empty folder.

## Troubleshoot It

Observe → investigate → root cause → fix → verify.

<!-- test: contains=sitee -->
```bash
docker inspect web --format '{{json .Mounts}}'
```

The `Source` shows `.../sitee`: a folder you never meant to use. Check the host:

<!-- test: contains=sitee -->
```bash
ls -d sitee
```

Root cause: a typo in the host path, and `-v` created the folder instead of complaining. Fix it, then verify:

```bash
docker rm -f web
rmdir sitee
docker run -d --name web -p 8080:80 -v "$(pwd)/site":/usr/share/nginx/html:ro nginx:1.30-alpine
```

<!-- test: retry=15; contains=Hello from my container -->
```bash
curl -s http://localhost:8080
```

Use `--mount` when you want Docker to **refuse** a missing path on Linux (Docker Desktop may still create it).
The full investigation is in [troubleshooting/09-host-changes-not-reflected](../troubleshooting/09-host-changes-not-reflected/README.md).

```bash
docker rm -f web
```

## Common Mistakes

- Relative paths: `-v site:/usr/share/nginx/html` is a **volume named "site"**, not your folder. Use `"$(pwd)/site"`.
- Forgetting the quotes around `"$(pwd)/..."` when the path contains spaces.
- Mounting over a folder that already has files in the image: the image's files are **hidden** while the mount exists.
- Editing files on the host for a container that was started from an image built with `COPY` and no mount: nothing
  changes until you rebuild.
- Git Bash on Windows rewriting container paths (use WSL2, PowerShell, or `MSYS_NO_PATHCONV=1`).

## Best Practices

- Bind mounts for development and for single config files; named volumes for data the application owns.
- Add `:ro` whenever the container only reads.
- Prefer `--mount` in scripts so a wrong path fails loudly (on Linux).
- Never bind-mount your whole home folder or `/` into a container.

## Challenge

**Task:** serve the page from `examples/nginx/site` on port 8082, read-only, using the `--mount` syntax instead of `-v`.

**Requirements:** container name `web2`; `curl http://localhost:8082` shows "Hello from my container".

**Hints:** `--mount type=bind,src=...,dst=...,readonly`.

## Solution

<details><summary>Solution</summary>

Still inside `examples/nginx`:

```bash
docker run -d --name web2 -p 8082:80 --mount type=bind,src="$(pwd)/site",dst=/usr/share/nginx/html,readonly nginx:1.30-alpine
```

<!-- test: retry=15; contains=Hello from my container -->
```bash
curl -s http://localhost:8082
docker rm -f web2
```

`--mount` names every part (`type`, `src`, `dst`, `readonly`), which makes the command longer but much easier to read.
</details>

## Verification

- [ ] I can explain the difference between a bind mount and a named volume.
- [ ] I can start nginx with my own folder mounted and see live changes.
- [ ] I know why a typo in a `-v` path gives an empty folder (and a 403 from nginx).
- [ ] I know how to make a mount read-only.

## Real-World Usage

DevOps engineers use bind mounts for **local development environments** (code mounted into a container with
the right language version), for **configuration files** (nginx configs, database init scripts) and for
**sharing build output** between the host and a container. Production data usually lives on named volumes or
managed storage instead.

## Key Takeaways

- A bind mount is a live window from the container into a folder on your computer.
- Path before the `:` → bind mount; plain name → volume.
- `-v` creates missing folders silently; `--mount` (on Linux) refuses them.
- Use `:ro` when the container only needs to read.

Next: [14-networking.md](14-networking.md)
