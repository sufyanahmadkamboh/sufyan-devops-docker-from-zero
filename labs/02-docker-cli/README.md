# Lab 02 · The Docker CLI

> **Goal:** get comfortable with the commands an engineer uses to look inside and around containers.
> **Time:** about 40 minutes · **You need:** [Lab 01](../01-first-container/README.md)

## What you will learn

- `docker version` and `docker info`: is Docker healthy, and what does it run on?
- `docker logs`: what did the program inside the container print?
- `docker exec`: run a command inside a running container
- `docker inspect`: every detail Docker knows about a container
- `docker stats` and `docker top`: how much CPU and memory, which processes
- `docker cp`: copy files between your computer and a container

```text
            your terminal
                 |
        docker <command>           (the CLI = client)
                 |
                 v
          Docker Engine            (the daemon, does the real work)
     +-----------+-----------+
     |           |           |
  images     containers   networks / volumes
```

Every `docker ...` command is a request to the Docker Engine. The CLI itself does almost nothing; it sends the request and prints the answer.

## Step 1 · Prepare a container to explore

From the repository root:

```bash
cd labs/02-docker-cli
docker run -d --name web nginx:1.30-alpine
```

We keep this `web` container running for the whole lab.

## Step 2 · `docker version` and `docker info`

<!-- test: output=head:12; contains=Client; contains=Server -->
```bash
docker version
```

```text
Client:
 Version:           29.4.3
 API version:       1.54
 Go version:        go1.26.2
 Git commit:        055a478
 Built:             Wed May  6 17:10:36 2026
 OS/Arch:           windows/amd64
 Context:           desktop-linux

Server: Docker Desktop 4.74.0 (227015)
 Engine:
  Version:          29.4.3
...
```

**What you see:** two sections. **Client** is the `docker` command you type. **Server** is the Docker Engine. If the Server part is missing and you get `Cannot connect to the Docker daemon`, the engine is not running (on Windows and macOS: start Docker Desktop).

`docker info` describes the engine itself. It prints a lot, so we ask for a few fields with `--format`:

<!-- test: output; contains=Containers -->
```bash
docker info --format 'Server version: {{.ServerVersion}}
Operating system: {{.OperatingSystem}}
Containers: {{.Containers}} (running: {{.ContainersRunning}})
Images: {{.Images}}'
```

```text
Server version: 29.4.3
Operating system: Docker Desktop
Containers: 2 (running: 1)
Images: 17
```

Run plain `docker info` yourself to see everything: storage driver, number of CPUs and memory available to containers, and more.

## Step 3 · `docker logs`: what did the container print?

A container's **logs** are whatever its main process writes to the screen (standard output and standard error). Docker records them for you.

<!-- test: output=head:8; contains=docker-entrypoint -->
```bash
docker logs web
```

```text
/docker-entrypoint.sh: /docker-entrypoint.d/ is not empty, will attempt to perform configuration
/docker-entrypoint.sh: Looking for shell scripts in /docker-entrypoint.d/
/docker-entrypoint.sh: Launching /docker-entrypoint.d/10-listen-on-ipv6-by-default.sh
10-listen-on-ipv6-by-default.sh: info: Getting the checksum of /etc/nginx/conf.d/default.conf
10-listen-on-ipv6-by-default.sh: info: Enabled listen on IPv6 in /etc/nginx/conf.d/default.conf
/docker-entrypoint.sh: Sourcing /docker-entrypoint.d/15-local-resolvers.envsh
/docker-entrypoint.sh: Launching /docker-entrypoint.d/20-envsubst-on-templates.sh
/docker-entrypoint.sh: Launching /docker-entrypoint.d/30-tune-worker-processes.sh
...
```

**What you see:** the start-up messages of nginx. Useful options:

<!-- test: output -->
```bash
docker logs --tail 3 web
docker logs --since 10m --timestamps web | tail -n 2
```

