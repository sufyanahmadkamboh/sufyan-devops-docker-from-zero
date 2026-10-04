Docker From Zero, part 1 of 2: learn Docker by using it, breaking it and fixing it. We start at docker --version and run, inspect, stop and remove containers, explain why a container stops, publish ports, configure containers with environment variables, and write a Dockerfile one instruction at a time. Then layers and the build cache (bad order vs. good order), and .dockerignore (50 MB of build context, and a password that ended up inside an image). Every terminal shows real output recorded on a fresh Docker engine.

▶️ Part 2 (volumes, networks, Compose, security, optimization, troubleshooting, capstone): {{PART2_LINK}}

💻 The lab (free, open source): https://github.com/sufyanahmadkamboh/sufyan-devops-docker-from-zero
🌐 All my projects: https://sufyanahmadkamboh.github.io/

🧪 Do it yourself (only Docker and Git needed, no cloud account):
1. git clone https://github.com/sufyanahmadkamboh/sufyan-devops-docker-from-zero.git
2. Open tutorial/00-start-here.md and type every command yourself
3. After each chapter, do the matching lab in labs/ (each one has a "Break it" exercise)

⏱️ Chapters
{{CHAPTERS}}

📊 What you will see (all recorded)
• docker run hello-world, nginx, logs, exec: process 1 is the main process
• docker run ubuntu exits immediately, and why
• a wrong port mapping (-p 8082:8080) and "port is already allocated", investigated
• PostgreSQL refusing to start without POSTGRES_PASSWORD
• ModuleNotFoundError: the image only contains what the Dockerfile puts in it
• bad layer order re-runs pip install; good order: CACHED
• build context 50.02 MB → 63 B with .dockerignore

#Docker #DevOps #Containers
