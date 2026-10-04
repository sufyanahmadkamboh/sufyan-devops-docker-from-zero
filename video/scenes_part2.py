"""Docker From Zero, part 2 of 2: data, networks, Compose, operations, troubleshooting and the capstone.

Every terminal in this video shows real output, recorded while the tutorial chapters ran on a fresh Docker engine
(tests/mdrun.py --record). rec() looks the commands up in video/recordings/.
"""

from __future__ import annotations

from components import arrow, box, card, checklist, code, grid, label, notes, svg, terminal, tile
from recordings import rec


def S(say: str, hl: tuple[int, int] | None = None, tts: str | None = None) -> dict:
    return {"say": say, "hl": hl, "tts": tts}


def shot(s: int, src: str, alt: str, style: str = "height:640px;width:auto") -> str:
    return f'<img class="shot st" data-s="{s}" src="../../assets/{src}" alt="{alt}" style="{style}">'


SCENES: list[dict] = []


def no_command_column(lines):
    """docker compose ps is too wide for a slide: leave out the COMMAND column (nothing else changes)."""
    import re
    out = []
    for s, text, kind in lines:
        if kind != "cmd":
            text = re.sub(r'"[^"]*"\s+', "", text) if '"' in text else re.sub(r"COMMAND\s+", "", text)
        out.append((s, text, kind))
    return out


def scene(chapter, kicker, title, body, steps, layout="full"):
    SCENES.append({"chapter": chapter, "kicker": kicker, "title": title, "body": body, "steps": steps, "layout": layout})


T4, T5, T6, T7, T8, T9, T10 = ("tutorial/04-data.md", "tutorial/05-networking.md", "tutorial/06-compose.md",
                               "tutorial/07-operate.md", "tutorial/08-secure-optimize-share.md",
                               "tutorial/09-troubleshooting.md", "tutorial/10-capstone.md")
CAP = "capstone/README.md"

# ---------------------------------------------------------------- 1. Hook
scene("Where we are", "Docker From Zero · part 2 of 2", "From one container to a real application", grid([
    card(0, "✅", "Part 1", "images, containers, ports, env vars, Dockerfiles, layers, .dockerignore", "ok"),
    card(1, "💾", "Data", "volumes and bind mounts: what survives, and what does not", "blue"),
    card(1, "🌐", "Networks", "how containers find each other, and how to keep them apart", "blue"),
    card(2, "🧩", "Compose", "a three-container app with one file and one command", "blue"),
    card(2, "🛡️", "Operate, secure, optimize, share", "logs, inspect, limits, non-root, 16× smaller images, registries", "amber"),
    card(3, "🔧", "Troubleshoot + capstone", "real failures, investigated; then the final project", "bad"),
], cols=2), [
    S("Welcome to part two. In part one you learned images, containers, ports, configuration and Dockerfiles."),
    S("Now we make data survive, and we connect containers with networks."),
    S("We run a three container application, first by hand, then with Docker Compose. Then we operate it, secure it, "
      "make its image sixteen times smaller, and share it through a registry."),
    S("Finally, real troubleshooting, and the capstone: everything together, the way you would build it at work."),
])

# ---------------------------------------------------------------- 2. Volumes
scene("Volumes: data that survives", "Why data disappears", "A container's files die with the container", svg(
    box(0, 0, 60, 760, 300, "📦", "container writer", ["its own writable layer", "/data.txt  ← written here"], "blue")
    + label(1, 380, 420, "docker rm writer  →  the layer is gone, and the file with it", 26, "bad", "middle", 700)
    + box(2, 940, 60, 780, 300, "💾", "volume notes", ["storage managed by Docker", "outside every container"], "ok", "#0f2a22")
    + arrow(2, 1330, 365, 1330, 470)
    + box(2, 940, 475, 780, 200, "📦", "any container -v notes:/data", ["sees the same files"], "ok", "#0f2a22")
), [
    S("Every container has its own writable layer. Write a file into it, and it lives exactly as long as the container."),
    S("docker rm, and the file is gone. That is fine for a web server, and a disaster for a database.",
      tts="docker R M, and the file is gone. That is fine for a web server, and a disaster for a database."),
    S("A volume is storage managed by Docker, outside every container. Mount it with dash v, name colon path, and any "
      "container that mounts it sees the same files."),
])

scene(None, "Recorded · tutorial chapter 04", "Prove it", terminal(
    rec(T4, "docker run --name writer", tones={"important data": "ok"})
    + rec(T4, "docker rm writer", step=1, tones={"can't open": "bad"})
    + rec(T4, "docker volume create notes", step=2)
    + rec(T4, "echo \"written by the first container\"", step=2, width=120)
    + rec(T4, "cat /data/message.txt", step=3, tones={"written by the first container": "ok"}),
    "bash (recorded)"), [
    S("Let's prove it. A container writes important data into a file, and reads it back."),
    S("Remove the container and start a new one: can't open data dot txt. The data died with the container."),
    S("Now with a volume. Create it, and let a container with dash dash rm write a message into it. That container is "
      "deleted the moment it finishes.",
      tts="Now with a volume. Create it, and let a container with dash dash R M write a message into it. That container is "
          "deleted the moment it finishes."),
    S("A brand new container mounts the same volume, and the message is still there. The data outlived its container."),
])

