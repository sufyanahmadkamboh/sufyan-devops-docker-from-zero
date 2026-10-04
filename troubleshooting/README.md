# Troubleshooting Lab

> Ten things that really go wrong with Docker, broken on purpose so you can practise fixing them.
> Time: 2–3 hours for all ten · You need: labs 01–13 (at least up to Docker Compose)

Every problem in this folder is reproducible. You start the broken setup, you watch it fail,
and then you find the cause **with evidence**, not by guessing.

## The method

Use the same five steps every time, in this order:

```text
  1. OBSERVE        What exactly is the symptom? Write it down in one sentence.
         |          ("The container is not in docker ps", "the browser shows 502")
         v
  2. INVESTIGATE    Which command gives me evidence? Run it and READ the output.
         |          docker ps -a, docker logs, docker inspect, docker exec ...
         v
  3. ROOT CAUSE     What does the evidence say? Name the cause in one sentence.
         |          ("CMD points at main.py, but the file is app.py")
         v
  4. FIX            Change ONE thing, the thing the evidence pointed at.
         |
         v
  5. VERIFY         Prove it works with a command, not with a feeling.
```

Two rules that save hours:

- **Don't change anything before you have evidence.** Restarting, rebuilding and deleting things
  "to see if it helps" destroys the evidence you need.
- **Read the whole error message.** Docker's errors are long, but the important part is almost
  always in them: a file name, a port, a container name, an exit code.

## The ten scenarios

| # | Scenario | The symptom you see | First command to run |
|---|---|---|---|
| 01 | [Container exits immediately](01-container-exits-immediately/README.md) | `docker run -d` printed an ID, but the container is not in `docker ps` | `docker ps -a`, then `docker logs <name>` |
| 02 | [Port already in use](02-port-already-in-use/README.md) | `docker run` fails: `port is already allocated` | `docker ps --filter publish=8080` |
| 03 | [Containers cannot communicate](03-containers-cannot-communicate/README.md) | The web container keeps stopping, the site is down | `docker compose ps -a`, then `docker compose logs web` |
| 04 | [Volume data appears missing](04-volume-data-missing/README.md) | The file you saved is gone in the new container | `docker volume ls` |
| 05 | [Dockerfile build fails](05-dockerfile-build-fails/README.md) | `docker build` stops: `"/requirements.txt": not found` | `cat .dockerignore` |
| 06 | [Environment variable missing](06-environment-variable-missing/README.md) | The page loads, but the API answers `502` | `docker compose ps -a`, then `docker compose logs api` |
| 07 | [Running but not reachable](07-running-but-not-reachable/README.md) | `docker ps` says Up, the port is mapped, but `curl` fails | `docker logs <name>` (look at the address it listens on) |
| 08 | [Image too large](08-image-too-large/README.md) | A tiny app produces an image of more than a gigabyte | `docker history <image>` |
| 09 | [Host changes not reflected](09-host-changes-not-reflected/README.md) | You edit a file, the browser still shows the old page (or 403) | `docker inspect <name> --format '{{json .Mounts}}'` |
| 10 | [Database data disappears](10-database-data-disappears/README.md) | After `down` and `up`, all rows are gone (or the database will not start) | `docker inspect <name> --format '{{json .Mounts}}'` |

Each scenario folder has a `README.md` with the same sections:
**Problem → Symptoms → Investigation → Commands → Root Cause → Fix → Verification → Lesson Learned**.
The broken files stay broken in the repository; fixed versions sit next to them
(`Dockerfile.fixed`, `docker-compose.fixed.yml`, `fixed/`), so you can always start again.

## Investigation toolkit (print this)

```text
WHAT IS RUNNING?
  docker ps                         running containers
  docker ps -a                      ALL containers, also stopped ones (look at STATUS and the exit code)
  docker compose ps -a              the same, for one Compose project

WHY DID IT STOP / WHAT DID IT SAY?
  docker logs <name>                everything the main process printed
  docker logs --tail 20 <name>      only the last 20 lines
  docker compose logs <service>     logs of one Compose service
  docker inspect <name> --format '{{.State.ExitCode}} {{.State.OOMKilled}}'

  Exit codes:  0   the process finished normally (it had nothing more to do)
               1   generic error (read the logs)
               2   often "file not found" / wrong command-line usage
               3   our API: a required setting is missing
               125 docker itself failed (bad option, port taken, ...)
               126 command found but not executable
               127 command not found
               137 killed (SIGKILL): docker kill, or out of memory (OOMKilled=true)

WHAT IS THE CONFIGURATION?
  docker inspect <name>                                        everything (long JSON)
  docker inspect <name> --format '{{json .Config.Env}}'        environment variables
  docker inspect <name> --format '{{json .Config.Cmd}}'        the command it runs
  docker inspect <name> --format '{{json .Mounts}}'            volumes and bind mounts
  docker inspect <name> --format '{{json .NetworkSettings.Ports}}'   published ports
  docker port <name>                                           published ports, short

LOOK INSIDE
  docker exec <name> ls -la /app      run one command in a running container
  docker exec -it <name> sh           open a shell (bash may not exist in small images)
  docker run --rm <image> ls /app     look inside an image whose container will not stay up

NETWORKS
  docker network ls
  docker network inspect <network>    which containers are attached, with their IPs
  docker run --rm --network <network> busybox:1.37 ping -c 1 <name>   can this name be resolved?

PORTS
  docker ps --filter publish=8080     which container uses host port 8080
  curl -v http://localhost:8080       what does the client really get?

VOLUMES
  docker volume ls
  docker volume inspect <volume>

IMAGES AND BUILDS
  docker images
  docker history <image>              which instruction made which layer, and how big
  docker build --progress=plain .     full build output, including RUN output
```

## Clean up after a scenario

Each README ends with its own clean-up. If you get lost, this removes the containers and
networks of all ten scenarios (it does **not** touch your other projects):

<!-- test: skip -->
```bash
docker rm -f exits exits-fixed idle web web2 web3 simple writer reader 2>/dev/null
for p in ts03 ts06 ts10 ts10b; do docker compose -p "$p" down -v 2>/dev/null; done
```

## Next

When you can solve these without opening the README, go to the [capstone](../capstone/README.md).
The capstone ends with you breaking it yourself.
