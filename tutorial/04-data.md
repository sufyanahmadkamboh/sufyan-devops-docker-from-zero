# 04 · Data: volumes and bind mounts

> Containers are disposable. Data is not. Learn where data lives, lose some on purpose, keep it with a volume, keep a
> real database alive across containers, and edit a website live with a bind mount.
> Time: about 60 minutes. You need: [03 · Dockerfiles](03-dockerfiles.md).

## Part 1 · Data inside a container dies with the container

Every container gets its own writable layer on top of the image. Let's write a file into it:

```bash
docker run --name writer alpine:3.24 sh -c 'echo "important data" > /data.txt && cat /data.txt'
```

The file existed. Now remove the container and create a new one from the same image:

<!-- test: fail; contains=No such file or directory -->
```bash
docker rm writer
docker run --rm alpine:3.24 cat /data.txt
```

Gone. Of course: the new container is a fresh copy of the image, and the old container's writable layer was deleted with
`docker rm`.

```text
  image alpine:3.24 (read-only)
      |                      |
  container "writer"     new container
  [writable layer]       [writable layer]   <- empty, fresh
  /data.txt              (nothing)
      x  removed with docker rm
```

That is fine for temporary files. For a database, it would be a disaster. We need storage that lives **outside** the
container's lifecycle.

## Part 2 · Volumes

A **volume** is storage managed by Docker, independent of any container. You mount it into a container at a path; what the
container writes there goes into the volume.

```text
  container "writer" ----+
                          \  mounted at /data
                           +----> volume "notes"  (lives on, managed by Docker)
                          /
  container "reader" ----+
```

### Create and use a volume

<!-- test: contains=notes -->
```bash
docker volume create notes
docker volume ls
```

Write into it from one container:

```bash
docker run --rm -v notes:/data alpine:3.24 sh -c 'echo "written by the first container" > /data/message.txt'
```

`-v notes:/data` means **VOLUME_NAME : PATH_IN_CONTAINER**. That container is already gone (`--rm`). Now read the
file from a brand-new container:

<!-- test: contains=written by the first container -->
```bash
docker run --rm -v notes:/data alpine:3.24 cat /data/message.txt
```

The data survived the container. That is the whole point of volumes.

### Where is it?

<!-- test: output; contains=Mountpoint -->
```bash
docker volume inspect notes
```

```text
[
    {
        "CreatedAt": "2026-10-04T04:38:18Z",
        "Driver": "local",
        "Labels": null,
        "Mountpoint": "/var/lib/docker/volumes/notes/_data",
        "Name": "notes",
        "Options": null,
        "Scope": "local"
    }
]
```

`Mountpoint` is where the engine keeps the files (`/var/lib/docker/volumes/notes/_data`). On Docker Desktop this path is
inside Docker's Linux VM, not on your Windows or Mac disk, so you cannot open it in your file explorer. You never need to:
you work with volumes **through containers**.

### Remove a volume

<!-- test: fail; contains=volume is in use -->
```bash
docker run -d --name holder -v notes:/data alpine:3.24 sleep 300
docker volume rm notes
```

Docker refuses to remove a volume that a container uses (even a stopped one). That protects you. Remove the container
first:

```bash
docker rm -f holder
docker volume rm notes
```

<!-- test: absent=notes -->
```bash
docker volume ls
```

> `docker volume rm` deletes the data for good. There is no recycle bin.

## Part 3 · A real database that survives

Let's do this with PostgreSQL, the way it is done at work. PostgreSQL 18 keeps its data under `/var/lib/postgresql`,
so that is where we mount the volume:

```bash
docker run -d --name db \
  -e POSTGRES_PASSWORD=lab-only-password \
  -v pgdata:/var/lib/postgresql \
  postgres:18-alpine
```

`-v pgdata:...` with a volume that does not exist yet simply creates it. Wait until the database is ready:

<!-- test: retry=30; contains=accepting connections -->
```bash
docker exec db pg_isready -U postgres
```

Create a table and a row with `psql`, the database's command-line client, which is inside the container:

<!-- test: retry=10; contains=INSERT 0 1 -->
```bash
docker exec db psql -U postgres -c "CREATE TABLE IF NOT EXISTS notes (text TEXT); INSERT INTO notes VALUES ('I must survive');"
```

Now the dramatic part. Destroy the database container completely:

```bash
docker rm -f db
```

Start a **new** container from the same image, with the same volume:

```bash
docker run -d --name db \
  -e POSTGRES_PASSWORD=lab-only-password \
  -v pgdata:/var/lib/postgresql \
  postgres:18-alpine
```

<!-- test: retry=30; output; contains=I must survive -->
```bash
docker exec db psql -U postgres -c "SELECT * FROM notes;"
```

```text
      text      
----------------
 I must survive
(1 row)
```

The row is still there. The container is new; the data is not. This is how every database runs in Docker.

### Experiment · the mount path matters

Many older tutorials mount `/var/lib/postgresql/data`. That was right up to PostgreSQL 17. Let's try it on 18:

<!-- test: fail -->
```bash
docker run --name olddb -e POSTGRES_PASSWORD=lab-only-password -v olddata:/var/lib/postgresql/data postgres:18-alpine
```

<!-- test: contains=in 18+ -->
```bash
docker logs olddb 2>&1 | grep -A 3 "in 18+"
```

The image refuses to start and explains why: from 18 on, mount the parent folder `/var/lib/postgresql`. Lesson: **the
path inside the container is decided by the image**. Always check the image's documentation on Docker Hub for where it
stores data.

```bash
docker rm -f db olddb
docker volume rm pgdata olddata
```

## Part 4 · Bind mounts: your folder inside the container

A **bind mount** maps a folder of **your computer** into the container. Change a file on your computer, and the container
sees the change immediately. This is how developers work on code without rebuilding images all the time.

```text
  Your computer                                 Container "site"
  examples/nginx/site/index.html  <==== same file ====>  /usr/share/nginx/html/index.html
```

Volume vs bind mount:

| | Volume | Bind mount |
|---|---|---|
| Who manages it | Docker | You (it is a normal folder) |
| Where it lives | Docker's storage area | Anywhere on your computer |
| Typical use | Database data, anything the app owns | Source code during development, config files |
| Syntax | `-v name:/path` | `-v /absolute/host/path:/path` |

### Serve the website from your folder

From the repository root:

<!-- test: contains=0.0.0.0:8080->80/tcp -->
```bash
docker run -d --name site -p 8080:80 \
  -v "$(pwd)/examples/nginx/site:/usr/share/nginx/html:ro" \
  nginx:1.30-alpine
docker ps --filter name=site
```

- `"$(pwd)/examples/nginx/site"` is the **absolute path** of the folder (bind mounts need an absolute host path; in
  PowerShell write `${PWD}/examples/nginx/site`).
- `/usr/share/nginx/html` is where nginx serves files from.
- `:ro` makes it **read-only** for the container: nginx can read your files but not change them.

<!-- test: retry=15; contains=Hello from my container! -->
```bash
curl -s http://localhost:8080 | grep h1
```

Our page, not nginx's welcome page. Open <http://localhost:8080> in your browser.

### Edit it live

Open `examples/nginx/site/index.html` in your editor and change the text. Or, from the terminal, append a line:

```bash
echo '<p>Edited on my computer, served by the container!</p>' >> examples/nginx/site/index.html
```

<!-- test: retry=5; contains=Edited on my computer -->
```bash
curl -s http://localhost:8080 | grep Edited
```

No rebuild, no restart. The container reads the file straight from your folder. Refresh your browser to see it.

Put the file back the way it was:

```bash
git checkout -- examples/nginx/site/index.html
```

### The same with `--mount`

`-v` is short. `--mount` is longer but explicit, with named fields:

```bash
docker rm -f site
docker run -d --name site -p 8080:80 \
  --mount type=bind,source="$(pwd)/examples/nginx/site",target=/usr/share/nginx/html,readonly \
  nginx:1.30-alpine
```

<!-- test: retry=15; contains=Hello from my container! -->
```bash
curl -s http://localhost:8080 | grep h1
```

Same result. Many teams prefer `--mount` in scripts because each field is named. There is also one important
difference, which we will now discover the hard way.

### Failure · "my changes don't show up" (and a 403)

A colleague runs the site with a small typo in the folder name:

```bash
docker rm -f site
docker run -d --name site -p 8080:80 -v "$(pwd)/examples/nginx/sitee:/usr/share/nginx/html" nginx:1.30-alpine
```

The container starts fine. But:

<!-- test: retry=10; contains=403 -->
```bash
curl -s http://localhost:8080 | grep -o '403 Forbidden'
```

Don't fix it yet. Let's investigate.

- **Symptom:** nginx answers, but with `403 Forbidden` instead of our page.
- **What should we check?** What is actually in the folder nginx serves.

<!-- test: absent=index.html -->
```bash
docker exec site ls -la /usr/share/nginx/html
```

- **Evidence:** the folder in the container is **empty**.
- And on our side?

<!-- test: contains=sitee -->
```bash
ls -d examples/nginx/sitee
```

- **Root cause:** `sitee` did not exist. With `-v`, Docker **silently creates** a missing host folder (empty), mounts it,
  and nginx has nothing to serve, so it answers 403.
- **Fix:** correct the path. With `--mount`, native Linux Docker refuses to start instead (`bind source path does not
  exist`), which is why scripts often prefer it. Docker Desktop on Windows and Mac may create the folder anyway, so do not
  rely on it there.

```bash
docker rm -f site
rmdir examples/nginx/sitee
docker run -d --name site -p 8080:80 -v "$(pwd)/examples/nginx/site:/usr/share/nginx/html:ro" nginx:1.30-alpine
```

<!-- test: retry=15; contains=Hello from my container! -->
```bash
curl -s http://localhost:8080 | grep h1
```

- **Verify:** our page is back. Lesson: **when a bind-mounted folder looks empty, check the host path first.**

```bash
docker rm -f site
```

## Where would I use this as a DevOps engineer?

- **Volumes** hold every stateful thing you run in containers: databases, message queues, uploaded files. Backups of
  those volumes are a core operations task.
- **Bind mounts** give a developer a live-reload environment, and give a container its configuration file
  (`-v ./nginx.conf:/etc/nginx/nginx.conf:ro`).
- "The data is gone after the update" is almost always a missing volume or a changed volume name. You will investigate
  exactly that in [troubleshooting/04](../troubleshooting/04-volume-data-missing/README.md) and
  [troubleshooting/10](../troubleshooting/10-database-data-disappears/README.md).

## What you learned

- A container's own files disappear with the container.
- `docker volume create | ls | inspect | rm`, and `-v name:/path`.
- A database keeps its data across containers when its data folder is on a volume, at the path the image expects.
- Bind mounts (`-v "$(pwd)/folder:/path"` or `--mount type=bind,...`) share a host folder; `:ro` makes it read-only.
- A typo in a bind mount path gives you an empty folder, not an error.

## Try it yourself

- Labs: [09-volumes](../labs/09-volumes/README.md), [10-bind-mounts](../labs/10-bind-mounts/README.md)
- Troubleshooting: [09-host-changes-not-reflected](../troubleshooting/09-host-changes-not-reflected/README.md)
- Challenges: the "Data" section of [challenges/README.md](../challenges/README.md)
- Deeper: [docs/12-volumes.md](../docs/12-volumes.md), [docs/13-bind-mounts.md](../docs/13-bind-mounts.md)

## Next

[05 · Networking](05-networking.md)
