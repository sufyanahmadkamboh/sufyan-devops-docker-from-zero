# Learning roadmap

Work from top to bottom. Each stage lists the guided **tutorial** chapter, the hands-on **lab**, the **concept lesson**
and the **challenges** that belong together. Time estimates are for a first pass, typing every command yourself.

```text
Stage 1   First container            ┐
Stage 2   Docker CLI                 │  PART 1 · Containers                ~3 h
Stage 3   Container lifecycle        │
Stage 4   Port mapping               │
Stage 5   Environment variables      ┘
Stage 6   Dockerfile                 ┐
Stage 7   Layers and cache           │  PART 2 · Images                    ~2.5 h
Stage 8   .dockerignore              ┘
Stage 9   Volumes                    ┐
Stage 10  Bind mounts                │  PART 3 · Data and networks         ~3 h
Stage 11  Networking                 │
Stage 12  Multi-container by hand    ┘
Stage 13  Docker Compose             ┐
Stage 14  Logs, inspect, resources   │
Stage 15  Security basics            │  PART 4 · Run it like an engineer   ~4 h
Stage 16  Image optimization         │
Stage 17  Registries and Docker Hub  │
Stage 18  Safe cleanup               ┘
Stage 19  Troubleshooting lab        ┐
Stage 20  Challenges                 │  PART 5 · Prove it                  ~4 h
Stage 21  Capstone                   │
Stage 22  Knowledge check            ┘
```

| Stage | Tutorial (guided) | Lab (hands-on) | Lesson (concepts) |
|---|---|---|---|
| 1 First container | [01](tutorial/01-first-container.md) | [labs/01](labs/01-first-container/README.md) | [docs/01](docs/01-docker-introduction.md), [03](docs/03-images.md), [04](docs/04-containers.md) |
| 2 Docker CLI | [01](tutorial/01-first-container.md) | [labs/02](labs/02-docker-cli/README.md) | [docs/05](docs/05-docker-cli.md) |
| 3 Container lifecycle | [01](tutorial/01-first-container.md) | [labs/03](labs/03-container-lifecycle/README.md) | [docs/06](docs/06-container-lifecycle.md) |
| 4 Port mapping | [02](tutorial/02-ports-and-config.md) | [labs/04](labs/04-port-mapping/README.md) | [docs/07](docs/07-ports.md) |
| 5 Environment variables | [02](tutorial/02-ports-and-config.md) | [labs/05](labs/05-environment-variables/README.md) | [docs/08](docs/08-environment-variables.md) |
| 6 Dockerfile | [03](tutorial/03-dockerfiles.md) | [labs/06](labs/06-first-dockerfile/README.md) | [docs/09](docs/09-dockerfile.md) |
| 7 Layers and cache | [03](tutorial/03-dockerfiles.md) | [labs/07](labs/07-layers-and-cache/README.md) | [docs/10](docs/10-image-layers.md) |
| 8 .dockerignore | [03](tutorial/03-dockerfiles.md) | [labs/08](labs/08-dockerignore/README.md) | [docs/11](docs/11-dockerignore.md) |
| 9 Volumes | [04](tutorial/04-data.md) | [labs/09](labs/09-volumes/README.md) | [docs/12](docs/12-volumes.md) |
| 10 Bind mounts | [04](tutorial/04-data.md) | [labs/10](labs/10-bind-mounts/README.md) | [docs/13](docs/13-bind-mounts.md) |
| 11 Networking | [05](tutorial/05-networking.md) | [labs/11](labs/11-networking/README.md) | [docs/14](docs/14-networking.md) |
| 12 Multi-container | [05](tutorial/05-networking.md) | [labs/12](labs/12-multi-container/README.md) | [docs/14](docs/14-networking.md) |
| 13 Docker Compose | [06](tutorial/06-compose.md) | [labs/13](labs/13-docker-compose/README.md) | [docs/15](docs/15-docker-compose.md) |
| 14 Logs, inspect, resources | [07](tutorial/07-operate.md) | [labs/14](labs/14-logs-inspect-resources/README.md) | [docs/16](docs/16-logs-and-debugging.md), [17](docs/17-docker-inspect.md), [18](docs/18-resource-management.md) |
| 15 Security basics | [08](tutorial/08-secure-optimize-share.md) | [labs/15](labs/15-security/README.md) | [docs/19](docs/19-security-basics.md) |
| 16 Image optimization | [08](tutorial/08-secure-optimize-share.md) | [labs/16](labs/16-image-optimization/README.md) | [docs/20](docs/20-image-optimization.md) |
| 17 Docker Hub | [08](tutorial/08-secure-optimize-share.md) | [labs/17](labs/17-docker-hub/README.md) | [docs/21](docs/21-docker-hub.md) |
| 18 Safe cleanup | [08](tutorial/08-secure-optimize-share.md) | [labs/18](labs/18-cleanup/README.md) | [docs/05](docs/05-docker-cli.md) |
| 19 Troubleshooting | [09](tutorial/09-troubleshooting.md) | [troubleshooting/](troubleshooting/README.md) | [docs/22](docs/22-troubleshooting.md) |
| 20 Challenges | | [challenges/](challenges/README.md) | |
| 21 Capstone | [10](tutorial/10-capstone.md) | [capstone/](capstone/README.md) | [docs/23](docs/23-capstone.md) |
| 22 Knowledge check | [11](tutorial/11-knowledge-check.md) | | [CHECKLIST.md](CHECKLIST.md) |

After every stage, try the matching section of [challenges/README.md](challenges/README.md) before moving on.

## How to know where you are

- **Where am I?** The stage table above, and the "Next" link at the bottom of every page.
- **What have I learned?** Tick the lines in [CHECKLIST.md](CHECKLIST.md) as you go.
- **What should I do next?** Follow the next row. If a stage felt hard, do its challenges before moving on.

## After this course

Docker is the base for most DevOps tools you will meet next: CI pipelines build and push images, Kubernetes runs
containers across many machines, and cloud services run the same images. None of that is needed here, but everything
you practise in this lab carries over directly.