scene(None, "Recorded · a real database", "PostgreSQL 18 on a named volume", terminal(
    rec(T4, "SELECT * FROM notes;", nth=0, tones={"I must survive": "ok"},
        cmd="docker exec db psql -U postgres -c \"SELECT * FROM notes;\"    # after docker rm -f db + a new container")
    + [(1, "# an older tutorial mounts /var/lib/postgresql/data:", "dim")]
    + rec(T4, "grep -A 3 \"in 18+\"", step=1, cmd="docker logs olddb", tones={"Error": "bad"}),
    "bash (recorded)"), [
    S("Now a real database. PostgreSQL 18, with a named volume. We insert a row, delete the container completely, start "
      "a new one on the same volume, and the row is still there: I must survive.",
      tts="Now a real database. postgres Q L 18, with a named volume. We insert a row, delete the container completely, start "
          "a new one on the same volume, and the row is still there: I must survive."),
    S("And a trap that will catch you, because most tutorials on the internet are older than PostgreSQL 18. They mount "
      "the volume at var lib postgresql data. Version 18 refuses to start, with this error. The new place is var lib "
      "postgresql, one level up. Read the error. It tells you exactly that.",
      tts="And a trap that will catch you, because most tutorials on the internet are older than postgres Q L 18. They mount "
          "the volume at var lib postgres Q L data. Version 18 refuses to start, with this error. The new place is var lib "
          "postgres Q L, one level up. Read the error. It tells you exactly that."),
])

scene("Bind mounts", "Recorded · live editing", "Your folder, inside the container", terminal(
    rec(T4, "curl -s http://localhost:8080 | grep h1", nth=0, tones={"h1": "ok"},
        cmd="docker run -d --name site -p 8080:80 -v \"$(pwd)/examples/nginx/site:/usr/share/nginx/html:ro\" nginx:1.30-alpine\ncurl -s http://localhost:8080 | grep h1")
    + rec(T4, "curl -s http://localhost:8080 | grep Edited", step=1, tones={"Edited": "ok"},
          cmd="echo '<p>Edited on my computer, served by the container!</p>' >> examples/nginx/site/index.html\ncurl -s http://localhost:8080 | grep Edited")
    + [(2, "# a typo in the path: examples/nginx/sitee", "dim")]
    + rec(T4, "grep -o '403 Forbidden'", step=2, tones={"403": "bad"})
    + rec(T4, "docker exec site ls -la /usr/share/nginx/html", step=3, tones={"total 4": "warn"}),
    "bash (recorded)"), [
    S("A bind mount shows a folder of your computer inside a container. Here, nginx serves the site folder of the "
      "repository, mounted read only.",
      tts="A bind mount shows a folder of your computer inside a container. Here, engine x serves the site folder of the "
          "repository, mounted read only."),
    S("Edit the file on your computer, and the container serves the change immediately. No rebuild. That is the local "
      "development workflow."),
    S("Now a typo in the path: sitee, with two e's. The container starts happily, and returns 403 Forbidden.",
      tts="Now a typo in the path: site with two E's. The container starts happily, and returns 403 Forbidden."),
    S("Investigate: list the folder inside the container. It is empty. With dash v, Docker silently created an empty "
      "folder for the path that did not exist. Volumes are for data Docker manages; bind mounts are for your files. "
      "And always double check the path."),
])

# ---------------------------------------------------------------- 3. Networking
scene("Networking", "How containers find each other", "Names work only on your own networks", svg(
    box(0, 0, 40, 800, 330, "🔌", "default network \"bridge\"", ["containers get IP addresses", "no name resolution",
                                                                 "wget http://web  →  bad address"], "bad", "#2a1520")
    + box(1, 900, 40, 820, 330, "🌐", "your network: docker network create labnet",
          ["Docker's built-in DNS", "every container name is a host name", "wget http://web2  →  works"], "ok", "#0f2a22")
    + box(2, 900, 430, 820, 230, "🧱", "a different network: othernet", ["cannot reach labnet, cannot even resolve its names"], "amber", "#2b2410")
    + label(2, 30, 520, "Isolation is a feature:", 28, "amber", "start", 800)
    + label(2, 30, 565, "your database should not be", 26, "amber", "start", 700)
    + label(2, 30, 605, "reachable from everything.", 26, "amber", "start", 700)
), [
    S("How do containers talk to each other? On Docker's default network, called bridge, every container gets an IP "
      "address, but there is no name resolution. Ask for the name web, and you get bad address.",
      tts="How do containers talk to each other? On Docker's default network, called bridge, every container gets an I P "
          "address, but there is no name resolution. Ask for the name web, and you get bad address."),
    S("Create your own network, and Docker runs a small DNS server for it. Every container name becomes a host name. "
      "That is how a web container finds its API, and an API finds its database.",
      tts="Create your own network, and Docker runs a small D N S server for it. Every container name becomes a host name. "
          "That is how a web container finds its A P I, and an A P I finds its database."),
    S("And containers on different networks cannot reach each other, or even resolve each other's names. That is "
      "isolation, and it is a security feature."),
])

