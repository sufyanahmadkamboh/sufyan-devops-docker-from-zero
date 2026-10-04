# Lab 04 · Port Mapping

> **Goal:** open your containers to your browser, and learn to investigate when "it's running but I can't reach it".
> **Time:** about 40 minutes · **You need:** [Lab 03](../03-container-lifecycle/README.md)

## What you will learn

- Why a running web server in a container is not reachable by default
- `-p HOST_PORT:CONTAINER_PORT` and how to read it
- How to check mappings with `docker ps` and `docker port`
- What happens when you map the wrong container port
- What happens when two containers want the same host port, and how to find who has it

```text
   your browser
        |
        |  http://localhost:8080
        v
  +---------------- your computer ----------------+
  |   port 8080  ----------------+                |
  |                              |  -p 8080:80    |
  |   +---------- container -----v------------+   |
  |   |   nginx listening on port 80          |   |
  |   +---------------------------------------+   |
  +-----------------------------------------------+

        -p  8080 : 80
            ^^^^   ^^
            HOST   CONTAINER
```

A container has its own network. nginx listens on port 80 **inside** the container. Your computer's port 8080 is a different port on a different network. `-p` builds the bridge between them.

## Step 1 · A container without `-p`

From the repository root:

```bash
cd labs/04-port-mapping
docker run -d --name hidden nginx:1.30-alpine
```

<!-- test: output; contains=80/tcp -->
```bash
docker ps --filter name=hidden --format '{{.Names}}  ports: {{.Ports}}'
```

```text
hidden  ports: 80/tcp
```

**What you see:** `80/tcp` with no arrow. nginx listens on 80 inside the container, but nothing on your computer is connected to it. The browser has no way in.

```bash
docker rm -f hidden
```

## Step 2 · Publish a port

<!-- test: output -->
```bash
docker run -d --name web -p 8080:80 nginx:1.30-alpine
docker ps --filter name=web --format '{{.Names}}  ports: {{.Ports}}'
```

```text
ce9ab6d232d65d3189b2d056ccb7326fd7afcbfb47060fdd801a180a7fea8c5b
web  ports: 0.0.0.0:8080->80/tcp, [::]:8080->80/tcp
```

Now the `PORTS` column shows `0.0.0.0:8080->80/tcp`: "every network address of this computer, port 8080, forwards to port 80 of the container" (the `[::]` part is the same for IPv6).

Let's run this:

<!-- test: retry=15; contains=Welcome to nginx! -->
```bash
curl -s http://localhost:8080
```

You get the HTML of the nginx welcome page. Open **http://localhost:8080** in your browser too: you should see *Welcome to nginx!*.

`docker port` answers the question "which host port goes where?" for one container:

<!-- test: output; contains=8080 -->
```bash
docker port web
```

```text
80/tcp -> 0.0.0.0:8080
80/tcp -> [::]:8080
```

Every request is also visible in the logs (one line per request, with the address it came from):

<!-- test: retry=15; output=tail:2; contains=GET / -->
```bash
docker logs web
```

```text
...
2026/10/04 04:52:24 [notice] 1#1: start worker process 43
172.17.0.1 - - [04/Oct/2026:04:52:25 +0000] "GET / HTTP/1.1" 200 896 "-" "curl/8.19.0" "-"
```

## Step 3 · Same container port, different host ports

Two containers can both listen on port 80 **inside**, because each has its own network. They only need different **host** ports:

<!-- test: retry=15; contains=Welcome to nginx! -->
```bash
docker run -d --name web2 -p 8081:80 nginx:1.30-alpine
curl -s http://localhost:8081
```

<!-- test: output -->
```bash
docker ps --format '{{.Names}}  {{.Ports}}'
```

```text
web2  0.0.0.0:8081->80/tcp, [::]:8081->80/tcp
web  0.0.0.0:8080->80/tcp, [::]:8080->80/tcp
```

> Option: `-p 127.0.0.1:8082:80` publishes only on your own machine (not to other computers in your network). Good practice for things like databases on a laptop.

## Break it 1 · The container is running, but the app is unreachable

A colleague says: "nginx listens on 8080, right?" and starts this:

```bash
docker run -d --name broken -p 8082:8080 nginx:1.30-alpine
```

<!-- test-run: sleep 2 -->
<!-- test: fail -->
```bash
curl -sS --max-time 5 http://localhost:8082
```

`curl` fails: an empty reply, a reset connection or a timeout (the exact wording depends on your system). Don't fix it yet. We intentionally broke it. Before changing anything, let's investigate rather than guess.

## Troubleshoot it 1

**Observe.** The request fails, but is the container even running?

<!-- test: output; contains=Up -->
```bash
docker ps --filter name=broken --format '{{.Names}}  {{.Status}}  {{.Ports}}'
```

```text
broken  Up 2 seconds  0.0.0.0:8082->8080/tcp, [::]:8082->8080/tcp
```

It is `Up`, and the mapping `8082->8080` exists. So Docker did its part.

**Investigate.** Is nginx healthy? Check the logs:

<!-- test: output=tail:3 -->
```bash
docker logs broken
```

