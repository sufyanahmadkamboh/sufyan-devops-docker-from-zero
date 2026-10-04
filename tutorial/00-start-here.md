# 00 · Start here

> Check your installation, get the repository, find your way around it, and see the big picture.
> Time: about 30 minutes.

## What this project is

Docker From Zero is a **Docker learning lab**. It is not a slide deck and it is not a list of commands to
memorise. It is a repository full of small, real things you will run, inspect, break and fix:

- a static website served by nginx
- a tiny Python web app (`simple-app`) to learn Dockerfiles on
- a three-container message board (web → api → database → volume)
- a capstone: the same message board, built the way you would build it at work

The applications are deliberately boring. You never need to understand Python, JavaScript or SQL to follow along.
They exist only so you have something real to put into containers.

The way we learn here is:

```text
Learn → Build → Run → Break → Troubleshoot → Understand → Improve
```

## Who it is for

You know how to open a terminal, move between folders (`cd`, `ls`) and edit a text file. You have never used
Docker, never written a Dockerfile, never heard of a bridge network. Good. That is exactly who this is for.

## How to use this repository

| Folder | What it is | When you use it |
|---|---|---|
| `tutorial/` | This guided path, chapter by chapter | First. Follow it in order |
| `labs/` | 18 short workbooks, one topic each, with a "break it" and a challenge | After each tutorial chapter, to practise alone |
| `docs/` | 23 reference lessons: what, why, how, best practices | When you want the concept explained properly |
| `troubleshooting/` | 10 broken setups, each with a full investigation | When you want to practise fixing things (and when something breaks for real) |
| `challenges/` | Tasks with hidden solutions | To prove to yourself that you can do it without help |
| `capstone/` | The complete application, secured and optimised | At the end, to put everything together |
| `examples/` | The applications all the lessons use | You will open these files a lot |

## Step 1 · Is Docker installed?

You need Docker Engine (or Docker Desktop) and the Compose plugin. If you have not installed them yet, follow
[docs/02-docker-installation.md](../docs/02-docker-installation.md) and come back.

> **Windows users:** the most comfortable setup is Docker Desktop with the **WSL 2** backend, and a WSL terminal
> (Ubuntu) for all commands in this course. If you prefer Git Bash, run `export MSYS_NO_PATHCONV=1` once per
> terminal, otherwise Git Bash rewrites paths like `/app` into `C:/Program Files/Git/app`. In PowerShell most commands
> work as shown, but write `${PWD}` where we write `"$(pwd)"`.

Let's run the first command of the course.

<!-- test: contains=Docker version -->
```bash
docker --version
```

You should see one line like `Docker version 29.x.x, build ...`. That is the version of the **Docker CLI**, the
`docker` program you type commands into. Now ask for more detail:

<!-- test: output=head:20; contains=Client; contains=Server -->
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
  API version:      1.54 (minimum version 1.40)
  Go version:       go1.26.2
  Git commit:       56be731
  Built:            Wed May  6 17:07:37 2026
  OS/Arch:          linux/amd64
  Experimental:     false
 containerd:
  Version:          v2.2.3
...
```

Now look at the output. There are two sections:

- **Client**: the `docker` command you just ran.
- **Server**: the **Docker Engine** (the daemon, `dockerd`). This is the program that actually builds images and runs
  containers.

If you only see the Client section and an error like `Cannot connect to the Docker daemon`, the CLI is installed but the
engine is not running. On Docker Desktop: start Docker Desktop and wait until it says it is running. On Linux:
`sudo systemctl start docker`. This is your first troubleshooting lesson: **the CLI and the engine are two different
programs**, and the error tells you which one is missing.

Compose is a separate plugin. Check it too:

<!-- test: contains=Docker Compose version -->
```bash
docker compose version
```

## Step 2 · Your very first container

<!-- test: output; contains=Hello from Docker! -->
```bash
docker run hello-world
```

```text
Unable to find image 'hello-world:latest' locally
latest: Pulling from library/hello-world
4f55086f7dd0: Pulling fs layer
4f55086f7dd0: Download complete
4f55086f7dd0: Pull complete
d5e71e642bf5: Download complete
Digest: sha256:5e23090353324d887c48ad5e5c56d294eab81588df9605b07d1afe895f9cc8f8
Status: Downloaded newer image for hello-world:latest

Hello from Docker!
This message shows that your installation appears to be working correctly.

To generate this message, Docker took the following steps:
 1. The Docker client contacted the Docker daemon.
 2. The Docker daemon pulled the "hello-world" image from the Docker Hub.
    (amd64)
 3. The Docker daemon created a new container from that image which runs the
    executable that produces the output you are currently reading.
 4. The Docker daemon streamed that output to the Docker client, which sent it
    to your terminal.

To try something more ambitious, you can run an Ubuntu container with:
 $ docker run -it ubuntu bash

Share images, automate workflows, and more with a free Docker ID:
 https://hub.docker.com/

For more examples and ideas, visit:
 https://docs.docker.com/get-started/
