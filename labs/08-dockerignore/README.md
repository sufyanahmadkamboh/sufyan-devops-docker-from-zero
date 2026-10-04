# Lab 08 · .dockerignore: Keep Junk and Secrets Out of Your Image

> **Goal:** see what `docker build` actually sends to Docker, and use `.dockerignore` to keep big files and secrets out.
> **Time:** about 20 minutes · **You need:** [Lab 06](../06-first-dockerfile/README.md) and [Lab 07](../07-layers-and-cache/README.md)

## What you will learn

- What the **build context** is: the folder (and everything in it) that `docker build` sends to the Docker engine.
- How a big file you forgot about makes every build slower.
- How `COPY . .` silently copies a secret file (`.env`) **into the image**, where anyone with the image can read it.
- How a `.dockerignore` file fixes both problems.
- How a too-eager `.dockerignore` can also break a build.

```text
your folder (build context)                     Docker engine
──────────────────────────────                  ─────────────────────────
app.py              ✔ sent                       ┌─────────────────────┐
requirements.txt    ✔ sent      docker build     │  COPY . .  copies   │
junk/big.bin        ✘ ignored  ─────────────────►│  only what it       │
.env (secret!)      ✘ ignored   (.dockerignore   │  received           │
                                 filters first)  └─────────────────────┘
```

## Step 1 · Create junk and a fake secret

Every real project folder collects things that should never be inside an image: logs, test data, downloads, and files
with passwords. Let's create two of them in the simple app:

- `junk/big.bin`: a 100 MB file full of zeros (pretend it is a database dump someone left there)
- `.env`: a file with a **fake** API key (in a real project this would be a real secret)

```bash
cd examples/simple-app
mkdir -p junk
dd if=/dev/zero of=junk/big.bin bs=1M count=100
echo "API_KEY=lab-fake-key-not-a-real-secret" > .env
ls -la
```

(On macOS, `dd` wants a lowercase unit: `bs=1m`.)

## Step 2 · Build WITHOUT a .dockerignore

The simple app already has a `.dockerignore`. To see the "before" picture, switch it off by renaming it:

```bash
mv .dockerignore .dockerignore.disabled
```

Now build with `dockerfile-steps/02.Dockerfile`, which uses `COPY . .` (copy everything):

<!-- test: output=head:14; contains=transferring context -->
```bash
docker build -f dockerfile-steps/02.Dockerfile -t simple-app:no-ignore .
```

```text
#0 building with "desktop-linux" instance using docker driver

#1 [internal] load build definition from 02.Dockerfile
#1 transferring dockerfile: 170B done
#1 DONE 0.0s

#2 [internal] load metadata for docker.io/library/python:3.14-slim
#2 DONE 0.0s

#3 [internal] load .dockerignore
#3 transferring context: 2B done
#3 DONE 0.0s

#4 [1/3] FROM docker.io/library/python:3.14-slim@sha256:c3e521df8b2b498a7a682e7e18676771cb80c6b75b8699af886b2d554ce40151
...
```

**What you see:** near the top there is a line like `#N [internal] load build context` followed by
`transferring context: ...MB`. That number is how much data was sent to Docker *before* any instruction ran.
It includes our 100 MB `junk/big.bin`.

Now look inside the image. We override the command with `ls -la` (the image's own command would try to start the
app, and this early step does not even install Flask yet):

<!-- test: output; contains=junk; contains=.env -->
```bash
docker run --rm simple-app:no-ignore ls -la
```

```text
total 40
drwxr-xr-x 1 root root 4096 Oct  4 04:03 .
drwxr-xr-x 1 root root 4096 Oct  4 04:03 ..
-rwxr-xr-x 1 root root  253 Oct  4 03:32 .dockerignore.disabled
-rwxr-xr-x 1 root root   39 Oct  4 04:03 .env
-rwxr-xr-x 1 root root 1013 Oct  4 03:32 Dockerfile
-rwxr-xr-x 1 root root 1087 Oct  4 04:02 app.py
drwxr-xr-x 2 root root 4096 Oct  4 03:32 dockerfile-steps
drwxr-xr-x 2 root root 4096 Oct  4 04:03 junk
drwxr-xr-x 2 root root 4096 Oct  4 03:33 optimization
-rwxr-xr-x 1 root root   13 Oct  4 04:03 requirements.txt
```

