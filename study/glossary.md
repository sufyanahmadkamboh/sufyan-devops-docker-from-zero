# Glossary

Every Docker word used in this lab, in plain language, with where you practise it.

| Term | Meaning | Practise it in |
|---|---|---|
| **Anonymous volume** | A volume with a random name, created when an image declares `VOLUME` and you do not mount anything there. Easy to lose track of. | [troubleshooting/10](../troubleshooting/10-database-data-disappears/README.md) |
| **Base image** | The image a Dockerfile starts `FROM`, e.g. `python:3.14-slim`. | [labs/06](../labs/06-first-dockerfile/README.md) |
| **Bind mount** | A folder or file from your computer shown inside a container. Changes are visible on both sides immediately. | [labs/10](../labs/10-bind-mounts/README.md) |
| **Bridge network** | The default kind of Docker network: a private network on one machine that containers join. | [labs/11](../labs/11-networking/README.md) |
| **Build cache** | Results of earlier build steps that Docker reuses when nothing they depend on has changed. Shown as `CACHED`. | [labs/07](../labs/07-layers-and-cache/README.md) |
| **Build context** | The folder you pass to `docker build` (often `.`). Everything in it is sent to the builder, minus `.dockerignore`. | [labs/08](../labs/08-dockerignore/README.md) |
| **BuildKit** | The engine that runs `docker build` in current Docker versions. Its output lines start with `#1`, `#2`, ... | [labs/06](../labs/06-first-dockerfile/README.md) |
| **Capability** | A piece of root's power in Linux (for example "change file owners"). `--cap-drop ALL` removes them all from a container. | [labs/15](../labs/15-security/README.md) |
| **cgroups** | The Linux feature Docker uses to limit memory and CPU (`--memory`, `--cpus`). | [labs/14](../labs/14-logs-inspect-resources/README.md) |
| **CMD** | Dockerfile instruction: the default command of the container. Replaced by anything you type after the image name. | [labs/06](../labs/06-first-dockerfile/README.md) |
| **Compose** | `docker compose`: describe several containers, networks and volumes in one YAML file and manage them together. | [labs/13](../labs/13-docker-compose/README.md) |
| **Compose project** | The group of resources Compose manages together. Its name prefixes containers, networks and volumes. | [labs/13](../labs/13-docker-compose/README.md) |
| **Container** | A running (or stopped) instance of an image: an isolated process with its own filesystem, network and settings. | [labs/01](../labs/01-first-container/README.md) |
| **Container ID** | The unique 64-character hex ID of a container; Docker usually shows the first 12. Also the default hostname. | [labs/02](../labs/02-docker-cli/README.md) |
| **Daemon (dockerd)** | The background service that does the real work. The `docker` command only sends it requests. | [docs/01](../docs/01-docker-introduction.md) |
| **Digest** | `sha256:...`: the content hash of an image. Unlike a tag, it can never point to different content. | [labs/17](../labs/17-docker-hub/README.md) |
| **Docker Desktop** | Docker for Windows and macOS: a small Linux virtual machine plus the Docker tools and a GUI. | [docs/02](../docs/02-docker-installation.md) |
| **Docker Engine** | Docker on Linux: the daemon, the CLI and the container runtime. | [docs/02](../docs/02-docker-installation.md) |
| **Docker Hub** | The default public registry. `nginx` really means `docker.io/library/nginx`. | [labs/17](../labs/17-docker-hub/README.md) |
| **Dockerfile** | A text file of instructions that builds an image, one layer per file-changing instruction. | [labs/06](../labs/06-first-dockerfile/README.md) |
| **.dockerignore** | A list of files and folders that are not sent to the build (keeps builds fast and secrets out). | [labs/08](../labs/08-dockerignore/README.md) |
| **ENTRYPOINT** | Dockerfile instruction: the fixed program of the container. `CMD` then supplies its default arguments. | [labs/06](../labs/06-first-dockerfile/README.md) |
| **Environment variable** | A `NAME=value` setting given to the process, e.g. `-e APP_ENV=production`. | [labs/05](../labs/05-environment-variables/README.md) |
| **exec** | `docker exec`: run an extra command inside a running container. | [labs/02](../labs/02-docker-cli/README.md) |
| **Exit code** | The number a process returns when it ends. 0 = success, 137 = killed (often out of memory), 1/2/3 = errors. | [labs/03](../labs/03-container-lifecycle/README.md) |
| **EXPOSE** | Dockerfile documentation of the port the app listens on. It does not publish anything; `-p` does. | [labs/04](../labs/04-port-mapping/README.md) |
| **Health check** | A command Docker runs regularly to ask "is the app working?". `docker ps` shows `(healthy)`. | [capstone](../capstone/README.md) |
| **Image** | A read-only template: a filesystem plus settings. Containers are created from images. | [labs/01](../labs/01-first-container/README.md) |
| **Image ID** | The unique ID of an image (a hash of its configuration). | [labs/01](../labs/01-first-container/README.md) |
| **inspect** | `docker inspect`: the full JSON description of a container, image, network or volume. | [labs/14](../labs/14-logs-inspect-resources/README.md) |
| **Layer** | One step of an image's filesystem. Layers are stacked, shared between images and cached. | [labs/07](../labs/07-layers-and-cache/README.md) |
| **Logs** | Everything the main process writes to stdout and stderr. Read with `docker logs`. | [labs/02](../labs/02-docker-cli/README.md) |
| **Main process (PID 1)** | The process started by `CMD`/`ENTRYPOINT`. When it ends, the container stops. | [labs/03](../labs/03-container-lifecycle/README.md) |
| **Multi-stage build** | A Dockerfile with several `FROM` stages; only what you `COPY --from` reaches the final image. | [labs/16](../labs/16-image-optimization/README.md) |
| **Named volume** | A volume you name (`db-data`); it survives until you delete it yourself. | [labs/09](../labs/09-volumes/README.md) |
| **Network isolation** | Containers on different networks cannot reach, or even resolve, each other. | [labs/11](../labs/11-networking/README.md) |
| **OOMKilled** | "Out of memory killed": the container hit its memory limit and the kernel killed it (exit code 137). | [labs/14](../labs/14-logs-inspect-resources/README.md) |
| **Port mapping (publishing)** | `-p 8080:80`: traffic to port 8080 on your computer goes to port 80 in the container. | [labs/04](../labs/04-port-mapping/README.md) |
| **Prune** | Delete unused objects (`docker container prune`, `image prune`, `volume prune`, `system prune`). Read the warning first. | [labs/18](../labs/18-cleanup/README.md) |
| **Pull / push** | Download an image from a registry / upload one to it. | [labs/17](../labs/17-docker-hub/README.md) |
| **Read-only filesystem** | `--read-only`: the container cannot change its own files; attackers cannot either. | [labs/15](../labs/15-security/README.md) |
| **Registry** | A server that stores images, e.g. Docker Hub, or `registry:3` running on your computer. | [labs/17](../labs/17-docker-hub/README.md) |
| **Repository** | A named collection of image versions in a registry, e.g. `sufibaba6629/docker-from-zero-web`. | [labs/17](../labs/17-docker-hub/README.md) |
| **Restart policy** | What Docker does when a container stops: `no`, `on-failure`, `always`, `unless-stopped`. | [capstone](../capstone/README.md) |
| **Secret** | Sensitive data (a password) given as a file instead of an environment variable, so `docker inspect` does not show it. | [labs/15](../labs/15-security/README.md) |
| **Service (Compose)** | One entry under `services:` in a Compose file; Compose runs one or more containers for it. | [labs/13](../labs/13-docker-compose/README.md) |
| **Tag** | A human-friendly version label after the colon: `nginx:1.30-alpine`. Without one, Docker uses `latest`. | [labs/01](../labs/01-first-container/README.md) |
| **tmpfs** | An in-memory folder inside a container; disappears when the container stops. | [labs/15](../labs/15-security/README.md) |
| **USER** | Dockerfile instruction: run the container's process as this user instead of root. | [labs/15](../labs/15-security/README.md) |
| **Volume** | Storage managed by Docker, outside the container's own filesystem, so data survives the container. | [labs/09](../labs/09-volumes/README.md) |
| **WORKDIR** | Dockerfile instruction: the folder later instructions (and the container) work in. | [labs/06](../labs/06-first-dockerfile/README.md) |
| **WSL2** | Windows Subsystem for Linux: a real Linux on Windows; the recommended terminal for these labs on Windows. | [docs/02](../docs/02-docker-installation.md) |
