# Volumes

> Lesson 12 · about 45 minutes · you need: [04 · Containers](04-containers.md), [06 · Container Lifecycle](06-container-lifecycle.md)

## What is it?

A **volume** is storage that Docker manages **outside** any container's writable layer. You mount
it into a container at a path (for example `/data`). Files written there survive when the
container is removed, and another container can mount the same volume later.

```text
   docker run -v notes:/data ...

   +----------------------+          +----------------------+
   | container "writer"   |          | container "reader"   |  (created later)
   |   /data  ----------+ |          | +-------  /data      |
   +--------------------|-+          +-|--------------------+
                        |              |
                        v              v
                 +--------------------------+
                 |  volume "notes"          |   managed by Docker,
                 |  (lives on the host /    |   independent of containers
                 |   inside Docker Desktop) |
                 +--------------------------+
```

## Why do we need it?

A container's writable layer is deleted with the container. That is great for apps and terrible
for **data**. Databases, uploaded files and anything you must keep belong on a volume, so you can
upgrade, recreate or replace the container without losing them.

## How does it work?

| Command | What it does |
|---|---|
| `docker volume create notes` | create a named volume |
| `docker volume ls` | list volumes |
| `docker volume inspect notes` | details: driver, **Mountpoint** (where the data really is), labels |
| `docker volume rm notes` | delete it (refused while a container uses it) |
| `docker run -v notes:/data ...` | mount volume `notes` at `/data` (created automatically if missing) |
| `docker run --mount type=volume,src=notes,dst=/data ...` | the same, longer but more explicit |

Three kinds of storage you will meet:

```text
   named volume      -v notes:/data             managed by Docker, has a name      (this lesson)
   anonymous volume  -v /data  or image VOLUME  managed by Docker, random name     (easy to lose!)
   bind mount        -v "$(pwd)/site:/data"     a folder of YOUR computer          (lesson 13)
```

If the volume is new and empty, Docker first copies whatever the image already has at that path
into it. If it already contains data, the image's files at that path are hidden by the volume.

## Prerequisites

- `alpine:3.24` and `postgres:18-alpine` images (pulled automatically).

## Hands-on Lab

Create a volume and look at it:

<!-- test: contains=notes; output -->
```bash
docker volume create notes
docker volume ls
docker volume inspect notes
```

```text
notes
DRIVER    VOLUME NAME
local     notes
[
    {
        "CreatedAt": "2026-10-04T04:17:13Z",
        "Driver": "local",
        "Labels": null,
        "Mountpoint": "/var/lib/docker/volumes/notes/_data",
        "Name": "notes",
        "Options": null,
        "Scope": "local"
    }
]
```

Write data with one container, then **remove that container**:

<!-- test: contains=written by the writer -->
```bash
docker run --name writer -v notes:/data alpine:3.24 sh -c 'echo "written by the writer at $(date)" > /data/note.txt; cat /data/note.txt'
docker rm writer
```

A brand-new container mounts the same volume and finds the file:

<!-- test: contains=written by the writer -->
```bash
docker run --rm --name reader -v notes:/data alpine:3.24 cat /data/note.txt
```

The guided lab, with more experiments, is [labs/09-volumes](../labs/09-volumes/README.md).

## Expected Result

- `docker volume inspect` shows `"Driver": "local"` and a `"Mountpoint"` such as
  `/var/lib/docker/volumes/notes/_data` (on Docker Desktop that path is inside its Linux VM).
- The reader prints `written by the writer at ...`: the data outlived the container that wrote it.

## Experiment

Compare with **no** volume. Data written to the container's own layer dies with the container:

<!-- test: contains=No such file -->
```bash
docker run --name temp alpine:3.24 sh -c 'echo "I will be lost" > /tmp/note.txt'
docker rm temp
docker run --rm alpine:3.24 cat /tmp/note.txt 2>&1 || true
```

A real database. PostgreSQL 18 keeps its data under `/var/lib/postgresql`, so we mount a volume
there, create a table, delete the container, and start a new one on the same volume:

<!-- test: timeout=120 -->
```bash
docker run -d --name db1 -e POSTGRES_PASSWORD=lab-only-password -v pgdata:/var/lib/postgresql postgres:18-alpine
```

