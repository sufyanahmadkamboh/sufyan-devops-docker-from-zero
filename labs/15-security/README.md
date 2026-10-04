# Lab 15 · Security basics

> Goal: run containers with less power: as a normal user, with a read-only filesystem, without extra Linux
> capabilities, and without passwords in environment variables. · Time: 45 minutes · You need: labs 05, 06 and 14.

A container is isolated, but it is not magic. If an attacker finds a bug in your application, they get exactly the
powers your container process has. Security for beginners comes down to one idea: **least privilege**. Give the
container only what it needs, nothing more. Every step in this lab removes one unnecessary power and checks that the
application still works.

## What you will learn

- Why running as `root` inside a container is risky, and how `USER` fixes it
- `--read-only` and `--tmpfs`: a filesystem the application cannot change
- `--cap-drop ALL`: removing Linux capabilities the application never uses
- Why passwords in environment variables leak, and how secret files help
- Trusted and minimal images, and what image scanning is

## Step 1 · Build two versions of the same app

From the repository root:

```bash
cd examples/simple-app
```

`dockerfile-steps/05.Dockerfile` has no `USER` instruction. The final `Dockerfile` is identical except for two lines:

```dockerfile
RUN useradd --create-home --uid 10001 appuser
USER appuser
```

Build both:

<!-- test: timeout=600 -->
```bash
docker build -f dockerfile-steps/05.Dockerfile -t simple-app:root .
docker build -t simple-app:1.0 .
```

## Step 2 · Who am I inside the container?

<!-- test: output; contains=root -->
```bash
docker run --rm simple-app:root whoami
docker run --rm simple-app:root id
```

```text
root
uid=0(root) gid=0(root) groups=0(root)
```

<!-- test: output; contains=appuser; contains=uid=10001 -->
```bash
docker run --rm simple-app:1.0 whoami
docker run --rm simple-app:1.0 id
```

```text
appuser
uid=10001(appuser) gid=10001(appuser) groups=10001(appuser)
```

Without `USER`, the process runs as **root** (uid 0). With `USER appuser`, it runs as an ordinary user with uid 10001.

Why does it matter? Let's pretend an attacker can run commands in our app. As root, they can change system files of
the container:

<!-- test: contains=wrote /etc/motd -->
```bash
docker run --rm simple-app:root sh -c "echo hacked > /etc/motd && echo wrote /etc/motd"
```

As `appuser`, the same attempt is refused:

<!-- test: fail; contains=Permission denied -->
```bash
docker run --rm simple-app:1.0 sh -c "echo hacked > /etc/motd"
```

Root inside a container is not automatically root on your computer, but it is the first step of many container
escapes, and it lets an attacker install tools, change the application and read every file. A normal user cannot.

> `USER` in the Dockerfile is a default. Anyone starting the container can override it with
> `docker run --user root ...`. So the image sets a safe default, and the people running it must not undo it.

## Step 3 · A read-only filesystem

Your application's code should never change while it runs. `--read-only` makes the container's whole filesystem
read-only:

```bash
docker run -d --name ro --read-only -p 5000:5000 simple-app:1.0
```

<!-- test: retry=15; contains=Hello -->
```bash
curl -s http://localhost:5000/
```

The app works, because it only **reads** its files. But nobody can write:

<!-- test: fail; contains=Read-only file system -->
```bash
docker exec ro touch /app/backdoor.py
```

Many programs need a place for temporary files. Give them a small in-memory folder with `--tmpfs`, and keep
everything else read-only:

<!-- test: contains=/tmp is writable -->
```bash
docker run --rm --read-only --tmpfs /tmp simple-app:1.0 sh -c "touch /tmp/ok && echo /tmp is writable"
```

> macOS note: port 5000 is used by the AirPlay Receiver on recent macOS versions. If `-p 5000:5000` says the address
> is already in use, use `-p 5050:5000` and `http://localhost:5050` instead.

## Step 4 · Drop Linux capabilities

Linux splits root's power into about 40 **capabilities**: changing file owners (`CAP_CHOWN`), binding ports below
1024, changing network settings, and so on. Docker gives every container a default set of about 14. A web app needs
none of them. Look at the difference:

<!-- test: contains=chown worked -->
```bash
docker run --rm alpine:3.24 sh -c "chown nobody /tmp && echo chown worked"
```

<!-- test: fail; contains=Operation not permitted -->
```bash
docker run --rm --cap-drop ALL alpine:3.24 chown nobody /tmp
```

Even root inside the container can no longer change a file owner, because the capability is gone.

