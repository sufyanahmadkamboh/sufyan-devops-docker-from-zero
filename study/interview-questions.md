# Interview questions

Questions you can expect in a junior DevOps or developer interview about Docker. Answer out loud first, then open the
answer. Every answer points to the place in this lab where you saw it happen.

## Basics

**1. What is the difference between an image and a container?**
<details><summary>Answer</summary>

An image is a read-only template: a filesystem plus settings (command, environment, ports). A container is a running or
stopped instance created from an image, with its own writable layer on top. One image can run as many containers.
Like a class and its objects, or a recipe and the meals cooked from it. ([labs/01](../labs/01-first-container/README.md))
</details>

**2. How is a container different from a virtual machine?**
<details><summary>Answer</summary>

A virtual machine runs a whole operating system with its own kernel on emulated hardware. A container is an isolated
process that shares the host's kernel, so it starts in milliseconds and uses far less memory. The trade-off: weaker
isolation than a VM, and Linux containers need a Linux kernel (Docker Desktop provides one in a small VM).
([docs/01](../docs/01-docker-introduction.md))
</details>

**3. Why does a container stop by itself?**
<details><summary>Answer</summary>

A container lives exactly as long as its main process (PID 1). When that process finishes or crashes, the container
stops. `docker run ubuntu:26.04` stops immediately because bash has no terminal and exits. Check `docker ps -a` for the
exit code and `docker logs` for the reason. ([labs/03](../labs/03-container-lifecycle/README.md),
[troubleshooting/01](../troubleshooting/01-container-exits-immediately/README.md))
</details>

**4. What do exit codes 0, 1 and 137 tell you?**
<details><summary>Answer</summary>

0: the process finished normally. 1 (or 2, 3, ...): the application reported an error, read the logs. 137 = 128 + 9: the
process was killed with SIGKILL, typically by `docker kill` or by the kernel because the container exceeded its memory
limit (`docker inspect` then shows `OOMKilled: true`). ([labs/14](../labs/14-logs-inspect-resources/README.md))
</details>

**5. What does `-p 8080:80` mean, and what does `EXPOSE` do?**
<details><summary>Answer</summary>

`-p 8080:80` publishes the container's port 80 on port 8080 of the host: host first, container second. `EXPOSE` in a
Dockerfile only documents which port the application uses; it publishes nothing. ([labs/04](../labs/04-port-mapping/README.md))
</details>

**6. A container is running and the port is published, but the browser gets no answer. What do you check?**
<details><summary>Answer</summary>

`docker ps` (is the mapping right, host:container?), `docker logs` (on which address and port did the app start?),
`docker exec` to test from inside the container. A common cause: the app listens on 127.0.0.1 inside the container,
which only accepts connections from inside; it must listen on 0.0.0.0. Another: the mapping points to a container port
nothing listens on. ([troubleshooting/07](../troubleshooting/07-running-but-not-reachable/README.md))
</details>

## Images and Dockerfiles

**7. What is the difference between `CMD` and `ENTRYPOINT`?**
<details><summary>Answer</summary>

`ENTRYPOINT` is the fixed program; `CMD` is the default command or the default arguments to the entrypoint. Anything you
type after the image name in `docker run` replaces `CMD`, not `ENTRYPOINT`. ([labs/06](../labs/06-first-dockerfile/README.md))
</details>

**8. What are layers, and why does the order of Dockerfile instructions matter?**
<details><summary>Answer</summary>

Instructions that change files (`RUN`, `COPY`, `ADD`) each create a layer. Docker caches layers and reuses them while
nothing they depend on has changed; once one layer changes, all layers after it are rebuilt. So copy the dependency list
and install dependencies first, and copy the frequently changing source code last. ([labs/07](../labs/07-layers-and-cache/README.md))
</details>

**9. What is the build context, and what is `.dockerignore` for?**
<details><summary>Answer</summary>

The build context is the folder given to `docker build`; it is sent to the builder and `COPY` can only use files from
it. `.dockerignore` excludes files from it: faster builds, smaller images, and no `.env` files, keys or `.git` folders
accidentally copied into an image. ([labs/08](../labs/08-dockerignore/README.md))
</details>

**10. How do you make an image smaller?**
<details><summary>Answer</summary>

A slim or alpine base image, a multi-stage build that leaves compilers and build tools behind, no package-manager
caches (`--no-cache-dir`, `--no-cache`), only the packages you need, a `.dockerignore`, and combining related commands
in one `RUN`. Measure with `docker images` and `docker history`. ([labs/16](../labs/16-image-optimization/README.md))
</details>

**11. Why should you not use the `latest` tag in production?**
<details><summary>Answer</summary>

`latest` is just a tag name that moves whenever a new version is pushed. The same command can give different images on
different days, so builds are not repeatable and rollbacks are unclear. Pin a version (`nginx:1.30-alpine`), or a digest
for full certainty. ([docs/03](../docs/03-images.md))
</details>

**12. What is a multi-stage build?**
<details><summary>Answer</summary>

