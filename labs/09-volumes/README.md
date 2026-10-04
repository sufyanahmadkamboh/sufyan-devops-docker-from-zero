# Lab 09 · Volumes: Data That Survives the Container

> **Goal:** store data outside the container, remove the container, and prove the data is still there.
> **Time:** about 25 minutes · **You need:** [Lab 03](../03-container-lifecycle/README.md) (you know `docker rm` removes a container)

## What you will learn

- Why data written **inside** a container disappears when the container is removed.
- How to create, list, inspect and remove **volumes** (`docker volume create / ls / inspect / rm`).
- How to mount a volume into a container with `-v name:/path`.
- How a database keeps its data across container replacements.
- How a one-letter typo in a volume name makes your data "disappear".

```text
WITHOUT a volume                         WITH a volume
────────────────────                     ──────────────────────────────
┌──────────────┐                         ┌──────────────┐
│ container    │                         │ container    │
│  /data/x.txt │ ← lives in the          │  /data ──────┼──┐
└──────────────┘   container's own       └──────────────┘  │  mounted
   docker rm  →  gone, forever             docker rm  →    ▼
                                                    ┌───────────────┐
                                                    │ volume "notes"│  ← managed by Docker,
                                                    │  x.txt        │    outlives containers
                                                    └───────────────┘
```

## Step 1 · Prove that container data is temporary

```bash
cd labs/09-volumes
docker run --name nodata alpine:3.24 sh -c 'echo "important data" > /data.txt && cat /data.txt'
```

The container wrote a file and printed it. Now remove the container and start a fresh one from the same image:

```bash
docker rm nodata
```

<!-- test: fail; contains=No such file -->
```bash
docker run --rm alpine:3.24 cat /data.txt
```

`cat: can't open '/data.txt': No such file or directory`. Each container gets its own writable layer on top of the
image. Removing the container deletes that layer, and our file with it. **The image never changes.**

## Step 2 · Create a volume

```bash
docker volume create notes
```

<!-- test: output; contains=notes -->
```bash
docker volume ls
```

```text
DRIVER    VOLUME NAME
local     notes
```

**What you see:** `DRIVER local` (stored on this machine) and `VOLUME NAME notes`. You may see other volumes from your
own projects; that is fine.

<!-- test: output; contains=Mountpoint -->
```bash
docker volume inspect notes
```

```text
[
    {
        "CreatedAt": "2026-10-04T04:53:39Z",
        "Driver": "local",
        "Labels": null,
        "Mountpoint": "/var/lib/docker/volumes/notes/_data",
        "Name": "notes",
        "Options": null,
        "Scope": "local"
    }
]
```

**What you see:** JSON with the `Name`, the `Driver` and the `Mountpoint`, the real folder where Docker keeps the
data (`/var/lib/docker/volumes/notes/_data`). On Docker Desktop (Windows/macOS) that folder is inside Docker's small
Linux virtual machine, not directly on your disk. You never need to touch it: you use the volume through containers.

## Step 3 · Write with one container, read with another

Start a container called `writer` that mounts the volume at `/data` and writes a file:

```bash
docker run --name writer -v notes:/data alpine:3.24 sh -c 'echo "Hello from the writer container" > /data/hello.txt'
```

`-v notes:/data` means: *mount the volume `notes` at the path `/data` inside the container.*

Remove the writer completely:

```bash
docker rm writer
```

Now a brand-new container, `reader`, mounts the same volume:

<!-- test: contains=Hello from the writer container -->
```bash
docker run --rm --name reader -v notes:/data alpine:3.24 cat /data/hello.txt
```

The file is still there. The container that wrote it no longer exists, but the data lived in the volume.

Two containers can also use one volume **at the same time**:

<!-- test: contains=line 2 -->
```bash
docker run --rm -v notes:/data alpine:3.24 sh -c 'echo "line 2, from another container" >> /data/hello.txt'
docker run --rm -v notes:/data alpine:3.24 cat /data/hello.txt
```

## Step 4 · A real database on a volume

This is the main reason volumes exist: databases. Start PostgreSQL with its data folder on a volume called `pgdata`.

> PostgreSQL 18 images store data under `/var/lib/postgresql` (older tutorials mount `/var/lib/postgresql/data`,
> which PostgreSQL 18 refuses; see [troubleshooting/10](../../troubleshooting/10-database-data-disappears/README.md)).

```bash
docker run -d --name db -e POSTGRES_PASSWORD=lab-password -v pgdata:/var/lib/postgresql postgres:18-alpine
```