```text
...
2026/10/04 04:52:26 [notice] 1#1: start worker process 41
2026/10/04 04:52:26 [notice] 1#1: start worker process 42
2026/10/04 04:52:26 [notice] 1#1: start worker process 43
```

No errors: nginx started normally. Next question: **which port does nginx really listen on inside the container?** `netstat` (included in the Alpine image) lists listening ports:

<!-- test: output; contains=:80 -->
```bash
docker exec broken netstat -tln
```

```text
Active Internet connections (only servers)
Proto Recv-Q Send-Q Local Address           Foreign Address         State       
tcp        0      0 0.0.0.0:80              0.0.0.0:*               LISTEN      
tcp        0      0 :::80                   :::*                    LISTEN      
```

nginx listens on `:80`. Nothing listens on 8080. The port documented by the image confirms it:

<!-- test: output; contains=80/tcp -->
```bash
docker image inspect nginx:1.30-alpine --format '{{json .Config.ExposedPorts}}'
```

```text
{"80/tcp":{}}
```

**Root cause.** `-p 8082:8080` forwards host port 8082 to container port **8080**, where nobody is listening. The right side of `-p` must be the port the application *really* uses inside the container.

**Fix.** You cannot change the ports of an existing container: remove it and create it again with the right mapping:

<!-- test: retry=15; contains=Welcome to nginx! -->
```bash
docker rm -f broken
docker run -d --name broken -p 8082:80 nginx:1.30-alpine
curl -s http://localhost:8082
```

**Verify.** The welcome page is back. This is exactly the type of problem you may encounter in a real DevOps environment: the container is green, the application is fine, and the wiring between them is wrong.

## Break it 2 · Port already in use

`web` already uses host port 8080. Let's start another container on the same host port:

<!-- test: fail; contains=port is already allocated -->
```bash
docker run -d --name web3 -p 8080:80 nginx:1.30-alpine
```

## Troubleshoot it 2

**Observe.** `Bind for 0.0.0.0:8080 failed: port is already allocated`.

**Investigate.** Who holds port 8080? Docker can filter containers by published port:

<!-- test: output; contains=web -->
```bash
docker ps --filter publish=8080 --format '{{.Names}} uses {{.Ports}}'
```

```text
web uses 0.0.0.0:8080->80/tcp, [::]:8080->80/tcp
```

If nothing shows up, the port is taken by a program **outside** Docker (another web server, a development tool...). On Linux/macOS `sudo lsof -i :8080` finds it; on Windows `netstat -ano | findstr :8080` shows the process ID.

Also notice: the failed command still **created** the container `web3`, it just could not start it:

<!-- test: output; contains=Created -->
```bash
docker ps -a --filter name=web3 --format '{{.Names}}  {{.Status}}'
```

```text
web3  Created
```

**Root cause.** A host port can be used by only one thing at a time. Container ports never conflict (each container has its own), host ports do.

**Fix.** Remove the half-created container and use a free host port:

<!-- test: retry=15; contains=Welcome to nginx! -->
```bash
docker rm web3
docker run -d --name web3 -p 8083:80 nginx:1.30-alpine
curl -s http://localhost:8083
```

**Verify.**

<!-- test: output; contains=8083 -->
```bash
docker ps --format '{{.Names}}  {{.Ports}}'
```

```text
web3  0.0.0.0:8083->80/tcp, [::]:8083->80/tcp
broken  0.0.0.0:8082->80/tcp, [::]:8082->80/tcp
web2  0.0.0.0:8081->80/tcp, [::]:8081->80/tcp
web  0.0.0.0:8080->80/tcp, [::]:8080->80/tcp
```

Four containers, four different host ports, all pointing to container port 80.

## Challenge

**Task:** serve the same nginx welcome page on two host ports from **one** container.

**Requirements:** one container named `multi`, reachable on `http://localhost:9090` **and** `http://localhost:9091`.

**Hints:** `-p` can be given more than once.

**Expected result:** both URLs return the welcome page; `docker port multi` shows two lines (plus IPv6 variants).

<details>
<summary>Solution</summary>

<!-- test: retry=15; contains=Welcome to nginx! -->
```bash
docker run -d --name multi -p 9090:80 -p 9091:80 nginx:1.30-alpine
curl -s http://localhost:9090
```

<!-- test: contains=Welcome to nginx! -->
```bash
curl -s http://localhost:9091
docker port multi
```

**Explanation:** each `-p` adds a forwarding rule from a host port to a container port. Several host ports may point to the same container port.

</details>

## Verify

You can now:

- [ ] explain why a container's port is not reachable without `-p`
- [ ] read `-p 8080:80` as HOST:CONTAINER without hesitating
- [ ] check mappings with `docker ps` and `docker port`
- [ ] find out which port an application really listens on (`docker exec ... netstat -tln`, `EXPOSE`)
- [ ] find which container holds a host port with `docker ps --filter publish=PORT`

## Clean up

```bash
docker rm -f web web2 web3 broken multi
```

## Next

➡️ [Lab 05 · Environment variables](../05-environment-variables/README.md) · 📖 Concepts: [docs/07-ports.md](../../docs/07-ports.md)