```text
2026/10/04 03:58:19 [notice] 1#1: start worker process 41
2026/10/04 03:58:19 [notice] 1#1: start worker process 42
2026/10/04 03:58:19 [notice] 1#1: start worker process 43
2026-10-04T03:58:19.406799310Z 2026/10/04 03:58:19 [notice] 1#1: using the "epoll" event method
2026-10-04T03:58:19.406830698Z 2026/10/04 03:58:19 [notice] 1#1: nginx/1.30.5
2026-10-04T03:58:19.406833899Z 2026/10/04 03:58:19 [notice] 1#1: built by gcc 15.2.0 (Alpine 15.2.0) 
2026-10-04T03:58:19.406835632Z 2026/10/04 03:58:19 [notice] 1#1: OS: Linux 6.6.114.1-microsoft-standard-WSL2
2026-10-04T03:58:19.406837158Z 2026/10/04 03:58:19 [notice] 1#1: getrlimit(RLIMIT_NOFILE): 1048576:1048576
2026-10-04T03:58:19.406932139Z 2026/10/04 03:58:19 [notice] 1#1: start worker processes
2026-10-04T03:58:19.407273054Z 2026/10/04 03:58:19 [notice] 1#1: start worker process 30
2026-10-04T03:58:19.407478687Z 2026/10/04 03:58:19 [notice] 1#1: start worker process 31
2026-10-04T03:58:19.407708708Z 2026/10/04 03:58:19 [notice] 1#1: start worker process 32
2026-10-04T03:58:19.407888498Z 2026/10/04 03:58:19 [notice] 1#1: start worker process 33
2026-10-04T03:58:19.408213857Z 2026/10/04 03:58:19 [notice] 1#1: start worker process 34
2026-10-04T03:58:19.408407213Z 2026/10/04 03:58:19 [notice] 1#1: start worker process 35
2026-10-04T03:58:19.408555339Z 2026/10/04 03:58:19 [notice] 1#1: start worker process 36
2026-10-04T03:58:19.408838285Z 2026/10/04 03:58:19 [notice] 1#1: start worker process 37
2026-10-04T03:58:19.409433624Z 2026/10/04 03:58:19 [notice] 1#1: start worker process 38
2026-10-04T03:58:19.409920130Z 2026/10/04 03:58:19 [notice] 1#1: start worker process 39
2026-10-04T03:58:19.410527011Z 2026/10/04 03:58:19 [notice] 1#1: start worker process 40
2026-10-04T03:58:19.410975289Z 2026/10/04 03:58:19 [notice] 1#1: start worker process 41
2026-10-04T03:58:19.411227236Z 2026/10/04 03:58:19 [notice] 1#1: start worker process 42
2026-10-04T03:58:19.411634049Z 2026/10/04 03:58:19 [notice] 1#1: start worker process 43
2026-10-04T03:58:19.400599207Z /docker-entrypoint.sh: Launching /docker-entrypoint.d/30-tune-worker-processes.sh
2026-10-04T03:58:19.401903230Z /docker-entrypoint.sh: Configuration complete; ready for start up
```

`--tail 3` shows only the last 3 lines. `--since 10m` only the last 10 minutes. `--timestamps` adds the time to each line.

To **follow** the logs live (like `tail -f`), use `-f`. Press `Ctrl+C` to stop following (the container keeps running):

<!-- test: skip -->
```bash
docker logs -f web
```

## Step 4 · `docker exec`: run a command inside the container

<!-- test: output; contains=nginx version -->
```bash
docker exec web nginx -v
docker exec web cat /etc/os-release
```

```text
nginx version: nginx/1.30.5
NAME="Alpine Linux"
ID=alpine
VERSION_ID=3.24.2
PRETTY_NAME="Alpine Linux v3.24"
HOME_URL="https://alpinelinux.org/"
BUG_REPORT_URL="https://gitlab.alpinelinux.org/alpine/aports/-/issues"
```