<!-- test: retry=30; contains=INSERT 0 1 -->
```bash
docker exec db1 psql -U postgres -c "CREATE TABLE IF NOT EXISTS notes (text TEXT); INSERT INTO notes VALUES ('survives container removal');"
```

```bash
docker rm -f db1
docker run -d --name db2 -e POSTGRES_PASSWORD=lab-only-password -v pgdata:/var/lib/postgresql postgres:18-alpine
```

Give PostgreSQL two or three seconds to start, then ask the **new** container:

<!-- test: retry=30; contains=survives container removal -->
```bash
docker exec db2 psql -U postgres -c "SELECT * FROM notes;"
```

If it says the server is still starting up, wait a moment and run it again. This time the
database found existing data on the volume, so it skipped initialisation and just started.

## Break It

Try to delete a volume that a container is using:

<!-- test: fail; contains=in use -->
```bash
docker volume rm pgdata
```

## Troubleshoot It

- **Observe:** `Error response from daemon: remove pgdata: volume is in use - [<container id>]`.
- **Investigate:** which container? Filter containers by volume:

<!-- test: contains=db2 -->
```bash
docker ps -a --filter volume=pgdata --format '{{.Names}} {{.Status}}'
```

- **Root cause:** Docker protects volumes that are mounted by a container (running **or** stopped).
- **Fix:** remove the container first, **then** the volume, and only if you really want to delete
  the data. There is no undo and no recycle bin.
- **Verify:**

```bash
docker rm -f db2
docker volume rm pgdata
```

<!-- test: absent=pgdata -->
```bash
docker volume ls
```

Related scenarios: [04 · volume data appears missing](../troubleshooting/04-volume-data-missing/README.md)
(a typo in the volume name) and [10 · database data disappears](../troubleshooting/10-database-data-disappears/README.md)
(no named volume, or the wrong path).

## Common Mistakes

- A typo in the volume name (`-v note:/data` instead of `notes`): Docker silently creates a new,
  empty volume, and your data seems "gone".
- Mounting at the wrong path: the app writes somewhere else, the volume stays empty.
  PostgreSQL 18 needs `/var/lib/postgresql`; older tutorials use `/var/lib/postgresql/data`,
  which the 18 image refuses.
- `docker rm -v` or `docker compose down -v`: the `-v` also deletes volumes.
- Relying on anonymous volumes: every new container gets a new one; old ones pile up unnoticed.

## Best Practices

- Always use **named** volumes for data you care about.
- Know exactly which path the image stores data in (read the image's documentation).
- Back up volumes (for databases: with the database's own dump tool).
- Treat `docker volume rm` and `prune` as data deletion, because they are.

## Challenge

Create a volume `counter`. Run a container three times, each time with `--rm`, that adds one line
to `/data/visits.txt` on that volume. Then print how many lines the file has. It must be 3.

## Solution

<details><summary>Show the solution</summary>

<!-- test: contains=3 -->
```bash
docker volume create counter
for i in 1 2 3; do docker run --rm -v counter:/data alpine:3.24 sh -c 'echo visit >> /data/visits.txt'; done
docker run --rm -v counter:/data alpine:3.24 wc -l /data/visits.txt
```

`--rm` deleted each container right away, yet every visit was kept: the file lives on the volume.

</details>

## Verification

- [ ] You can create, list, inspect and remove volumes.
- [ ] You proved that data on a volume survives container removal.
- [ ] You know where PostgreSQL 18 keeps its data.
- [ ] You know why a typo in a volume name looks like data loss.

Clean up:

```bash
docker volume rm notes counter
```

## Real-World Usage

- Every containerised database (PostgreSQL, MySQL, Redis with persistence) runs on a volume.
- Upgrading a database container means: stop, start the new image version on the **same** volume.
- Volume backups are part of every serious operations runbook.

## Key Takeaways

- Volumes keep data outside the container's lifecycle.
- Named volumes: `-v name:/path`; the name is the key, so typos create new empty volumes.
- Docker refuses to remove a volume in use; removing it deletes the data for good.
- Next: [13 · Bind Mounts](13-bind-mounts.md).