Now combine everything we have so far: normal user, read-only, no capabilities, and `no-new-privileges` (a program
cannot gain more rights later, for example through a setuid binary):

```bash
docker run -d --name hardened --read-only --tmpfs /tmp --cap-drop ALL --security-opt no-new-privileges -p 5001:5000 simple-app:1.0
```

<!-- test: retry=15; output; contains=Hello -->
```bash
curl -s http://localhost:5001/
```

```text
Hello from simple-app!
environment: production
container hostname: 577468af3332
```

The application does not notice anything: it never needed those powers.

## Step 5 · Secrets: environment variables leak

Passing a password with `-e` is easy, and you will see it in many tutorials. Let's see who else can read it:

```bash
docker run -d --name leaky -e DB_PASSWORD=lab-password-123 alpine:3.24 sleep 300
```

<!-- test: output; contains=lab-password-123 -->
```bash
docker inspect --format '{{json .Config.Env}}' leaky
```

```text
["DB_PASSWORD=lab-password-123","PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"]
```

Anyone who can run `docker inspect` sees it, in plain text. It also shows up in `docker exec leaky env`, in crash
reports and debug pages that print the environment, in shell history, and in Compose files committed to Git.

The better pattern is a **secret file**: the password lives in a file, the file is mounted read-only into the
container, and only its **path** is in the configuration. Many official images support this with a `_FILE`
variable, for example `POSTGRES_PASSWORD_FILE`, and the message board API supports `DB_PASSWORD_FILE`. Let's mount the
example password file from the capstone:

```bash
docker run -d --name tidy -e DB_PASSWORD_FILE=/run/secrets/db_password -v "$(pwd)/../../capstone/secrets/db_password.txt.example:/run/secrets/db_password:ro" alpine:3.24 sleep 300
```

<!-- test: output; contains=DB_PASSWORD_FILE; absent=change-me -->
```bash
docker inspect --format '{{json .Config.Env}}' tidy
```

```text
["DB_PASSWORD_FILE=/run/secrets/db_password","PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"]
```

The configuration only shows **where** the secret is. The application reads the file:

<!-- test: contains=change-me -->
```bash
docker exec tidy cat /run/secrets/db_password
```

The capstone does this with Compose `secrets:`. It is not perfect (someone with access to the container can still read
the file), but the password no longer appears in `inspect`, in the Compose file, or in Git. Production systems go one
step further with a secrets manager.

> Windows: run this in WSL or Git Bash. In PowerShell, replace `"$(pwd)/..."` with `"${PWD}/..."`.

## Step 6 · Trusted and minimal images

Every image you use is code written by someone else, running on your machine. Three habits:

1. **Use trusted sources.** On Docker Hub, prefer **Docker Official Images** (like `nginx`, `python`, `postgres`) and
   **Verified Publisher** images. Avoid random images with no documentation and no updates.
2. **Pin versions.** `python:3.14-slim` instead of `python:latest`. You know what you run, and nothing changes behind
   your back.
3. **Smaller is safer.** Every package in an image is something that can have a vulnerability. `-slim` and `-alpine`
   images contain far fewer packages than the full images (Lab 16 measures this).

## Step 7 · Image scanning (concept)

An **image scanner** lists every package inside an image and compares it with public databases of known
vulnerabilities (CVEs). It is how teams find out that a library in their image needs an update.