**What you see:** the nginx version, then the operating system **inside the container**: Alpine Linux, even if your own computer runs Windows, macOS or Ubuntu. A container has its own filesystem.

For an interactive shell inside the container, add `-it` (interactive + terminal). Alpine images have `sh` instead of `bash`. Type `exit` to leave; the container keeps running:

<!-- test: skip -->
```bash
docker exec -it web sh
```

## Step 5 · `docker inspect`: everything Docker knows

<!-- test: output=head:15; contains="Id" -->
```bash
docker inspect web
```

```text
[
    {
        "Id": "79eafa5a5d801ad316236e19eccb380d7b46ea02f3ca4c6e9681f425fcad3915",
        "Created": "2026-10-04T03:58:19.189511996Z",
        "Path": "/docker-entrypoint.sh",
        "Args": [
            "nginx",
            "-g",
            "daemon off;"
        ],
        "State": {
            "Status": "running",
            "Running": true,
            "Paused": false,
            "Restarting": false,
...
```

**What you see:** a long JSON document: state, image, configuration, network settings, mounts... Nobody reads all of it. Use `--format` to pick one value:

<!-- test: output; contains=running -->
```bash
docker inspect web --format 'status: {{.State.Status}}'
docker inspect web --format 'started at: {{.State.StartedAt}}'
docker inspect web --format 'IP address: {{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'
```

```text
status: running
started at: 2026-10-04T03:58:19.25581861Z
IP address: 172.17.0.2
```

Lab 14 goes much deeper into `inspect`.

## Step 6 · `docker stats` and `docker top`

<!-- test: output; contains=web -->
```bash
docker stats --no-stream web
```

```text
CONTAINER ID   NAME      CPU %     MEM USAGE / LIMIT     MEM %     NET I/O         BLOCK I/O         PIDS
79eafa5a5d80   web       0.00%     11.82MiB / 15.35GiB   0.08%     1.17kB / 126B   16.4kB / 8.19kB   15
```

**What you see:** CPU %, memory used and its limit, network and disk input/output, and `PIDS` (number of processes). Without `--no-stream` the numbers refresh live until you press `Ctrl+C`:

<!-- test: skip -->
```bash
docker stats
```

`docker top` lists the processes inside one container:

<!-- test: output; contains=nginx -->
```bash
docker top web
```

```text
UID                 PID                 PPID                C                   STIME               TTY                 TIME                CMD
root                1574032             1574009             0                   03:58               ?                   00:00:00            nginx: master process nginx -g daemon off;
statd               1574068             1574032             0                   03:58               ?                   00:00:00            nginx: worker process
statd               1574069             1574032             0                   03:58               ?                   00:00:00            nginx: worker process
statd               1574070             1574032             0                   03:58               ?                   00:00:00            nginx: worker process
statd               1574071             1574032             0                   03:58               ?                   00:00:00            nginx: worker process
statd               1574072             1574032             0                   03:58               ?                   00:00:00            nginx: worker process
statd               1574073             1574032             0                   03:58               ?                   00:00:00            nginx: worker process
statd               1574074             1574032             0                   03:58               ?                   00:00:00            nginx: worker process
statd               1574075             1574032             0                   03:58               ?                   00:00:00            nginx: worker process
statd               1574076             1574032             0                   03:58               ?                   00:00:00            nginx: worker process
statd               1574077             1574032             0                   03:58               ?                   00:00:00            nginx: worker process
statd               1574078             1574032             0                   03:58               ?                   00:00:00            nginx: worker process
statd               1574079             1574032             0                   03:58               ?                   00:00:00            nginx: worker process
statd               1574080             1574032             0                   03:58               ?                   00:00:00            nginx: worker process
statd               1574081             1574032             0                   03:58               ?                   00:00:00            nginx: worker process
```

