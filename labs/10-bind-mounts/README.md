# Lab 10 · Bind Mounts: Your Folder, Inside the Container

> **Goal:** share a folder from your computer with a container, edit a file on your computer, and see the change live.
> **Time:** about 25 minutes · **You need:** [Lab 04](../04-port-mapping/README.md) (ports) and [Lab 09](../09-volumes/README.md) (volumes)

## What you will learn

- What a **bind mount** is: a folder (or file) from your computer that appears inside the container.
- The live-editing workflow developers use every day: change a file, refresh the browser, no rebuild.
- The difference between a bind mount and an image built with `COPY` (and why "my change does not show up").
- `-v` versus `--mount`, and read-only mounts.
- What happens when the path you mount has a typo.

```text
your computer                                  container "web"
────────────────────────────                   ──────────────────────────────
examples/nginx/site/         ◄────────────────►  /usr/share/nginx/html/
   index.html                  the SAME files     index.html  (nginx serves this)
                               (not a copy)
edit on the host  ─────────────────────────────►  nginx serves the new version immediately
```

> **Windows users:** run these labs in **WSL2** (Ubuntu) for the smoothest experience. In **Git Bash**, first run
> `export MSYS_NO_PATHCONV=1`, otherwise Git Bash rewrites the container path `/usr/share/nginx/html`. In **PowerShell**,
> write `${PWD}` instead of `$(pwd)`.

## Step 1 · Serve a folder from your computer

```bash
cd examples/nginx
ls site
```

Start nginx with the `site` folder mounted where nginx looks for web pages:

```bash
docker run -d --name web -p 8080:80 -v "$(pwd)/site:/usr/share/nginx/html" nginx:1.30-alpine
```

`-v HOST_PATH:CONTAINER_PATH`. When the left side is a **path** (it starts with `/` or `.`), it is a bind mount.
When it is a plain **name** (like `notes` in Lab 09), it is a volume. `$(pwd)` is your current folder; Docker needs
an absolute path for bind mounts.

<!-- test: retry=15; contains=Hello from my container -->
```bash
curl -s http://localhost:8080
```

Open <http://localhost:8080> in your browser too. This page was **not** copied into any image: nginx reads it straight
from your folder.

## Step 2 · Edit on your computer, see it in the container

Keep a copy of the original page so we can restore it, then change the file **on your computer**:

```bash
cp site/index.html site/index.html.backup
echo "<p>Edited on my computer, served by the container without a rebuild.</p>" >> site/index.html
```

(You can also open `examples/nginx/site/index.html` in your editor and change the heading. Same effect.)

<!-- test: retry=5; contains=Edited on my computer -->
```bash
curl -s http://localhost:8080
```

Refresh the browser: the new line is there. No rebuild, no restart. Let's look from the container's side too:

<!-- test: contains=Edited on my computer -->
```bash
docker exec web tail -n 3 /usr/share/nginx/html/index.html
```

Both sides see one and the same file. Put the original back:

```bash
mv site/index.html.backup site/index.html
```

**Why it matters:** this is how developers work with Docker locally: the code lives on their laptop (in their editor
and in git), the container runs it, and every save is visible immediately.

## Step 3 · Compare with an image built with COPY

`examples/nginx/Dockerfile` bakes the page **into** an image:

<!-- test: contains=COPY site/ -->
```bash
cat Dockerfile
```

Build it and run it next to the first container, on port 8081:

```bash
docker build -t my-nginx:1.0 .
docker run -d --name web2 -p 8081:80 my-nginx:1.0
```

Now edit the host file again:

```bash
cp site/index.html site/index.html.backup
echo "<p>Second edit on the host.</p>" >> site/index.html
```

Ask both containers:

<!-- test: retry=15; contains=Second edit on the host -->
```bash
curl -s http://localhost:8080
```

<!-- test: retry=15; absent=Second edit on the host -->
```bash
curl -s http://localhost:8081
```

`web` (bind mount) shows the edit. `web2` (image) does **not**: its copy of the page was frozen into the image when
you ran `docker build`. To get the change into `web2` you would rebuild the image and replace the container. This is
the cause of [troubleshooting/09](../../troubleshooting/09-host-changes-not-reflected/README.md).

Restore the page and remove `web2`:

```bash
mv site/index.html.backup site/index.html
docker rm -f web2
```

| | Bind mount | Image (`COPY`) | Volume |
|---|---|---|---|
| Where the files live | a folder you choose on your computer | inside the image layers | a place Docker manages |
| Change a file | visible at once | needs a rebuild | through a container |
| Typical use | local development, config files | what you ship to servers | database and app data |

## Step 4 · `-v` versus `--mount`, and read-only mounts

`--mount` is the longer, more explicit way to write the same thing. Each part is named, so it is easier to read:

```bash
docker run -d --name web3 -p 8082:80 \
  --mount type=bind,source="$(pwd)/site",target=/usr/share/nginx/html,readonly \
  nginx:1.30-alpine
```

