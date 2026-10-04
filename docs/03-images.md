# Images

> Lesson 03 · about 30 minutes · you need: [02 · Installation](02-docker-installation.md) done

## What is it?

A Docker **image** is a read-only package that contains:

- a filesystem: the files of a small operating-system userland (for example Alpine or Debian),
  plus the language runtime, libraries and your application;
- metadata: which command to start, which user to run as, default environment variables,
  which port the app listens on.

An image never runs by itself. You start a **container** from it. One image can start many
containers, just like one recipe can be cooked many times.

```text
         IMAGE (read-only)                          CONTAINERS (running instances)
   +----------------------------+
   | nginx:1.30-alpine          |   docker run   +---------------------+
   |  - Alpine Linux files      | -------------> | web   (running)     |
   |  - nginx binary            |                +---------------------+
   |  - default config          |   docker run   +---------------------+
   |  - CMD: nginx -g daemon off| -------------> | web2  (running)     |
   +----------------------------+                +---------------------+
```

## Why do we need it?

An image is the **unit of delivery** in the container world. Instead of "install Python 3.14,
then pip install these packages, then copy these files", you ship one image that already contains
all of that. The same image runs on your laptop, on a colleague's laptop, and on a server.

## How does it work?

### Image names

A full image name has four parts. Docker fills in defaults for the parts you leave out:

```text
   docker.io / library / nginx : 1.30-alpine
   ---------   -------   -----   -----------
   registry    namespace  repo     tag

   nginx                         ->  docker.io/library/nginx:latest
   nginx:1.30-alpine             ->  docker.io/library/nginx:1.30-alpine
   sufibaba6629/docker-from-zero-web:1.0.0
                                 ->  docker.io/sufibaba6629/docker-from-zero-web:1.0.0
```

- **registry:** where the image lives (`docker.io` = Docker Hub, the default).
- **namespace:** the account. `library` is reserved for **official images** maintained with Docker.
- **repository:** the image's name.
- **tag:** a label for a version. If you omit it, Docker uses `latest`.

### Tags versus digests

A **tag** is a movable label: the owner can point `nginx:1.30-alpine` at a newer build tomorrow
(for example after a security fix). A **digest** (`sha256:...`) identifies one exact image
content and never changes.

`latest` is just a tag name; it does **not** mean "newest". It means "whatever the owner tagged
`latest`". That is why this course always names a version (`nginx:1.30-alpine`). The one
exception is `hello-world`, which has no meaningful versions.

### Layers

An image is a stack of read-only **layers**. Each layer is a set of file changes. Images that
share a base share those layers on disk, so ten Alpine-based images do not store Alpine ten times.
Lesson [10 · Image Layers](10-image-layers.md) goes deeper.

```text
   +---------------------------+   <- your app files
   +---------------------------+   <- pip install flask
   +---------------------------+   <- python runtime
   +---------------------------+   <- debian slim base
```

## Prerequisites

- A working Docker installation (`docker run hello-world` works).

## Hands-on Lab

Download (pull) an image from Docker Hub without starting it:

<!-- test: contains=nginx:1.30-alpine; output=head:12 -->
```bash
docker pull nginx:1.30-alpine
```

```text
1.30-alpine: Pulling from library/nginx
Digest: sha256:0985e772fb9f729e6fa0980da05fca5d9c468e870eed43071545afa9d2e27d94
Status: Image is up to date for nginx:1.30-alpine
docker.io/library/nginx:1.30-alpine
```

List the images stored on your computer:

<!-- test: contains=nginx; output -->
```bash
docker images nginx
```

```text
IMAGE               ID             DISK USAGE   CONTENT SIZE   EXTRA
nginx:1.30-alpine   0985e772fb9f       93.6MB           27MB        
```

The full step-by-step version is part of [labs/01-first-container](../labs/01-first-container/README.md).

## Expected Result

- `docker pull` prints one line per layer (`Pull complete` or `Download complete`), then a
  `Digest: sha256:...` line and `Status: Downloaded newer image for nginx:1.30-alpine`.
- `docker images nginx` shows one line per image: **IMAGE** (`nginx:1.30-alpine`), **ID** (the first 12
  characters of the image's own hash), **DISK USAGE**, **CONTENT SIZE** (what was downloaded) and **EXTRA** (`U` when a
  container uses it). Docker versions before 29, and `docker images --format table`, show the classic columns
  REPOSITORY, TAG, IMAGE ID, CREATED (when the image was built by its maintainer) and SIZE.