scene(None, "Recorded · tutorial chapter 05", "bad address, then DNS, then isolation", terminal(
    rec(T5, "docker run --rm busybox:1.37 wget -qO- -T 3 http://web", grep="bad address", tones={"bad address": "bad"})
    + rec(T5, "wget -qO- -T 3 http://web2 | grep title", step=1, nth=0, tones={"Welcome": "ok"})
    + rec(T5, "docker exec client wget -qO- -T 3 http://web2", step=2, nth=0, tones={"bad address": "bad"})
    + rec(T5, "docker network connect labnet client", step=3)
    + rec(T5, "docker exec client wget -qO- -T 3 http://web2 | grep title", step=3, tones={"Welcome": "ok"}),
    "bash (recorded)"), [
    S("Recorded. On the default network: wget, bad address."),
    S("On our own network, labnet: the name web two resolves, and nginx answers.",
      tts="On our own network, labnet: the name web two resolves, and engine x answers."),
    S("A container on another network, othernet, cannot even resolve web two."),
    S("Connect it to labnet as well, a container can be on several networks at once, and now it works."),
])

scene(None, "Recorded · the message board, by hand", "Browser → web → api → db → volume", terminal(
    [(0, "$ docker network create board-net", "cmd"),
     (0, "$ docker run -d --name db  --network board-net -v board-data:/var/lib/postgresql -e POSTGRES_PASSWORD=... postgres:18-alpine", "cmd"),
     (0, "$ docker run -d --name api --network board-net -e DB_HOST=db -e DB_PASSWORD=... board-api", "cmd"),
     (0, "$ docker run -d --name web --network board-net -p 8080:80 board-web", "cmd")]
    + rec(T5, "curl -s http://localhost:8080/api/health", step=1, nth=0, tones={"ok": "ok"})
    + rec(T5, "curl -s http://localhost:8080/api/info", step=1, width=130, tones={"greeting": "ok"})
    + rec(T5, "curl -s http://localhost:8080/api/messages", step=2, nth=0, width=130),
    "bash (recorded, simplified)"), [
    S("Now the application this course is built around: a tiny message board. A web container with nginx, an API "
      "container written in Python, and a PostgreSQL database with its data on a volume. Four commands: a network, "
      "then the three containers, each with its own settings.",
      tts="Now the application this course is built around: a tiny message board. A web container with engine x, an A P I "
          "container written in Python, and a postgres Q L database with its data on a volume. Four commands: a network, "
          "then the three containers, each with its own settings."),
    S("And it works: the API reports the database as healthy, and info shows which container answered.",
      tts="And it works: the A P I reports the database as healthy, and info shows which container answered."),
    S("Messages are stored in the database. It works, but look at those commands: long, easy to get wrong, and the start "
      "order matters. There must be a better way."),
])

# ---------------------------------------------------------------- 4. Compose
COMPOSE = """services:
  web:
    build: ./web
    ports:
      - "8080:80"
    depends_on: [api]
  api:
    build: ./api
    environment:
      DB_HOST: db          # the service name is its DNS name
      DB_PASSWORD: board-lab-password
    depends_on: [db]
  db:
    image: postgres:18-alpine
    volumes:
      - db-data:/var/lib/postgresql
volumes:
  db-data:"""
scene("Docker Compose", "examples/multi-container-app/docker-compose.yml (shortened)", "The same app: one file, one command",
      code("docker-compose.yml", COMPOSE, "yaml", 24) + notes([
          (0, "services", "one entry per container"),
          (1, "build / image", "build from a folder, or pull"),
          (2, "environment", "the same -e settings"),
          (3, "volumes", "the named volume, declared once"),
          (4, "one command", "docker compose up -d --build"),
      ]), [
    S("Docker Compose describes the whole application in one file. Under services, one entry per container: web, api "
      "and db.", hl=(1, 1)),
    S("Each service either builds an image from a folder, or uses an existing image. Ports and the start order with "
      "depends on.", hl=(2, 6)),
    S("Environment variables, exactly like dash e. And the service name db is also its DNS name on the network Compose "
      "creates.", hl=(9, 11), tts="Environment variables, exactly like dash e. And the service name D B is also its D N S name on the network Compose "
                                  "creates."),
    S("The named volume is declared once, at the bottom, and mounted by the database.", hl=(15, 18)),
    S("And then one command starts everything: docker compose up dash d dash dash build."),
], layout="code")

