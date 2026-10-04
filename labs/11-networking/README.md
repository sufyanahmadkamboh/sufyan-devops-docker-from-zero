# Lab 11 · Networking: How Containers Find Each Other

> **Goal:** make containers talk to each other by name, and understand why sometimes they can't.
> **Time:** about 30 minutes · **You need:** [Lab 02](../02-docker-cli/README.md) (`exec`, `inspect`) and [Lab 04](../04-port-mapping/README.md) (ports)

## What you will learn

- The networks Docker creates for you (`bridge`, `host`, `none`).
- Why containers on the **default** bridge network cannot find each other by name.
- How a **user-defined network** gives containers a built-in DNS: the container name becomes a hostname.
- `docker network create / ls / inspect / connect / disconnect / rm`.
- How networks **isolate** containers, and how to troubleshoot "they can't talk to each other".

```text
user-defined network "labnet"                       network "othernet"
┌──────────────────────────────────────────┐          ┌─────────────────────┐
│  ┌──────────┐  http://web2  ┌──────────┐ │          │  ┌──────────┐       │
│  │ busybox  │ ────────────► │   web2   │ │    ✘     │  │ backend  │       │
│  │ (client) │  DNS answers  │ (nginx)  │ │◄────────►│  │ (nginx)  │       │
│  └──────────┘  127.0.0.11   └──────────┘ │  no path │  └──────────┘       │
└──────────────────────────────────────────┘          └─────────────────────┘
 Containers on the same network: reachable by name.  Different networks: invisible to each other.
```

We use two small images: `nginx:1.30-alpine` as a server and `busybox:1.37` as a client. Busybox is a tiny image
with many little tools: `ping`, `wget`, `nslookup`, `cat`.

## Step 1 · The networks Docker already has

```bash
cd labs/11-networking
```

<!-- test: output; contains=bridge; contains=host; contains=none -->
```bash
docker network ls
```

```text
NETWORK ID     NAME      DRIVER    SCOPE
9c28fbb933f7   bridge    bridge    local
6278dc274ea1   host      host      local
3d5e01f105cb   none      null      local
```

**What you see:**

| Network | Meaning |
|---|---|
| `bridge` | the **default** network. Every container you start without `--network` joins it |
| `host` | the container uses your computer's network directly (no isolation; rarely what you want) |
| `none` | no network at all |

## Step 2 · The default bridge: no names

Start nginx without choosing a network:

```bash
docker run -d --name web nginx:1.30-alpine
```

Now try to reach it **by name** from another container:

<!-- test: fail; contains=bad address -->
```bash
docker run --rm busybox:1.37 ping -c 1 web
```

`ping: bad address 'web'`. The busybox container has no idea who `web` is. On the default `bridge` network there is
no name resolution. The containers *can* reach each other by IP address. Let's find `web`'s IP:

<!-- test: contains=. -->
```bash
docker inspect web --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'
```

And use it:

<!-- test: retry=10; contains=Welcome to nginx -->
```bash
WEB_IP=$(docker inspect web --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}')
docker run --rm busybox:1.37 wget -qO- "http://$WEB_IP"
```

It works, but IP addresses change every time a container is recreated. We need names.

## Step 3 · A user-defined network: names work

Create your own network and start a second nginx on it:

```bash
docker network create labnet
docker run -d --name web2 --network labnet nginx:1.30-alpine
```

From a client on the **same** network, use the name:

<!-- test: retry=10; contains=Welcome to nginx -->
```bash
docker run --rm --network labnet busybox:1.37 wget -qO- http://web2
```

The name `web2` was turned into an IP address. Who answered that question? Look at the client's DNS settings:

<!-- test: contains=127.0.0.11 -->
```bash
docker run --rm --network labnet busybox:1.37 cat /etc/resolv.conf
```

`nameserver 127.0.0.11` is Docker's **built-in DNS server**. On user-defined networks it knows every container by
its name. That is why, in a multi-container app, the API can simply connect to the host `db`.

## Step 4 · Inspect the network

<!-- test: output=head:40; contains=web2 -->
```bash
docker network inspect labnet
```

```text
[
    {
        "Name": "labnet",
        "Id": "957292d8950bc6defdd2ac86e438f2c94920d9536423067377c71df72a15f0c6",
        "Created": "2026-10-04T04:04:27.379458038Z",
        "Scope": "local",
        "Driver": "bridge",
        "EnableIPv4": true,
        "EnableIPv6": false,
        "IPAM": {
            "Driver": "default",
            "Options": {},
            "Config": [
                {
                    "Subnet": "172.18.0.0/16",
                    "Gateway": "172.18.0.1"
                }
            ]
        },
        "Internal": false,
        "Attachable": false,
        "Ingress": false,
        "ConfigFrom": {
            "Network": ""
        },
        "ConfigOnly": false,
        "Options": {
            "com.docker.network.enable_ipv4": "true",
            "com.docker.network.enable_ipv6": "false"
        },
        "Labels": {},
        "Containers": {
            "d90707c5d9170e278f154a4e5682d94b7d0ed744916cd1e9277059da437b4963": {
                "Name": "web2",
                "EndpointID": "d2a42e7f82c6e8cd8772656bc5ec49cdfc3c61a62f023f76c0e3cc83c60e565f",
                "MacAddress": "ca:6b:ad:98:bc:7a",
                "IPv4Address": "172.18.0.2/16",
                "IPv6Address": ""
            }
        },
...
```