## Experiment

Pull the same image again. Docker compares digests, sees that it already has it, and downloads
nothing:

<!-- test: contains=Image is up to date -->
```bash
docker pull nginx:1.30-alpine
```

Pull a second, unrelated image and compare sizes. `alpine` is a complete (tiny) Linux userland:

<!-- test: output -->
```bash
docker pull -q alpine:3.24
docker images --format 'table {{.Repository}}:{{.Tag}}\t{{.Size}}' | grep -E 'alpine|REPOSITORY'
```

```text
docker.io/library/alpine:3.24
REPOSITORY:TAG                   SIZE
nginx:1.30-alpine                93.6MB
postgres:18-alpine               433MB
alpine:3.24                      13MB
```

Look at how an image was configured. `docker image inspect` prints its metadata as JSON; the
`--format` option picks out single fields (here: the command and the exposed ports):

<!-- test: contains=nginx; output -->
```bash
docker image inspect nginx:1.30-alpine --format 'CMD: {{.Config.Cmd}}  ports: {{.Config.ExposedPorts}}'
```

```text
CMD: [nginx -g daemon off;]  ports: map[80/tcp:{}]
```

## Break It

Ask for a tag that does not exist:

<!-- test: fail; contains=not found -->
```bash
docker pull nginx:9.99-alpine
```

## Troubleshoot It

- **Observe:** the pull fails with a message that the manifest for `nginx:9.99-alpine` is
  **not found** (wording differs slightly between Docker versions).
- **Investigate:** the repository exists (it is `nginx`), so the problem is the tag. Check the
  available tags on the image's page on Docker Hub (<https://hub.docker.com/_/nginx>, tab "Tags").
- **Root cause:** a tag that was never published.
- **Fix:** use an existing tag, for example `nginx:1.30-alpine`.
- **Verify:** `docker pull nginx:1.30-alpine` ends with `Status: ... nginx:1.30-alpine`.

## Common Mistakes

- Using `latest` and getting a different version next month without noticing.
- Thinking `CREATED` in `docker images` is the download date. It is the build date.
- Deleting an image that a container still uses: Docker refuses (`image is being used by stopped
  container`). Remove the container first.
- Pulling random images from unknown accounts. Anyone can publish to Docker Hub.

## Best Practices

- Pin a version tag (`postgres:18-alpine`, `python:3.14-slim`). For maximum reproducibility,
  pin the digest too: `nginx:1.30-alpine@sha256:...`.
- Prefer **Docker Official Images** (`library/...`) and **Verified Publisher** images.
- Prefer small variants (`-alpine`, `-slim`) when they work for your app: less to download,
  fewer packages that could contain vulnerabilities.
- Remove images you no longer need (`docker rmi`, lesson [05 · Docker CLI](05-docker-cli.md)).

## Challenge

Pull `busybox:1.37` and find out its size and the command it runs by default, without starting
a container.

## Solution

<details><summary>Show the solution</summary>

<!-- test: contains=sh; output -->
```bash
docker pull -q busybox:1.37
docker images busybox:1.37 --format '{{.Repository}}:{{.Tag}} is {{.Size}}'
docker image inspect busybox:1.37 --format 'default command: {{.Config.Cmd}}'
```

```text
docker.io/library/busybox:1.37
busybox:1.37 is 6.77MB
default command: [sh]
```

The default command is a shell (`sh`). Started without a terminal, a shell has nothing to do and
exits immediately; lesson [06 · Container Lifecycle](06-container-lifecycle.md) explains why.

</details>

## Verification

- [ ] You can explain registry / namespace / repository / tag.
- [ ] You can pull an image and list your images.
- [ ] You can explain why `latest` is risky.
- [ ] You can read an image's default command with `docker image inspect`.

## Real-World Usage

- Teams publish their applications as images to a registry; deployments pull a specific tag
  (often a version number or a git commit) so they know exactly what runs.
- Security teams scan images for known vulnerabilities and require trusted base images.
- Pinning tags and digests keeps builds reproducible: the build next year uses the same base.

## Key Takeaways

- An image is a read-only package of files plus metadata; containers are started from it.
- Name format: `registry/namespace/repository:tag`; defaults are `docker.io`, `library`, `latest`.
- Tags can move, digests cannot. Never rely on `latest`.
- Images are made of shared layers.
- Next: [04 · Containers](04-containers.md).
