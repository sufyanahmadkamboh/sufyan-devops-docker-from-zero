# 04 · Volume data appears missing

> You saved data on a volume. The next container cannot find it. Is the data lost?
> Time: 15 minutes · You need: labs 09 and 13

## Problem

Volumes exist so that data outlives containers. So when data "disappears", the first thought is
*Docker deleted my data*. Almost always the data is still there, and the new container is simply
looking at a **different volume**.

Let's reproduce it. From the repository root:

```bash
cd troubleshooting/04-volume-data-missing
```

Create a volume called `notes` and write a file into it with a short-lived `writer` container:

```bash
docker volume create notes
docker run --rm --name writer -v notes:/data alpine:3.24 sh -c 'echo "remember the milk" > /data/todo.txt'
```

The `writer` container is gone (`--rm`), the volume stays. Later, a `reader` container wants the file.
Look closely at the command: it was typed in a hurry.

<!-- test: fail; contains=No such file or directory -->
```bash
docker run --rm --name reader -v note:/data alpine:3.24 cat /data/todo.txt
```

## Symptoms

```text
cat: can't open '/data/todo.txt': No such file or directory
```

The folder `/data` exists in the reader, but it is empty. Symptom in one sentence:
*"The file I saved on the volume is not there in the new container."*

## Investigation

**Step 1: which volumes exist?**

<!-- test: output; contains=notes -->
```bash
docker volume ls
```

```text
DRIVER    VOLUME NAME
local     note
local     notes
```

There are **two** volumes: `notes` (we created it) and `note`, which we never created on purpose.

**Step 2: when was each one created?**

<!-- test: output; contains=note -->
```bash
docker volume inspect notes note --format '{{.Name}}  created {{.CreatedAt}}'
```

```text
notes  created 2026-10-04T04:09:31Z
note  created 2026-10-04T04:09:32Z
```

`note` was created seconds ago, by the `reader` command.

**Step 3: what is inside each volume?** We look with a throw-away container:

<!-- test: contains=todo.txt -->
```bash
docker run --rm -v notes:/data alpine:3.24 ls -la /data
```

<!-- test: absent=todo.txt -->
```bash
docker run --rm -v note:/data alpine:3.24 ls -la /data
```

The data is safe in `notes`. `note` is empty.

## Commands

| Command | What it told us |
|---|---|
| `docker volume ls` | a second, unexpected volume `note` exists |
| `docker volume inspect <vol> --format '{{.CreatedAt}}'` | `note` is brand new |
| `docker run --rm -v <vol>:/data alpine:3.24 ls -la /data` | which volume really holds the file |

## Root Cause

`-v note:/data` contains a typo: `note` instead of `notes`. When `-v` names a volume that does not
exist, Docker does **not** report an error; it silently creates a new, empty volume with that name.
The reader looked into an empty volume.

## Fix

Use the correct volume name:

<!-- test: contains=remember the milk -->
```bash
docker run --rm --name reader -v notes:/data alpine:3.24 cat /data/todo.txt
```

Then remove the accidental volume, so nobody uses it by mistake later:

```bash
docker volume rm note
```

## Verification

<!-- test: contains=[notes]; absent=[note] -->
```bash
docker volume ls --format '[{{.Name}}]' --filter name=note
```

Only `notes` is left, and it still holds the file.

### The same trap with Docker Compose

Compose puts the **project name** in front of every volume name: the volume `db-data` of a project
called `multi-container-app` is really `multi-container-app_db-data`. The project name is the folder
name, unless you set it with `-p` or `name:`. Rename the folder, or start with another `-p`, and Compose
looks for a different volume: your data is still there, under the old name.

Let's see it with the message board's database (we start only the `db` service):

```bash
cd ../../examples/multi-container-app
docker compose up -d db
docker compose -p renamed-project up -d db
```

<!-- test: output; contains=multi-container-app_db-data; contains=renamed-project_db-data -->
```bash
docker volume ls --filter name=db-data
```

```text
DRIVER    VOLUME NAME
local     multi-container-app_db-data
local     renamed-project_db-data
```

Two volumes, one per project name. Each project sees only its own. Clean this demo up:

```bash
docker compose down -v
docker compose -p renamed-project down -v
cd ../../troubleshooting/04-volume-data-missing
```

## Clean up

```bash
docker volume rm notes
cd ../..
```

## Lesson Learned

- `-v <name>:/path` with an unknown name creates a new empty volume. No error, no warning.
- When data "disappears", run `docker volume ls` before anything else. Most of the time the data is
  in a volume you are not looking at.
- Compose volume names start with the project name. Renaming the folder (or using another `-p`) means a
  new, empty volume.
- Look inside a volume with a throw-away container: `docker run --rm -v <vol>:/data alpine:3.24 ls -la /data`.

Next: [05 · Dockerfile build fails](../05-dockerfile-build-fails/README.md)
