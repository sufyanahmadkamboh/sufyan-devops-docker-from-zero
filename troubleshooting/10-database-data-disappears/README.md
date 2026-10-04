# 10 · Database data disappears

> After `docker compose down` and `up`, every row you saved is gone. In a second setup, the database will not even start.
> Time: 25 minutes · You need: labs 09 and 13 (volumes, Compose)

## Problem

Losing database data is the most expensive Docker mistake. This scenario has two parts:

- **Part 1:** a Compose file with no named volume. The data is written to disk, but after
  `down` + `up` the database starts empty.
- **Part 2:** a Compose file copied from an older tutorial. On PostgreSQL 18 the database refuses to start.

From the repository root:

```bash
cd troubleshooting/10-database-data-disappears
```

<!-- test: contains=init.sql -->
```bash
cat docker-compose.yml
```

Notice: the only entry under `volumes:` is the `init.sql` bind mount. Nothing is mounted on the
folder where PostgreSQL keeps its data. Start the database and save a row:

```bash
docker compose up -d
```

The database needs a few seconds to initialise the first time. The command is repeated until it works:

<!-- test: retry=30; contains=INSERT 0 1 -->
```bash
docker compose exec -T db psql -U board -d board -c "INSERT INTO messages (text) VALUES ('do not lose me');"
```

<!-- test: contains=do not lose me -->
```bash
docker compose exec -T db psql -U board -d board -c "SELECT id, text FROM messages;"
```

Two rows: the one from `init.sql` and ours. Now the normal end of a working day:

```bash
docker compose down
docker compose up -d
```

## Symptoms

<!-- test: retry=30; contains=Hello!; absent=do not lose me -->
```bash
docker compose exec -T db psql -U board -d board -c "SELECT id, text FROM messages;"
```

Only the `init.sql` row is back. Our row is gone. Even more telling: `init.sql` ran **again**, which only
happens when PostgreSQL finds an empty data folder.

Symptom in one sentence: *"After down + up, the database starts like new."*

## Investigation

**Step 1: where does the container store its data?**

<!-- test: output; contains=/var/lib/postgresql -->
```bash
docker inspect ts10-db-1 --format '{{range .Mounts}}{{.Type}}  {{.Name}}  ->  {{.Destination}}{{println}}{{end}}'
```

```text
bind    ->  /docker-entrypoint-initdb.d/init.sql
volume  0e961e143b35ec23e02249af03d98686c4e3e72a8fe577211e2dcd28570b3da8  ->  /var/lib/postgresql
```

One bind mount (`init.sql`) and one **volume** on `/var/lib/postgresql` with a long random name.
We never declared that volume. Where does it come from?

**Step 2: the image declares it.** The postgres image says "this folder holds data" with a `VOLUME`
instruction in its Dockerfile:

<!-- test: contains=/var/lib/postgresql -->
```bash
docker image inspect postgres:18-alpine --format '{{json .Config.Volumes}}'
```

When you do not mount anything there, Docker creates an **anonymous volume** for every new container.

**Step 3: list the volumes.**

<!-- test: output -->
```bash
docker volume ls
```

```text
DRIVER    VOLUME NAME
local     0e961e143b35ec23e02249af03d98686c4e3e72a8fe577211e2dcd28570b3da8
local     84c5f920ac401794c3987f9e69c9f3d9ad376693119be09b5f09018ca0f65a66
```

Two anonymous volumes with random names: the one from the first container (our row is still in it!)
and a new, empty one for the new container. `docker compose down` removed the old container; the new
container had no way to find the old anonymous volume, because nothing names it.

## Commands

| Command | What it told us |
|---|---|
| `docker compose exec -T db psql ... -c "SELECT ..."` | the data is gone, `init.sql` ran again |
| `docker inspect <container> --format '{{range .Mounts}}...{{end}}'` | the data folder is on an unnamed volume |
| `docker image inspect postgres:18-alpine --format '{{json .Config.Volumes}}'` | the image declares `VOLUME /var/lib/postgresql` |
| `docker volume ls` | one more anonymous volume after every down + up |

## Root Cause

The Compose file does not mount a named volume on PostgreSQL's data folder. Docker gives each new
container a fresh anonymous volume. After `down` + `up` there is a new container, so a new, empty
volume. The old data still sits in an orphaned volume that nothing uses. Repeat this daily and both
things happen: the data "disappears", and the disk slowly fills up with orphaned volumes.

## Fix

Give the data a **name**. `docker-compose.fixed.yml` adds a named volume `db-data` mounted on
`/var/lib/postgresql`:

<!-- test: contains=db-data:/var/lib/postgresql -->
```bash
cat docker-compose.fixed.yml
```

First clean up the broken setup. `down -v` removes the volumes of the current containers;
`docker volume prune -f` removes the orphaned anonymous volume left from the first run.
(`volume prune` deletes **unused anonymous volumes**, also from other projects. Read lab 18 before using it elsewhere.)

```bash
docker compose down -v
docker volume prune -f
```

Start the fixed version and save a row again:

```bash
docker compose -f docker-compose.fixed.yml up -d
```

<!-- test: retry=30; contains=INSERT 0 1 -->
```bash
docker compose -f docker-compose.fixed.yml exec -T db psql -U board -d board -c "INSERT INTO messages (text) VALUES ('do not lose me');"
```

## Verification

The same end of day as before:

```bash
docker compose -f docker-compose.fixed.yml down
docker compose -f docker-compose.fixed.yml up -d
```

<!-- test: retry=30; contains=do not lose me -->
```bash
docker compose -f docker-compose.fixed.yml exec -T db psql -U board -d board -c "SELECT id, text FROM messages;"
```

The row survived. The volume has a readable name, and `down` (without `-v`) did not touch it:

<!-- test: contains=ts10_db-data -->
```bash
docker volume ls --filter name=ts10
```

Clean up part 1. **This** command deletes the data on purpose:

```bash
docker compose -f docker-compose.fixed.yml down -v
```

## Part 2: the database refuses to start

Here is a Compose file copied from an older tutorial. It has a named volume. What could go wrong?

<!-- test: contains=/var/lib/postgresql/data -->
```bash
cat docker-compose.old-tutorial.yml
```

```bash
docker compose -f docker-compose.old-tutorial.yml up -d
```

<!-- test-run: sleep 8 -->

**Symptom:** the database container stops right away.

<!-- test: contains=Exited (1) -->
```bash
docker compose -f docker-compose.old-tutorial.yml ps -a --format 'table {{.Service}}\t{{.Status}}'
```

**Investigation:** read its logs.

<!-- test: output=head:12; contains=Error: in 18+ -->
```bash
docker compose -f docker-compose.old-tutorial.yml logs db
```

```text
db-1  | Error: in 18+, these Docker images are configured to store database data in a
db-1  |        format which is compatible with "pg_ctlcluster" (specifically, using
db-1  |        major-version-specific directory names).  This better reflects how
db-1  |        PostgreSQL itself works, and how upgrades are to be performed.
db-1  | 
db-1  |        See also https://github.com/docker-library/postgres/pull/1259
db-1  | 
db-1  |        Counter to that, there appears to be PostgreSQL data in:
db-1  |          /var/lib/postgresql/data (unused mount/volume)
db-1  | 
db-1  |        This is usually the result of upgrading the Docker image without
db-1  |        upgrading the underlying database using "pg_upgrade" (which requires both
...
```

The image explains the problem itself: since PostgreSQL 18, the official image stores its data in a
version-specific subfolder (`/var/lib/postgresql/18/docker`) and expects the volume on the **parent**
folder `/var/lib/postgresql`. A mount on the old path `/var/lib/postgresql/data` would put the data
outside the volume, so the image refuses to start instead of silently losing data.

**Root cause:** the old mount path `/var/lib/postgresql/data` (correct for PostgreSQL 17 and older)
is wrong for PostgreSQL 18.

**Fix:** mount `/var/lib/postgresql`:

<!-- test: contains=db-data:/var/lib/postgresql -->
```bash
grep -n 'db-data:' docker-compose.old-tutorial.fixed.yml
```

```bash
docker compose -f docker-compose.old-tutorial.yml down -v
docker compose -f docker-compose.old-tutorial.fixed.yml up -d
```

**Verification:**

<!-- test: retry=30; contains=accepting connections -->
```bash
docker compose -f docker-compose.old-tutorial.fixed.yml exec -T db pg_isready
```

## Clean up

```bash
docker compose -f docker-compose.old-tutorial.fixed.yml down -v
cd ../..
```

## Lesson Learned

- Databases in containers need a **named volume** on their data folder. Without one, every new
  container starts empty, and old data hides in orphaned anonymous volumes.
- `docker compose down` keeps named volumes. `docker compose down -v` deletes them: that is the
  command that really loses data.
- Check where a container keeps its data: `docker inspect --format '{{json .Mounts}}'` and the image's `Config.Volumes`.
- Copying configuration from old tutorials is risky. Read the logs: official images often tell you exactly what is wrong.

Back to the [troubleshooting overview](../README.md), or on to the [capstone](../../capstone/README.md).
