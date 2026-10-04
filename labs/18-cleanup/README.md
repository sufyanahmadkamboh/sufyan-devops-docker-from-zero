# Lab 18 · Safe cleanup

> Goal: free disk space without deleting something you still need. Know exactly what every `prune` command removes,
> and how to limit it. · Time: 30 minutes · You need: labs 01 to 17.

After a few weeks of practice, Docker quietly fills your disk: stopped containers, old images, build cache, volumes
from experiments. Docker has powerful cleanup commands, the `prune` family. They are also the easiest way to delete a
database by accident. This lab teaches the safe order: **look first, clean narrowly, keep what matters, back up data
before you delete it.**

## What you will learn

- `docker system df`: what uses space
- `docker container prune`, `image prune`, `volume prune`, `network prune`, `system prune`: what each one removes
- `--filter` to clean only old or labelled things
- Why `docker system prune -a --volumes` is dangerous
- How to back up a volume before deleting it

## Step 1 · Look before you delete

From the repository root:

```bash
cd labs/18-cleanup
```

<!-- test: output -->
```bash
docker system df
```

```text
TYPE            TOTAL     ACTIVE    SIZE      RECLAIMABLE
Images          26        1         6.679GB   3.03GB (45%)
Containers      1         0         147.5kB   147.5kB (100%)
Local Volumes   0         0         0B        0B
Build Cache     103       0         2.874GB   2.349GB
```

| Column | Meaning |
|---|---|
| `TYPE` | Images, Containers, Local Volumes, Build Cache |
| `TOTAL` | How many exist |
| `ACTIVE` | How many are in use by a container (running **or stopped**) |
| `SIZE` | Disk space used |
| `RECLAIMABLE` | Space that a prune could free, because nothing uses it |

`docker system df -v` lists every single image, container and volume with its size.

## Step 2 · Make some mess to clean up

Let's create one of everything that typically piles up:

```bash
docker run --name old1 alpine:3.24 echo "I ran once"
docker run --name old2 alpine:3.24 echo "me too"
docker run --name labeled --label course=docker-from-zero alpine:3.24 echo "I have a label"
docker run --name anon -v /data alpine:3.24 echo "I created an anonymous volume"
docker network create lab18-unused
docker volume create lab18-keep
```

And a **dangling image**: we build the same tag twice. The second build takes the name, the first image is left with
no name (`<none>`):

```bash
docker build -t lab18-demo - <<'EOF'
FROM alpine:3.24
RUN echo one > /version
EOF
docker build -t lab18-demo - <<'EOF'
FROM alpine:3.24
RUN echo two > /version
EOF
```

(`docker build -t name -` reads the Dockerfile from standard input and uses no build context at all.)

<!-- test: output; contains=old1; contains=labeled -->
```bash
docker ps -a
```

```text
CONTAINER ID   IMAGE         COMMAND                  CREATED         STATUS                     PORTS     NAMES
3f96efc22c7c   alpine:3.24   "echo 'I created an …"   3 seconds ago   Exited (0) 3 seconds ago             anon
1d3ada6a04e2   alpine:3.24   "echo 'I have a labe…"   4 seconds ago   Exited (0) 3 seconds ago             labeled
cdbde784fc8d   alpine:3.24   "echo 'me too'"          4 seconds ago   Exited (0) 4 seconds ago             old2
adc3cd3a08f0   alpine:3.24   "echo 'I ran once'"      5 seconds ago   Exited (0) 4 seconds ago             old1
```

Four stopped containers, all `Exited (0)`.

## Step 3 · Containers: prune with a filter first

`docker container prune` removes **every stopped container**. Before that, the precise version: only containers with
our label.

<!-- test: output; contains=Total reclaimed space -->
```bash
docker container prune -f --filter label=course=docker-from-zero
```

```text
Deleted Containers:
1d3ada6a04e296f42e3935f277c418be091a61cd8168c4e4330518a927b8f85e

Total reclaimed space: 4.096kB
```

<!-- test: contains=old1; absent=labeled -->
```bash
docker ps -a --format '{{.Names}} {{.Status}}'
```

Only `labeled` is gone. `--filter until=24h` is another useful filter: only containers created more than 24 hours ago.

Now all stopped containers:

<!-- test: output; contains=Total reclaimed space -->
```bash
docker container prune -f
```

