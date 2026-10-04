# Chapter 8 · Secure, optimise and share your images

> **Where you are:** you build images, run applications with Compose, and investigate them with logs and inspect.
> **In this chapter:** four things you need before an image leaves your laptop: basic security, a smaller image,
> publishing it to a registry, and cleaning up safely.
> **Time:** about 60 minutes.

We work with `simple-app` again (`examples/simple-app`). Let's build the finished version and an older step of it,
so we can compare them:

<!-- test: timeout=600; output=tail:3 -->
```bash
cd examples/simple-app
docker build -t simple-app:1.0 .
docker build -f dockerfile-steps/03.Dockerfile -t simple-app:root .
```

```text
...
#9 DONE 0.1s

View build details: docker-desktop://dashboard/build/desktop-linux/desktop-linux/pu91d93wpfl6rg86lbqf5s6t4
```

`simple-app:1.0` is built from the finished `Dockerfile`. `simple-app:root` is built from step 3, before we added a
`USER` instruction.

## Part 1 · Security basics

Docker security is a big topic. As a beginner you need six habits, and you will practise all of them here:

```text
  1. Do not run as root            USER in the Dockerfile
  2. Use small, trusted images     official / verified images, pinned versions, slim or alpine
  3. Give only what is needed      --read-only, --cap-drop ALL, publish only the ports you need
  4. Keep secrets out of images    and out of environment variables when you can (use files)
  5. Scan images                   know which known vulnerabilities are inside
  6. Limit resources               --memory, --cpus (Chapter 7)
```

### 8.1 Who am I inside the container?

Let's run this:

<!-- test: output; contains=root -->
```bash
docker run --rm simple-app:root whoami
```

```text
root
```

`root`. By default, the process in a container runs as the root user. Containers are isolated, but if an attacker
breaks into a process running as root and finds a weakness in that isolation, they are root on your machine.
Now the finished image:

<!-- test: output; contains=uid=10001 -->
```bash
docker run --rm simple-app:1.0 id
```

```text
uid=10001(appuser) gid=10001(appuser) groups=10001(appuser)
```

`uid=10001(appuser)`. These two lines in the `Dockerfile` did that:

```dockerfile
RUN useradd --create-home --uid 10001 appuser
USER appuser
```

Everything after `USER` (including the running application) runs as `appuser`. Can this user change the
application's files? Let's try:

<!-- test: fail; contains=Permission denied -->
```bash
docker run --rm simple-app:1.0 touch /usr/local/bin/hacked
```

`Permission denied`. That is least privilege: the app can run, but it cannot modify the system it runs on.

### 8.2 A read-only filesystem

Even a non-root process can write to its own home folder or `/tmp`. If the application never needs to write files,
make the whole container filesystem read-only:

<!-- test: fail; contains=Read-only file system -->
```bash
docker run --rm --read-only simple-app:1.0 touch /home/appuser/notes.txt
```

`Read-only file system`. Does the app itself still work? Let's start it read-only and ask it:

<!-- test: output -->
```bash
docker run -d --name secure --read-only -p 5000:5000 simple-app:1.0
```

```text
c494a6ee3a5982e510e9d443cb9203c1630e1b10393ffdc71b188145c867d8c6
```

<!-- test: retry=15; output; contains=Hello from simple-app -->
```bash
curl -s http://localhost:5000/
```

```text
Hello from simple-app!
environment: production
container hostname: c494a6ee3a59
```