scene(None, "Recorded · tutorial chapter 06", "What Compose creates", terminal(
    rec(T6, "docker compose ps", nth=0, width=150, tones={"Up": "ok"})
    + rec(T6, "docker network ls --filter name=multi-container-app", step=1)
    + rec(T6, "docker volume ls --filter name=multi-container-app", step=1, nth=0)
    + rec(T6, "curl -s http://localhost:8080/api/health", step=2, nth=0, tones={"ok": "ok"}),
    "bash (recorded)"), [
    S("docker compose ps: three containers, named after the project, which is the folder name, and the service."),
    S("Compose also created a network, multi container app underscore default, and the volume, with the project name in front."),
    S("And the application works, exactly like the hand made version, from one file you can commit to Git."),
])

scene(None, "Recorded · down vs. down -v", "The most dangerous two letters in Compose", terminal(
    rec(T6, "docker compose down", nth=0, tail=2)
    + rec(T6, "docker volume ls --filter name=multi-container-app", step=1, nth=1, tones={"db-data": "ok"})
    + rec(T6, "curl -s http://localhost:8080/api/messages", step=1, width=130, tones={"Written in chapter 6": "ok"})
    + rec(T6, "docker compose down -v", step=2, tail=2, tones={"Volume": "bad"})
    + rec(T6, "docker volume ls --filter name=multi-container-app", step=2, nth=2),
    "bash (recorded)"), [
    S("docker compose down removes the containers and the network, and keeps the volume."),
    S("So after up again, our message, written in chapter six, is still there."),
    S("docker compose down dash v also deletes the volumes. The data is gone, for good. Two letters. Use them only when "
      "you really want an empty database."),
])

# ---------------------------------------------------------------- 5. Operate
scene("Logs, inspect, resources", "Recorded · tutorial chapter 07", "Limits, and what happens when you hit them", terminal(
    rec(T7, "docker stats --no-stream limited", tones={"256MiB": "warn"})
    + rec(T7, "docker run --name oom --memory=64m", step=1, drop=r"Unable|Pulling|Digest|Status|Download|Pull ")
    + rec(T7, "docker ps -a --filter name=oom", step=1, width=150, tones={"137": "bad"})
    + rec(T7, "docker inspect oom --format", step=2, tones={"OOMKilled=true": "bad"}),
    "bash (recorded)"), [
    S("Operating containers means knowing what they use. docker stats shows CPU, memory, network and disk per "
      "container. This one was started with dash dash memory 256 megabytes and half a CPU, and the limit column shows it.",
      tts="Operating containers means knowing what they use. docker stats shows C P U, memory, network and disk per "
          "container. This one was started with dash dash memory 256 megabytes and half a C P U, and the limit column shows it."),
    S("Now a Python program that wants 256 megabytes, in a container limited to 64. It is killed: Exited, 137.",
      tts="Now a Python program that wants 256 megabytes, in a container limited to 64. It is killed: Exited, 1 3 7."),
    S("docker inspect confirms it: OOMKilled true. 137 means killed, and OOMKilled means by the kernel, for using too "
      "much memory. When you see 137 at work, this is the first thing to check.",
      tts="docker inspect confirms it: O O M killed, true. 1 3 7 means killed, and O O M killed means by the kernel, for using too "
          "much memory. When you see 1 3 7 at work, this is the first thing to check."),
])

# ---------------------------------------------------------------- 6. Security
scene("Security basics", "Recorded · tutorial chapter 08", "Least privilege, in four commands", terminal(
    rec(T8, "docker run --rm simple-app:root whoami", tones={"root": "bad"})
    + rec(T8, "docker run --rm simple-app:1.0 id", step=0, tones={"10001": "ok"})
    + rec(T8, "touch /usr/local/bin/hacked", step=1, tones={"Permission denied": "ok"})
    + rec(T8, "--read-only simple-app:1.0 touch", step=1, tones={"Read-only": "ok"})
    + rec(T8, "--cap-drop ALL", step=2, tones={"not permitted": "ok"})
    + rec(T8, "docker inspect leaky --format", step=3, tones={"DB_PASSWORD": "bad"}),
    "bash (recorded)"), [
    S("Security basics. By default, a container runs as root. Our final Dockerfile adds a user, and USER switches to it: "
      "id shows user ten thousand and one, not root.",
      tts="Security basics. By default, a container runs as root. Our final docker file adds a user, and user switches to it: "
          "I D shows user ten thousand and one, not root."),
    S("So the app cannot change system files: permission denied. With dash dash read only, it cannot change any file at all."),
    S("Dash dash cap drop ALL removes the special powers root still has inside a container."),
    S("And remember the password from part one? An environment variable is visible to everyone who can run docker "
      "inspect. The capstone passes the database password as a secret file instead, so it never appears there."),
])

