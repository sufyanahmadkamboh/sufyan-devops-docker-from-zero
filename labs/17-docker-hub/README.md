# Lab 17 · Docker Hub and registries

> Goal: share an image: tag it, push it to a registry, delete it locally, pull it back and run it. First with a
> practice registry on your own computer, then with Docker Hub. · Time: 40 minutes · You need: labs 06 and 07.

So far every image lived only on your computer. To run it on a server, or to give it to a colleague, you put it in a
**registry**: a server that stores images. Docker Hub is the default public registry (every `docker pull nginx` comes
from there). Companies also run private registries.

```text
 your computer                    registry                     another computer
 docker build  ->  docker tag  ->  docker push  ->  [ image ]  ->  docker pull  ->  docker run
```

## What you will learn

- Registry, repository, tag: what each word means, and how image names are built
- `docker tag`, `docker push`, `docker pull`
- How to practise safely with a registry running in a container
- How to publish to Docker Hub with a free account, and log out again

## Image names, decoded

```text
docker.io / library / nginx : 1.30-alpine
   |           |        |         |
registry   namespace  repository  tag
```

- **Registry**: the server. Leave it out and Docker uses Docker Hub (`docker.io`).
- **Namespace**: the account or organisation. Official images use `library`, which is also left out.
- **Repository**: one application, many versions.
- **Tag**: one version. Leave it out and Docker uses `latest` (which is just a name, not "the newest").

So `nginx:1.30-alpine` really means `docker.io/library/nginx:1.30-alpine`, and `localhost:5000/simple-app:1.0` means
"repository `simple-app`, tag `1.0`, on the registry at `localhost:5000`".

## Part A · A practice registry on your computer

### Step 1 · Build the image we want to share

From the repository root:

<!-- test: timeout=600 -->
```bash
cd examples/simple-app
docker build -t simple-app:1.0 .
```

### Step 2 · Start a registry

The registry software itself is an image, `registry:3`. It listens on port 5000.

```bash
docker run -d --name registry -p 5000:5000 registry:3
```

> macOS: port 5000 is used by the AirPlay Receiver. Use `-p 5050:5000` and replace `localhost:5000` with
> `localhost:5050` in every command of this lab (or turn off AirPlay Receiver in System Settings).

The registry has a small HTTP API. Ask it which repositories it stores:

<!-- test: retry=15; output; contains=repositories -->
```bash
curl -s http://localhost:5000/v2/_catalog
```

```text
{"repositories":[]}
```

An empty list: nothing pushed yet.

### Step 3 · Tag the image for this registry

`docker push` sends an image to the registry that is written in its **name**. So we give our image a second name that
starts with `localhost:5000/`:

```bash
docker tag simple-app:1.0 localhost:5000/simple-app:1.0
```

<!-- test: output=head:10; contains=localhost:5000/simple-app -->
```bash
docker images
```

```text
IMAGE                            ID             DISK USAGE   CONTENT SIZE   EXTRA
alpine:3.24                      294b683cb724         13MB         3.94MB        
board-api:1.0                    351aa764af08        243MB         58.5MB        
board-api:latest                 6e0b9b3fce93        243MB         58.5MB        
board-web:1.0                    89ee006648dd       92.8MB         26.1MB        
board-web:latest                 ab2522c6f2d8       92.8MB         26.1MB        
busybox:1.37                     bdf57e528e45       6.77MB         2.22MB        
docker-from-zero/api:1.0.0       07a9a8fe1d97        247MB         58.8MB        
docker-from-zero/web:1.0.0       c41020e7b136       81.5MB         23.1MB        
greeter:latest                   15597981addb       12.9MB         3.85MB        
...
```

Both names show the **same IMAGE ID**. `docker tag` copies nothing: it adds a second label to the same image.

### Step 4 · Push

<!-- test: output=tail:4 -->
```bash
docker push localhost:5000/simple-app:1.0
```