<!-- test: retry=15; contains=Hello from my container -->
```bash
curl -s http://localhost:8082
```

`readonly` (with `-v` you write `:ro` at the end) means the container can read the files but not change them.
Let's try to write from inside the container:

<!-- test: fail; contains=Read-only file system -->
```bash
docker exec web3 touch /usr/share/nginx/html/hacked.html
```

`Read-only file system`. A good habit for anything a container only needs to read, such as configuration files.

```bash
docker rm -f web3
```

## Break it

Don't fix it yet: we break it on purpose. Replace `web` with a new container whose path has a typo: `sitee`
instead of `site`.

```bash
docker rm -f web
docker run -d --name web -p 8080:80 -v "$(pwd)/sitee:/usr/share/nginx/html" nginx:1.30-alpine
```

The container starts without any error. But:

<!-- test: retry=15; contains=403 -->
```bash
curl -s -o /dev/null -w "HTTP status: %{http_code}\n" http://localhost:8080
```

`HTTP status: 403`. Forbidden. Where did our page go?

## Troubleshoot it

1. **Observe:** the container is running (`docker ps`), the port works, but nginx answers 403.
2. **Investigate the logs:**

   <!-- test: retry=5; contains=forbidden -->
   ```bash
   docker logs web
   ```

   nginx says the `directory index of "/usr/share/nginx/html/" is forbidden`: there is no `index.html` to serve.
3. **Investigate inside the container:**

   ```bash
   docker exec web ls -la /usr/share/nginx/html
   ```

   The folder is empty.
4. **Investigate the mount:** what did Docker actually mount?

   <!-- test: contains=sitee -->
   ```bash
   docker inspect web --format '{{json .Mounts}}'
   ```

   The `Source` ends in `/sitee`. And on your computer:

   <!-- test: contains=sitee -->
   ```bash
   ls -d sitee
   ```

   A new, empty `sitee` folder appeared next to `site`!
5. **Root cause:** with `-v`, if the host path does not exist, Docker **creates an empty folder** and mounts it.
   The empty folder hides everything nginx would normally serve.
6. **Fix:** remove the container and the accidental folder, then use the correct path:

   ```bash
   docker rm -f web
   rmdir sitee
   docker run -d --name web -p 8080:80 -v "$(pwd)/site:/usr/share/nginx/html" nginx:1.30-alpine
   ```

7. **Verify:**

   <!-- test: retry=15; contains=Hello from my container -->
   ```bash
   curl -s http://localhost:8080
   ```

**`--mount` is stricter.** On Linux, `--mount type=bind` refuses a missing source path with an error like
`bind source path does not exist`, which catches the typo immediately. Docker Desktop (Windows/macOS) may instead
create the folder, just like `-v`. Try it on your machine (then remove `sitee` again if it appeared):

<!-- test: skip -->
```bash
docker run --rm --mount type=bind,source="$(pwd)/sitee",target=/usr/share/nginx/html nginx:1.30-alpine true
```

## Challenge

**Task:** serve your own mini website with a read-only bind mount.

**Requirements:**
- Create a folder `my-site` inside `examples/nginx` with an `index.html` that contains `<h1>My own site</h1>`.
- Run `nginx:1.30-alpine` as container `mysite` on host port 8082, using `--mount` and `readonly`.
- `curl http://localhost:8082` shows your page; editing the file on your computer changes the page.

**Hints:** Step 4 has a `--mount` example. The folder must exist before you start the container.

**Expected result:** `<h1>My own site</h1>`

<details><summary>Solution</summary>

```bash
mkdir -p my-site
echo "<h1>My own site</h1>" > my-site/index.html
docker run -d --name mysite -p 8082:80 \
  --mount type=bind,source="$(pwd)/my-site",target=/usr/share/nginx/html,readonly \
  nginx:1.30-alpine
```

<!-- test: retry=15; contains=My own site -->
```bash
curl -s http://localhost:8082
```

**Explanation:** the files stay on your computer; nginx only reads them. Edit `my-site/index.html`, refresh, and the
change appears. `readonly` guarantees the container cannot modify your files.

</details>

## Verify

- [ ] I can bind mount a folder with `-v "$(pwd)/folder:/path"` and with `--mount type=bind,...`.
- [ ] I changed a file on my computer and saw it inside the container without rebuilding.
- [ ] I can explain why an image built with `COPY` does not see later edits.
- [ ] I can make a mount read-only.
- [ ] I know that `-v` with a wrong path silently creates an empty folder, and how to find out with `docker inspect`.

## Clean up

```bash
docker rm -f web mysite
docker rmi my-nginx:1.0
rm -rf my-site
```

<!-- test-run: if [ -f site/index.html.backup ]; then mv site/index.html.backup site/index.html; fi; rmdir sitee 2>/dev/null || true; rm -rf my-site -->

## Next

- Next lab: [Lab 11 · Networking](../11-networking/README.md)
- Concept lesson: [docs/13-bind-mounts.md](../../docs/13-bind-mounts.md)
