Docker From Zero, part 2 of 2: volumes (data that survives, and the PostgreSQL 18 mount path trap), bind mounts, networks (DNS and isolation), a three-container app by hand and then with Docker Compose, logs, inspect and resource limits (an out-of-memory kill, exit code 137), security basics (non-root, read-only, secrets), image optimization (1.75 GB → 212 MB → 108 MB), registries, three real troubleshooting scenarios, and the capstone: web + API + database + volume with 18 automatic checks. Every terminal shows real output recorded on a fresh Docker engine.

◀️ Part 1 (containers, ports, env vars, Dockerfiles, layers, .dockerignore): {{PART1_LINK}}

💻 The lab (free, open source): https://github.com/sufyanahmadkamboh/sufyan-devops-docker-from-zero
🌐 All my projects: https://sufyanahmadkamboh.github.io/

🧪 Do it yourself (only Docker and Git needed, no cloud account):
1. git clone https://github.com/sufyanahmadkamboh/sufyan-devops-docker-from-zero.git
2. Open tutorial/00-start-here.md and type every command yourself
3. After each chapter, do the matching lab in labs/ (each one has a "Break it" exercise)

🐳 Run the finished capstone from Docker Hub:
cd capstone && cp secrets/db_password.txt.example secrets/db_password.txt && docker compose -f docker-compose.hub.yml up -d

⏱️ Chapters
0:00 Where we are
0:33 Volumes: data that survives
2:07 Bind mounts
2:53 Networking
4:32 Docker Compose
5:57 Logs, inspect, resources
6:39 Security basics
7:20 Image optimization
9:04 Troubleshooting like an engineer
11:38 The capstone
14:00 Safe cleanup
14:38 What you can do now

📊 What you will see (all recorded)
• a file that dies with its container, and a volume that outlives it
• PostgreSQL 18 refusing the old /var/lib/postgresql/data mount
• a bind-mount typo → 403 Forbidden, investigated
• "bad address" on the default network, DNS on your own network, isolation between networks
• docker compose down vs. down -v
• OOMKilled=true, exit code 137
• image size: 1.75 GB → 212 MB → 108 MB
• troubleshooting: Exited (2), host not found in upstream, a missing DB_PASSWORD (exit code 3)
• capstone verify.sh: all 18 checks passed, including data surviving down + up

#Docker #DockerCompose #DevOps
