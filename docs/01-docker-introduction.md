# Docker Introduction

> Lesson 01 · about 20 minutes · you need: nothing yet (Docker installed is a bonus; see [02 · Installation](02-docker-installation.md))

## What is it?

Docker is a tool that packages an application **together with everything it needs to run**
(the right language version, libraries, configuration files, a small operating-system userland)
into one unit called an **image**. When you start an image, you get a **container**: a normal
process on your computer that is isolated from the other processes, with its own files, its own
network address and its own view of the system.

Think of a shipping container. The port crane does not care whether the container holds bananas
or car parts: every container has the same shape, so every crane, ship and truck can move it.
Docker does the same for software. Every container is started, stopped, moved and inspected with
the same commands, whatever is inside.

```text
   Without Docker                         With Docker
   --------------                         -----------
   "It works on my machine"               The machine is part of the package

   your laptop:   Python 3.12             image: python:3.14-slim
   test server:   Python 3.10               + Flask 3.1.3
   production:    Python 3.14 ???           + your app.py
                                          same image on every computer
```

## Why do we need it?

Before containers, installing an application meant following a long list of manual steps on
every server: install this package, that library, copy these files, set those variables. Every
server ended up slightly different, and the differences caused bugs that nobody could reproduce.

Docker solves four everyday problems:

| Problem | How Docker helps |
|---|---|
| "It works on my machine" | The image contains the exact versions, so it runs the same everywhere |
| Slow, manual setup | `docker run` starts a complete PostgreSQL, nginx or Python in seconds |
| Conflicts between apps | Two containers can use different Python versions on the same computer |
| Messy clean-up | Remove the container and nothing is left behind on your computer |

## How does it work?

Docker is a **client-server** system. The command you type (`docker run ...`) is only the
client. It sends a request to the **Docker Engine** (the daemon, `dockerd`), which does the work:
it downloads images from a **registry**, and asks **containerd** and **runc** to create the
isolated process.

```text
   You
    |
    v
 +-------------------+        REST API         +---------------------------------------+
 |  docker CLI       | ----------------------> |  Docker Engine (dockerd)              |
 |  docker compose   |                         |    images · networks · volumes        |
 +-------------------+                         |         |                             |
                                               |         v                             |
                                               |    containerd  -->  runc              |
                                               |                      |                |
                                               |        +-------------+-------------+  |
                                               |        v             v             v  |
                                               |   [container]   [container]   [container]
                                               +---------------------------------------+
                                                         ^
                                       docker pull       |      docker push
                                                         v
                                          +-----------------------------+
                                          |  Registry (Docker Hub, ...) |
                                          |  nginx, python, postgres ...|
                                          +-----------------------------+
```

The isolation comes from features of the **Linux kernel**:

- **namespaces** give each container its own view: its own process list (PID 1 is your app),
  its own hostname, its own network interfaces, its own filesystem tree;
- **cgroups** limit how much CPU and memory a container may use;
- a **layered filesystem** lets many containers share the same read-only image files.

A container is **not** a virtual machine. A VM runs a complete second operating system with its
own kernel. A container shares the kernel of the host and only adds isolation around a process.
That is why containers start in milliseconds and use little memory.

```text
   Virtual machines                         Containers
   +--------+ +--------+                    +--------+ +--------+ +--------+
   |  App   | |  App   |                    |  App   | |  App   | |  App   |
   |  libs  | |  libs  |                    |  libs  | |  libs  | |  libs  |
   | Guest  | | Guest  |                    +--------+ +--------+ +--------+
   |  OS    | |  OS    |                    |        Docker Engine         |
   +--------+ +--------+                    +------------------------------+
   |     Hypervisor     |                   |   Host OS (one Linux kernel) |
   +--------------------+                   +------------------------------+
   |      Hardware      |                   |           Hardware           |
   +--------------------+                   +------------------------------+
```

On Windows and macOS, Docker Desktop runs a small Linux virtual machine in the background, and
your containers run inside it. You will not notice it in daily use.

Three words you will use in every lesson:

| Word | Meaning | Analogy |
|---|---|---|
| **Image** | A read-only package: files + settings + the command to run | A recipe, or a class in programming |
| **Container** | A running (or stopped) instance of an image | The cooked meal, or an object |
| **Registry** | A server that stores images (Docker Hub is the public one) | An app store for images |

## Prerequisites

- Basic terminal skills: `cd`, `ls`, `cat`, running a command and reading its output.
- For the hands-on parts: Docker installed ([02 · Installation](02-docker-installation.md)).

## Hands-on Lab

Check that the Docker client can talk to the Docker Engine. `docker version` prints two parts:
**Client** (the CLI you typed) and **Server** (the engine). If the Server part is missing, the
engine is not running.