```

Read that output slowly. It is one of the best explanations of Docker ever written, and it describes exactly what just
happened:

1. The CLI asked the engine to run `hello-world`.
2. The engine did not have the **image** `hello-world`, so it **pulled** (downloaded) it from **Docker Hub**.
3. The engine created a **container** from that image and started it.
4. The program inside printed this message and exited, so the container stopped.

Run it again:

<!-- test: contains=Hello from Docker!; absent=Pulling from -->
```bash
docker run hello-world
```

This time there is no "Unable to find image" and no download. The image is already on your machine. Images are
downloaded once and reused.

> A note on `hello-world`: we ran it without a version tag, which means the tag `latest`. For this one demo image that
> is fine. Everywhere else in this course we pin a version, like `nginx:1.30-alpine`, because `latest` changes under
> your feet. You will see why that matters in chapter 03.

## Step 3 · Get the repository

If you are reading this on GitHub, clone the repository first:

<!-- test: skip -->
```bash
git clone https://github.com/sufyanahmadkamboh/sufyan-devops-docker-from-zero.git
cd sufyan-devops-docker-from-zero
```

From now on, **every chapter starts in this folder** (the repository root).

## Step 4 · Explore the repository

<!-- test: output; contains=examples; contains=capstone -->
```bash
ls
```

```text
CHECKLIST.md
LICENSE
README.md
ROADMAP.md
capstone
challenges
docs
examples
labs
linkedin
study
tests
troubleshooting
tutorial
video
```

The interesting part for now is `examples/`. These are the applications everything else uses:

<!-- test: output; contains=simple-app; contains=multi-container-app -->
```bash
ls examples examples/simple-app examples/multi-container-app
```

```text
examples:
multi-container-app
nginx
simple-app

examples/multi-container-app:
api
database
docker-compose.yml
web

examples/simple-app:
Dockerfile
app.py
dockerfile-steps
optimization
requirements.txt
```

- `examples/nginx/` is a one-page website. You will serve it with nginx.
- `examples/simple-app/` is a small Python web app. Its `dockerfile-steps/` folder contains the Dockerfile we will
  write together, one instruction at a time.
- `examples/multi-container-app/` is the message board: `web/`, `api/`, `database/` and a `docker-compose.yml`.

Open `examples/simple-app/app.py` in your editor. It is about 40 lines. You do not need to understand Python; notice
only that it reads two **environment variables** (`APP_ENV` and `GREETING`) and prints the container's hostname. We will
use both later.

## Step 5 · The big picture

### How Docker works

```text
   You
    |
    |  docker run / docker build / docker ps ...
    v
+-----------+        REST API        +--------------------------------------------+
| Docker    | ---------------------> | Docker Engine (dockerd)                    |
| CLI       |                        |                                            |
+-----------+                        |   images:      nginx  python  postgres     |
                                     |                   |                        |
                                     |   containers:  [web] [api]  [db]           |
                                     |                                            |
                                     |   networks, volumes                        |
                                     +---------------------+----------------------+
                                                           |
                                               docker pull |  docker push
                                                           v
                                                 +-------------------+
                                                 | Registry          |
                                                 | (Docker Hub)      |
                                                 +-------------------+
```

- The **CLI** only sends requests.
- The **engine** does the work: it stores images, runs containers, creates networks and volumes.
- A **registry** like Docker Hub stores images so anyone can pull them.

### Image vs container

```text
  IMAGE  (read-only template)              CONTAINERS  (running instances)
  +------------------------+   docker run   +-----------+  +-----------+
  | nginx:1.30-alpine      | -------------> | web       |  | web2      |
  | files + default command|                | (process) |  | (process) |
  +------------------------+                +-----------+  +-----------+
```

An image is like a class, a container is like an object. Or, if you prefer: the image is the recipe, the container is
the meal. One image, as many containers as you like.

### The application we will build up to

```text
                    Browser
                       |
                       |  http://localhost:8080
                       v
                Web container            nginx: the web page, forwards /api/ ...
                       |
                       v
                 API container           Python: reads and writes messages ...
                       |
                       v
              Database container         PostgreSQL: stores them ...
                       |
                       v
                 Docker volume           ... on a volume, so they survive the containers
```

### The capstone, end to end

```text
                         Developer
                             |
                             v
                      Docker CLI  (docker compose up -d --build)
                             |
                             v
                      Docker Engine
                             |
          +------------------+------------------+
          |                  |                  |
          v                  v                  v
      Web Container      API Container    Database Container
          |                  |                  |
          +---- frontend ----+---- backend -----+
                     Docker networks
                             |
                             v
                       Docker Volume  (capstone_db-data)
```

You will build every piece of this yourself before you see the finished capstone.

## Where would I use this as a DevOps engineer?

Every day. Checking `docker version` is the first thing you do when a build server says "Cannot connect to the Docker
daemon". Understanding "CLI vs engine vs registry" is what lets you tell whether a failed deployment is a network problem
(cannot reach the registry), a permissions problem (cannot talk to the engine) or an application problem (the container
starts and dies).

## What you learned

- Docker has a **CLI**, an **engine** and **registries**; the engine does the real work.
- An **image** is a read-only template; a **container** is a running instance of it.
- Images are pulled once and reused.
- Where everything lives in this repository.

## Try it yourself

- Run `docker run hello-world` once more and count how many containers you have now with `docker ps -a`. (We will
  explain that list in the next chapter.)
- Read [docs/01-docker-introduction.md](../docs/01-docker-introduction.md) for the full "why containers" story.

## Next

[01 · Your first container](01-first-container.md)