`junk`, `.env`, the Dockerfile steps and everything else ended up in `/app`. And the secret is readable by anyone who
can run the image:

<!-- test: contains=lab-fake-key -->
```bash
docker run --rm simple-app:no-ignore cat .env
```

**Why it matters:** images get pushed to registries, shared with teammates, deployed to servers. A secret inside an
image is a leaked secret. Even if a later Dockerfile step deletes the file, it still exists in the earlier layer
(remember `docker history` from Lab 07).

Compare the sizes:

<!-- test: output -->
```bash
docker images simple-app:no-ignore
```

```text
WARNING: This output is designed for human readability. For machine-readable output, please use --format.
IMAGE                  ID             DISK USAGE   CONTENT SIZE   EXTRA
simple-app:no-ignore   da0f174fe1c4        294MB         46.6MB        
```

## Step 3 · Turn the .dockerignore back on

Put the file back. Run this even if something above failed:

```bash
mv .dockerignore.disabled .dockerignore
```

Let's read it:

<!-- test: contains=.env; contains=junk/ -->
```bash
cat .dockerignore
```

Each line is a pattern, like in `.gitignore`. `junk/` excludes the folder, `.env` excludes the secret, `*.log`
excludes every log file, and so on.

## Step 4 · Build WITH the .dockerignore

<!-- test: output=head:14; contains=transferring context -->
```bash
docker build -f dockerfile-steps/02.Dockerfile -t simple-app:with-ignore .
```

```text
#0 building with "desktop-linux" instance using docker driver

#1 [internal] load build definition from 02.Dockerfile
#1 transferring dockerfile: 170B done
#1 DONE 0.0s

#2 [internal] load metadata for docker.io/library/python:3.14-slim
#2 DONE 0.0s

#3 [internal] load .dockerignore
#3 transferring context: 295B done
#3 DONE 0.0s

#4 [internal] load build context
...
```

**What you see:** `transferring context` is now a few kilobytes instead of more than 100 MB.

<!-- test: output; absent=junk; absent=.env -->
```bash
docker run --rm simple-app:with-ignore ls -la
```

```text
total 16
drwxr-xr-x 1 root root 4096 Oct  4 03:48 .
drwxr-xr-x 1 root root 4096 Oct  4 04:03 ..
-rwxr-xr-x 1 root root 1087 Oct  4 03:32 app.py
-rwxr-xr-x 1 root root   13 Oct  4 03:32 requirements.txt
```

The image only contains `app.py` and `requirements.txt`. And the secret is gone:

<!-- test: fail; contains=No such file -->
```bash
docker run --rm simple-app:with-ignore cat .env
```

`cat: .env: No such file or directory` is exactly what we want to see.

<!-- test: output -->
```bash
docker images simple-app
```

```text
WARNING: This output is designed for human readability. For machine-readable output, please use --format.
IMAGE                    ID             DISK USAGE   CONTENT SIZE   EXTRA
simple-app:1.0           25032a644e9c        212MB         51.9MB        
simple-app:fixed         18b09356d161        212MB         51.9MB        
simple-app:no-ignore     da0f174fe1c4        294MB         46.6MB        
simple-app:step1         c28c9280bf77        189MB         46.5MB        
simple-app:step2         85904782ffb9        189MB         46.5MB        
simple-app:step4         e0d9c69ee329        212MB         51.9MB        
simple-app:with-ignore   c9b031fdee6d        189MB         46.5MB        
```