# ---------------------------------------------------------------- 7. Optimization
scene("Image optimization", "Recorded · same app, three Dockerfiles", "1.75 GB → 212 MB → 108 MB", terminal(
    rec(T8, "docker images simple-app", grep=r"IMAGE|:fat|:1\.0 |:multistage",
        tones={"fat": "bad", "multistage": "ok", "simple-app:1.0": "warn"})
    + rec(T8, "docker history simple-app:fat", step=1, grep=r"apt-get update && apt-get ins|pip install -r requirements", width=118, tones={"apt-get": "bad"}),
    "bash (recorded)") + grid([
    tile(2, "🐘", "fat", "1.75 GB", "bad", "full python + build tools + bad order"),
    tile(2, "🥗", "slim", "212 MB", "amber", "slim base, deps first, no cache"),
    tile(3, "🪶", "multi-stage", "108 MB", "ok", "build in stage 1, ship only results"),
], cols=3, gap=18), [
    S("Same application, same code, three Dockerfiles. The typical first attempt: 1.75 gigabytes."),
    S("docker history shows why: the full Python image, plus compilers and tools installed just in case."),
    S("The slim base with a cache friendly order and no pip cache: 212 megabytes. Same app."),
    S("And a multi stage build: stage one has the build tools, stage two copies only the finished result into a small "
      "Alpine image. 108 megabytes, sixteen times smaller than where we started. Smaller images download faster, start "
      "faster, and contain less software that can have vulnerabilities."),
])

scene(None, "Recorded · a registry on your own computer", "build → tag → push → pull → run", terminal(
    rec(T8, "docker tag simple-app:1.0 localhost:5000/simple-app:1.0")
    + rec(T8, "docker push localhost:5000/simple-app:1.0", step=0, tail=2)
    + rec(T8, "curl -s http://localhost:5000/v2/_catalog", step=1, tones={"simple-app": "ok"})
    + rec(T8, "docker rmi localhost:5000/simple-app:1.0", step=2, grep=r"Downloaded newer image|Status:", tones={"Downloaded": "ok"})
    + rec(T8, "curl -s http://localhost:8080/", step=2, cmd="docker run -d --name from-registry -p 8080:5000 localhost:5000/simple-app:1.0\ncurl -s http://localhost:8080/",
          tones={"Hello": "ok"}),
    "bash (recorded)"), [
    S("Images are shared through registries. To practise without any account, run your own: the registry image, on port "
      "5000. Tag the image with the registry's address in its name, and push."),
    S("The registry now lists simple app."),
    S("Delete the local copy, run it again, and Docker pulls it back from the registry. Build, tag, push, pull, run: "
      "that is exactly how images travel from a laptop to a server."),
    S("Docker Hub works the same way, with your user name in front of the image name. The capstone images of this "
      "course are published there, for Intel and for ARM computers like Apple Silicon Macs."),
])

scene(None, "Docker Hub", "The capstone images, published", shot(0, "docker-hub.png", "Docker Hub repository page", "height:640px;width:auto"), [
    S("Here they are on Docker Hub: docker from zero web and API, version 1.0.0, with a description that tells you how to "
      "run the capstone straight from these images. Anyone, anywhere, can now pull and run exactly what we built. "
      "Docker Hub is free for public images.",
      tts="Here they are on Docker Hub: docker from zero web and A P I, version 1 point 0 point 0, with a description that tells you how to "
          "run the capstone straight from these images. Anyone, anywhere, can now pull and run exactly what we built. "
          "Docker Hub is free for public images."),
])

# ---------------------------------------------------------------- 8. Troubleshooting
scene("Troubleshooting like an engineer", "The method", "Observe → Investigate → Root cause → Fix → Verify", checklist([
    (0, "1", "Observe", "what exactly is the symptom? (curl, the browser, docker ps)"),
    (1, "2", "Investigate", "collect evidence: docker ps -a, logs, inspect, exec, network inspect"),
    (2, "3", "Root cause", "one sentence that explains every symptom"),
    (3, "4", "Fix", "change one thing"),
    (4, "5", "Verify", "run the check that failed, again"),
]), [
    S("Now the most important skill in this course: troubleshooting. Not guessing. The repository has ten broken "
      "setups. We will solve three of them, always the same way. First, observe: what exactly is the symptom?"),
    S("Second, investigate. Collect evidence with docker ps dash a, logs, inspect, exec. Before changing anything.",
      tts="Second, investigate. Collect evidence with docker P S dash a, logs, inspect, exec. Before changing anything."),
    S("Third, the root cause: one sentence that explains every symptom you saw."),
    S("Fourth, fix it, by changing one thing."),
    S("And fifth, verify: run the check that failed again. Not it should work now. Proof."),
])