```text
...
e42bb4d14bbe: Pushed
6b37362b3da7: Pushed
c5e6e50697ef: Pushed
1.0: digest: sha256:8e4b2f4b8a3767276532d3dc589d719cd7d3f21eaaf8088ab911a1b608b45a08 size: 856
```

Docker uploads the image layer by layer and ends with the **digest** (`sha256:...`), the unique fingerprint of exactly
this image content. Check the registry:

<!-- test: output; contains=simple-app -->
```bash
curl -s http://localhost:5000/v2/_catalog
curl -s http://localhost:5000/v2/simple-app/tags/list
```

```text
{"repositories":["simple-app"]}
{"name":"simple-app","tags":["1.0"]}
```

> Docker only allows plain HTTP registries on `localhost`. A registry on another machine must use HTTPS, or be listed
> as an "insecure registry" in Docker's settings (fine for a lab, never for real work).

### Step 5 · Delete it locally, pull it back

Remove both names from your computer. Now the only copy is in the registry:

```bash
docker rmi simple-app:1.0 localhost:5000/simple-app:1.0
```

<!-- test: output; contains=localhost:5000/simple-app:1.0 -->
```bash
docker pull localhost:5000/simple-app:1.0
```

```text
1.0: Pulling from simple-app
Digest: sha256:8e4b2f4b8a3767276532d3dc589d719cd7d3f21eaaf8088ab911a1b608b45a08
Status: Downloaded newer image for localhost:5000/simple-app:1.0
localhost:5000/simple-app:1.0
```

### Step 6 · Run what you pulled

```bash
docker run -d --name from-registry -p 5001:5000 localhost:5000/simple-app:1.0
```

<!-- test: retry=15; output; contains=Hello from simple-app -->
```bash
curl -s http://localhost:5001/
```

```text
Hello from simple-app!
environment: production
container hostname: ff566b091a5f
```

That is the whole idea of a registry: **build once, run anywhere**. The machine that runs the image never needs your
source code or the Dockerfile.

## Part B · Docker Hub

Docker Hub is free for public images. The commands are exactly the same as in Part A, with your account name instead
of `localhost:5000`. These steps need an account and internet, so try them when you are ready.

### Step 1 · Create an account

Sign up at <https://hub.docker.com>. Your **username** becomes your namespace: `<your-username>/<repository>:<tag>`.
For logging in from the terminal, create a **personal access token** (Account settings → Personal access tokens) and
use it instead of your password: you can give it limited rights and delete it at any time.

### Step 2 · Log in

<!-- test: skip -->
```bash
docker login -u your-username
```

Docker asks for the password: paste the access token. You should see `Login Succeeded`. Docker stores the credential
in your system's credential store (or in `~/.docker/config.json`), not in your project.

### Step 3 · Tag and push

Put your username in a variable once, so you can copy the next commands as they are:

<!-- test: skip -->
```bash
export DOCKERHUB_USER=your-username
docker build -t simple-app:1.0 .
docker tag simple-app:1.0 "$DOCKERHUB_USER/simple-app:1.0"
docker push "$DOCKERHUB_USER/simple-app:1.0"
```

Open `https://hub.docker.com/r/<your-username>/simple-app`: your image is online, with its tag and size.

### Step 4 · Pull it somewhere else

On another computer (or after deleting your local copy):

<!-- test: skip -->
```bash
docker pull "$DOCKERHUB_USER/simple-app:1.0"
docker run -d --name from-hub -p 5003:5000 "$DOCKERHUB_USER/simple-app:1.0"
```

### Public or private?

- **Public** repositories can be pulled by anyone, without logging in. Never push an image that contains passwords,
  keys or company code to a public repository (lab 08 showed how secrets end up in images by accident).
- **Private** repositories need a login to pull. The free plan includes a limited number; check Docker's pricing page
  for the current limits. Docker Hub also limits how many pulls anonymous and free users can make per hour.

### Step 5 · The images of this course

The finished capstone images of this course are published on Docker Hub, for both Intel/AMD and ARM computers
(including Apple Silicon):

