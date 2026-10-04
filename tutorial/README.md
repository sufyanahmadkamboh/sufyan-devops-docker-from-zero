# The Docker From Zero Training Tutorial

This is the guided path through the whole repository. Think of it as a senior DevOps engineer sitting next to you:
we run every command together, look at the output, break things on purpose, investigate, and fix them.

Every command in these chapters is real. It runs against the files in this repository, and the outputs you see
in the grey boxes were captured from a real run of the tests (`tests/mdrun.py`). Your IDs, times and sizes will be
different. That is normal.

| Chapter | What you do | Time |
|---|---|---|
| [00 · Start here](00-start-here.md) | Check your installation, clone the repo, explore it, understand the architecture | 30 min |
| [01 · Your first container](01-first-container.md) | Images, containers, `run`, `ps`, `stop`, `start`, `rm`, the container lifecycle, interactive shells | 60 min |
| [02 · Ports and configuration](02-ports-and-config.md) | Port mapping, port conflicts, environment variables, configuration that changes behaviour | 60 min |
| [03 · Dockerfiles](03-dockerfiles.md) | Write a Dockerfile step by step, build images, layers, the build cache, `.dockerignore` | 90 min |
| [04 · Data](04-data.md) | Volumes, persistence, a database that survives, bind mounts for live editing | 60 min |
| [05 · Networking](05-networking.md) | Bridge networks, Docker DNS, isolation, and a 3-container app wired by hand | 75 min |
| [06 · Docker Compose](06-compose.md) | The same app with one file and one command; what Compose creates and removes | 60 min |
| [07 · Operate it](07-operate.md) | Logs, `inspect`, `stats`, `top`, memory and CPU limits | 45 min |
| [08 · Secure, optimise, share](08-secure-optimize-share.md) | Non-root users, read-only containers, secrets, smaller images, Docker Hub, safe cleanup | 90 min |
| [09 · Troubleshooting](09-troubleshooting.md) | Three real failures, investigated live; the method you will use for every other problem | 60 min |
| [10 · Capstone](10-capstone.md) | Build, run, verify, break, fix and clean up the complete application | 90 min |
| [11 · Knowledge check](11-knowledge-check.md) | The checklist and self-test questions | 20 min |

## How to use it

1. Read a chapter top to bottom, typing the commands yourself. Copy-paste is fine, but read each one first.
2. Before you look at the explanation under an output box, look at your own terminal and guess what it means.
3. When a chapter says "don't fix it yet", don't. The investigation is the lesson.
4. After each chapter, do the matching labs in [`labs/`](../labs/) and the challenges in [`challenges/`](../challenges/README.md).

Every chapter starts from the repository root, and assumes no containers are running. If you are unsure, run
`docker ps -a` before you start: an empty list is a clean start.

Ready? Open [00 · Start here](00-start-here.md).