scene(None, "Recorded · troubleshooting/01", "The container exits immediately", terminal(
    rec(T9, "docker ps -a --filter name=ts01", width=150, tones={"Exited (2)": "bad"})
    + rec(T9, "docker logs ts01", step=1, tones={"can't open file": "bad"})
    + rec(T9, "docker run --rm ts01 ls /app", step=2)
    + rec(T9, "grep CMD Dockerfile", step=2, tones={"main.py": "bad"})
    + rec(T9, "curl -s http://localhost:5000/", step=3, nth=0, tones={"Hello": "ok"},
          cmd="docker build -f Dockerfile.fixed -t ts01:fixed . && docker run -d --name ts01 -p 5000:5000 ts01:fixed\ncurl -s http://localhost:5000/"),
    "bash (recorded)"), [
    S("Scenario one. A colleague says: the container does not start. docker ps dash a: Exited with code 2, seconds after starting.",
      tts="Scenario one. A colleague says: the container does not start. docker P S dash a: Exited with code 2, seconds after starting."),
    S("The logs say it directly: python cannot open file app main dot py."),
    S("What is actually in app? List it: app dot py. And the Dockerfile's CMD runs main dot py. Root cause: the command "
      "names a file that does not exist.",
      tts="What is actually in app? List it: app dot py. And the docker file's C M D runs main dot py. Root cause: the command "
          "names a file that does not exist."),
    S("Fix the CMD, rebuild, run, and verify with curl. Fixed, and proven.",
      tts="Fix the C M D, rebuild, run, and verify with curl. Fixed, and proven."),
])

scene(None, "Recorded · troubleshooting/03", "The containers cannot talk to each other", terminal(
    rec(T9, "curl -s --max-time 5 http://localhost:8080/", cmd="curl -s --max-time 5 http://localhost:8080/") +
    [(0, "(no answer: curl exit code 7)", "bad")]
    + rec(T9, "docker compose ps -a", step=1, nth=0, width=150, tones={"Exited (1)": "bad"})
    + rec(T9, "docker compose logs web", step=1, grep="emerg", tones={"host not found": "bad"})
    + rec(T9, "docker inspect ts03-web-1", step=2, tones={"frontend": "warn"})
    + rec(T9, "docker inspect ts03-api-1", step=2, tones={"backend": "warn"}),
    "bash (recorded)"), [
    S("Scenario three. Nothing answers on port 8080."),
    S("docker compose ps: the web container Exited with code 1. Its logs: host not found in upstream api. nginx could "
      "not find the API by name.",
      tts="docker compose P S: the web container Exited with code 1. Its logs: host not found in upstream A P I. engine x could "
          "not find the A P I by name."),
    S("Which networks are they on? web is only on frontend. api is only on backend. They share no network, so the name "
      "api does not exist for web. The fix: put the API on both networks, exactly like the capstone does.",
      tts="Which networks are they on? web is only on frontend. A P I is only on backend. They share no network, so the name "
          "A P I does not exist for web. The fix: put the A P I on both networks, exactly like the capstone does."),
])

scene(None, "Recorded · troubleshooting/06", "HTTP 502, and nothing looks wrong", terminal(
    rec(T9, "-w \"HTTP %{http_code}", tones={"502": "bad"})
    + rec(T9, "docker compose ps -a", step=1, nth=1, width=150, tones={"Exited": "bad"})
    + rec(T9, "docker compose logs api", step=1, grep="ERROR: required", width=150, tones={"ERROR": "bad"})
    + rec(T9, "docker inspect ts06-api-1", step=2, tones={"DB_": "warn"}),
    "bash (recorded)"), [
    S("Scenario six. The page loads, but every API call returns 502, bad gateway: nginx is up, but nothing behind it answers.",
      tts="Scenario six. The page loads, but every A P I call returns 502, bad gateway: engine x is up, but nothing behind it answers."),
    S("The api container Exited with code 3. Its logs say it in one line: required setting DB_PASSWORD is missing. "
      "The application was written to fail fast, with a clear message. Write yours the same way.",
      tts="The A P I container Exited with code 3. Its logs say it in one line: required setting D B password is missing. "
          "The application was written to fail fast, with a clear message. Write yours the same way."),
    S("docker inspect lists the variables the container really got: host, name and user. No password. Add it, recreate, "
      "and verify. Three scenarios, three root causes, and not one guess.",
      tts="docker inspect lists the variables the container really got: host, name and user. No password. Add it, recreate, "
          "and verify. Three scenarios, three root causes, and not one guess."),
])