```text
Deleted Containers:
3f96efc22c7c4ada67874dc1fe706f16b7e78db3c64a1475f4740f93b4273015
cdbde784fc8d88891b9ffbd67c7ec563b1fcae68be328f897d39ab56c402af4d
adc3cd3a08f0f3b3d445bf21a1559b1f4571c2444496fa06469dcf3292fcb22b
4f8407918c036a6a0e3f257313b084fabdc35e2b364afaa51b29cf5b8f8cd11f

Total reclaimed space: 163.8kB
```

> A stopped container is not garbage by definition. It may be a database you stopped for the weekend, and `docker
> start` would bring it back with all its settings. After `container prune` it is gone. `-f` skips the "Are you sure?"
> question: leave it out when you type the command yourself, and read the question.

## Step 4 · Images: dangling vs unused

<!-- test: output -->
```bash
docker images --filter dangling=true
```

```text
WARNING: This output is designed for human readability. For machine-readable output, please use --format.
IMAGE   ID             DISK USAGE   CONTENT SIZE   EXTRA
```

The first `lab18-demo` build lost its name: `<none>`. That is a **dangling** image, and it is always safe to remove:

<!-- test: output; contains=Total reclaimed space -->
```bash
docker image prune -f
```

```text
Total reclaimed space: 0B
```

<!-- test: contains=lab18-demo -->
```bash
docker images lab18-demo
```

The named `lab18-demo` image is still there. Plain `image prune` only removes dangling images.

`docker image prune -a` is different: it removes **every image not used by a container**, including `nginx`, `python`
and everything you built. Nothing is lost forever (you can pull or build again), but it costs time and bandwidth:

<!-- test: skip -->
```bash
docker image prune -a
```

## Step 5 · Volumes: where your data lives

Volumes hold **data**: databases, uploads. That is why Docker is careful here.

<!-- test: output; contains=lab18-keep -->
```bash
docker volume ls
```

```text
DRIVER    VOLUME NAME
local     db9ab4b140e8178dafcf4e576c7fe5bcd9d2077393b82d9c471b5c9db39b6cf5
local     lab18-keep
```

You see `lab18-keep` and a volume with a long random name: the **anonymous** volume that the `anon` container created
for `/data` (we removed the container, the volume stayed behind). Plain `volume prune` only removes **anonymous**
volumes that no container uses:

<!-- test: output; contains=Total reclaimed space -->
```bash
docker volume prune -f
```

```text
Deleted Volumes:
db9ab4b140e8178dafcf4e576c7fe5bcd9d2077393b82d9c471b5c9db39b6cf5

Total reclaimed space: 0B
```

<!-- test: contains=lab18-keep -->
```bash
docker volume ls
```

`lab18-keep` survived because it has a name. To remove a named volume you either name it explicitly
(`docker volume rm lab18-keep`) or use `docker volume prune -a`, which removes **all** unused volumes, named ones
included. That second command is the one that deletes databases. Never use it without reading the list first.

## Step 6 · Networks

<!-- test: output; contains=lab18-unused -->
```bash
docker network prune -f
```

```text
Deleted Networks:
lab18-unused
```

Unused networks you created are removed. The built-in `bridge`, `host` and `none` networks are never touched.
Networks take no disk space; this is just tidying up.

## Step 7 · system prune, and the command to be careful with

`docker system prune` combines the safe parts: stopped containers, unused networks, dangling images and unused build
cache.

<!-- test: output=tail:3; contains=Total reclaimed space -->
```bash
docker system prune -f
```

```text
...
7uxjpeok3ckhzkeihnpjj83ig

Total reclaimed space: 2.349GB
```

> **⚠ WARNING: `docker system prune -a --volumes`**
>
> This removes **all** stopped containers, **all** unused networks, **all** images not used by a running or stopped
> container, **all** build cache, and **all** volumes not used by a container: including the volumes with your
> databases. There is no undo, no recycle bin. It is the "factory reset" of Docker.
> Use it only on a machine where you are sure nothing matters (a throw-away VM, a CI runner), and run
> `docker system df -v` before it.

<!-- test: skip -->
```bash
docker system prune -a --volumes
```

## Break it

Let's lose some data on purpose, so it never happens to you for real. We create a volume with an "important" file,
and no container uses it. Don't fix it yet, we break it on purpose.