It works, because it never writes anything. (If an app needs to write temporary files, you add a small in-memory
folder with `--tmpfs /tmp`. The capstone's API does exactly that.)

> **macOS users:** if port 5000 is already taken, it is usually "AirPlay Receiver". Use `-p 5001:5000` and
> `http://localhost:5001` instead, or turn AirPlay Receiver off in the system settings.

### 8.3 Drop capabilities

Linux splits root's power into pieces called *capabilities*: changing file owners (`CHOWN`), binding low ports,
and so on. Docker gives containers a default set. Most apps need none of them. Watch the difference:

<!-- test: output; contains=changed owner -->
```bash
docker run --rm alpine:3.24 sh -c 'touch /tmp/f && chown nobody /tmp/f && echo changed owner'
```

```text
changed owner
```

<!-- test: fail; contains=Operation not permitted -->
```bash
docker run --rm --cap-drop ALL alpine:3.24 sh -c 'touch /tmp/f && chown nobody /tmp/f && echo changed owner'
```

Same command, same root user, but with all capabilities dropped even root cannot change file owners anymore.
`--cap-drop ALL` is a cheap, strong default for applications that do not need special powers.

### 8.4 Secrets: environment variables are not secret

Let's start a container with a password in an environment variable, the way many tutorials do it:

<!-- test: output -->
```bash
docker run -d --name leaky -e DB_PASSWORD=super-secret-lab-value alpine:3.24 sleep 300
```

```text
c9fd6960656aba37db1e3820a1b4509a76fa19daf662d65129933a9f787207e8
```

Now, as anyone who can use Docker on this machine:

<!-- test: output; contains=DB_PASSWORD=super-secret-lab-value -->
```bash
docker inspect leaky --format '{{json .Config.Env}}'
```

```text
["DB_PASSWORD=super-secret-lab-value","PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"]
```

There it is, in plain text. Environment variables also appear in debug output, crash reports and `docker compose config`.
The better way is a **file** that is mounted into the container and read by the application. The capstone does this
with Compose *secrets*:

```yaml
# capstone/docker-compose.yml (excerpt)
  api:
    environment:
      DB_PASSWORD_FILE: /run/secrets/db_password   # the app reads the password from this file
    secrets: [db_password]
secrets:
  db_password:
    file: ./secrets/db_password.txt                # on your computer, never committed to Git
```

Two more rules about secrets:

- **Never `COPY` a secret into an image.** Anyone who pulls the image can read it, even if a later layer deletes the file
  (you saw that layers keep everything in [Chapter 3](03-dockerfiles.md)).
- **Keep `.env` and secret files out of the build context** with `.dockerignore` and out of Git with `.gitignore`.

### 8.5 Trusted images and scanning (concept)

Every image you `FROM` brings someone else's software into your application. Habits:

- Prefer **Docker Official Images** (`nginx`, `python`, `postgres`) and verified publishers; avoid random images.
- **Pin versions** (`python:3.14-slim`, not `python:latest`), so builds are repeatable and upgrades are deliberate.
- **Scan** images for known vulnerabilities (CVEs). A scanner compares the packages inside your image with public
  vulnerability databases.

This step is optional (it downloads a scanner and its database, a few hundred MB), so the tests skip it. With Trivy, a
free open-source scanner that itself runs as a container:

<!-- test: skip -->
```bash
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy:0.75.0 image --severity HIGH,CRITICAL simple-app:1.0
```

If you use Docker Desktop, `docker scout quickview simple-app:1.0` gives a similar summary. The lesson is the habit,
not the tool: **know what is inside your images**, and rebuild them regularly so base-image security fixes reach you.

Clean up the security containers:

```bash
docker rm -f secure leaky
```

## Part 2 · Image optimisation

Smaller images download faster, start faster, cost less storage and contain fewer things that can have
vulnerabilities. Let's measure it instead of believing it. The folder `optimization/` has two more Dockerfiles for the
same app:

- `optimization/fat.Dockerfile`: a typical first attempt. The full `python:3.14` image, build tools "just in case",
  pip cache kept, everything copied before installing.
- `optimization/multistage.Dockerfile`: a multi-stage build on Alpine.

### 8.6 The fat image

Let's build it. This takes a while; that slowness is part of the lesson.

<!-- test: timeout=1200; output=tail:3 -->
```bash
docker build -f optimization/fat.Dockerfile -t simple-app:fat .
```

```text
...
#10 DONE 3.2s

View build details: docker-desktop://dashboard/build/desktop-linux/desktop-linux/fayntr446w8ybnk3a79szyoia
```

### 8.7 The multi-stage image

A multi-stage build uses one stage to **build** and another, fresh stage to **run**. Only what you copy with
`COPY --from=builder` reaches the final image. Read it:

<!-- test: output; contains=AS builder; contains=COPY --from=builder -->
```bash
grep -E "^(FROM|COPY|RUN)" optimization/multistage.Dockerfile
```

```text
FROM python:3.14-alpine AS builder
RUN apk add --no-cache build-base
RUN python -m venv /opt/venv
COPY requirements.txt .
RUN /opt/venv/bin/pip install --no-cache-dir -r requirements.txt
FROM python:3.14-alpine
COPY --from=builder /opt/venv /opt/venv
COPY app.py .
RUN adduser -D -u 10001 appuser
```

The first stage installs `build-base` (compilers) and the Python packages into a virtual environment in `/opt/venv`.
The second stage starts again from a clean `python:3.14-alpine` and copies only `/opt/venv` and `app.py`.
The compilers never reach the final image.

<!-- test: timeout=900; output=tail:3 -->
```bash
docker build -f optimization/multistage.Dockerfile -t simple-app:multistage .
```

```text
...
#14 DONE 1.1s

View build details: docker-desktop://dashboard/build/desktop-linux/desktop-linux/387s5qjzcfuu9vlhclacnymuh
```

### 8.8 Compare

Now compare the three images:

<!-- test: output; contains=fat; contains=multistage -->
```bash
docker images simple-app
```

```text
IMAGE                   ID             DISK USAGE   CONTENT SIZE   EXTRA
simple-app:1.0          20aeb3209e8f        212MB         51.9MB        
simple-app:clean        614749901fce        189MB         46.5MB        
simple-app:fat          f29822dcd7e5       1.75GB          454MB        
simple-app:leaky        06809757035e        239MB         46.5MB        
simple-app:multistage   2bcbfd28cfde        108MB         26.1MB        
simple-app:root         939d3ab86401        212MB         51.9MB        
simple-app:step1        a9edeb483f3f        189MB         46.5MB        
simple-app:step2        a885aefc3259        189MB         46.5MB        
simple-app:step3        b7b846326047        212MB         51.9MB        
simple-app:step4        d0c998f34082        212MB         51.9MB        
simple-app:step5        667a8d95bf73        212MB         51.9MB        
```

Look at the `DISK USAGE` column (`SIZE` on Docker versions before 29; your numbers may differ a little, the order will not). The fat image is many times bigger
than `1.0` (slim base, no build tools, no pip cache), and the multi-stage Alpine image is the smallest. All three run
the same application. Check that the smallest one really works:

<!-- test: output; contains=Hello from simple-app -->
```bash
docker run --rm simple-app:multistage python -c "import urllib.request, subprocess, time; p = subprocess.Popen(['python', 'app.py']); time.sleep(2); print(urllib.request.urlopen('http://127.0.0.1:5000').read().decode()); p.terminate()"
```

```text
simple-app starting on 0.0.0.0:5000 (APP_ENV=production)
 * Serving Flask app 'app'
 * Debug mode: off
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://172.17.0.2:5000
Press CTRL+C to quit
127.0.0.1 - - [04/Oct/2026 04:48:11] "GET / HTTP/1.1" 200 -
Hello from simple-app!
environment: production
container hostname: 4100729239fc
```

> That long command starts the app inside the container and asks it for its home page, all in one go. You could also
> run it with `-p 5000:5000` and use `curl` as before.

Where does the size of the fat image come from? `docker history` shows the size of each layer:

<!-- test: output=head:8 -->
```bash
docker history simple-app:fat
```

```text
IMAGE          CREATED          CREATED BY                                      SIZE      COMMENT
f29822dcd7e5   23 seconds ago   CMD ["python" "app.py"]                         0B        buildkit.dockerfile.v0
<missing>      23 seconds ago   RUN /bin/sh -c pip install -r requirements.t…   18.4MB    buildkit.dockerfile.v0
<missing>      25 seconds ago   COPY . . # buildkit                             16.4kB    buildkit.dockerfile.v0
<missing>      25 seconds ago   WORKDIR /app                                    8.19kB    buildkit.dockerfile.v0
<missing>      25 seconds ago   RUN /bin/sh -c apt-get update && apt-get ins…   74.5MB    buildkit.dockerfile.v0
<missing>      2 days ago       CMD ["python3"]                                 0B        buildkit.dockerfile.v0
<missing>      2 days ago       RUN /bin/sh -c set -eux;  for src in idle3 p…   16.4kB    buildkit.dockerfile.v0
...
```

The biggest layers are the full Python base image and the `apt-get install` of build tools the app never uses.

**Optimisation checklist** (each item is something you practised in this repo):

| Technique | Why it helps |
|---|---|
| slim or alpine base image | far fewer packages to download and to patch |
| multi-stage build | build tools stay in the builder stage |
| `--no-cache-dir`, `rm -rf /var/lib/apt/lists/*` | no caches inside layers |
| install only what runs | no `vim`, no `curl` "just in case" |
| `.dockerignore` | no junk, no secrets in the build context ([Chapter 3](03-dockerfiles.md)) |
| dependencies before code | fast rebuilds through the layer cache |

## Part 3 · Share your image through a registry

```text
   docker build  ->  docker tag  ->  docker push  ->  registry  ->  docker pull  ->  docker run
                     (name it for                    (Docker Hub,     (any machine)
                      the registry)                   or your own)
```

- A **registry** is a server that stores images (Docker Hub is the default one).
- A **repository** is one image name in a registry, for example `nginx` or `your-username/simple-app`.
- A **tag** is one version in a repository, for example `1.0`.

The full name of an image is `registry/repository:tag`. When the registry part is missing, Docker means Docker Hub.

### 8.9 Practise with your own local registry (no account needed)

The registry software is itself a container image. Let's run one on your machine:

<!-- test: output -->
```bash
docker run -d --name registry -p 5000:5000 registry:3
```

```text
Unable to find image 'registry:3' locally
3: Pulling from library/registry
8dc2188d2a74: Pulling fs layer
90764beeca7f: Pulling fs layer
2aef3a8beb68: Pulling fs layer
783ed5b12fca: Pulling fs layer
8dc2188d2a74: Download complete
90764beeca7f: Download complete
783ed5b12fca: Download complete
90764beeca7f: Pull complete
d561fdf230c8: Download complete
2aef3a8beb68: Download complete
6c18a739ea63: Download complete
8dc2188d2a74: Pull complete
783ed5b12fca: Pull complete
2aef3a8beb68: Pull complete
Digest: sha256:ddf754342cfc8acc51a56d5d0ab6af06826461864460636d8bd5c546dab2a7b8
Status: Downloaded newer image for registry:3
9d88ff40131e4060951463cb8fc9d3629921a60d64167017526471734bc2b139
```

Tag the image with the registry's address. This does not copy anything; it adds a second name to the same image:

```bash
docker tag simple-app:1.0 localhost:5000/simple-app:1.0
```

Push it:

<!-- test: retry=10; output=tail:3; contains=digest: sha256 -->
```bash
docker push localhost:5000/simple-app:1.0
```

```text
...
c5e6e50697ef: Pushed
c4d667dbb95c: Pushed
1.0: digest: sha256:20aeb3209e8f8b24bb1576144d489d260045bbbadf7fc9633b09d8dff01fedfe size: 856
```

Each layer is uploaded, then you get a **digest**: the unique fingerprint of exactly this image content. Ask the
registry what it stores:

<!-- test: output; contains=simple-app -->
```bash
curl -s http://localhost:5000/v2/_catalog
```

```text
{"repositories":["simple-app"]}
```

Now pretend you are another machine: delete the local copy and pull it back from the registry.

<!-- test: output=tail:3; contains=Downloaded newer image -->
```bash
docker rmi localhost:5000/simple-app:1.0
docker image rm simple-app:1.0
docker pull localhost:5000/simple-app:1.0
```

```text
...
Digest: sha256:20aeb3209e8f8b24bb1576144d489d260045bbbadf7fc9633b09d8dff01fedfe
Status: Downloaded newer image for localhost:5000/simple-app:1.0
localhost:5000/simple-app:1.0
```

And run the pulled image:

<!-- test: output -->
```bash
docker run -d --name from-registry -p 8080:5000 localhost:5000/simple-app:1.0
```

```text
c118863029efeaceb70e038c8ae134826fafdd27ec9185dc8c6a83b3f340dc0c
```

<!-- test: retry=15; contains=Hello from simple-app -->
```bash
curl -s http://localhost:8080/
```

That is the whole publishing workflow. Docker Hub works the same way; only the name and the login change.

### 8.10 Docker Hub

You need a free Docker Hub account (<https://hub.docker.com>). These steps are not run by the tests, because they need
your account. Replace `your-username` with your Docker Hub username:

<!-- test: skip -->
```bash
export DOCKERHUB_USER=your-username
docker login -u "$DOCKERHUB_USER"
docker tag localhost:5000/simple-app:1.0 "$DOCKERHUB_USER/simple-app:1.0"
docker push "$DOCKERHUB_USER/simple-app:1.0"
```

`docker login` asks for your password (use an *access token* from the Docker Hub security settings instead of your
real password). After the push, anyone can run your image:

<!-- test: skip -->
```bash
docker run --rm -p 5000:5000 "$DOCKERHUB_USER/simple-app:1.0"
```

The images of this course's capstone are published the same way. You can run them without building anything:

<!-- test: skip -->
```bash
docker pull sufibaba6629/docker-from-zero-web:1.0.0
docker pull sufibaba6629/docker-from-zero-api:1.0.0
```

> **Never push secrets.** A public repository means anyone can pull your image and look through every layer.

Clean up:

```bash
docker rm -f registry from-registry
```

## Part 4 · Cleaning up safely

Images, stopped containers, volumes and build cache add up to many gigabytes. First, look before you delete:

<!-- test: output; contains=Images; contains=Build Cache -->
```bash
docker system df
```

```text
TYPE            TOTAL     ACTIVE    SIZE      RECLAIMABLE
Images          25        0         5.534GB   5.284GB (95%)
Containers      0         0         0B        0B
Local Volumes   1         0         51.92MB   51.92MB (100%)
Build Cache     60        0         2.54GB    2.057GB
```

`RECLAIMABLE` is what Docker could free because nothing uses it. Now the prune commands, from harmless to dangerous:

| Command | Removes | Risk |
|---|---|---|
| `docker container prune` | all **stopped** containers | low: running containers are kept |
| `docker image prune` | **dangling** images (no tag, e.g. old builds) | low |
| `docker image prune -a` | **every image not used by a container** | medium: everything must be pulled/built again |
| `docker network prune` | networks no container uses | low |
| `docker volume prune` | unused **anonymous** volumes | medium |
| `docker volume prune -a` | **every unused volume, including named ones** | **high: databases are deleted** |
| `docker system prune` | stopped containers, unused networks, dangling images, build cache | low to medium |
| `docker system prune -a --volumes` | all of the above, every unused image, every unused volume | **very high** |

The safe ones (each asks "Are you sure?"; `-f` answers yes, so read the table first):

<!-- test: output -->
```bash
docker container prune -f
docker image prune -f
docker network prune -f
```

```text
Total reclaimed space: 0B
Total reclaimed space: 0B
```

Filters make pruning precise. For example, only stopped containers older than one day:

```bash
docker container prune -f --filter "until=24h"
```

> **Warning:** `docker system prune -a --volumes` removes **every** image not used by a running container and **every**
> volume not used by a container, including databases from projects that are just stopped right now. Only run it when
> you have read the list it prints and you are sure nothing on this machine needs that data. I will not run it here.

<!-- test: skip -->
```bash
docker system prune -a --volumes
```

## Where would I use this as a DevOps engineer?

- **Security basics** are reviewed in every serious code review of a Dockerfile: non-root user, pinned base image,
  no secrets, minimal packages.
- **Small images** make deployments faster and security scans quieter.
- **Registries** are how images travel from a build to every server that runs them: Docker Hub, GitHub Container
  Registry, or a company's private registry.
- **Cleanup** keeps build servers and laptops from running out of disk, which is one of the most common Docker problems.

## What you learned

- Containers run as root unless the image sets `USER`; check with `whoami` / `id`.
- `--read-only`, `--cap-drop ALL` and publishing only needed ports reduce what an attacker could do.
- Environment variables are visible in `docker inspect`; pass secrets as files.
- Pin trusted base images and scan what is inside.
- Slim/alpine bases and multi-stage builds shrink images dramatically; `docker history` shows where the size comes from.
- `tag` names an image for a registry, `push` uploads it, `pull` downloads it.
- `docker system df` first, then prune with care. Never prune volumes without knowing what they hold.

## Try it yourself

1. Add `--cap-drop ALL` to the `docker run` of `simple-app:1.0`. Does the app still work?
2. Write a Dockerfile for `examples/nginx` that runs as non-root (hint: `nginxinc/nginx-unprivileged:1.30-alpine`,
   which listens on 8080).
3. Push `simple-app:multistage` to your local registry as version `1.1`, then list the tags with
   `curl -s http://localhost:5000/v2/simple-app/tags/list`.

## Next

Things will break. Now you learn to fix them methodically.
Continue with [Chapter 9 · Troubleshooting](09-troubleshooting.md).