# ---------------------------------------------------------------- 9. Capstone
scene("The capstone", "Everything together", "Built the way you would build it at work", svg(
    box(0, 0, 20, 360, 150, "🌐", "Browser", ["localhost:8080 only"], "blue")
    + arrow(0, 365, 95, 455, 95)
    + box(1, 460, 0, 1260, 300, "🔵", "frontend network", [], "blue", "#111c2e")
    + box(1, 500, 70, 520, 200, "🌐", "web", ["nginx, non-root, port 8080", "health check"], "ok", "#0f2a22")
    + box(1, 1100, 70, 580, 200, "🐍", "api", ["non-root, read-only", "256 MiB, 0.5 CPU, health check"], "ok", "#0f2a22")
    + box(2, 1060, 340, 660, 340, "🟣", "backend network", [], "violet", "#161130")
    + box(2, 1100, 420, 580, 200, "🐘", "db", ["PostgreSQL 18", "password from a secret file"], "ok", "#0f2a22")
    + arrow(2, 1390, 275, 1390, 415)
    + box(3, 460, 420, 520, 200, "💾", "volume capstone_db-data", ["survives docker compose down"], "amber", "#2b2410")
    + arrow(3, 1095, 520, 985, 520)
    + label(4, 230, 660, "web cannot even resolve db", 26, "bad", "middle", 400)
), [
    S("The capstone is the same message board, built the way you would build it at work. Only the web container is "
      "published, on port 8080."),
    S("web and api share a frontend network. Both run as normal users, with health checks. The API's filesystem is read "
      "only, and it has memory and CPU limits.",
      tts="web and A P I share a frontend network. Both run as normal users, with health checks. The A P I's filesystem is read "
          "only, and it has memory and C P U limits."),
    S("The database is on a separate backend network, with the API, and its password comes from a secret file.",
      tts="The database is on a separate backend network, with the A P I, and its password comes from a secret file."),
    S("Its data lives on a named volume."),
    S("And because web and db share no network, the web container cannot even resolve the database's name."),
])

scene(None, "Recorded · tutorial chapter 10", "Up, healthy, isolated, non-root", '<div style="zoom:0.86">' + terminal(
    no_command_column(rec(T10, "docker compose ps", nth=0, width=150, tones={"healthy": "ok"}))
    + rec(T10, "docker compose exec -T web wget", step=1, tones={"bad address": "ok"})
    + rec(T10, "docker inspect capstone-api-1 --format 'user=", step=2, tones={"readonly=true": "ok"})
    + rec(T10, "grep DB_", step=2, nth=0, tones={"FILE": "ok"}),
    "bash (recorded)") + "</div>", [
    S("One command: docker compose up dash d. The database and the API are already healthy, and the web container's "
      "health check is just starting. Compose waited for each health check before starting the next service."),
    S("From the web container, the database is a bad address. Isolation, verified."),
    S("The API runs as user app with a read only filesystem, and its database setting is a password file, not a password. "
      "docker inspect has nothing to leak.",
      tts="The A P I runs as user app with a read only filesystem, and its database setting is a password file, not a password. "
          "docker inspect has nothing to leak."),
])

scene(None, "In the browser", "The message board, running on the capstone", shot(0, "message-board.png", "The message board app", "height:640px;width:auto"), [
    S("And here it is in a browser. The page comes from the web container, the info line from one of the API's "
      "processes, which shows the container's short ID, and the messages from PostgreSQL. These four messages survived "
      "docker compose down, when not a single container was left, because they live on the volume.",
      tts="And here it is in a browser. The page comes from the web container, the info line from one of the A P I's "
          "processes, which shows the container's short I D, and the messages from postgres Q L. These four messages survived "
          "docker compose down, when not a single container was left, because they live on the volume."),
])

VERIFY = rec(CAP, "./verify.sh --persistence", width=96, drop=r"^$", tones={"PASS": "ok", "FAIL": "bad", "All checks passed": "ok"})
_half = next(i for i, line in enumerate(VERIFY) if line[1].startswith("4."))
scene(None, "Recorded · capstone/verify.sh --persistence", "18 checks. Proof, not hope.",
      '<div style="display:grid;grid-template-columns:1fr 1fr;gap:18px;zoom:0.86">'
      + terminal(VERIFY[:_half], "bash (recorded) · part 1") + terminal(VERIFY[_half:], "bash (recorded) · part 2") + "</div>", [
    S("And then we prove it. verify dot sh runs eighteen checks, the way an engineer would check a system by hand: "
      "containers healthy, only the web port published, the application end to end, both networks, non root users, the "
      "read only filesystem, no password in the environment, the memory limit, and finally docker compose down and up "
      "again, to prove that the data survived. All checks passed.",
      tts="And then we prove it. verify dot S H runs eighteen checks, the way an engineer would check a system by hand: "
          "containers healthy, only the web port published, the application end to end, both networks, non root users, the "
          "read only filesystem, no password in the environment, the memory limit, and finally docker compose down and up "
          "again, to prove that the data survived. All checks passed."),
])

