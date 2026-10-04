# 🐳 Docker From Zero · A Complete Hands-On Learning Lab

[![test-lessons](https://github.com/sufyanahmadkamboh/sufyan-devops-docker-from-zero/actions/workflows/test.yaml/badge.svg)](https://github.com/sufyanahmadkamboh/sufyan-devops-docker-from-zero/actions/workflows/test.yaml)

Learn Docker by **using it, breaking it, fixing it and building something with it**.

You start with `docker --version`. You finish by running a three-container application with `docker compose up -d`,
and you understand every step in between: what Docker does, why each command is used, and how to find the cause when
something fails.

```text
Learn  ->  Build  ->  Run  ->  Break  ->  Troubleshoot  ->  Understand  ->  Improve
```

Every command in this repository is executed automatically on a fresh Docker engine (see [tests/](tests/README.md)),
so what you read is what actually happens.

## 1. What this project is

A Docker practice platform you clone and work through on your own computer:

| Folder | What it is for | Use it when... |
|---|---|---|
| [tutorial/](tutorial/README.md) | the **guided training**: a senior engineer walks you through the repository, step by step | you want to be taught (start here) |
| [labs/](labs/) | 18 hands-on **workbooks**, one skill each, with "Break it" and "Troubleshoot it" | you want to practise one topic |
| [docs/](docs/) | 23 **concept lessons**: what, why, how, best practices, real-world usage | you want to understand or look something up |
| [troubleshooting/](troubleshooting/README.md) | 10 realistic **failures** to reproduce, investigate and fix | you want to learn debugging |
| [challenges/](challenges/README.md) | **tasks without instructions**, solutions hidden | you want to test yourself |
| [capstone/](capstone/README.md) | the **final project**: web + API + database + volume, done properly | you finished the labs |
| [examples/](examples/) | the small applications the labs use | |

The application is deliberately tiny. It is only the vehicle; **Docker is the subject**.

## 2. Who it is for

Someone who knows basic terminal commands (`cd`, `ls`, files and folders) and has **never** used Docker: never run a
container, never written a Dockerfile, never used Compose, volumes or networks. No DevOps experience needed.

## 3. What you will learn

- What Docker is, and the difference between an **image** and a **container**
- Running, stopping, starting, inspecting and removing containers; reading **logs**; running commands inside with **exec**
- **Port mapping** and **environment variables**
- Writing **Dockerfiles** step by step; **image layers**, the **build cache** and **.dockerignore**
- Keeping data with **volumes**, live editing with **bind mounts**
- **Networking**: how containers find each other by name, and how to keep them apart
- Running a **multi-container application**, first by hand, then with **Docker Compose**
- **Resource limits**, **security basics** (non-root, read-only, secrets) and **image optimization** (multi-stage builds)
- Sharing images through a **registry** (your own, and Docker Hub)
- **Troubleshooting**: observe, investigate, find the root cause, fix, verify
- **Safe cleanup**, and what each `prune` command really deletes

## 4. Prerequisites

| You need | Check it with |
|---|---|
| Docker Engine or Docker Desktop (any current version) | `docker --version` |
| Docker Compose v2 (included in Docker Desktop and the Docker Engine packages) | `docker compose version` |
| Git | `git --version` |
| A terminal: Linux/macOS terminal, or **WSL2** on Windows (recommended) | |
| About 5 GB of free disk space, and an internet connection for downloading images | |

No cloud account, no paid service, no Kubernetes. Everything runs on your computer.

## 5. Installation

Full instructions for Windows, macOS and Linux: [docs/02-docker-installation.md](docs/02-docker-installation.md).

When Docker is installed, check it:

<!-- test: contains=Docker version -->
```bash
docker --version
```

<!-- test: contains=Docker Compose version -->
```bash
docker compose version
```

Then get the lab:

<!-- test: skip -->
```bash
git clone https://github.com/sufyanahmadkamboh/sufyan-devops-docker-from-zero.git
cd sufyan-devops-docker-from-zero
```

> **Windows:** use the Ubuntu terminal of WSL2 for the labs. In Git Bash, run `export MSYS_NO_PATHCONV=1` first, or
> paths like `/app` are rewritten into Windows paths. Details in [docs/02](docs/02-docker-installation.md).

## 6. Learning roadmap

```text
 PART 1 · Containers                     PART 2 · Images                  PART 3 · Data and networks
 ----------------------                  ----------------                 ---------------------------
 01 First container                      06 First Dockerfile              09 Volumes
 02 Docker CLI                           07 Layers and cache              10 Bind mounts
 03 Container lifecycle                  08 .dockerignore                 11 Networking
 04 Port mapping                                                          12 Multi-container (by hand)
 05 Environment variables
            |                                     |                                |
            +-------------------------------------+--------------------------------+
                                                  |
 PART 4 · Running it like an engineer             v                 PART 5 · Prove it
 --------------------------------------                             ------------------
 13 Docker Compose          16 Image optimization                   Troubleshooting 01-10
 14 Logs, inspect, resources 17 Registries / Docker Hub             Challenges
 15 Security basics         18 Safe cleanup                         Capstone  ->  Knowledge check
```

The detailed roadmap, with the matching tutorial chapter, lab and lesson for each stage, is in
[ROADMAP.md](ROADMAP.md).

## 7. Repository structure

```text
sufyan-devops-docker-from-zero/
├── README.md              you are here
├── ROADMAP.md             the learning path, stage by stage
├── CHECKLIST.md           the knowledge checklist
├── tutorial/              guided training (12 chapters)
├── labs/                  18 hands-on workbooks
├── docs/                  23 concept lessons
├── troubleshooting/       10 deliberate failures with full investigations
├── challenges/            practice tasks with hidden solutions
├── examples/
│   ├── nginx/             a static web page (ports, bind mounts, first custom image)
│   ├── simple-app/        a tiny Python app (Dockerfiles, layers, .dockerignore, security, optimization)
│   └── multi-container-app/  web + api + database (networking, multi-container, Compose)
├── capstone/              the final project (hardened web + api + database + volume)
├── study/                 study guide (PDF), glossary, interview questions
└── tests/                 runs every lesson automatically (for maintainers)
```

## 8. How to start

1. Install Docker and clone the repository (section 5).
2. Open [tutorial/00-start-here.md](tutorial/00-start-here.md) and follow the chapters in order.
3. After each chapter, do the matching lab in [labs/](labs/) and try the [challenges](challenges/README.md).
4. Use [docs/](docs/) whenever you want the full explanation of a concept.
5. Finish with the [capstone](capstone/README.md) and the [knowledge check](tutorial/11-knowledge-check.md).

Always run commands from the **repository root** unless a step says `cd` somewhere else.

**Where am I? What have I learned? What next?** Every chapter and lab ends with a "Next" link, and
[CHECKLIST.md](CHECKLIST.md) shows what you can already do.

## 9. Labs

| # | Lab | You will be able to... |
|---|---|---|
| 01 | [First container](labs/01-first-container/README.md) | pull an image, run, list, stop, start, restart and remove containers |
| 02 | [Docker CLI](labs/02-docker-cli/README.md) | use logs, exec, inspect, stats, top and cp |
| 03 | [Container lifecycle](labs/03-container-lifecycle/README.md) | explain created, running, stopped and removed, and why containers stop |
| 04 | [Port mapping](labs/04-port-mapping/README.md) | publish a port, and debug a running container you cannot reach |
| 05 | [Environment variables](labs/05-environment-variables/README.md) | configure containers with -e and --env-file |
| 06 | [First Dockerfile](labs/06-first-dockerfile/README.md) | write a Dockerfile instruction by instruction and build your own image |
| 07 | [Layers and cache](labs/07-layers-and-cache/README.md) | order a Dockerfile so rebuilds take seconds |
| 08 | [.dockerignore](labs/08-dockerignore/README.md) | keep junk and secrets out of the build and the image |
| 09 | [Volumes](labs/09-volumes/README.md) | keep data after a container is deleted |
| 10 | [Bind mounts](labs/10-bind-mounts/README.md) | edit files on your computer and see them live in a container |
| 11 | [Networking](labs/11-networking/README.md) | connect containers by name, and isolate them |
| 12 | [Multi-container](labs/12-multi-container/README.md) | run web + api + database by hand |
| 13 | [Docker Compose](labs/13-docker-compose/README.md) | run the same application with one file and one command |
| 14 | [Logs, inspect, resources](labs/14-logs-inspect-resources/README.md) | investigate containers and limit memory and CPU |
| 15 | [Security](labs/15-security/README.md) | run as non-root, read-only, and keep secrets out of environment variables |
| 16 | [Image optimization](labs/16-image-optimization/README.md) | make images much smaller with slim bases and multi-stage builds |
| 17 | [Docker Hub](labs/17-docker-hub/README.md) | tag, push and pull images (local registry and Docker Hub) |
| 18 | [Cleanup](labs/18-cleanup/README.md) | free disk space safely, knowing exactly what prune deletes |

## 10. Challenges

[challenges/README.md](challenges/README.md): one or more tasks after every major topic, each with requirements, hints,
the expected result, and a hidden solution with an explanation. Try first; open the solution only to check.

## 11. Troubleshooting

[troubleshooting/README.md](troubleshooting/README.md): ten failures you will meet in real work, each reproduced from
files in this repository and solved step by step.

| # | Failure |
|---|---|
| 01 | [Container exits immediately](troubleshooting/01-container-exits-immediately/README.md) |
| 02 | [Port already in use](troubleshooting/02-port-already-in-use/README.md) |
| 03 | [Containers cannot communicate](troubleshooting/03-containers-cannot-communicate/README.md) |
| 04 | [Volume data appears missing](troubleshooting/04-volume-data-missing/README.md) |
| 05 | [Dockerfile build fails](troubleshooting/05-dockerfile-build-fails/README.md) |
| 06 | [Environment variable missing](troubleshooting/06-environment-variable-missing/README.md) |
| 07 | [Container running but not reachable](troubleshooting/07-running-but-not-reachable/README.md) |
| 08 | [Image too large](troubleshooting/08-image-too-large/README.md) |
| 09 | [Host changes not reflected](troubleshooting/09-host-changes-not-reflected/README.md) |
| 10 | [Database data disappears](troubleshooting/10-database-data-disappears/README.md) |

## 12. Capstone

```text
                     Browser
                        |
                        v   http://localhost:8080
          web container (nginx, non-root)
                        |   frontend network
                        v
          api container (Python, non-root, read-only)
                        |   backend network
                        v
          database container (PostgreSQL 18)
                        |
                        v
          Docker volume (capstone_db-data)
```

One `docker compose up -d --build` starts it; `./verify.sh` proves it works: health checks, networks, non-root users,
read-only filesystem, secrets, resource limits and data that survives. Start at [capstone/README.md](capstone/README.md)
or the guided [tutorial/10-capstone.md](tutorial/10-capstone.md).

## 13. Knowledge checklist

When you can tick every line of [CHECKLIST.md](CHECKLIST.md), you can honestly say:

> **"I understand Docker because I actually used it, broke it, fixed it, and built something with it."**

## Study material

- [Study guide (PDF)](study/study-guide.pdf): all 23 lessons in one document, for reading offline
- [Glossary](study/glossary.md) and [interview questions](study/interview-questions.md)

## Author

Sufyan Ahmad · DevOps Engineer · [Portfolio](https://sufyanahmadkamboh.github.io/) ·
[LinkedIn](https://www.linkedin.com/in/sufyanahmadkamboh/)

Licensed under the [MIT License](LICENSE).