**What you see:** the network's `Subnet` and `Gateway` (under `IPAM`), its `Driver` (`bridge`), and under
`Containers` every container attached to it, with its IP address. Only `web2` is listed: `web` is not on this network.

A shorter question, using a Go template:

<!-- test: contains=web2 -->
```bash
docker network inspect labnet --format '{{range .Containers}}{{.Name}} {{end}}'
```

## Step 5 · Connect and disconnect a running container

`web` is still only on the default bridge. Attach it to `labnet` too, without restarting it:

```bash
docker network connect labnet web
```

<!-- test: retry=10; contains=Welcome to nginx -->
```bash
docker run --rm --network labnet busybox:1.37 wget -qO- http://web
```

Now detach it again:

```bash
docker network disconnect labnet web
```

<!-- test: fail; contains=bad address -->
```bash
docker run --rm --network labnet busybox:1.37 wget -qO- -T 3 http://web
```

A container can be on several networks at the same time. That is how a "middle" service (an API) can talk to both
the web container and the database, while web and database never see each other. The capstone uses exactly this.

## Step 6 · Isolation between networks

Create a second network and a client on it. Can it reach `web2`, which lives on `labnet`?

```bash
docker network create othernet
```

<!-- test: fail; contains=bad address -->
```bash
docker run --rm --network othernet busybox:1.37 wget -qO- -T 3 http://web2
```

No. Different networks are isolated: they cannot even resolve each other's names. Isolation is a security feature:
put containers on the same network **only** if they need to talk.

## Break it

Don't fix it yet; this one is broken on purpose. A teammate started the `backend` service on the wrong network:

```bash
docker run -d --name backend --network othernet nginx:1.30-alpine
```

The client lives on `labnet` and needs `backend`:

<!-- test: fail; contains=bad address -->
```bash
docker run --rm --network labnet busybox:1.37 wget -qO- -T 3 http://backend
```

`bad address 'backend'`. The backend is running, so what is wrong?

## Troubleshoot it

Before changing anything, let's investigate.

1. **Observe:** is the backend running at all?

   <!-- test: contains=backend -->
   ```bash
   docker ps --filter name=backend
   ```

   Yes, `Up`. So the problem is not a crashed container.
2. **Investigate:** which networks is the backend on?

   <!-- test: contains=othernet -->
   ```bash
   docker inspect backend --format '{{range $name, $net := .NetworkSettings.Networks}}{{$name}} {{end}}'
   ```

   `othernet`.
3. **Investigate:** which containers are on the client's network?

   ```bash
   docker network inspect labnet --format '{{range .Containers}}{{.Name}} {{end}}'
   ```

   Only `web2`. The backend is missing.
4. **Root cause:** client and backend are on different networks, so Docker's DNS on `labnet` does not know `backend`.
5. **Fix:** attach the backend to the client's network:

   ```bash
   docker network connect labnet backend
   ```

6. **Verify:**

   <!-- test: retry=10; contains=Welcome to nginx -->
   ```bash
   docker run --rm --network labnet busybox:1.37 wget -qO- http://backend
   ```

"bad address" almost always means **name resolution failed**: wrong network, a typo in the name, or the target
container is not running (stopped containers are removed from Docker's DNS). Compare
[troubleshooting/03](../../troubleshooting/03-containers-cannot-communicate/README.md).

## Challenge

**Task:** create two communicating containers on your own network.

**Requirements:**
- A network called `shop`.
- An nginx container called `store` on `shop` (no published ports needed).
- From a `busybox:1.37` container on `shop`, fetch `http://store` and see the nginx welcome page.
- Show with `docker network inspect` that `store` is attached to `shop`.

**Hints:** Step 3 has all the commands; only the names change.

**Expected result:** the HTML of "Welcome to nginx!".

<details><summary>Solution</summary>

```bash
docker network create shop
docker run -d --name store --network shop nginx:1.30-alpine
```

<!-- test: retry=10; contains=Welcome to nginx -->
```bash
docker run --rm --network shop busybox:1.37 wget -qO- http://store
```

<!-- test: contains=store -->
```bash
docker network inspect shop --format '{{range .Containers}}{{.Name}} {{end}}'
```

**Explanation:** a user-defined network gives both containers Docker's DNS, so `store` resolves to the nginx
container's current IP address. No ports had to be published: `-p` is only for traffic from *your computer* into a
container, not between containers.

</details>

## Verify

- [ ] I can list, create, inspect and remove networks.
- [ ] I can explain why names do not work on the default bridge network.
- [ ] I can make two containers talk by name on a user-defined network.
- [ ] I can connect and disconnect a running container.
- [ ] I can troubleshoot "bad address" by checking which networks each container is on.

## Clean up

A network can only be removed when no container uses it, so remove the containers first:

```bash
docker rm -f web web2 backend store
docker network rm labnet othernet shop
```

## Next

- Next lab: [Lab 12 · Multi-container app, the hard way](../12-multi-container/README.md)
- Concept lesson: [docs/14-networking.md](../../docs/14-networking.md)