scene(None, "Recorded · break the capstone", "Stop the database. Watch. Fix. Verify.", terminal(
    rec(T10, "docker compose stop db", tail=1)
    + rec(T10, "curl -s http://localhost:8080/api/health", step=1, nth=1, width=130, tones={"error": "bad"})
    + rec(T10, "docker compose ps -a", step=1, width=150, tones={"Exited": "bad"})
    + rec(T10, "docker compose start db", step=2, tail=1)
    + rec(T10, "curl -s http://localhost:8080/api/health", step=2, nth=2, tones={"ok": "ok"}),
    "bash (recorded)"), [
    S("One last break. Stop the database."),
    S("The API still answers, but with status error and HTTP 503, and docker compose ps shows the database Exited. "
      "Root cause: the database is not running.",
      tts="The A P I still answers, but with status error and H T T P 503, and docker compose P S shows the database Exited. "
          "Root cause: the database is not running."),
    S("Start it, and verify: database ok. The messages are still there, because they live on the volume, not in a container."),
])

# ---------------------------------------------------------------- 10. Cleanup + end
scene("Safe cleanup", "Recorded · docker system df", "Read before you prune", terminal(
    rec(T8, "docker system df", tones={"Images": "warn", "Build Cache": "warn"})
    + [(1, "$ docker system prune -a --volumes     # ⚠ every unused image, all build cache, and every unused volume (= data)", "bad")],
    "bash (recorded)") + grid([
    card(2, "✅", "Safe habits", "docker system df first · prune with --filter · docker compose down (no -v) · name your volumes", "ok"),
], cols=1), [
    S("Docker uses disk space: images, build cache, volumes. docker system df shows how much, and how much you could "
      "reclaim."),
    S("And here is the command you will find in many blog posts: docker system prune dash a dash dash volumes. It "
      "deletes every unused image, all build cache, and every volume no container uses right now. Including the database "
      "of a project you stopped yesterday."),
    S("So: look first with docker system df, prune with filters, and treat anything with volumes in it as deleting data. "
      "The cleanup lab explains each prune command."),
])

scene("What you can do now", "Knowledge check", "You built it, broke it, fixed it", grid([
    card(0, "📦", "Containers and images", "run, inspect, logs, exec, lifecycle, ports, env vars"),
    card(0, "📝", "Images", "Dockerfiles, layers, cache, .dockerignore, multi-stage, registries"),
    card(1, "💾🌐", "Data and networks", "volumes, bind mounts, DNS, isolation"),
    card(1, "🧩", "Compose", "a multi-container app from one file"),
    card(2, "🛡️", "Operate and secure", "limits, OOM, non-root, read-only, secrets"),
    card(2, "🔧", "Troubleshoot", "observe, investigate, root cause, fix, verify"),
    card(3, "📚", "Keep going", "18 labs · 19 challenges · 10 failures · study guide PDF", "ok"),
], cols=2), [
    S("Let's look back. You can run, inspect and debug containers, and configure them with ports and environment variables."),
    S("You can write Dockerfiles that build fast, stay small and contain no secrets, and share images through a registry."),
    S("You can keep data with volumes, connect containers with networks and isolate them, run a multi container "
      "application with Compose, limit and secure it, and troubleshoot it without guessing."),
    S("Now it is your turn. Everything is in the repository: eighteen labs, nineteen challenges, ten troubleshooting "
      "scenarios, the capstone, and a study guide as a PDF. Clone it, type every command yourself, break things, and "
      "fix them. When you have ticked the knowledge checklist, you can honestly say: I understand Docker, because I "
      "actually used it, broke it, fixed it, and built something with it. Thanks for watching."),
])


# ---------------------------------------------------------------- production: title card, end card, sound cues
from production import package  # noqa: E402

package(SCENES, 2, "Data, networks, Compose and the capstone", ["volumes", "networks", "Compose", "security", "capstone"], {
    "Prove it": {1: "error", 3: "success"},
    "PostgreSQL 18 on a named volume": {0: "success", 1: "error"},
    "Your folder, inside the container": {2: "error"},
    "bad address, then DNS, then isolation": {0: "error", 1: "success", 3: "success"},
    "Limits, and what happens when you hit them": {1: "error"},
    "build → tag → push → pull → run": {2: "success"},
    "The container exits immediately": {0: "error", 3: "success"},
    "The containers cannot talk to each other": {1: "error"},
    "HTTP 502, and nothing looks wrong": {1: "error"},
    "18 checks. Proof, not hope.": {0: "success"},
    "Stop the database. Watch. Fix. Verify.": {1: "error", 2: "success"},
})
