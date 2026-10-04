# Chapter 11 · Knowledge check

> **Where you are:** you have finished the course and the capstone.
> **In this chapter:** an honest check of what you can do now, and where to go next.
> **Time:** about 20 minutes.

Be strict with yourself. Tick a box only if you could do it **right now, without looking it up**, or explain it to a
friend. If a box stays empty, the link next to it takes you back to the right place.

## The checklist

```text
[ ] I understand what Docker is                       tutorial/00-start-here.md, docs/01-docker-introduction.md
[ ] I understand images                               docs/03-images.md
[ ] I understand containers                           docs/04-containers.md
[ ] I can run a container                             labs/01-first-container
[ ] I can inspect a container                         labs/14-logs-inspect-resources, docs/17-docker-inspect.md
[ ] I can read logs                                   tutorial/07-operate.md
[ ] I can execute commands inside containers          labs/02-docker-cli
[ ] I understand port mapping                         labs/04-port-mapping
[ ] I can write a Dockerfile                          labs/06-first-dockerfile
[ ] I can build an image                              labs/06-first-dockerfile
[ ] I understand image layers                         labs/07-layers-and-cache
[ ] I understand build cache                          labs/07-layers-and-cache
[ ] I understand .dockerignore                        labs/08-dockerignore
[ ] I understand volumes                              labs/09-volumes
[ ] I understand bind mounts                          labs/10-bind-mounts
[ ] I understand networking                           labs/11-networking
[ ] I can connect containers                          labs/12-multi-container
[ ] I can use Docker Compose                          labs/13-docker-compose
[ ] I can troubleshoot containers                     tutorial/09-troubleshooting.md, troubleshooting/
[ ] I understand basic Docker security                labs/15-security
[ ] I can optimize an image                           labs/16-image-optimization
[ ] I can build a multi-container application         capstone/, tutorial/10-capstone.md
```

## Self-test: 15 questions

Answer each question out loud or on paper first. Then open the answer.

**1. What is the difference between an image and a container?**

<details><summary>Answer</summary>

An image is a read-only template: files plus instructions for what to run. A container is a running (or stopped)
instance of an image, with its own writable layer, process, network and name. One image can start many containers,
just like one program file can start many processes.

</details>

**2. You run `docker run -d nginx:1.30-alpine`, then `docker ps` shows nothing. Where do you look next?**

<details><summary>Answer</summary>

nginx normally keeps running, so first check whether it exited: `docker ps -a` shows the status and the exit code.
Then `docker logs <container>` shows what the main process said before it stopped. Exit code + logs explain almost
every "container stopped" case.

</details>

**3. Why does `docker run ubuntu:26.04` exit immediately, while `docker run -d nginx:1.30-alpine` keeps running?**

<details><summary>Answer</summary>

A container lives as long as its main process. Ubuntu's default command is `bash`; without an interactive terminal
(`-it`) bash has no input, so it ends at once and the container stops. nginx is a server that runs until it is stopped.

</details>

**4. What does `-p 8080:80` mean, and which side is which?**

<details><summary>Answer</summary>

`HOST:CONTAINER`. Connections to port 8080 on your computer are forwarded to port 80 inside the container. The left
side must be free on your computer; the right side must be the port the application really listens on.

</details>

**5. A container is running and the port is published, but `curl` from your computer fails. Name two possible root causes and how you would tell them apart.**

<details><summary>Answer</summary>

(a) The mapping points at the wrong container port (e.g. `-p 8080:8080` while nginx listens on 80): check
`docker port <container>` against the port in the app's logs/config. (b) The app listens on `127.0.0.1` inside the
container, so it only accepts connections from inside the container: the logs show the listen address, and a request
via `docker exec` from inside works while the request from outside fails.

</details>

**6. Why do we copy `requirements.txt` and run `pip install` before copying the rest of the code?**

<details><summary>Answer</summary>

Each instruction creates a layer, and Docker reuses (caches) a layer as long as the instruction and its input files
did not change. Code changes often, dependencies rarely. With dependencies first, a code change only rebuilds the
last, fast layer instead of reinstalling every package.

</details>

**7. What does `.dockerignore` protect you from? Give two examples.**

<details><summary>Answer</summary>