You see the nginx **master** process (the container's main process) and its **worker** processes.

## Step 7 · `docker cp`: copy files in and out

Copy nginx's default page **out** of the container:

<!-- test: contains=Welcome to nginx -->
```bash
docker cp web:/usr/share/nginx/html/index.html ./index-from-container.html
cat index-from-container.html
```

Now create a page on your computer and copy it **into** the container:

```bash
printf '<h1>Copied in with docker cp</h1>\n' > hello.html
docker cp hello.html web:/usr/share/nginx/html/hello.html
```

Ask nginx (from inside the container, because we have not published any port yet; that is Lab 04):

<!-- test: contains=Copied in with docker cp -->
```bash
docker exec web wget -qO- http://localhost/hello.html
```

> `docker cp` is great for quick debugging. It is **not** how you deliver files to containers for real: changes made this way are lost when the container is removed. Real files go into the image (Lab 06) or into volumes and bind mounts (Labs 09 and 10).

## Command reference

| Command | What it does | Why you use it | Syntax | Important options | Common mistake | Real-world usage |
|---|---|---|---|---|---|---|
| `docker version` | client + engine versions | first check when something "does not work" | `docker version` | `--format` | ignoring a missing **Server** section (engine not running) | bug reports, checking compatibility |
| `docker info` | engine details | how many containers, CPUs, memory, storage | `docker info` | `--format` | reading only the first lines | checking a build server |
| `docker images` | list images | what is on this machine, how big | `docker images [name]` | `-q`, `--filter`, `--format` | confusing images and containers | disk space checks |
| `docker pull` | download an image | get a specific version before running | `docker pull name:tag` | `--platform` | forgetting the tag (you get `latest`) | pre-pulling on servers |
| `docker run` | create + start a container | start anything | `docker run [options] image [command]` | `-d`, `--name`, `-p`, `-e`, `-v`, `--rm` | options after the image name (they are passed to the program instead) | every container you start |
| `docker ps` | list containers | what is running | `docker ps` | `-a`, `-q`, `--filter`, `--format` | forgetting `-a` and thinking a container "disappeared" | daily |
| `docker stop` / `start` / `restart` | change state | maintenance, config reloads | `docker stop name` | `-t` (seconds to wait) | stopping instead of fixing the cause of a crash | deployments |
| `docker rm` | delete a container | clean up | `docker rm name` | `-f` (force), `-v` (also anonymous volumes) | removing a container that held important data | cleanup |
| `docker rmi` | delete an image | free disk space | `docker rmi name:tag` | `-f` | images still used by containers | cleanup on build servers |
| `docker logs` | container output | first step of every investigation | `docker logs name` | `-f`, `--tail`, `--since`, `--timestamps` | expecting logs written to files inside the container | incident analysis |
| `docker exec` | run a command in a running container | look around, test from the inside | `docker exec [-it] name command` | `-it`, `-u` (user), `-e` | using it on a stopped container | debugging |
| `docker inspect` | full JSON details | IPs, mounts, env, exit codes | `docker inspect name` | `--format` | scrolling the whole JSON instead of `--format` | runtime investigation, scripts |
| `docker stats` | live resource usage | which container eats CPU/memory | `docker stats [name]` | `--no-stream` | forgetting it never ends without `--no-stream` | performance checks |
| `docker top` | processes in a container | what is actually running inside | `docker top name` | `ps` options after the name | expecting it to work on stopped containers | debugging |
| `docker cp` | copy files in/out | grab a config or log file | `docker cp src dest` (`name:/path` on one side) | `-a` (keep owner) | using it to "deploy" files | collecting evidence |

## Break it

Two classic mistakes. First, a typo in the container name:

<!-- test: fail; contains=No such container -->
```bash
docker logs wbe
```

Second, `exec` into a container that is not running:

```bash
docker stop web
```

<!-- test: fail; contains=is not running -->
```bash
docker exec web nginx -v
```

Before changing anything, let's investigate.

## Troubleshoot it

**Observe.** The first error says `No such container: wbe`. The second says the container `is not running`.

**Investigate.** Which containers exist, and in which state?

<!-- test: output; contains=Exited -->
```bash
docker ps -a --format '{{.Names}}: {{.Status}}'
```

```text
web: Exited (0) Less than a second ago
```

**Root cause.** There is no container called `wbe` (typo), and `web` exists but is `Exited`. `docker exec` starts a *new process in a running container*; with no running container, there is nothing to run it in.

**Fix.** Use the right name, and start the container first:

```bash
docker start web
```

**Verify.**

<!-- test: contains=nginx version -->
```bash
docker exec web nginx -v
```

## Challenge

**Task:** find out three facts about your `web` container using only the CLI.

**Requirements:** find (1) the command of its main process (PID 1), (2) the image it was created from, (3) the full path of the HTML folder nginx serves, by looking inside the container.

**Hints:** `docker top`, `docker inspect --format '{{.Config.Image}}'`, `docker exec web ls ...`

**Expected result:** `nginx: master process nginx -g daemon off;`, `nginx:1.30-alpine`, and a listing of `/usr/share/nginx/html` that includes `index.html` and your `hello.html`.

<details>
<summary>Solution</summary>

<!-- test: output; contains=master process; contains=nginx:1.30-alpine; contains=hello.html -->
```bash
docker top web
docker inspect web --format '{{.Config.Image}}'
docker exec web ls /usr/share/nginx/html
```

```text
UID                 PID                 PPID                C                   STIME               TTY                 TIME                CMD
root                1574216             1574192             3                   03:58               ?                   00:00:00            nginx: master process nginx -g daemon off;
statd               1574246             1574216             0                   03:58               ?                   00:00:00            nginx: worker process
statd               1574247             1574216             0                   03:58               ?                   00:00:00            nginx: worker process
statd               1574248             1574216             0                   03:58               ?                   00:00:00            nginx: worker process
statd               1574249             1574216             0                   03:58               ?                   00:00:00            nginx: worker process
statd               1574250             1574216             0                   03:58               ?                   00:00:00            nginx: worker process
statd               1574251             1574216             0                   03:58               ?                   00:00:00            nginx: worker process
statd               1574252             1574216             0                   03:58               ?                   00:00:00            nginx: worker process
statd               1574253             1574216             0                   03:58               ?                   00:00:00            nginx: worker process
statd               1574254             1574216             0                   03:58               ?                   00:00:00            nginx: worker process
statd               1574255             1574216             0                   03:58               ?                   00:00:00            nginx: worker process
statd               1574256             1574216             0                   03:58               ?                   00:00:00            nginx: worker process
statd               1574257             1574216             0                   03:58               ?                   00:00:00            nginx: worker process
statd               1574258             1574216             0                   03:58               ?                   00:00:00            nginx: worker process
statd               1574259             1574216             0                   03:58               ?                   00:00:00            nginx: worker process
nginx:1.30-alpine
50x.html
hello.html
index.html
```

**Explanation:** `docker top` lists the processes, the first one is the main process. `inspect` with `--format` reads one field of the JSON. `exec` runs `ls` inside the container's own filesystem.

</details>

## Verify

You can now:

- [ ] tell whether the Docker Engine is running (`docker version`)
- [ ] read a container's logs, only the last lines, or follow them live
- [ ] run commands inside a running container, including an interactive shell
- [ ] extract a single value with `docker inspect --format`
- [ ] check CPU, memory and processes with `docker stats` and `docker top`
- [ ] copy files in and out with `docker cp`, and know why it is not for real deployments

## Clean up

```bash
docker rm -f web
rm -f index-from-container.html hello.html
```

## Next

➡️ [Lab 03 · Container lifecycle](../03-container-lifecycle/README.md) · 📖 Concepts: [docs/05-docker-cli.md](../../docs/05-docker-cli.md)
