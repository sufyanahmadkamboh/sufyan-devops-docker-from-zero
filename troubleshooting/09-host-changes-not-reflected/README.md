# 09 · Host changes not reflected

> You edit the web page on your computer, refresh the browser, and nothing changes. Or worse: 403 Forbidden.
> Time: 20 minutes · You need: labs 06 and 10 (Dockerfile, bind mounts)

## Problem

Two different mistakes, the same feeling: *"Docker ignores my files."* This folder contains a tiny site
(`site/index.html`, which says `Version 1`) and a Dockerfile that copies it into an nginx image.

From the repository root:

```bash
cd troubleshooting/09-host-changes-not-reflected
```

<!-- test: contains=Version 1 -->
```bash
cat site/index.html Dockerfile
```

**Case A: the edit that does nothing.** Build the image, run it, check the page:

```bash
docker build -t my-site:1.0 .
docker run -d --name web -p 8080:80 my-site:1.0
```

<!-- test: retry=15; contains=Version 1 -->
```bash
curl -s http://localhost:8080
```

Now edit the page on your computer:

```bash
echo '<h1>Version 2</h1>' > site/index.html
```

**Case B: the bind mount that shows nothing.** A second server should serve the folder live,
with a bind mount. Someone types the folder name quickly
(PowerShell: use `${PWD}` instead of `"$(pwd)"`; Git Bash: run `export MSYS_NO_PATHCONV=1` first):

```bash
docker run -d --name web3 -p 8082:80 -v "$(pwd)/sitee:/usr/share/nginx/html" nginx:1.30-alpine
```

## Symptoms

Case A: the file on disk says `Version 2`, the server still says `Version 1`:

<!-- test: contains=Version 1; absent=Version 2 -->
```bash
curl -s http://localhost:8080
```

Case B: the second server answers `403 Forbidden`. (`-w '%{http_code}'` prints only the HTTP status.)

<!-- test: retry=15; contains=403 -->
```bash
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:8082
```

In one sentence: *"A: I changed the file, but the container serves the old version. B: the container
runs, but serves nothing."*

## Investigation

### Case A

**Step 1: what does the container itself see?**

<!-- test: contains=Version 1 -->
```bash
docker exec web cat /usr/share/nginx/html/index.html
```

The container has its own copy, and that copy is old. nginx is not caching anything: the file inside is different.

**Step 2: is any folder from the computer connected to the container?** `Mounts` lists volumes and bind mounts:

<!-- test: contains=[] -->
```bash
docker inspect web --format '{{json .Mounts}}'
```

`[]`: nothing is mounted. Everything the container sees comes from the **image**.

**Step 3: how did the page get into the image?**

<!-- test: contains=COPY site/ -->
```bash
grep COPY Dockerfile
```

`COPY` takes a snapshot of the file **at build time**.

### Case B

**Step 1: what does the container see?**

<!-- test: absent=index.html -->
```bash
docker exec web3 ls -la /usr/share/nginx/html
```

The web root is empty. With no `index.html` (and no permission to list folders), nginx answers 403.

**Step 2: which host folder is mounted?**

<!-- test: contains=sitee -->
```bash
docker inspect web3 --format '{{range .Mounts}}{{.Type}}: {{.Source}} -> {{.Destination}}{{println}}{{end}}'
```

`sitee`, with two `e`. And look at your folder:

<!-- test: contains=sitee -->
```bash
ls -d site*
```

A folder `sitee` now exists. You never created it: **Docker did**.

## Commands

| Command | What it told us |
|---|---|
| `docker exec <name> cat <file>` | the file the container really serves |
| `docker inspect <name> --format '{{json .Mounts}}'` | `[]` = nothing mounted, all content comes from the image |
| `grep COPY Dockerfile` | the content was copied at build time |
| `curl -s -o /dev/null -w '%{http_code}\n' <url>` | 403: the server runs but has nothing to show |
| `docker inspect ... {{.Source}} -> {{.Destination}}` | the exact host path that is mounted |
| `ls -d site*` | Docker created the mistyped folder |

## Root Cause

- **Case A:** the page was baked into the image by `COPY`. After the build, the image does not know
  your disk exists. Editing the file changes nothing in existing images or containers.
- **Case B:** with `-v`, a host path that does not exist is not an error. Docker creates an empty folder
  there and mounts it. The container sees an empty web root, so nginx returns 403.

## Fix

### Case A

There are two correct answers, for two different situations.

**For a release** (production, sharing the image): rebuild, then replace the container.

```bash
docker build -t my-site:1.1 .
docker rm -f web
docker run -d --name web -p 8080:80 my-site:1.1
```

<!-- test: retry=15; contains=Version 2 -->
```bash
curl -s http://localhost:8080
```

**For development** (you edit all day): use a **bind mount**, so the container reads the folder on
your computer directly. `:ro` makes it read-only for the container.

```bash
docker rm -f web
docker run -d --name web -p 8080:80 -v "$(pwd)/site:/usr/share/nginx/html:ro" nginx:1.30-alpine
```

### Case B

Remove the container and the accidental folder, then mount the right path:

```bash
docker rm -f web3
rmdir sitee
docker run -d --name web3 -p 8082:80 -v "$(pwd)/site:/usr/share/nginx/html:ro" nginx:1.30-alpine
```

The stricter `--mount` syntax protects you from this typo on Linux: it refuses a missing source with
`bind source path does not exist`. (Docker Desktop on Windows and macOS may create the folder anyway,
so this command is not part of the automatic tests.)

<!-- test: skip -->
```bash
docker run --rm --mount type=bind,src="$(pwd)/sitee",dst=/usr/share/nginx/html nginx:1.30-alpine true
```

## Verification

Edit the page once more. Both bind-mounted servers show the change at once, without a rebuild:

```bash
echo '<h1>Version 3</h1>' > site/index.html
```

<!-- test: retry=15; contains=Version 3 -->
```bash
curl -s http://localhost:8080
```

<!-- test: retry=15; contains=Version 3 -->
```bash
curl -s http://localhost:8082
```

<!-- test: contains=bind -->
```bash
docker inspect web3 --format '{{range .Mounts}}{{.Type}}: {{.Source}} -> {{.Destination}}{{println}}{{end}}'
```

## Clean up

Put the page back to its original text, so the scenario works again next time:

```bash
docker rm -f web web3
docker rmi my-site:1.0 my-site:1.1
echo '<h1>Version 1</h1>' > site/index.html
cd ../..
```

## Lesson Learned

- `COPY` = snapshot at build time. Changes on disk need a rebuild (and a new container).
- A bind mount (`-v "$(pwd)/folder:/path"`) shows live changes: the right tool while developing.
- `-v` with a wrong host path silently creates an empty folder. An empty web root gives `403`.
- `docker inspect --format '{{json .Mounts}}'` answers "where does this container get its files from?".

Next: [10 · Database data disappears](../10-database-data-disappears/README.md)