It keeps files out of the build context, the files sent to Docker for the build. That prevents (a) slow builds and big
images from junk like `.git`, logs or large data folders, and (b) secrets like `.env` from being copied into an image by
`COPY . .`, where anyone with the image could read them.

</details>

**8. What is the difference between a named volume and a bind mount? When would you use each?**

<details><summary>Answer</summary>

A named volume is storage managed by Docker (`docker volume ls`), ideal for application data such as databases. A
bind mount maps a folder of your computer into the container; ideal for local development, where you edit files on
your computer and the container sees the changes immediately.

</details>

**9. You remove a database container and start a new one. The data is gone. What was most likely missing?**

<details><summary>Answer</summary>

A named volume mounted at the database's data directory. Without it, the data lived in the container's writable layer
(or in an anonymous volume that the new container does not reuse) and was thrown away with the container. With
PostgreSQL 18 images the volume belongs at `/var/lib/postgresql`.

</details>

**10. Two containers are on the default `bridge` network. Why can't one reach the other by name, and how do you fix it?**

<details><summary>Answer</summary>

Docker's built-in DNS (container names as hostnames) only works on user-defined networks. Create one with
`docker network create mynet` and start (or `docker network connect`) both containers on it. Compose does this for you
automatically.

</details>

**11. What does `docker compose down` remove, and what does `docker compose down -v` remove in addition?**

<details><summary>Answer</summary>

`down` removes the project's containers and networks; named volumes (your data) stay. `down -v` also removes the
project's volumes, which deletes the data.

</details>

**12. A container stopped with exit code 137 and `docker logs` is empty. What do you check?**

<details><summary>Answer</summary>

137 = killed with signal 9. Check `docker inspect <container> --format '{{.State.OOMKilled}}'`. If it says `true`, the
container exceeded its memory limit (`--memory`) and the kernel killed it. Give it more memory or make it use less.

</details>

**13. Why should an image set `USER`, and how do you check which user a container runs as?**

<details><summary>Answer</summary>

Without `USER`, the process runs as root. If an attacker takes over the process, root makes everything worse. A normal
user limits the damage (least privilege). Check with `docker exec <container> id` or `docker run --rm <image> id`, or
`docker inspect --format '{{.Config.User}}'`.

</details>

**14. Why is passing a password with `-e DB_PASSWORD=...` considered weak, and what is better?**

<details><summary>Answer</summary>

Environment variables are visible to anyone who can run `docker inspect`, and they often end up in logs and debug
output. Better: pass the secret as a file mounted into the container (Compose `secrets:` → `/run/secrets/...`, read via
`*_FILE` variables), and never bake secrets into images.

</details>

**15. Name three ways to make an image smaller, and the command that shows where the size comes from.**

<details><summary>Answer</summary>

Use a slim or alpine base image; use a multi-stage build so build tools stay in the builder stage; don't install
unnecessary packages and clean caches (`--no-cache-dir`, no `vim`/`curl` "just in case"); use `.dockerignore`.
`docker history <image>` shows the size of every layer.

</details>

## Can you do it without the guide?

A last practical test. Without opening any lesson, in an empty folder:

1. Write a Dockerfile for a tiny web page served by nginx, running as a non-root user.
2. Build it with a version tag and run it on port 8090.
3. Write a `docker-compose.yml` that runs your page together with `postgres:18-alpine` on a named volume.
4. Make the page container unable to reach the database (separate networks), and prove it with a command.
5. Stop everything without losing the database volume, then remove everything including the volume.

If you can do all five, you can honestly say:

> **"I understand Docker because I actually used it, broke it, fixed it, and built something with it."**

## Where to go next

You now have a solid Docker foundation. The natural next topics build directly on it; none of them are needed for
this course:

- **CI/CD:** let a pipeline build, scan and push your images automatically on every commit.
- **Kubernetes:** run containers across many machines, with the same ideas you know (images, ports, configuration,
  volumes, health checks) at a larger scale.
- **Observability:** collect the logs and metrics you read by hand here from many containers at once.

Until then: keep this repository, come back to the [troubleshooting scenarios](../troubleshooting/) once in a while,
and try to solve them faster each time.

[Back to the start](00-start-here.md)