<!-- test: skip -->
```bash
docker pull sufibaba6629/docker-from-zero-web:1.0.0
docker pull sufibaba6629/docker-from-zero-api:1.0.0
docker images 'sufibaba6629/*'
```

### Step 6 · Log out

On shared or borrowed computers, always log out:

<!-- test: skip -->
```bash
docker logout
```

## Break it

You want version `2.0`, but nobody ever pushed a `2.0`. Don't fix it yet, we broke it on purpose.

<!-- test: fail; contains=not found -->
```bash
docker pull localhost:5000/simple-app:2.0
```

## Troubleshoot it

**Observe.** The pull fails with a "not found" / "manifest unknown" error. Before changing anything, let's
investigate.

**Investigate.** Is the registry reachable at all, and which tags does it really have?

<!-- test: output; contains=1.0 -->
```bash
curl -s http://localhost:5000/v2/_catalog
curl -s http://localhost:5000/v2/simple-app/tags/list
```

```text
{"repositories":["simple-app"]}
{"name":"simple-app","tags":["1.0"]}
```

The registry answers, the repository exists, but its only tag is `1.0`.

**Root cause.** The tag `2.0` was never pushed. A tag only exists in a registry after someone pushes it. (On Docker
Hub, a typo in the username or repository gives a similar error, often worded "pull access denied ... repository does
not exist or may require docker login".)

**Fix.** Either pull a tag that exists, or publish `2.0`:

<!-- test: contains=2.0 -->
```bash
docker tag localhost:5000/simple-app:1.0 localhost:5000/simple-app:2.0
docker push localhost:5000/simple-app:2.0
curl -s http://localhost:5000/v2/simple-app/tags/list
```

**Verify.**

<!-- test: contains=localhost:5000/simple-app:2.0 -->
```bash
docker pull localhost:5000/simple-app:2.0
```

## Challenge

**Task:** Publish a version `1.1` of simple-app with a different greeting to the practice registry, and run `1.0` and
`1.1` side by side.

**Requirements:**
- Version `1.1` says `Hello from version 1.1` on its home page.
- Both versions are in the registry's tag list.
- `1.0` answers on host port 5001 (already running), `1.1` on host port 5004.

**Hints:**
- You don't need to change `app.py`: the greeting comes from the `GREETING` environment variable, and a Dockerfile can
  set it with `ENV`.
- A Dockerfile can start `FROM` your own image.

<details><summary>Solution</summary>

<!-- test: timeout=300 -->
```bash
docker build -t localhost:5000/simple-app:1.1 -f - . <<'EOF'
FROM localhost:5000/simple-app:1.0
ENV GREETING="Hello from version 1.1"
EOF
docker push localhost:5000/simple-app:1.1
docker run -d --name v11 -p 5004:5000 localhost:5000/simple-app:1.1
```

<!-- test: retry=15; contains=Hello from version 1.1; contains=Hello from simple-app; contains=1.1 -->
```bash
curl -s http://localhost:5004/
curl -s http://localhost:5001/
curl -s http://localhost:5000/v2/simple-app/tags/list
```

Building `FROM` your own image reuses all its layers; the new version only adds one tiny layer for the `ENV`.

</details>

## Verify

- [ ] I can split an image name into registry, namespace, repository and tag
- [ ] I can tag, push and pull an image with a registry
- [ ] I proved that the pulled image runs without the source code
- [ ] I know how to log in to Docker Hub with an access token, and to log out
- [ ] I know the difference between public and private repositories

## Clean up

```bash
docker rm -f registry from-registry v11 2>/dev/null || true
docker rmi localhost:5000/simple-app:1.0 localhost:5000/simple-app:1.1 localhost:5000/simple-app:2.0 2>/dev/null || true
cd ../..
```

The registry stored its data in an anonymous volume; lab 18 shows how to find and remove leftovers like that.

## Next

- Concept lesson: [docs/21-docker-hub.md](../../docs/21-docker-hub.md)
- Next lab: [Lab 18 · Safe cleanup](../18-cleanup/README.md)
