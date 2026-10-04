# Docker From Zero · project summary

**What:** a complete, hands-on Docker learning lab for absolute beginners. You clone it and work through it on your
own computer, from `docker --version` to a hardened three-container application started with `docker compose up -d`.

**Problem:** beginners learn commands without understanding them, never see failures until they hit real ones, follow
outdated guides (for example the pre-PostgreSQL-18 volume path), and debug by guessing.

**Contents**
- 23 concept lessons (`docs/`), a 12-chapter guided tutorial (`tutorial/`), 18 hands-on labs (`labs/`)
- 10 deliberate failure scenarios with full investigations (`troubleshooting/`), 19 challenges with hidden solutions
- Capstone: nginx (non-root) → Python API (non-root, read-only, 256 MiB / 0.5 CPU limit) → PostgreSQL 18 on a named
  volume; frontend and backend networks so the web container cannot reach the database; the database password as a
  Compose secret file; health checks with `depends_on: service_healthy`; `verify.sh` runs 18 checks, including data
  surviving `docker compose down` + `up`
- Study guide PDF, glossary, 25 interview questions, a 2-part video walkthrough

**Engineering details**
- `tests/mdrun.py` executes every bash block in every lesson on a clean Docker engine (with annotations for
  expected failures, required output and retries) and writes the real output back into the docs; GitHub Actions runs
  all lessons on fresh Linux machines on every change and weekly
- Image optimization in the lab (same app): 1.75 GB → 212 MB → 108 MB (multi-stage Alpine)
- Current behaviour covered: Docker 29 image list layout, Compose v5, PostgreSQL 18 data path

**Tech:** Docker Engine 29, Docker Compose, nginx, Python (Flask, gunicorn), PostgreSQL 18, Bash, GitHub Actions.

**Links:** https://github.com/sufyanahmadkamboh/sufyan-devops-docker-from-zero · https://sufyanahmadkamboh.github.io/