A Dockerfile with several `FROM` stages. Early stages build or install things with all the tools they need; the final
stage starts from a small base and copies only the results (`COPY --from=builder ...`). The tools never reach the final
image. ([labs/16](../labs/16-image-optimization/README.md))
</details>

## Data and networking

**13. What is the difference between a volume and a bind mount?**
<details><summary>Answer</summary>

A volume is storage managed by Docker (`docker volume ls`); it is the right place for database data. A bind mount shows
a specific folder of the host inside the container; it is ideal for development (edit on the host, see it live) and for
config files. Both survive the container. ([labs/09](../labs/09-volumes/README.md), [labs/10](../labs/10-bind-mounts/README.md))
</details>

**14. You deleted a database container and recreated it. The data is gone. Why could that be?**
<details><summary>Answer</summary>

The data was in the container's own writable layer or in an anonymous volume, not in a named volume; or the new
container mounts a different volume name (a typo, or a different Compose project name); or the volume is mounted at
the wrong path (PostgreSQL 18 expects `/var/lib/postgresql`); or someone ran `docker compose down -v`.
([troubleshooting/04](../troubleshooting/04-volume-data-missing/README.md), [troubleshooting/10](../troubleshooting/10-database-data-disappears/README.md))
</details>

**15. How do containers find each other?**
<details><summary>Answer</summary>

On a user-defined network (and every Compose project has one), Docker's built-in DNS resolves container names and
Compose service names to the container's IP address. The default `bridge` network has no name resolution.
([labs/11](../labs/11-networking/README.md))
</details>

**16. Why not connect to other containers by IP address?**
<details><summary>Answer</summary>

Container IPs change when containers are recreated. Names stay the same, and Docker's DNS always returns the current
address. ([labs/11](../labs/11-networking/README.md))
</details>

**17. How would you stop a web container from reaching the database directly?**
<details><summary>Answer</summary>

Put them on different networks: web and API on a frontend network, API and database on a backend network. The web
container cannot even resolve the database's name. That is exactly what the capstone does. ([capstone](../capstone/README.md))
</details>

## Compose and operations

**18. What does `docker compose up -d` create, and what does `docker compose down` remove?**
<details><summary>Answer</summary>

`up` creates a network for the project, the named volumes, and one container per service (building images if needed).
`down` removes the containers and networks but keeps named volumes; `down -v` also deletes the volumes and their data.
([labs/13](../labs/13-docker-compose/README.md))
</details>

**19. `depends_on` is set, but the API still fails because the database is not ready. Why, and what is the fix?**
<details><summary>Answer</summary>

Plain `depends_on` only waits until the database container has started, not until PostgreSQL accepts connections. Give
the database a `healthcheck` and use `depends_on: db: condition: service_healthy`, as the capstone does.
([capstone](../capstone/README.md))
</details>

**20. How do you debug a container that keeps restarting?**
<details><summary>Answer</summary>

`docker ps -a` for the status and exit code, `docker logs` (with `--tail`) for the error message, `docker inspect` for
the configuration (environment, mounts, command, `OOMKilled`), and if it stays up long enough, `docker exec` to look
inside. Read the evidence before changing anything. ([troubleshooting/](../troubleshooting/README.md))
</details>

**21. How do you limit a container's memory and CPU, and how do you see its usage?**
<details><summary>Answer</summary>

`docker run --memory=256m --cpus=0.5 ...` (in Compose: `deploy.resources.limits`). `docker stats` shows live CPU,
memory, network and disk I/O; `docker top` shows the processes. ([labs/14](../labs/14-logs-inspect-resources/README.md))
</details>

## Security

**22. Why run containers as a non-root user?**
<details><summary>Answer</summary>

If the application is compromised, the attacker gets the rights of its user. As root inside the container they can
change any file in it, and a container escape bug becomes much more dangerous. Add a user in the Dockerfile and
switch to it with `USER`. ([labs/15](../labs/15-security/README.md))
</details>

**23. Why are environment variables not ideal for passwords?**
<details><summary>Answer</summary>

They are visible to anyone who can run `docker inspect`, they appear in process listings and crash reports, and they
are inherited by child processes. Pass secrets as files (Compose `secrets:`, `*_FILE` variables) or use a secrets
manager. ([labs/15](../labs/15-security/README.md))
</details>

**24. Name five basic ways to make a container more secure.**
<details><summary>Answer</summary>

Official or trusted, version-pinned base images; a minimal image; a non-root `USER`; `--read-only` with a `tmpfs` for
temporary files; `--cap-drop ALL`; secrets as files; only the ports you need published; resource limits; scanning
images for known vulnerabilities. ([docs/19](../docs/19-security-basics.md))
</details>

**25. A colleague wants to free disk space with `docker system prune -a --volumes`. What do you tell them?**
<details><summary>Answer</summary>

That it deletes every stopped container, every unused network, every image not used by a container (so everything has
to be downloaded or rebuilt again), the build cache, and every volume not used by a container, including database data
of stopped projects. Check `docker system df` first, and prefer targeted commands with filters.
([labs/18](../labs/18-cleanup/README.md))
</details>