<!-- test: contains=Client; contains=Server; output=head:12 -->
```bash
docker version
```

```text
Client:
 Version:           29.4.3
 API version:       1.54
 Go version:        go1.26.2
 Git commit:        055a478
 Built:             Wed May  6 17:10:36 2026
 OS/Arch:           windows/amd64
 Context:           desktop-linux

Server: Docker Desktop 4.74.0 (227015)
 Engine:
  Version:          29.4.3
...
```

Then run your very first container:

<!-- test: contains=Hello from Docker -->
```bash
docker run hello-world
```

The full guided version of this is [labs/01-first-container](../labs/01-first-container/README.md).

## Expected Result

- `docker version` shows a **Client** section and a **Server** section (Docker Engine).
- `docker run hello-world` prints a message that starts with `Hello from Docker!` and then
  explains the four steps Docker just performed (contact the daemon, pull the image, create the
  container, stream the output to your terminal).

## Experiment

Run `hello-world` a second time. Compare the output with the first time: the lines about
"Unable to find image locally" and "Pulling from library/hello-world" are gone. The image is now
stored on your computer, so Docker reuses it.

<!-- test: absent=Pulling from -->
```bash
docker run hello-world
```

Now list the containers, including stopped ones. Every `docker run` created a **new** container:

<!-- test: contains=hello-world -->
```bash
docker ps -a
```

## Break It

Ask Docker for an image that does not exist:

<!-- test: fail; contains=repository does not exist -->
```bash
docker run hello-wrld
```

## Troubleshoot It

- **Observe:** Docker first says `Unable to find image 'hello-wrld:latest' locally`, then fails
  with `pull access denied ... repository does not exist or may require 'docker login'`
  (the exact wording depends on your Docker version).
- **Investigate:** read the image name in the error. Docker added `:latest` (and, behind the
  scenes, `docker.io/library/`) to it: that is how Docker expands short image names. Docker Hub
  answered "no such repository". The `docker login` hint is a red herring: logging in will not
  make a misspelled image exist.
- **Root cause:** a typo in the image name (`hello-wrld`).
- **Fix:** use the correct name `hello-world`.
- **Verify:** `docker run hello-world` prints `Hello from Docker!`.

If instead you see `Cannot connect to the Docker daemon` or `error during connect`, the client
works but the engine is not running: start Docker Desktop (Windows/macOS) or run
`sudo systemctl start docker` (Linux). See [02 · Installation](02-docker-installation.md).

## Common Mistakes

- Thinking a container is a small virtual machine. It is an isolated process on a shared kernel.
- Thinking `docker` *is* the engine. The CLI is only a client; the work happens in `dockerd`.
- Expecting Windows programs to run in a Linux container. Containers share the host's kernel
  type; this course uses Linux containers only.
- Ignoring the output. Docker's messages are usually precise: read them before searching online.

## Best Practices

- Learn the three nouns (image, container, registry) first; every other topic builds on them.
- Use official or verified images as a starting point (`nginx`, `python`, `postgres`).
- Always say which **version** of an image you want (`nginx:1.30-alpine`, not just `nginx`);
  lesson [03 · Images](03-images.md) explains why.

## Challenge

Without looking at the solution: find out **which version** of the Docker Engine (the server)
you are running, using only one command and its output.

## Solution

<details><summary>Show the solution</summary>

`docker version` shows the Server version in its second half. A shorter way prints only that value
with a Go template (you will learn templates in [17 · docker inspect](17-docker-inspect.md)):

<!-- test: output -->
```bash
docker version --format '{{.Server.Version}}'
```

```text
29.4.3
```

</details>

## Verification

You understood this lesson if you can explain, in your own words:

- [ ] the difference between an image and a container;
- [ ] what the Docker client does and what the Docker Engine does;
- [ ] why a container starts faster than a virtual machine;
- [ ] what a registry is and where `hello-world` came from.

## Real-World Usage

As a DevOps engineer you use Docker every day:

- **Packaging:** developers hand over an image instead of installation instructions.
- **Local environments:** a new team member starts the whole stack with one command.
- **Testing:** CI systems run tests inside the same image that goes to production.
- **Running in production:** container platforms (later in your career: Kubernetes, managed
  container services) all run the same OCI images you learn to build here.

## Key Takeaways

- An **image** is a package; a **container** is a running instance of it.
- The `docker` command is a client; the **Docker Engine** does the work.
- Containers are isolated **processes** that share the host kernel; they are not VMs.
- Images come from a **registry**; Docker Hub is the default one.
- Next: [02 · Docker Installation](02-docker-installation.md).
