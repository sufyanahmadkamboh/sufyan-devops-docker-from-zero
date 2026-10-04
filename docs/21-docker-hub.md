# Docker Hub and Registries

## What is it?

A **registry** is a server that stores images so other computers can download them. **Docker Hub**
(<https://hub.docker.com>) is the default public registry: when you run `docker pull nginx:1.30-alpine`, Docker
downloads it from Docker Hub.

Vocabulary:

| Word | Meaning | Example |
|---|---|---|
| registry | the server | `docker.io` (Docker Hub), `localhost:5000` |
| repository | one image name, with all its versions | `sufibaba6629/docker-from-zero-web` |
| namespace | the account or organisation that owns repositories | `sufibaba6629`, `library` (official images) |
| tag | a human label for one version | `1.0.0`, `1.30-alpine` |
| digest | the content hash of an image, never changes | `sha256:0985e772...` |
| public / private | anyone can pull / only allowed accounts can pull | |

A full image name is `REGISTRY/NAMESPACE/REPOSITORY:TAG`. Docker fills in the defaults: `nginx:1.30-alpine` really
means `docker.io/library/nginx:1.30-alpine`.

## Why do we need it?

An image on your laptop is useless to a server or a teammate. Pushing it to a registry turns it into a **shareable,
versioned artifact**: build once, then pull and run the exact same image everywhere.

## How does it work?

```text
  your computer                         registry                       any other computer
 ┌────────────────────┐   docker push  ┌──────────────────────┐  docker pull  ┌────────────────────┐
 │ docker build       │ ─────────────► │ namespace/repo       │ ────────────► │ docker run         │
 │ docker tag         │   (layers it   │   :1.0.0  sha256:... │  (only layers │ the same image,    │
 │   NAME:1.0 ->      │    does not    │   :1.1.0  sha256:... │   it does not │ byte for byte      │
 │   user/NAME:1.0    │    have yet)   └──────────────────────┘   have yet)   └────────────────────┘
 └────────────────────┘
   build  →  tag  →  push  →  registry  →  pull  →  run
```

- `docker tag SOURCE TARGET` only adds a **second name** to the same image (same image ID). The target name decides
  where `docker push` sends it.
- Push and pull transfer **layers**; layers the other side already has are skipped.
- A tag can be moved to a new image later; a **digest** cannot. Pin by digest when you need to be 100 % sure.
- Docker Hub limits how many images **anonymous** users can pull in a period of time; logged-in (free) accounts get a
  higher limit. If you see a "rate limit" error, log in or wait.
- `docker login` should use an **access token** (Docker Hub → Account settings → Personal access tokens), not your
  account password. A token can be limited (read-only, read/write) and revoked at any time.

## Prerequisites

- [09-dockerfile.md](09-dockerfile.md), [03-images.md](03-images.md)

## Hands-on Lab

Full lab: [labs/17-docker-hub](../labs/17-docker-hub/README.md). You can practise the whole workflow **without an
account** by running your own registry locally (it is just another container):

```bash
docker run -d --name registry -p 5000:5000 registry:3
docker pull alpine:3.24
docker tag alpine:3.24 localhost:5000/my-alpine:1.0
```

<!-- test: retry=15; contains=1.0 -->
```bash
docker push localhost:5000/my-alpine:1.0
```

<!-- test: contains=my-alpine -->
```bash
curl -s http://localhost:5000/v2/_catalog
```

Now delete the local copy and pull it back from **your** registry:

```bash
docker rmi localhost:5000/my-alpine:1.0
```

<!-- test: contains=localhost:5000/my-alpine:1.0 -->
```bash
docker pull localhost:5000/my-alpine:1.0
```

<!-- test: contains=pulled from my own registry -->
```bash
docker run --rm localhost:5000/my-alpine:1.0 echo "pulled from my own registry"
```

> **macOS:** if port 5000 is taken (AirPlay Receiver uses it), use `-p 5001:5000` and `localhost:5001/...` instead.

## Expected Result

- `push` prints the layers it uploads and a line with the tag and a `digest: sha256:...`.
- The catalog answers `{"repositories":["my-alpine"]}`.
- `pull` downloads the image from `localhost:5000` and `run` works with it.

## Experiment

Tags are just names. Both names below point to the **same image ID**:

<!-- test: contains=my-alpine -->
```bash
docker images --format '{{.Repository}}:{{.Tag}} {{.ID}}' | grep alpine
```

## Break It

Push a name whose registry part points to nothing:

```bash
docker tag alpine:3.24 localhost:5999/my-alpine:1.0
```

<!-- test: fail; timeout=180; contains=dial tcp -->
```bash
docker push localhost:5999/my-alpine:1.0
```

The push retries for a while and then gives up with `dial tcp ...: connect: connection refused` on Linux, or
`dial tcp ...: i/o timeout` on Docker Desktop. Both mean the same thing: nothing answered at that address.

## Troubleshoot It

The name **is** the destination. `localhost:5999` means "a registry on this computer, port 5999", and nothing is
listening there. Check which registries actually run:

<!-- test: contains=5000 -->
```bash
docker ps --filter name=registry --format '{{.Names}} {{.Ports}}'
```

Fix: tag for the registry that exists (or start one on 5999), then verify:

```bash
docker rmi localhost:5999/my-alpine:1.0
docker tag alpine:3.24 localhost:5000/my-alpine:1.1
```

<!-- test: contains=1.1 -->
```bash
docker push localhost:5000/my-alpine:1.1
```

On Docker Hub, the same mistake looks like `denied: requested access to the resource is denied`: you tried to push to
a namespace that is not yours (or you are not logged in).

```bash
docker rm -f registry
docker rmi localhost:5000/my-alpine:1.0 localhost:5000/my-alpine:1.1
```

## Docker Hub for real

These steps need your own free Docker Hub account, so the automatic tests skip them. Replace `<your-username>` with
your Docker Hub **username** (not your e-mail address).

<!-- test: skip -->
```bash
docker login -u <your-username>
cd examples/simple-app
docker build -t simple-app:1.0 .
docker tag simple-app:1.0 <your-username>/simple-app:1.0
docker push <your-username>/simple-app:1.0
```

`docker login` asks for a password: paste an **access token**. Then, on any computer:

<!-- test: skip -->
```bash
docker pull <your-username>/simple-app:1.0
docker run -d -p 5000:5000 <your-username>/simple-app:1.0
docker logout
```

The author's images for this course are public, so you can pull them without an account:

<!-- test: skip -->
```bash
docker pull sufibaba6629/docker-from-zero-web:1.0.0
docker pull sufibaba6629/docker-from-zero-api:1.0.0
```

## Common Mistakes

- Pushing without tagging first (`docker push simple-app:1.0` tries `docker.io/library/simple-app`, which is not yours).
- Using the e-mail address instead of the username in the image name.
- Logging in with the account password instead of an access token, and storing it on shared machines.
- Pushing only `latest`: nobody knows which version is running. Use version tags.
- Accidentally pushing an image that contains secrets (`.dockerignore` and [19-security-basics.md](19-security-basics.md)).

## Best Practices

- Tag with a version (`1.0.0`) and, if you like, also a moving tag (`1.0`).
- Log in with access tokens; `docker logout` on machines you do not own.
- Public repositories for learning material only; private for company images.
- Pull official images by version; for critical deployments, pin by digest.

## Challenge

**Task:** using the local registry, publish `nginx:1.30-alpine` as `localhost:5000/team/web:2.0` and prove (with
`docker images`) that it has the same image ID as `nginx:1.30-alpine`.

## Solution

<details><summary>Solution</summary>

```bash
docker run -d --name registry -p 5000:5000 registry:3
docker pull nginx:1.30-alpine
docker tag nginx:1.30-alpine localhost:5000/team/web:2.0
```

<!-- test: retry=15; contains=2.0 -->
```bash
docker push localhost:5000/team/web:2.0
```

<!-- test: contains=team/web -->
```bash
docker images --format '{{.Repository}}:{{.Tag}} {{.ID}}' | grep -E 'nginx|team/web'
```

```bash
docker rm -f registry
docker rmi localhost:5000/team/web:2.0
```

Namespaces (`team/`) work the same in your own registry as on Docker Hub.
</details>

## Verification

- [ ] I can explain registry, repository, namespace, tag and digest.
- [ ] I can tag, push, pull and run an image from a registry.
- [ ] I know to log in with an access token, not my password.

## Real-World Usage

Every deployment pipeline ends with "push the image to a registry" and every server starts with "pull the image".
Companies use Docker Hub, GitHub Container Registry, or a registry from their cloud provider; the commands are the
same.

## Key Takeaways

- The image name decides where it is pushed: `REGISTRY/NAMESPACE/REPO:TAG`.
- `docker tag` adds a name; `push` uploads, `pull` downloads only missing layers.
- Tags are labels, digests are fingerprints.
- Use access tokens and version tags.

Next: [22-troubleshooting.md](22-troubleshooting.md)
