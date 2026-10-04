# Docker Inspect

## What is it?

`docker inspect` prints **everything Docker knows** about a container (or image, volume, network) as JSON: its
configuration, state, IP address, published ports, environment variables, mounts, networks, limits and more.
`--format` picks out exactly the field you need.

```text
docker inspect web
[
  {
    "Id": "3c6d...",                    full container ID
    "State": {                          running? exit code? OOMKilled? health?
      "Status": "running", "ExitCode": 0, "OOMKilled": false, ...
    },
    "Config": {                         what the image + docker run asked for
      "Image": "nginx:1.30-alpine",
      "Env": ["APP_ENV=dev", ...],
      "Cmd": ["nginx", "-g", "daemon off;"], ...
    },
    "HostConfig": {                     how Docker runs it on this computer
      "PortBindings": {"80/tcp": [{"HostPort": "8080"}]},
      "Memory": 0, "NanoCpus": 0, "ReadonlyRootfs": false, ...
    },
    "Mounts": [ {"Type": "volume", "Name": "...", "Destination": "..."} ],
    "NetworkSettings": {
      "Ports": {...},
      "Networks": { "bridge": {"IPAddress": "172.17.0.2", ...} }
    }
  }
]
```

## Why do we need it?

`docker ps` shows a summary. When you need **facts** ("which port is really published?", "which volume is mounted?",
"did the container get the environment variable?", "was it killed for using too much memory?"), `inspect` is the
source of truth. It replaces guessing with evidence.

## How does it work?

`--format` uses Go templates: `{{.Path.To.Field}}`. A few patterns cover almost everything:

| You want | Command |
|---|---|
| status and exit code | `docker inspect NAME --format '{{.State.Status}} {{.State.ExitCode}}'` |
| IP address (default bridge) | `docker inspect NAME --format '{{.NetworkSettings.IPAddress}}'` |
| IP on every network | `--format '{{range $n, $c := .NetworkSettings.Networks}}{{$n}}={{$c.IPAddress}} {{end}}'` |
| published ports | `--format '{{json .NetworkSettings.Ports}}'` |
| environment variables | `--format '{{json .Config.Env}}'` |
| mounts | `--format '{{json .Mounts}}'` |
| memory limit (bytes) | `--format '{{.HostConfig.Memory}}'` |

`{{json ...}}` prints a whole section as JSON, useful when you are not sure of the field names yet.

## Prerequisites

- [05-docker-cli.md](05-docker-cli.md), [07-ports.md](07-ports.md), [12-volumes.md](12-volumes.md)

## Hands-on Lab

Full lab: [labs/14-logs-inspect-resources](../labs/14-logs-inspect-resources/README.md). Start one container with a
port, an environment variable and a volume, then find each one with `inspect`:

```bash
docker run -d --name web -p 8080:80 -e APP_ENV=dev -v web-logs:/var/log/nginx nginx:1.30-alpine
```

<!-- test: output -->
```bash
docker inspect web --format 'status={{.State.Status}} image={{.Config.Image}}'
```

```text
status=running image=nginx:1.30-alpine
```

<!-- test: output -->
```bash
docker inspect web --format '{{.NetworkSettings.Networks.bridge.IPAddress}}'
```

```text
172.17.0.2
```

<!-- test: contains=8080 -->
```bash
docker inspect web --format '{{json .NetworkSettings.Ports}}'
```

<!-- test: contains=APP_ENV=dev -->
```bash
docker inspect web --format '{{json .Config.Env}}'
```

<!-- test: contains=web-logs -->
```bash
docker inspect web --format '{{range .Mounts}}{{.Type}} {{.Name}} -> {{.Destination}}{{end}}'
```

## Expected Result

- Status `running` and the image `nginx:1.30-alpine`.
- An IP address like `172.17.0.x` (yours may differ).
- Ports JSON containing `"HostPort":"8080"` for `80/tcp`.
- The environment list contains `APP_ENV=dev` plus the variables the image defines (`PATH`, `NGINX_VERSION`, ...).
- One mount: `volume web-logs -> /var/log/nginx`.

## Experiment

`inspect` works on other objects too:

<!-- test: contains=/var/lib/docker/volumes -->
```bash
docker volume inspect web-logs --format '{{.Mountpoint}}'
```

<!-- test: contains=Cmd -->
```bash
docker image inspect nginx:1.30-alpine --format '{{json .Config}}'
```

The volume lives in Docker's own storage area; the image config shows the default command (`Cmd`) and exposed ports
that every container from this image inherits.

## Break It

Ask for a field that does not exist:

<!-- test: fail; contains=map has no entry for key -->
```bash
docker inspect web --format '{{.State.Colour}}'
```

## Troubleshoot It

Template errors say **which** field is wrong. When you do not know the name, print the parent section as JSON and
look:

<!-- test: contains=Status -->
```bash
docker inspect web --format '{{json .State}}'
```

There is no `Colour`; the field you probably wanted is `Status` (or `Health.Status` for containers with a health
check). Verify:

<!-- test: contains=running -->
```bash
docker inspect web --format '{{.State.Status}}'
```

```bash
docker rm -f web
docker volume rm web-logs
```

## Common Mistakes

- Field names are case-sensitive: `.state.status` does not work.
- Using `.NetworkSettings.IPAddress` for containers on user-defined networks: it is empty there. Use the
  `Networks` map instead.
- Reading ports from `HostConfig.PortBindings` (what was **requested**) instead of `NetworkSettings.Ports` (what is
  **active**).
- Treating `inspect` output as a secret-free zone: environment variables, including passwords, are visible to anyone
  who can run `docker inspect` (see [19-security-basics.md](19-security-basics.md)).

## Best Practices

- Start with `{{json .Section}}`, then narrow down to the exact field.
- Use `inspect` in scripts instead of parsing `docker ps` text (the capstone's `verify.sh` does this).
- Inspect the **image** before running it, to know its default user, command and ports.

## Challenge

**Task:** for the running container below, find (1) the mapped host port, (2) the value of `GREETING`, (3) the
container's IP address, using only `docker inspect`.

```bash
docker run -d --name quiz -p 8082:80 -e GREETING=hello-inspect nginx:1.30-alpine
```

## Solution

<details><summary>Solution</summary>

<!-- test: contains=8082 -->
```bash
docker inspect quiz --format '{{(index (index .NetworkSettings.Ports "80/tcp") 0).HostPort}}'
```

<!-- test: contains=GREETING=hello-inspect -->
```bash
docker inspect quiz --format '{{range .Config.Env}}{{println .}}{{end}}'
```

<!-- test: contains=. -->
```bash
docker inspect quiz --format '{{.NetworkSettings.Networks.bridge.IPAddress}}'
```

```bash
docker rm -f quiz
```

`index` reads a map entry whose key has special characters (`80/tcp`); `range ... println` prints one variable per
line.
</details>

## Verification

- [ ] I can find a container's IP, ports, environment variables and mounts.
- [ ] I can print a whole section as JSON to discover field names.
- [ ] I know `inspect` also works for images, volumes and networks.

## Real-World Usage

Runtime investigation: "Is the config what we think it is?" is the first question in many incidents. Engineers use
`inspect` to confirm image versions, environment, limits, health and mounts, and in scripts that check deployments
automatically.

## Key Takeaways

- `docker inspect` is the full truth about a Docker object.
- `--format '{{...}}'` extracts single fields; `{{json ...}}` shows sections.
- Requested settings live in `Config`/`HostConfig`; live state in `State`/`NetworkSettings`.

Next: [18-resource-management.md](18-resource-management.md)