Compare the `DISK USAGE` (called `SIZE` on Docker versions before 29) of `no-ignore` and `with-ignore`: the difference is our junk.

> **Note:** `.dockerignore` also lists `Dockerfile*` and `dockerfile-steps/`. That is fine: Docker reads the Dockerfile
> you name with `-f` separately; ignoring it only keeps it out of `COPY . .`.

## Break it

Don't fix it yet, we break it on purpose. A teammate wants to keep text notes out of the image and adds `*.txt` to
`.dockerignore`. Make a backup first, then add the line:

```bash
cp .dockerignore .dockerignore.backup
echo "*.txt" >> .dockerignore
```

Build the cache-friendly Dockerfile from Lab 07:

<!-- test: fail; contains=not found -->
```bash
docker build -f dockerfile-steps/05.Dockerfile -t simple-app:broken .
```

The build fails at `COPY requirements.txt .` with `"/requirements.txt": not found`, even though the file is right
there in the folder.

## Troubleshoot it

1. **Observe:** "not found", but `ls` clearly shows `requirements.txt`:

   <!-- test: contains=requirements.txt -->
   ```bash
   ls
   ```

2. **Investigate:** the file exists on your disk, so ask: *did it reach Docker?* What is filtered before sending?

   <!-- test: contains=*.txt -->
   ```bash
   cat .dockerignore
   ```

3. **Root cause:** the new pattern `*.txt` also matches `requirements.txt`. The file never entered the build context,
   so `COPY` cannot find it.
4. **Fix:** remove the bad line (here: restore the backup). In a real project you could keep the rule and add an
   exception line `!requirements.txt` below it.

   ```bash
   mv .dockerignore.backup .dockerignore
   ```

5. **Verify:**

   <!-- test: contains=naming to -->
   ```bash
   docker build -f dockerfile-steps/05.Dockerfile -t simple-app:step5 .
   ```

The same mistake is the subject of [troubleshooting/05](../../troubleshooting/05-dockerfile-build-fails/README.md).

## Challenge

**Task:** make sure log files never reach the image.

**Requirements:**
- Create `debug.log` in `examples/simple-app`.
- Without editing `.dockerignore` (it already has the right rule), prove that `debug.log` is not inside an image built with `dockerfile-steps/02.Dockerfile`.
- Remove `debug.log` afterwards.

**Hints:** which pattern in `.dockerignore` matches `debug.log`? Use `docker run --rm <image> ls` to look inside.

**Expected result:** `ls` inside the image does not list `debug.log`.

<details><summary>Solution</summary>

```bash
echo "something went wrong at 03:00" > debug.log
docker build -f dockerfile-steps/02.Dockerfile -t simple-app:log-test .
```

<!-- test: absent=debug.log -->
```bash
docker run --rm simple-app:log-test ls
```

```bash
rm debug.log
docker rmi simple-app:log-test
```

**Explanation:** the pattern `*.log` matches any file ending in `.log` in the context root, so `debug.log` is filtered
out before the build even starts. (Use `**/*.log` to match log files in subfolders too.)

</details>

## Verify

- [ ] I can explain what the build context is.
- [ ] I can find `transferring context` in build output and say what it means.
- [ ] I know why a `.env` file must never be copied into an image.
- [ ] I can write `.dockerignore` patterns and an exception with `!`.
- [ ] I can recognise a `.dockerignore` that hides a file the Dockerfile needs.

## Clean up

```bash
rm -rf junk .env
docker rmi simple-app:no-ignore simple-app:with-ignore simple-app:step5
```

<!-- test-run: if [ -f .dockerignore.disabled ]; then mv .dockerignore.disabled .dockerignore; fi; if [ -f .dockerignore.backup ]; then mv .dockerignore.backup .dockerignore; fi; rm -rf junk .env debug.log -->

## Next

- Next lab: [Lab 09 · Volumes](../09-volumes/README.md)
- Concept lesson: [docs/11-dockerignore.md](../../docs/11-dockerignore.md)