This step is optional: it downloads a scanner and its vulnerability database (a few hundred MB). Trivy is a free,
open-source scanner that runs as a container. The version below may be outdated when you read this; check the
[Trivy releases page](https://github.com/aquasecurity/trivy/releases) for the current one.

<!-- test: skip -->
```bash
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy:0.69.3 image simple-app:1.0
```

Mounting `/var/run/docker.sock` lets Trivy read your local images. Note that this gives the scanner full control over
your Docker engine: only do it with tools you trust.

The report groups findings by severity (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`) and shows which version fixes each one.
Docker Desktop users can also try `docker scout quickview simple-app:1.0`.

<!-- test: skip -->
```bash
docker scout quickview simple-app:1.0
```

## Break it

A read-only container breaks an application that writes files where it should not. Our pretend app writes its log
into its own code folder. Don't fix it yet, we broke it on purpose.

<!-- test: fail; contains=Read-only file system -->
```bash
docker run --rm --read-only --tmpfs /tmp simple-app:1.0 sh -c "echo 'request served' >> /app/app.log"
```

## Troubleshoot it

**Observe.** The command fails with an error about the filesystem. Before changing anything, let's investigate.

**Investigate.** Which path is the problem, and is it writable at all?

<!-- test: output; contains=ro -->
```bash
docker run --rm --read-only --tmpfs /tmp simple-app:1.0 sh -c "grep ' / ' /proc/mounts; grep ' /tmp ' /proc/mounts"
```

```text
overlay / overlay ro,relatime,lowerdir=/var/lib/desktop-containerd/daemon/io.containerd.snapshotter.v1.overlayfs/snapshots/10858/fs:/var/lib/desktop-containerd/daemon/io.containerd.snapshotter.v1.overlayfs/snapshots/10395/fs:/var/lib/desktop-containerd/daemon/io.containerd.snapshotter.v1.overlayfs/snapshots/10394/fs:/var/lib/desktop-containerd/daemon/io.containerd.snapshotter.v1.overlayfs/snapshots/10157/fs:/var/lib/desktop-containerd/daemon/io.containerd.snapshotter.v1.overlayfs/snapshots/10156/fs:/var/lib/desktop-containerd/daemon/io.containerd.snapshotter.v1.overlayfs/snapshots/10155/fs:/var/lib/desktop-containerd/daemon/io.containerd.snapshotter.v1.overlayfs/snapshots/10143/fs:/var/lib/desktop-containerd/daemon/io.containerd.snapshotter.v1.overlayfs/snapshots/10142/fs:/var/lib/desktop-containerd/daemon/io.containerd.snapshotter.v1.overlayfs/snapshots/10141/fs:/var/lib/desktop-containerd/daemon/io.containerd.snapshotter.v1.overlayfs/snapshots/10140/fs,upperdir=/var/lib/desktop-containerd/daemon/io.containerd.snapshotter.v1.overlayfs/snapshots/10859/fs,workdir=/var/lib/desktop-containerd/daemon/io.containerd.snapshotter.v1.overlayfs/snapshots/10859/work 0 0
tmpfs /tmp tmpfs rw,nosuid,nodev,noexec,relatime 0 0
```

The root filesystem `/` is mounted `ro` (read-only); `/tmp` is a `tmpfs` mounted `rw`.

**Root cause.** The application tries to write into `/app`, which is part of the read-only image filesystem.

**Fix.** Do **not** remove `--read-only`. Write to the place that is meant for it: `/tmp` here (or a volume, if the
data must survive the container).

<!-- test: contains=request served -->
```bash
docker run --rm --read-only --tmpfs /tmp simple-app:1.0 sh -c "echo 'request served' >> /tmp/app.log && cat /tmp/app.log"
```

**Verify.** The line is written and read back. Even better for logs: write them to stdout, so `docker logs` shows them
and nothing needs to be written to disk at all.

## Challenge

**Task:** Run `simple-app:1.0` on host port 5002 as locked down as you can, and prove each protection is active.

**Requirements:**
- Normal user, read-only filesystem, all capabilities dropped, no new privileges, at most 128 MB of memory.
- `curl http://localhost:5002/` still answers.
- Show with commands: the user id, that writing to `/app` fails, and the memory limit.

**Hints:**
- Combine the flags from steps 3 and 4, plus `--memory` from lab 14.
- `docker exec <name> id`, `docker exec <name> touch /app/x`, `docker inspect --format '{{.HostConfig.Memory}}'`.

<details><summary>Solution</summary>

```bash
docker run -d --name fortress --read-only --tmpfs /tmp --cap-drop ALL --security-opt no-new-privileges --memory=128m -p 5002:5000 simple-app:1.0
```

<!-- test: retry=15; contains=Hello -->
```bash
curl -s http://localhost:5002/
```

<!-- test: contains=uid=10001; contains=Read-only file system; contains=134217728 -->
```bash
docker exec fortress id
docker exec fortress touch /app/x 2>&1 || true
docker inspect --format '{{.HostConfig.Memory}}' fortress
```

`134217728` bytes = 128 MiB. Every protection is in place and the application still answers.

</details>

## Verify

- [ ] I can explain why `USER` matters and check which user a container runs as
- [ ] I can run a container read-only, with a writable `/tmp` only
- [ ] I can drop all capabilities and know the application usually does not need them
- [ ] I know that `-e PASSWORD=...` is visible in `docker inspect`, and how a secret file avoids that
- [ ] I can explain trusted images, pinned versions, minimal images and image scanning

## Clean up

```bash
docker rm -f ro hardened leaky tidy fortress 2>/dev/null || true
docker rmi simple-app:root
cd ../..
```

## Next

- Concept lesson: [docs/19-security-basics.md](../../docs/19-security-basics.md)
- Next lab: [Lab 16 · Image optimization](../16-image-optimization/README.md)