The database needs a few seconds to initialise. Then create a table and insert one row (if you get
"the database system is starting up", wait a moment and run it again):

<!-- test: retry=30; contains=INSERT -->
```bash
docker exec db psql -U postgres -c "CREATE TABLE IF NOT EXISTS notes (text TEXT); INSERT INTO notes VALUES ('I survive container removal');"
```

Now destroy the database container. `-f` stops and removes it in one go:

```bash
docker rm -f db
```

Start a **new** database container, `db2`, on the same volume:

```bash
docker run -d --name db2 -e POSTGRES_PASSWORD=lab-password -v pgdata:/var/lib/postgresql postgres:18-alpine
```

<!-- test: retry=30; contains=I survive container removal -->
```bash
docker exec db2 psql -U postgres -t -c "SELECT text FROM notes;"
```

**What you see:** `I survive container removal`. The new container found an existing database in the volume and used
it (it did not initialise a new, empty one). In real life this is how you upgrade or replace a database container
without losing data.

## Break it

Volumes that are in use are protected. Try to delete the database's volume while `db2` is running:

<!-- test: fail; contains=in use -->
```bash
docker volume rm pgdata
```

Docker refuses: `volume is in use`. Good: Docker will not pull the floor out from under a running database.

Now a mistake Docker *cannot* catch: a typo. We wrote our note into `notes`. Read it from `note` (no "s"):

<!-- test: absent=hello.txt -->
```bash
docker run --rm -v note:/data alpine:3.24 ls -la /data
```

The folder is empty. "My data is gone!" It is not; read on.

## Troubleshoot it

1. **Observe:** the container works, but `/data` is empty.
2. **Investigate:** which volumes exist?

   <!-- test: contains=note -->
   ```bash
   docker volume ls
   ```

   There are now **two** volumes: `notes` and `note`. When you mount a volume that does not exist, Docker silently
   creates a new, empty one.
3. **Investigate further:** which volume did a container really mount? Start one and ask Docker:

   <!-- test: contains=volumes/note/_data -->
   ```bash
   docker run --name checker -v note:/data alpine:3.24 true
   docker inspect checker --format '{{json .Mounts}}'
   docker rm checker
   ```

   The `Mounts` section shows `"Name":"note"` (and a `Source` ending in `/volumes/note/_data`), not `notes`.
4. **Root cause:** a typo in the volume name, not lost data.
5. **Fix and verify:** use the right name:

   <!-- test: contains=Hello from the writer container -->
   ```bash
   docker run --rm -v notes:/data alpine:3.24 cat /data/hello.txt
   ```

The same problem in a Compose project is covered in [troubleshooting/04](../../troubleshooting/04-volume-data-missing/README.md).

## Challenge

**Task:** serve a web page that lives in a volume.

**Requirements:**
- Create a volume called `site-data`.
- Use a throw-away `alpine:3.24` container to write an `index.html` containing `<h1>Served from a volume</h1>` into it.
- Run `nginx:1.30-alpine` as container `web` on host port 8080 with the volume mounted at `/usr/share/nginx/html`.
- `curl http://localhost:8080` shows your page.

**Hints:** the alpine container needs `-v site-data:/site` and `sh -c 'echo ... > /site/index.html'`.

**Expected result:** `<h1>Served from a volume</h1>`

<details><summary>Solution</summary>

```bash
docker volume create site-data
docker run --rm -v site-data:/site alpine:3.24 sh -c 'echo "<h1>Served from a volume</h1>" > /site/index.html'
docker run -d --name web -p 8080:80 -v site-data:/usr/share/nginx/html nginx:1.30-alpine
```

<!-- test: retry=15; contains=Served from a volume -->
```bash
curl -s http://localhost:8080
```

**Explanation:** the volume outlives the alpine container that filled it, and nginx reads the same files. Remove
`web`, start it again with the same `-v`, and the page is still there.

</details>

## Verify

- [ ] I can explain why files written inside a container disappear with `docker rm`.
- [ ] I can create, list, inspect and remove volumes.
- [ ] I can mount a volume with `-v name:/path`.
- [ ] I proved a database kept its data after its container was removed.
- [ ] I can find which volume a container really uses with `docker inspect`.

## Clean up

Removing containers never deletes named volumes; you have to remove volumes explicitly. **This deletes the data in them.**

```bash
docker rm -f db2 web
docker volume rm notes note pgdata site-data
```

## Next

- Next lab: [Lab 10 · Bind mounts](../10-bind-mounts/README.md)
- Concept lesson: [docs/12-volumes.md](../../docs/12-volumes.md)
