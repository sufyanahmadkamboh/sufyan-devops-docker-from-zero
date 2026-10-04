# Lab 01 · Your First Container

> **Goal:** run your first containers and learn the handful of commands you will use every single day.
> **Time:** about 30 minutes · **You need:** Docker installed ([docs/02-docker-installation.md](../../docs/02-docker-installation.md)) and this repository cloned.

## What you will learn

- The difference between an **image** and a **container** (the most important idea in Docker)
- How to download an image from **Docker Hub** with `docker pull`
- How to start a container with `docker run`, in the background with `-d`, and with a name of your choice
- How to read every column of `docker ps`
- How to stop, start, restart and remove containers, and remove images

Before we type anything, one picture to keep in your head:

```text
   Docker Hub (online library of images)
          |
          |  docker pull
          v
   IMAGE   = a read-only package: files + "what to run"     (like a recipe, or a class)
          |
          |  docker run
          v
   CONTAINER = a running (or stopped) copy of that image    (like a cake made from the recipe, or an object)
```

One image can be used to create as many containers as you like.

## Step 1 · Check that Docker works

Open a terminal in the repository folder. Every lab starts from the **repository root**, so let's move into this lab's folder first:

```bash
cd labs/01-first-container
```

Now ask Docker which version you have:

<!-- test: output; contains=Docker version -->
```bash
docker --version
```

```text
Docker version 29.4.3, build 055a478
```

**What you see:** one line with the version of the Docker **client** (the `docker` command you type). If you get `command not found`, Docker is not installed or not on your `PATH`; go back to [docs/02-docker-installation.md](../../docs/02-docker-installation.md).

## Step 2 · Run your very first container

```text
You type  ->  docker (client)  ->  Docker Engine (daemon)  ->  pulls image  ->  creates container  ->  runs it
```

Let's run this:

<!-- test: output=head:12; contains=Hello from Docker! -->
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

