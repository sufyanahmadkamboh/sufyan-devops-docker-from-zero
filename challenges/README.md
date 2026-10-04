# Challenges

> Practice without a step-by-step guide. One challenge per major topic, in the order of the labs.

How to use this page:

1. Read the **Task** and the **Requirements**. Try it yourself, in your own terminal.
2. Stuck for more than 10 minutes? Open the **Hints**, one at a time.
3. Compare your result with the **Expected Result**.
4. Only then open the **Solution**, and read the **Explanation** even if you solved it: there is often a detail you can learn.

All solutions run from the **repository root** (the folder you cloned) and clean up after themselves,
so you can do the challenges in any order. Windows: use WSL2, or Git Bash with `export MSYS_NO_PATHCONV=1`
(see [installation](../docs/02-docker-installation.md)).

| # | Challenge | After |
|---|---|---|
| 1 | [Run Nginx on port 8080](#challenge-1-run-nginx-on-port-8080) | lab 01 |
| 2 | [Copy a file out of a running container](#challenge-2-copy-a-file-out-of-a-running-container) | lab 02 |
| 3 | [Watch a container go through its whole life](#challenge-3-watch-a-container-go-through-its-whole-life) | lab 03 |
| 4 | [Two web servers at the same time](#challenge-4-two-web-servers-at-the-same-time) | lab 04 |
| 5 | [Configure a container from a file](#challenge-5-configure-a-container-from-a-file) | lab 05 |
| 6 | [Create a custom Docker image](#challenge-6-create-a-custom-docker-image) | lab 06 |
| 7 | [Prove the build cache works](#challenge-7-prove-the-build-cache-works) | lab 07 |
| 8 | [Keep a secret out of the image](#challenge-8-keep-a-secret-out-of-the-image) | lab 08 |
| 9 | [Persist database data](#challenge-9-persist-database-data) | lab 09 |
| 10 | [Edit a page live with a bind mount](#challenge-10-edit-a-page-live-with-a-bind-mount) | lab 10 |
| 11 | [Create a custom network](#challenge-11-create-a-custom-network) | lab 11 |
| 12 | [Create two communicating containers](#challenge-12-create-two-communicating-containers) | lab 12 |
| 13 | [Create the complete Compose application](#challenge-13-create-the-complete-compose-application) | lab 13 |
| 14 | [Investigate a container you did not start](#challenge-14-investigate-a-container-you-did-not-start) | lab 14 |
| 15 | [Put a container on a diet](#challenge-15-put-a-container-on-a-diet) | lab 14 |
| 16 | [Prove a container is locked down](#challenge-16-prove-a-container-is-locked-down) | lab 15 |
| 17 | [Make the image smaller](#challenge-17-make-the-image-smaller) | lab 16 |
| 18 | [Ship an image through a registry](#challenge-18-ship-an-image-through-a-registry) | lab 17 |
| 19 | [Find out why it stopped](#challenge-19-find-out-why-it-stopped) | troubleshooting |

---

## Challenge 1: Run Nginx on port 8080

**Task:** Run an nginx web server that you can open in your browser at `http://localhost:8080`.

**Requirements**
- Image `nginx:1.30-alpine`, container name `my-nginx`.
- It runs in the background (your terminal stays free).
- `curl -s http://localhost:8080` shows the nginx welcome page.
- At the end, stop and remove the container.

<details><summary>Hints</summary>

- Background: one flag on `docker run`. Name: another flag.
- Port mapping is `-p HOST:CONTAINER`. nginx listens on port 80 inside the container.
</details>

**Expected Result:** the page title is `Welcome to nginx!`, and `docker ps` shows `0.0.0.0:8080->80/tcp`.

<details><summary>Solution</summary>

```bash
docker run -d --name my-nginx -p 8080:80 nginx:1.30-alpine
```

<!-- test: retry=15; contains=Welcome to nginx -->
```bash
curl -s http://localhost:8080 | grep '<title>'
```

```bash
docker rm -f my-nginx
```

</details>

**Explanation:** `-d` detaches (runs in the background), `--name` gives a name you can type instead of an ID,
`-p 8080:80` connects port 8080 of your computer to port 80 of the container. `docker rm -f` stops and
removes in one step.

---

## Challenge 2: Copy a file out of a running container

**Task:** Find out which nginx version runs inside a container, and copy nginx's main configuration file
out of the container onto your computer to read it.

**Requirements**
- Container name `cli-test`, image `nginx:1.30-alpine`, no port needed.
- Print the nginx version **from inside** the running container.
- Copy `/etc/nginx/nginx.conf` to a file `nginx-copy.conf` in the current folder and show the line with `worker_processes`.
- Remove the container and the copied file at the end.

<details><summary>Hints</summary>

- Running a command in a running container: `docker exec`.
- `nginx -v` prints the version.
- Copying between a container and your computer: `docker cp <container>:<path> <local path>`.
</details>

**Expected Result:** `nginx version: nginx/1.30.x` and a line like `worker_processes  auto;`.

<details><summary>Solution</summary>

```bash
docker run -d --name cli-test nginx:1.30-alpine
```

<!-- test: retry=10; contains=nginx/1.30 -->
```bash
docker exec cli-test nginx -v
```

<!-- test: contains=worker_processes -->
```bash
docker cp cli-test:/etc/nginx/nginx.conf ./nginx-copy.conf
grep worker_processes nginx-copy.conf
```

```bash
rm nginx-copy.conf
docker rm -f cli-test
```

</details>

**Explanation:** `docker exec` runs an extra process in a container that is already running; it is the
everyday tool for looking inside. `docker cp` works in both directions and even on stopped containers.

---

## Challenge 3: Watch a container go through its whole life

**Task:** Create a container that will run for 5 seconds, and observe it in each state: created, running, exited.

**Requirements**
- Image `alpine:3.24`, name `short`, command `sleep 5`.
- Create it **without** starting it, then check its status.
- Start it, check its status while it runs.
- Wait until it ends and check its status and exit code.

<details><summary>Hints</summary>

- `docker create` makes a container without starting it. `docker start` starts it.
- `docker ps -a --filter name=short --format '{{.Status}}'` prints only the status.
</details>

**Expected Result:** `Created`, then `Up ...`, then `Exited (0) ...`.

<details><summary>Solution</summary>

<!-- test: contains=Created -->
```bash
docker create --name short alpine:3.24 sleep 5
docker ps -a --filter name=short --format '{{.Status}}'
```

<!-- test: contains=Up -->
```bash
docker start short
docker ps -a --filter name=short --format '{{.Status}}'
```

<!-- test: retry=20; contains=Exited (0) -->
```bash
sleep 7
docker ps -a --filter name=short --format '{{.Status}}'
```

```bash
docker rm short
```

</details>

**Explanation:** the container's life is the life of its main process (`sleep 5`). When `sleep` finishes,
the container is `Exited (0)`: 0 means "finished without error". The stopped container stays until you `docker rm` it.

---

## Challenge 4: Two web servers at the same time

**Task:** Run two nginx containers side by side, reachable on two different ports of your computer.

**Requirements**
- Names `site-a` and `site-b`, image `nginx:1.30-alpine`.
- `site-a` on `http://localhost:8081`, `site-b` on `http://localhost:8082`.
- Prove both answer, then remove both.

<details><summary>Hints</summary>

- Both containers listen on port 80 **inside**. Only the host ports must differ.
</details>

**Expected Result:** both URLs return the nginx welcome page; `docker ps` shows `8081->80` and `8082->80`.

<details><summary>Solution</summary>

```bash
docker run -d --name site-a -p 8081:80 nginx:1.30-alpine
docker run -d --name site-b -p 8082:80 nginx:1.30-alpine
```

<!-- test: retry=15; contains=Welcome to nginx -->
```bash
curl -s http://localhost:8081 | grep '<title>'
```

<!-- test: retry=15; contains=Welcome to nginx -->
```bash
curl -s http://localhost:8082 | grep '<title>'
```

```bash
docker rm -f site-a site-b
```

</details>

**Explanation:** every container has its own network space, so both can use port 80. A port on **your
computer** can only be used once, so each container gets its own host port.

---

## Challenge 5: Configure a container from a file

**Task:** Pass configuration to a container in two ways: one variable on the command line, others from a file.

**Requirements**
- Create a file `my.env` with `GREETING=Hallo` and `TEAM=platform`.
- Run `alpine:3.24` once, with the file **and** an extra `-e LEVEL=beginner`, and print the three variables.
- Delete `my.env` at the end.

<details><summary>Hints</summary>

- `--env-file my.env` loads `NAME=value` lines from a file.
- `docker run --rm alpine:3.24 sh -c 'echo $GREETING'`: single quotes, so that **the container's** shell expands the variable, not yours.
</details>

**Expected Result:** `Hallo platform beginner`.

<details><summary>Solution</summary>

<!-- test: contains=Hallo platform beginner -->
```bash
printf 'GREETING=Hallo\nTEAM=platform\n' > my.env
docker run --rm --env-file my.env -e LEVEL=beginner alpine:3.24 sh -c 'echo $GREETING $TEAM $LEVEL'
```

```bash
rm my.env
```

</details>

**Explanation:** the same image behaves differently depending on its environment. That is how one image
runs in development and in production: only the configuration changes, never the image.
Keep real passwords out of env files you commit; see lab 15.

---

## Challenge 6: Create a custom Docker image

**Task:** Build your own nginx image with the page from `examples/nginx/site` baked in, and run it.

**Requirements**
- Image name and tag `my-site:1.0`, built from `examples/nginx`.
- Run it as `my-site` on port 8080 and prove your page (not the nginx welcome page) is served.
- Remove the container and the image at the end.

<details><summary>Hints</summary>

- `examples/nginx/Dockerfile` already exists. Read it first.
- `docker build -t <name:tag> <folder>`: the folder is the build context.
</details>

**Expected Result:** the page contains `Hello from my container!`.

<details><summary>Solution</summary>

```bash
docker build -t my-site:1.0 examples/nginx
docker run -d --name my-site -p 8080:80 my-site:1.0
```

<!-- test: retry=15; contains=Hello from my container -->
```bash
curl -s http://localhost:8080
```

```bash
docker rm -f my-site
docker rmi my-site:1.0
```

</details>

**Explanation:** `FROM nginx:1.30-alpine` reuses the official image; `COPY site/ /usr/share/nginx/html/`
adds your files as a new layer on top. Your image is the official one plus one small layer.

---

## Challenge 7: Prove the build cache works

**Task:** Build `simple-app` twice and prove that the second build reused every step from the cache.

**Requirements**
- Build `examples/simple-app` as `simple-app:1.0`, then build it again unchanged.
- Show the cache lines of the second build.

<details><summary>Hints</summary>

- Look for the word `CACHED` in the build output.
- `--progress=plain` prints one line per step, easier to read.
</details>

**Expected Result:** in the second build, every step shows `CACHED`, and it finishes in about a second.

<details><summary>Solution</summary>

```bash
docker build -t simple-app:1.0 examples/simple-app
```

<!-- test: contains=CACHED -->
```bash
docker build --progress=plain -t simple-app:1.0 examples/simple-app 2>&1 | grep CACHED
```

</details>

**Explanation:** Docker caches each instruction's result as a layer. If the instruction and its input files
are unchanged, the layer is reused. Change `app.py` and only the `COPY app.py` step and the ones after it re-run,
because the Dockerfile installs dependencies **before** copying the code.

---

## Challenge 8: Keep a secret out of the image

**Task:** Prove that a `.env` file with a secret does not end up in an image built with `COPY . .`.

**Requirements**
- Create `examples/simple-app/.env` containing `SECRET=demo`.
- Build `examples/simple-app/dockerfile-steps/02.Dockerfile` (it uses `COPY . .`) as `ignore-check`.
- List the files in `/app` of the image: `.env` must not be there.
- Remove `.env` and the image at the end.

<details><summary>Hints</summary>

- `-f` selects a Dockerfile, the last argument is the build context: `docker build -f <dockerfile> -t <name> <context>`.
- Override the image's command to list files: `docker run --rm <image> ls -A /app`.
- Why is it not there? Read `examples/simple-app/.dockerignore`.
</details>

**Expected Result:** `app.py` and `requirements.txt` are listed, `.env` is not.

<details><summary>Solution</summary>

```bash
printf 'SECRET=demo\n' > examples/simple-app/.env
docker build -f examples/simple-app/dockerfile-steps/02.Dockerfile -t ignore-check examples/simple-app
```

<!-- test: contains=app.py; absent=.env -->
```bash
docker run --rm ignore-check ls -A /app
```

```bash
rm examples/simple-app/.env
docker rmi ignore-check
```

</details>

**Explanation:** `.dockerignore` lists `.env`, so the file is never sent to the build. Without that line,
`COPY . .` would put your secret in a layer, and anyone with the image could read it, even after a later
`RUN rm .env` (the earlier layer still contains it).

---

## Challenge 9: Persist database data

**Task:** Store a row in PostgreSQL, delete the database container, start a new one, and get the row back.

**Requirements**
- Named volume `pgdata`, image `postgres:18-alpine`, password `lab` (a local lab only).
- First container `pg1` creates a table `notes` and inserts the text `survived`.
- Remove `pg1` completely, start `pg2` on the same volume, and read the row.
- Remove the container and the volume at the end.

<details><summary>Hints</summary>

- PostgreSQL 18 stores its data under `/var/lib/postgresql`: mount the volume there.
- The database needs a few seconds before it accepts commands. Just repeat the `psql` command.
- `docker exec <name> psql -U postgres -c "<SQL>"` runs SQL inside the container.
</details>

**Expected Result:** `pg2` returns the row `survived`, although it is a brand-new container.

<details><summary>Solution</summary>

```bash
docker volume create pgdata
docker run -d --name pg1 -e POSTGRES_PASSWORD=lab -v pgdata:/var/lib/postgresql postgres:18-alpine
```

<!-- test: retry=30; contains=INSERT 0 1 -->
```bash
docker exec pg1 psql -U postgres -c "CREATE TABLE IF NOT EXISTS notes (text TEXT); INSERT INTO notes VALUES ('survived');"
```

```bash
docker rm -f pg1
docker run -d --name pg2 -e POSTGRES_PASSWORD=lab -v pgdata:/var/lib/postgresql postgres:18-alpine
```

<!-- test: retry=30; contains=survived -->
```bash
docker exec pg2 psql -U postgres -c "SELECT * FROM notes;"
```

```bash
docker rm -f pg2
docker volume rm pgdata
```

</details>

**Explanation:** the container is disposable, the volume is not. Removing a container never removes a
named volume; only `docker volume rm` (or `down -v` / `prune`) does.

---

## Challenge 10: Edit a page live with a bind mount

**Task:** Serve a folder from your computer with nginx, change the page, and see the change without rebuilding or restarting.

**Requirements**
- Create a folder `my-page` with an `index.html` that says `bind mount works`.
- Run `nginx:1.30-alpine` as `live` on port 8080, serving that folder (read-only for the container).
- Change the page to `changed without restart` and prove the server shows it.
- Remove the container and the folder at the end.

<details><summary>Hints</summary>

- `-v "$(pwd)/my-page:/usr/share/nginx/html:ro"` (PowerShell: `${PWD}`).
- nginx serves files from `/usr/share/nginx/html`.
</details>

**Expected Result:** the second `curl` shows `changed without restart`.

<details><summary>Solution</summary>

```bash
mkdir my-page
echo '<h1>bind mount works</h1>' > my-page/index.html
docker run -d --name live -p 8080:80 -v "$(pwd)/my-page:/usr/share/nginx/html:ro" nginx:1.30-alpine
```

<!-- test: retry=15; contains=bind mount works -->
```bash
curl -s http://localhost:8080
```

<!-- test: retry=5; contains=changed without restart -->
```bash
echo '<h1>changed without restart</h1>' > my-page/index.html
curl -s http://localhost:8080
```

```bash
docker rm -f live
rm -rf my-page
```

</details>

**Explanation:** a bind mount shows a host folder inside the container: both see the same files. Perfect
while developing. For production you bake files into the image instead (challenge 6), so the image is
complete on its own.

---

## Challenge 11: Create a custom network

**Task:** Create your own network, put a web server on it, and reach the server **by its name** from a second container.

**Requirements**
- Network `chat`, server container `server` (`nginx:1.30-alpine`), no published port.
- From a throw-away `busybox:1.37` container on the same network, download `http://server`.
- Remove everything at the end.

<details><summary>Hints</summary>

- `docker network create <name>`, and `--network <name>` on `docker run`.
- `wget -q -O- <url>` prints a page in busybox.
</details>

**Expected Result:** the busybox container prints the nginx welcome page.

<details><summary>Solution</summary>

```bash
docker network create chat
docker run -d --name server --network chat nginx:1.30-alpine
```

<!-- test: retry=15; contains=Welcome to nginx -->
```bash
docker run --rm --network chat busybox:1.37 wget -q -O- http://server
```

```bash
docker rm -f server
docker network rm chat
```

</details>

**Explanation:** on a user-defined network, Docker runs a small DNS server: every container can find the
others by name. No published port is needed for container-to-container traffic; `-p` is only for traffic
from your computer.

---

## Challenge 12: Create two communicating containers

**Task:** Show that two containers on the **default** network cannot find each other by name, then fix
it **without** restarting the server.

**Requirements**
- Start `backend` (`nginx:1.30-alpine`) without `--network`.
- Prove that a `busybox:1.37` container cannot reach `http://backend` by name.
- Create a network `team`, connect the **running** `backend` to it, and prove the name now works from a container on `team`.
- Clean up.

<details><summary>Hints</summary>

- `docker network connect <network> <container>` attaches a running container.
- On the default `bridge` network there is no name resolution.
</details>

**Expected Result:** first `bad address 'backend'`, then the nginx welcome page.

<details><summary>Solution</summary>

```bash
docker run -d --name backend nginx:1.30-alpine
```

<!-- test: fail; contains=bad address -->
```bash
docker run --rm busybox:1.37 wget -q -O- -T 3 http://backend
```

```bash
docker network create team
docker network connect team backend
```

<!-- test: retry=10; contains=Welcome to nginx -->
```bash
docker run --rm --network team busybox:1.37 wget -q -O- http://backend
```

```bash
docker rm -f backend
docker network rm team
```

</details>

**Explanation:** the default `bridge` network exists for backwards compatibility and has no DNS for
container names. Always create your own network (Compose does this for you automatically).
A container can be on several networks at once; `network connect` adds one while it runs.

---

## Challenge 13: Create the complete Compose application

**Task:** Run the whole message board (web, api, db) with one command, add a message through the API, and
prove the message survives `docker compose down` + `up`.

**Requirements**
- Use `examples/multi-container-app/docker-compose.yml`.
- Add a message with the text `compose challenge` via `POST /api/messages`.
- `down`, then `up` again: the message must still be listed.
- Finally remove everything **including** the volume.

<details><summary>Hints</summary>

- Run Compose inside the folder, or use `docker compose -f <file>`.
- `curl -s -X POST -H 'Content-Type: application/json' -d '{"text":"..."}' http://localhost:8080/api/messages`
- Which `down` keeps the volume, which one deletes it?
</details>

**Expected Result:** after down + up, `GET /api/messages` still contains `compose challenge`.

<details><summary>Solution</summary>

<!-- test: timeout=900 -->
```bash
docker compose -f examples/multi-container-app/docker-compose.yml up -d --build
```

<!-- test: retry=30; contains="database":"ok" -->
```bash
curl -s http://localhost:8080/api/health
```

<!-- test: retry=5; contains=compose challenge -->
```bash
curl -s -X POST -H 'Content-Type: application/json' -d '{"text":"compose challenge"}' http://localhost:8080/api/messages
```

```bash
docker compose -f examples/multi-container-app/docker-compose.yml down
docker compose -f examples/multi-container-app/docker-compose.yml up -d
```

<!-- test: retry=30; contains=compose challenge -->
```bash
curl -s http://localhost:8080/api/messages
```

```bash
docker compose -f examples/multi-container-app/docker-compose.yml down -v
```

</details>

**Explanation:** Compose created a network, a named volume and three containers from one file. `down`
removes containers and the network, but keeps the named volume `multi-container-app_db-data`.
`down -v` removes the volume too: use it only when you really want the data gone.

---

## Challenge 14: Investigate a container you did not start

**Task:** Someone started a container called `inspect-me`. Without looking at the command they used, find
its host port, its environment variable `ROLE`, the volume it uses and its IP address.

Start it first (pretend you did not see this line):

```bash
docker run -d --name inspect-me -p 8085:80 -e ROLE=demo -v inspect-data:/data nginx:1.30-alpine
```

**Requirements**
- Answer the four questions with `docker port` and `docker inspect --format`, one command each.
- Clean up the container and the volume.

<details><summary>Hints</summary>

- `docker inspect inspect-me` prints everything. Find the keys: `Config.Env`, `Mounts`, `NetworkSettings.Networks`.
- Go templates: `{{range .Mounts}}{{.Name}}{{end}}`.
</details>

**Expected Result:** `8085`, `ROLE=demo`, `inspect-data`, and an address like `172.17.0.x`.

<details><summary>Solution</summary>

<!-- test: contains=8085 -->
```bash
docker port inspect-me
```

<!-- test: contains=ROLE=demo -->
```bash
docker inspect inspect-me --format '{{range .Config.Env}}{{println .}}{{end}}'
```

<!-- test: contains=inspect-data -->
```bash
docker inspect inspect-me --format '{{range .Mounts}}{{.Name}} -> {{.Destination}}{{end}}'
```

<!-- test: contains=. -->
```bash
docker inspect inspect-me --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'
```

```bash
docker rm -f inspect-me
docker volume rm inspect-data
```

</details>

**Explanation:** `docker inspect` is the source of truth about a container's configuration. `--format`
with a Go template cuts the long JSON down to the one value you need, which is also how you use it in scripts.

---

## Challenge 15: Put a container on a diet

**Task:** Run a container limited to 128 MiB of memory and half a CPU, and prove both limits are active.

**Requirements**
- Name `limited`, image `nginx:1.30-alpine`.
- Show the limits with `docker inspect` and the memory limit with `docker stats` (one snapshot, not live).
- Clean up.

<details><summary>Hints</summary>

- `--memory=128m --cpus=0.5`.
- `docker inspect` stores memory in bytes (`HostConfig.Memory`) and CPUs in billionths (`HostConfig.NanoCpus`).
- `docker stats --no-stream` prints once and exits.
</details>

**Expected Result:** `134217728 500000000`, and the `MEM USAGE / LIMIT` column ends with `128MiB`.

<details><summary>Solution</summary>

```bash
docker run -d --name limited --memory=128m --cpus=0.5 nginx:1.30-alpine
```

<!-- test: contains=134217728 500000000 -->
```bash
docker inspect limited --format '{{.HostConfig.Memory}} {{.HostConfig.NanoCpus}}'
```

<!-- test: contains=128MiB -->
```bash
docker stats --no-stream limited
```

```bash
docker rm -f limited
```

</details>

**Explanation:** 128 × 1024 × 1024 = 134217728 bytes; 0.5 CPU = 500,000,000 nano-CPUs. Without limits, one
misbehaving container can use all the memory of the machine and slow down everything else. If a container
goes over its memory limit, it is killed (exit code 137, `OOMKilled=true`; see lab 14).

---

## Challenge 16: Prove a container is locked down

**Task:** Show three security basics with real evidence: a non-root user, a read-only filesystem, and no extra capabilities.

**Requirements**
- Build `simple-app:1.0` from `examples/simple-app` and prove it does not run as root (uid is not 0).
- Prove that a container started with `--read-only` cannot write to its filesystem.
- Prove that with `--cap-drop ALL`, even root inside the container cannot change a file's owner.

<details><summary>Hints</summary>

- `id -u` prints the user ID; 0 is root.
- `touch /test` tries to create a file.
- `chown` needs the `CHOWN` capability.
</details>

**Expected Result:** `10001`; `Read-only file system`; `Operation not permitted`.

<details><summary>Solution</summary>

```bash
docker build -t simple-app:1.0 examples/simple-app
```

<!-- test: contains=10001 -->
```bash
docker run --rm simple-app:1.0 id -u
```

<!-- test: fail; contains=Read-only file system -->
```bash
docker run --rm --read-only alpine:3.24 touch /test
```

<!-- test: fail; contains=Operation not permitted -->
```bash
docker run --rm --cap-drop ALL alpine:3.24 chown nobody /etc/passwd
```

</details>

**Explanation:** if an attacker breaks into an app, these settings limit what they can do: no root user,
no changing files, no special kernel powers. Each costs one line in a Dockerfile or one flag, which is why
the capstone uses all of them.

---

## Challenge 17: Make the image smaller

**Task:** Compare the size of `simple-app` built with the standard Dockerfile and with the multi-stage
Dockerfile, and prove the small one still works.

**Requirements**
- Build `simple-app:1.0` (standard) and `simple-app:small` from `examples/simple-app/optimization/multistage.Dockerfile`.
- List both sizes in one command.
- Run the small image on port 5000 and get an answer.
- Clean up the container and `simple-app:small`.

<details><summary>Hints</summary>

- `docker images simple-app --format '{{.Tag}} {{.Size}}'`
- The multi-stage file uses Alpine Linux in its final stage.
</details>

**Expected Result:** the `small` image is clearly smaller, and `curl` answers `Hello from simple-app!`.

<details><summary>Solution</summary>

<!-- test: timeout=900 -->
```bash
docker build -t simple-app:1.0 examples/simple-app
docker build -f examples/simple-app/optimization/multistage.Dockerfile -t simple-app:small examples/simple-app
```

<!-- test: contains=small -->
```bash
docker images simple-app --format '{{.Tag}} {{.Size}}'
```

```bash
docker run -d --name small -p 5000:5000 simple-app:small
```

<!-- test: retry=15; contains=Hello from simple-app -->
```bash
curl -s http://localhost:5000
```

```bash
docker rm -f small
docker rmi simple-app:small
```

</details>

**Explanation:** the final stage starts from a smaller base image and copies only the finished virtual
environment from the builder stage. Compilers and caches stay behind in the builder, which is thrown away.

---

## Challenge 18: Ship an image through a registry

**Task:** Push `simple-app` to your own local registry, delete it locally, and pull it back.

**Requirements**
- Run `registry:3` as `registry` on port 5000.
- Tag `simple-app:1.0` as `localhost:5000/simple-app:1.0`, push it, remove the local tag, pull it again.
- Clean up the registry and the tag.
- (macOS: if port 5000 is taken by AirPlay Receiver, use 5001 everywhere.)

<details><summary>Hints</summary>

- The registry address is part of the image name: `<registry>/<repository>:<tag>`.
- `docker rmi` on a tag only removes the name if other tags point to the same image.
</details>

**Expected Result:** the push uploads the layers, and `docker pull localhost:5000/simple-app:1.0` gets the image back from your registry (Docker may report that the layers already exist locally, because `simple-app:1.0` still uses them).

<details><summary>Solution</summary>

```bash
docker build -t simple-app:1.0 examples/simple-app
docker run -d --name registry -p 5000:5000 registry:3
```

<!-- test: retry=15 -->
```bash
docker tag simple-app:1.0 localhost:5000/simple-app:1.0
docker push localhost:5000/simple-app:1.0
```

<!-- test: contains=localhost:5000/simple-app:1.0 -->
```bash
docker rmi localhost:5000/simple-app:1.0
docker pull localhost:5000/simple-app:1.0
```

```bash
docker rmi localhost:5000/simple-app:1.0
docker rm -f registry
```

</details>

**Explanation:** Docker Hub works the same way, with your username instead of `localhost:5000`
(`docker push <your-username>/simple-app:1.0`); see lab 17. A registry is just a server that stores image
layers; the name tells Docker which server to talk to.

---

## Challenge 19: Find out why it stopped

**Task:** A container called `mystery` stops right after starting. Find the exit code and the reason using
only `docker ps -a`, `docker logs` and `docker inspect`. Do not read the start command.

Start it (pretend you did not see this line):

```bash
docker run -d --name mystery alpine:3.24 sh -c 'echo "loading /config/app.conf"; cat /config/app.conf'
```

<!-- test-run: sleep 2 -->

**Requirements**
- Name the exit code and the root cause in one sentence each.
- Fix: start a new container `mystery-fixed` that gets a config file through a bind mount and stays successful.

<details><summary>Hints</summary>

- Status and exit code: `docker ps -a`. The reason: `docker logs`.
- `docker inspect mystery --format '{{json .Config.Cmd}}'` shows what it tried to run.
</details>

**Expected Result:** exit code 1; `/config/app.conf` does not exist in the container.

<details><summary>Solution</summary>

<!-- test: retry=20; contains=Exited (1) -->
```bash
docker ps -a --filter name=mystery --format '{{.Names}} {{.Status}}'
```

<!-- test: retry=15; contains=No such file or directory -->
```bash
docker logs mystery
```

<!-- test: contains=/config/app.conf -->
```bash
docker inspect mystery --format '{{json .Config.Cmd}}'
```

The fix: provide the file. We create a config folder and bind-mount it read-only:

<!-- test: contains=mode=demo -->
```bash
mkdir my-config
echo 'mode=demo' > my-config/app.conf
docker run --name mystery-fixed -v "$(pwd)/my-config:/config:ro" alpine:3.24 sh -c 'echo "loading /config/app.conf"; cat /config/app.conf'
```

<!-- test: retry=20; contains=Exited (0) -->
```bash
docker ps -a --filter name=mystery-fixed --format '{{.Names}} {{.Status}}'
```

```bash
docker rm mystery mystery-fixed
rm -rf my-config
```

</details>

**Explanation:** Exit code 1 + "No such file or directory" in the logs: the program expected a file that is
not in the container. Observe (`ps -a`), investigate (`logs`, `inspect`), find the root cause, fix one thing,
verify. That order works for every problem in the [troubleshooting lab](../troubleshooting/README.md).