```bash
docker volume create lab18-db
docker run --rm -v lab18-db:/data alpine:3.24 sh -c "echo 'customer orders' > /data/important.txt"
```

Someone "frees some disk space":

<!-- test: contains=lab18-db -->
```bash
docker volume prune -a -f
```

<!-- test: fail; contains=No such file or directory -->
```bash
docker run --rm -v lab18-db:/data alpine:3.24 cat /data/important.txt
```

## Troubleshoot it

**Observe.** The file is gone. Before doing anything else, let's investigate.

**Investigate.** The volume `lab18-db` exists again, but look at when it was created:

<!-- test: output; contains=CreatedAt -->
```bash
docker volume inspect lab18-db
```

```text
[
    {
        "CreatedAt": "2026-10-04T04:08:09Z",
        "Driver": "local",
        "Labels": null,
        "Mountpoint": "/var/lib/docker/volumes/lab18-db/_data",
        "Name": "lab18-db",
        "Options": null,
        "Scope": "local"
    }
]
```

The `-v lab18-db:/data` in our last command quietly created a **new, empty** volume with the same name. The old one
was deleted by `volume prune -a`, because no container was using it.

**Root cause.** A named volume that no container uses is "unused" for `prune -a`, even if it holds your only copy of
the data. There is no undo.

**Fix.** Data that was deleted without a backup is gone. The fix is prevention: **back up a volume before any
cleanup**. Let's do it properly this time. Write the data again:

```bash
docker run --rm -v lab18-db:/data alpine:3.24 sh -c "echo 'customer orders' > /data/important.txt"
```

Back it up into a file in this lab folder (a temporary container mounts the volume **and** the current folder, and
`tar` packs the data):

```bash
docker run --rm -v lab18-db:/data -v "$(pwd)":/backup alpine:3.24 tar czf /backup/lab18-db.tar.gz -C /data .
ls -l lab18-db.tar.gz
```

Now the accident can happen:

<!-- test: contains=lab18-db -->
```bash
docker volume prune -a -f
```

And we restore the backup into a fresh volume:

```bash
docker run --rm -v lab18-db:/data -v "$(pwd)":/backup alpine:3.24 tar xzf /backup/lab18-db.tar.gz -C /data
```

**Verify.**

<!-- test: contains=customer orders -->
```bash
docker run --rm -v lab18-db:/data alpine:3.24 cat /data/important.txt
```

The data is back. Two more protections: a **stopped** container that still uses a volume keeps it safe from `prune`,
and databases have their own backup tools (for PostgreSQL: `pg_dump`) that are better than copying files.

> Windows: run these commands in WSL or Git Bash. In PowerShell, use `"${PWD}:/backup"` instead of
> `"$(pwd)":/backup`.

## Challenge

**Task:** Remove only the **images** that you created in this lab, and nothing else.

**Requirements:**
- `lab18-demo` is gone.
- All other images (nginx, alpine, python, ...) are still there.
- No `prune -a`.

**Hints:**
- `docker rmi` accepts several names.
- `docker images --filter reference=...` shows what matches before you delete anything.

<details><summary>Solution</summary>

Look first:

<!-- test: contains=lab18-demo -->
```bash
docker images --filter reference='lab18-*'
```

Then remove exactly that:

```bash
docker rmi lab18-demo
```

And check that it is gone:

<!-- test: absent=lab18-demo -->
```bash
docker images --filter reference='lab18-*'
```

`--filter reference=` accepts patterns. The habit is the point: **list with a filter, read the list, then delete
exactly that list.**

</details>

## Verify

- [ ] I check `docker system df` before cleaning
- [ ] I know what `container`, `image`, `volume`, `network` and `system prune` remove
- [ ] I can limit a prune with `--filter label=...` or `--filter until=...`
- [ ] I know that `volume prune -a` and `system prune -a --volumes` can delete databases
- [ ] I can back up and restore a volume with a temporary container and `tar`

## Clean up

```bash
docker volume rm lab18-db lab18-keep 2>/dev/null || true
rm -f lab18-db.tar.gz
cd ../..
```

## Next

You have finished the labs. Now practise investigating real failures in [troubleshooting/](../../troubleshooting/),
then build the [capstone](../../capstone/README.md).

- Concept lesson: [docs/22-troubleshooting.md](../../docs/22-troubleshooting.md)