...
```

**What you see:**

1. `Unable to find image 'hello-world:latest' locally`: Docker looked on your computer first and did not find it.
2. `Pulling from library/hello-world`: so it downloaded the image from **Docker Hub**, the default public image registry.
3. `Hello from Docker!`: this text was printed **by a program running inside the container**.

Read the rest of the message in your terminal: it explains the same four steps you just watched.

> `hello-world` has no version tag, so Docker used the tag `latest`. That is fine for this one demo. For everything else we always write a tag such as `nginx:1.30-alpine`, so we know exactly which version we get. `latest` just means "whatever was published most recently" and can change under your feet.

Run it a second time:

<!-- test: contains=Hello from Docker!; absent=Unable to find image -->
```bash
docker run hello-world
```

This time there is no download: the image is already on your computer. Docker created a **second container** from the same image.

## Step 3 · Download an image without running it

`docker pull` only downloads. We'll use nginx, a very popular web server, in its small Alpine Linux variant:

<!-- test: output=tail:3 -->
```bash
docker pull nginx:1.30-alpine
```

```text
...
Digest: sha256:0985e772fb9f729e6fa0980da05fca5d9c468e870eed43071545afa9d2e27d94
Status: Image is up to date for nginx:1.30-alpine
docker.io/library/nginx:1.30-alpine
```

**What you see:** the image is downloaded in several **layers** (each `Pull complete` line is one layer; Lab 07 explains layers). The `Digest: sha256:...` line is the unique fingerprint of exactly this image content.

Now list the images on your computer:

<!-- test: output; contains=nginx -->
```bash
docker images nginx
```

```text
WARNING: This output is designed for human readability. For machine-readable output, please use --format.
IMAGE               ID             DISK USAGE   CONTENT SIZE   EXTRA
nginx:1.30-alpine   0985e772fb9f       93.6MB           27MB        
```

| Column | Meaning |
|---|---|
| `IMAGE` | the image name and tag (`nginx:1.30-alpine`). Official images on Docker Hub have no user name in front |
| `ID` | a short form of the image's unique ID. Two tags can point to the same ID |
| `DISK USAGE` | how much disk space the unpacked image uses (layers shared with other images are counted in each) |
| `CONTENT SIZE` | how much was downloaded (the compressed layers) |
| `EXTRA` | `U` means the image is **in use** by a container (running or stopped) |

This is the layout of Docker 29 and newer. Older versions (and `docker images --format table`) show the classic
columns `REPOSITORY`, `TAG`, `IMAGE ID`, `CREATED` (when the publisher **built** the image, not when you downloaded
it) and `SIZE`. The information is the same.

## Step 4 · Run a container in the background with a name

nginx is a **server**: it runs until someone stops it. If we started it in the foreground it would occupy our terminal. `-d` (detached) runs it in the background, and `--name` gives it a name we choose:

<!-- test: output -->
```bash
docker run -d --name web nginx:1.30-alpine
```

```text
ed6e0a9788b5f902fa7b6c66d7813487241d300ac4b7d95d21544c3332935956
```

**What you see:** one long hexadecimal string. That is the full **container ID**. Docker printed it and gave you your terminal back.

## Step 5 · See what is running: `docker ps`

<!-- test: output; contains=web -->
```bash
docker ps
```

```text
CONTAINER ID   IMAGE               COMMAND                  CREATED                  STATUS                  PORTS     NAMES
ed6e0a9788b5   nginx:1.30-alpine   "/docker-entrypoint.…"   Less than a second ago   Up Less than a second   80/tcp    web
```

Every column, one by one:

| Column | What it tells you | In our case |
|---|---|---|
| `CONTAINER ID` | first 12 characters of the container's unique ID. You can use it instead of the name | a random hex string |
| `IMAGE` | which image the container was created from | `nginx:1.30-alpine` |
| `COMMAND` | the main process Docker started inside the container (shortened) | `"/docker-entrypoint.…"` |
| `CREATED` | when the container was created | a few seconds ago |
| `STATUS` | `Up ...` = running, `Exited (code) ...` = stopped, `Created` = never started | `Up ...` |
| `PORTS` | network ports. `80/tcp` alone means "nginx listens on 80 inside", but nothing is published to your computer yet (Lab 04) | `80/tcp` |
| `NAMES` | the container name. Ours is `web`; without `--name`, Docker invents one like `quirky_hopper` | `web` |

Where are the two `hello-world` containers? They are not in the list because they are **not running**: they printed their message and stopped. Add `-a` (all) to also see stopped containers:

<!-- test: output; contains=hello-world; contains=Exited (0) -->
```bash
docker ps -a
```

```text
CONTAINER ID   IMAGE               COMMAND                  CREATED                  STATUS                     PORTS     NAMES
ed6e0a9788b5   nginx:1.30-alpine   "/docker-entrypoint.…"   Less than a second ago   Up Less than a second      80/tcp    web
9ebfe32742f4   hello-world         "/hello"                 3 seconds ago            Exited (0) 2 seconds ago             zen_matsumoto
85df79aa9634   hello-world         "/hello"                 3 seconds ago            Exited (0) 3 seconds ago             hardcore_meitner
```

The `hello-world` containers show `Exited (0)`: they finished their job and the main program returned exit code **0**, which means "success". Their names were invented by Docker because we did not give one.

## Step 6 · Stop, start, restart

<!-- test: contains=web -->
```bash
docker stop web
```

Docker prints the name back when it is done. Check the status:

<!-- test: output; contains=Exited -->
```bash
docker ps -a --filter name=web
```

```text
CONTAINER ID   IMAGE               COMMAND                  CREATED        STATUS                              PORTS     NAMES
ed6e0a9788b5   nginx:1.30-alpine   "/docker-entrypoint.…"   1 second ago   Exited (0) Less than a second ago             web
```

The container still exists, it is just stopped. Nothing was deleted. Start it again:

<!-- test: contains=web -->
```bash
docker start web
docker ps --filter name=web
```

`restart` is simply stop + start in one command (useful after changing configuration files):

<!-- test: output; contains=Up -->
```bash
docker restart web
docker ps --filter name=web --format '{{.Names}} is {{.Status}}'
```

```text
web
web is Up Less than a second
```

`--format` lets you choose exactly which columns to print. You will see it a lot.

## Step 7 · Remove containers and images

Removing a stopped container deletes it for good, including any file changes made inside it:

<!-- test: contains=web -->
```bash
docker stop web
docker rm web
```

Check it is gone:

<!-- test: absent= web -->
```bash
docker ps -a --filter name=web
```

Only the header line is left.

## Break it

Let's make two very common beginner mistakes on purpose. Start `web` again:

```bash
docker run -d --name web nginx:1.30-alpine
```

**Mistake 1:** remove a container that is still running.

<!-- test: fail; contains=container is running -->
```bash
docker rm web
```

**Mistake 2:** delete an image while containers still use it.

<!-- test: fail; contains=conflict -->
```bash
docker rmi hello-world
```

Don't fix it yet. We broke it on purpose. Let's investigate first.

## Troubleshoot it

**Observe.** Both commands failed with an `Error response from daemon` message. Read the message, it usually tells you exactly what is wrong:

- `docker rm web` says the container **is running** and suggests to stop it or force it.
- `docker rmi hello-world` reports a **conflict**: a container is using the image.

**Investigate.** Which containers use the `hello-world` image? The `ancestor` filter answers that:

<!-- test: output; contains=hello-world -->
```bash
docker ps -a --filter ancestor=hello-world
```

```text
CONTAINER ID   IMAGE         COMMAND    CREATED         STATUS                     PORTS     NAMES
9ebfe32742f4   hello-world   "/hello"   7 seconds ago   Exited (0) 6 seconds ago             zen_matsumoto
85df79aa9634   hello-world   "/hello"   7 seconds ago   Exited (0) 6 seconds ago             hardcore_meitner
```

Two stopped containers, the ones from Step 2. A stopped container still "holds" its image, because you could start it again at any time.

**Root cause.** Docker protects you: it refuses to delete a running container, and it refuses to delete an image that a container still needs.

**Fix.** Stop and remove `web`, then remove the `hello-world` containers and finally the image. `docker ps -aq` prints only the IDs (`-q` = quiet), so we can hand them straight to `docker rm`:

<!-- test: contains=web -->
```bash
docker stop web
docker rm web
docker rm $(docker ps -aq --filter ancestor=hello-world)
docker rmi hello-world
```

> `docker rm -f web` would stop **and** remove in one go. It is handy, but use it consciously: `-f` does not ask twice.

**Verify.** No containers left, and the `hello-world` image is gone:

<!-- test: output -->
```bash
docker ps -a
docker images hello-world
```

```text
CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES
WARNING: This output is designed for human readability. For machine-readable output, please use --format.
IMAGE   ID             DISK USAGE   CONTENT SIZE   EXTRA
```

Both lists show only their header line.

## Challenge

**Task:** prove to yourself that one image can produce several independent containers.

**Requirements:**
- Start **two** nginx containers from `nginx:1.30-alpine`, named `web` and `web2`, both in the background.
- Show that both are running, then stop and remove only `web2` while `web` keeps running.
- Finally remove `web` too.

**Hints:** `docker run -d --name ...`, `docker ps`, `docker stop`, `docker rm`. Each container needs its own name.

**Expected result:** `docker ps` shows two lines with the same IMAGE but different CONTAINER IDs and NAMES; after the clean-up nothing is left.

<details>
<summary>Solution</summary>

<!-- test: output; contains=web2 -->
```bash
docker run -d --name web nginx:1.30-alpine
docker run -d --name web2 nginx:1.30-alpine
docker ps --format '{{.ID}}  {{.Image}}  {{.Names}}'
```

```text
6ca5ede8c6bc60ec5bc4886bdb3da80af8706de7cb00aa8ee9125159d55b51b7
3a609b82e1a6ddf30f24b773088669d8c5dbae4c0a67f4b8a27f197f44a24838
3a609b82e1a6  nginx:1.30-alpine  web2
6ca5ede8c6bc  nginx:1.30-alpine  web
```

<!-- test: contains=web -->
```bash
docker stop web2
docker rm web2
docker ps --format '{{.Names}}'
docker rm -f web
```

**Explanation:** the image was downloaded once and is shared. Each `docker run` created a new container with its own ID, name, process and writable space. Removing `web2` did not affect `web` or the image.

</details>

## Verify

You can now:

- [ ] explain the difference between an image and a container
- [ ] pull an image with a specific tag from Docker Hub
- [ ] run a container in the background with a name
- [ ] read every column of `docker ps` and know why `-a` matters
- [ ] stop, start, restart and remove a container
- [ ] explain why `docker rmi` can refuse to delete an image, and fix it

## Clean up

Everything from this lab is already removed. We keep the `nginx:1.30-alpine` image, because the next labs use it. To check:

```bash
docker ps -a
```

## Next

➡️ [Lab 02 · The Docker CLI](../02-docker-cli/README.md) · 📖 Concepts: [docs/03-images.md](../../docs/03-images.md), [docs/04-containers.md](../../docs/04-containers.md)
