"""Docker From Zero, part 1 of 2: containers and images.

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


def scene(chapter, kicker, title, body, steps, layout="full"):
    SCENES.append({"chapter": chapter, "kicker": kicker, "title": title, "body": body, "steps": steps, "layout": layout})


T0, T1, T2, T3 = ("tutorial/00-start-here.md", "tutorial/01-first-container.md", "tutorial/02-ports-and-config.md",
                  "tutorial/03-dockerfiles.md")

# ---------------------------------------------------------------- 1. Hook
scene("Why Docker", "Docker From Zero · part 1 of 2", "\"It works on my machine.\"", svg(
    box(0, 0, 30, 520, 250, "💻", "Your laptop", ["Python 3.14, Flask 3.1", "it works ✅"], "ok", "#0f2a22")
    + box(1, 600, 30, 520, 250, "🖥️", "Your colleague", ["Python 3.11, no Flask", "ModuleNotFoundError ❌"], "bad", "#2a1520")
    + box(1, 1200, 30, 520, 250, "🏭", "The server", ["different OS, different libraries", "something else breaks ❌"], "bad", "#2a1520")
    + arrow(2, 860, 300, 860, 380)
    + box(2, 300, 390, 1120, 170, "📦", "A container image", ["the app + its exact Python + its libraries + its settings, in one package",
                                                           "runs the same on every machine that has Docker"], "blue", "#16306a")
    + label(3, 860, 640, "You will run it, break it, fix it, and build something real with it.", 32, "amber", "middle", 800)
), [
    S("It works on my machine. Every developer has said it, and every operations engineer has heard it. "
      "On your laptop, the app runs. On your colleague's laptop, a library is missing."),
    S("And on the server, something else is different. Same code, three different results."),
    S("Docker fixes this by packaging the app together with everything it needs: the exact language version, the "
      "libraries, the settings. That package is called an image, and it runs the same way on every machine that has Docker."),
    S("In this two part course you will not just read about Docker. You will run containers, break them on purpose, "
      "investigate like a real engineer, fix them, and finish with a complete three container application."),
])

scene(None, "How this course works", "Learn → Build → Run → Break → Troubleshoot → Understand", grid([
    card(0, "🧭", "tutorial/", "the guided path: 12 chapters, every command explained", "blue"),
    card(1, "🧪", "labs/", "18 hands-on workbooks, each with a deliberate failure", "ok"),
    card(1, "📚", "docs/", "23 concept lessons: what, why, how, best practices", "blue"),
    card(2, "🔧", "troubleshooting/", "10 real failures, investigated step by step", "bad"),
    card(2, "🎯", "challenges/", "19 tasks with hidden solutions", "amber"),
    card(3, "🏁", "capstone/", "web + API + database + volume, done properly", "ok"),
], cols=3), [
    S("Everything in this video comes from one free repository on GitHub. The tutorial folder is the guided path. "
      "This video follows it, chapter by chapter."),
    S("The labs are short workbooks you do on your own, and the docs explain each concept in depth."),
    S("There are ten troubleshooting scenarios with real failures, and nineteen challenges with hidden solutions.",
      tts="There are ten troubleshooting scenarios with real failures, and nineteen challenges with hidden solutions."),
    S("And the capstone puts everything together. One more thing: every command you see here was executed automatically "
      "on a fresh Docker engine, and the output on screen is the real output. Nothing is typed by hand."),
])

scene(None, "Before we start", "What you need: Docker, Git, a terminal", grid([
    card(0, "🪟", "Windows", "Docker Desktop with the WSL 2 backend; use the Ubuntu (WSL) terminal", "blue"),
    card(0, "🍎", "macOS", "Docker Desktop (Intel or Apple Silicon)", "blue"),
    card(0, "🐧", "Linux", "Docker Engine from Docker's apt repository", "blue"),
    card(1, "📥", "Get the lab", "git clone https://github.com/sufyanahmadkamboh/sufyan-devops-docker-from-zero", "ok"),
    card(2, "🆓", "Nothing else", "no cloud account, no paid service, no Kubernetes", "ok"),
    card(2, "📍", "Always start here", "every command runs from the repository root", "amber"),
], cols=3), [
    S("You need three things. Docker: Docker Desktop on Windows or Mac, and on Windows use the W S L two backend and its "
      "Ubuntu terminal. On Linux, Docker Engine. The installation lesson in docs walks you through each one.",
      tts="You need three things. Docker: Docker Desktop on Windows or Mac, and on Windows use the W S L two backend and its "
          "Ubuntu terminal. On Linux, Docker Engine. The installation lesson in docs walks you through each one."),
    S("Then Git, to clone the repository. The link is in the description."),
    S("That is all. No cloud account, nothing to pay. Every command in the course runs from the repository root, so if "
      "a command cannot find a file, check where you are first."),
])

# ---------------------------------------------------------------- 2. What Docker is
scene("What Docker is", "The big picture", "You type. The engine does the work.", svg(
    box(0, 0, 250, 330, 160, "⌨️", "docker CLI", ["what you type"], "blue")
    + arrow(1, 335, 330, 470, 330, label="request")
    + box(1, 475, 120, 640, 450, "⚙️", "Docker Engine (daemon)", ["builds images", "runs containers", "networks, volumes"], "amber", "#2b2410")
    + box(2, 515, 330, 260, 200, "📦", "images", ["read-only"], "violet")
    + box(3, 815, 330, 260, 200, "🟢", "containers", ["running"], "ok", "#0f2a22")
    + arrow(2, 1120, 330, 1290, 330, label="pull / push")
    + box(2, 1295, 250, 425, 160, "🌍", "Registry", ["Docker Hub"], "blue")
), [
    S("Before the first command, the big picture. You type commands into the Docker command line tool."),
    S("It sends each request to the Docker engine, a background service that does the real work: building images, "
      "running containers, creating networks and volumes."),
    S("Images come from a registry, usually Docker Hub. The engine pulls them down, and can push your own images up.",
      tts="Images come from a registry, usually Docker Hub. The engine pulls them down, and can push your own images up."),
    S("And from an image, the engine creates containers: running processes, isolated from each other and from your computer."),
])

scene(None, "The most important idea", "Image = recipe. Container = the meal.", svg(
    box(0, 80, 60, 640, 300, "📜", "IMAGE", ["a read-only package:", "files + \"what to run\"", "like a recipe, or a class"], "violet")
    + arrow(1, 730, 210, 960, 120, label="docker run")
    + arrow(1, 730, 210, 960, 300)
    + arrow(1, 730, 210, 960, 480)
    + box(1, 970, 40, 680, 150, "🟢", "container web", ["running"], "ok", "#0f2a22")
    + box(1, 970, 225, 680, 150, "🟢", "container web2", ["running"], "ok", "#0f2a22")
    + box(1, 970, 410, 680, 150, "⚪", "container old", ["stopped, still exists"], "blue")
    + label(2, 860, 660, "One image, as many containers as you like. Deleting a container never deletes the image.", 30, "amber", "middle", 800)
), [
    S("If you remember one idea from this video, make it this one. An image is a read-only package: files, plus "
      "instructions for what to run. Think of it as a recipe."),
    S("A container is what you get when you run an image. Like meals cooked from one recipe, you can create as many "
      "containers from one image as you like. Some running, some stopped."),
    S("And deleting a container never deletes the image. You can always cook again."),
])

# ---------------------------------------------------------------- 3. First container
scene("Your first container", "Recorded · tutorial chapter 00", "Is Docker installed?", terminal(
    rec(T0, "docker --version")
    + rec(T0, "docker compose version", step=1)
    + rec(T0, "docker run hello-world", step=2, head=13, tones={"Hello from Docker": "ok", "Unable to find": "warn"}),
    "bash (recorded)"), [
    S("Let's start. Open a terminal in the repository folder and ask Docker for its version. One line: the version of "
      "the Docker command line. This video uses Docker 29."),
    S("Compose is included too. We will need it in part two.", tts="Compose is included too. We will need it in part two."),
    S("Now run your very first container: docker run hello world. Look at the output. Unable to find image locally, "
      "so Docker pulls it from Docker Hub. Then: Hello from Docker. That line was printed by a program running inside "
      "a container. Your installation works.",
      tts="Now run your very first container: docker run hello world. Look at the output. Unable to find image locally, "
          "so Docker pulls it from Docker Hub. Then: Hello from Docker. That line was printed by a program running inside "
          "a container. Your installation works."),
])

scene(None, "Recorded · tutorial chapter 01", "A real server in a container", terminal(
    rec(T1, "docker pull nginx", tail=3)
    + rec(T1, "docker images", step=1, drop=r"jitesoft|linuxserver", tones={"nginx": "ok"})
    + rec(T1, "docker run -d --name web", step=2, tones={" web": "ok"}),
    "bash (recorded)"), [
    S("hello world exits immediately. Let's run something that keeps running: nginx, a popular web server. "
      "docker pull only downloads the image. The tag, one point thirty alpine, pins the exact version. Always use a tag.",
      tts="hello world exits immediately. Let's run something that keeps running: engine x, a popular web server. "
          "docker pull only downloads the image. The tag, one point thirty alpine, pins the exact version. Always use a tag."),
    S("docker images lists what you have. In Docker 29 the columns are: the image name and tag, its ID, the disk usage, "
      "the downloaded content size, and an extra column that shows U when a container uses the image.",
      tts="docker images lists what you have. In Docker 29 the columns are: the image name and tag, its I D, the disk usage, "
          "the downloaded content size, and an extra column that shows U when a container uses the image."),
    S("Now docker run, with dash d for detached, so it runs in the background, and dash dash name web. Docker prints the "
      "new container's ID, and docker ps shows it running: the image, the command, when it was created, the status, "
      "the ports, and the name we chose.",
      tts="Now docker run, with dash d for detached, so it runs in the background, and dash dash name web. Docker prints the "
          "new container's I D, and docker P S shows it running: the image, the command, when it was created, the status, "
          "the ports, and the name we chose."),
])

scene(None, "Recorded · inside a running container", "logs and exec", terminal(
    rec(T1, "docker logs web", tail=4)
    + rec(T1, "docker exec web ps", step=1, tones={"master process": "ok"})
    + rec(T1, "docker exec web hostname", step=2),
    "bash (recorded)"), [
    S("Two commands you will use every day. docker logs shows everything the container's main process printed. Here, "
      "nginx starting its worker processes.",
      tts="Two commands you will use every day. docker logs shows everything the container's main process printed. Here, "
          "engine x starting its worker processes."),
    S("docker exec runs an extra command inside a running container. ps lists the processes inside: process number one "
      "is the nginx master process. Inside its own world, the container's main process is P I D 1.",
      tts="docker exec runs an extra command inside a running container. P S lists the processes inside: process number one "
          "is the engine x master process. Inside its own world, the container's main process is P I D 1."),
    S("And the hostname of the container is its short ID. Remember that, we will use it later.",
      tts="And the hostname of the container is its short I D. Remember that, we will use it later."),
])

scene("The container lifecycle", "Created → Running → Exited → Removed", "Every state, on purpose", svg(
    box(0, 0, 280, 300, 150, "📜", "Image", [], "violet")
    + arrow(0, 305, 355, 395, 355, label="create")
    + box(1, 400, 280, 300, 150, "🆕", "Created", [], "blue")
    + arrow(1, 705, 355, 795, 355, label="start")
    + box(2, 800, 280, 300, 150, "🟢", "Running", [], "ok", "#0f2a22")
    + arrow(3, 1105, 355, 1195, 355, label="stop / exit")
    + box(3, 1200, 280, 300, 150, "⚪", "Exited", ["(exit code)"], "amber")
    + arrow(3, 1350, 275, 950, 140, "sky", True, "start again")
    + arrow(4, 1350, 435, 1350, 560)
    + box(4, 1200, 565, 300, 140, "🗑️", "Removed", ["docker rm"], "bad", "#2a1520")
), [
    S("Containers move through a small set of states. docker create makes a container from an image without starting it."),
    S("Its state is Created."),
    S("docker start runs its main process: Running. docker run is simply create plus start."),
    S("When the main process ends, by itself or because you ran docker stop, the container is Exited, with an exit code. "
      "It still exists, with its files, and you can start it again."),
    S("Only docker rm removes it for good."),
])

scene(None, "Recorded · why containers stop", "A container lives as long as its main process", terminal(
    rec(T1, "docker rm web", tones={"Error": "bad"}, wrap=104)
    + rec(T1, "docker run -d --name sleeper", step=1, drop=r"Unable|Pulling|Digest|Status|complete|^[0-9a-f]{12}:|^[0-9a-f]{64}$|sleeper: Up",
          cmd="docker run -d --name sleeper alpine:3.24 sleep 5")
    + rec(T1, "docker ps -a --filter name=sleeper", step=1, tones={"Exited": "warn"})
    + rec(T1, "docker run --name quick", step=2, tones={"Exited": "warn"})
    + rec(T1, "docker inspect ubuntu", step=3, tones={"bash": "ok"}),
    "bash (recorded)"), [
    S("Let's break things. docker rm on a running container fails, and the error tells you exactly why: the container is "
      "running, stop it first or force remove. Read errors. They usually contain the answer."),
    S("Now a container whose main process is sleep 5. Five seconds later, it is Exited with code 0. Nothing crashed: its "
      "only job was to sleep, and when the job ends, the container ends."),
    S("This one surprises every beginner. docker run ubuntu, and the container exits immediately. Why?",
      tts="This one surprises every beginner. docker run ubuntu, and the container exits immediately. Why?"),
    S("Inspect the image: its default command is bash. Without an interactive terminal, bash has nothing to read, so it "
      "exits, and the container exits with it. A container lives exactly as long as its main process. That one sentence "
      "explains half of all container problems.",
      tts="Inspect the image: its default command is bash. Without an interactive terminal, bash has nothing to read, so it "
          "exits, and the container exits with it. A container lives exactly as long as its main process. That one sentence "
          "explains half of all container problems."),
])

scene(None, "Recorded · interactive containers", "A shell inside a container", terminal(
    [(0, "$ docker run -it --name shell ubuntu:26.04 bash", "cmd"), (0, "root@4f2c…:/# cat /etc/os-release   (you are inside)", "dim"),
     (0, "root@4f2c…:/# exit", "dim")]
    + rec(T1, "docker ps -a --filter name=shell", step=1, tones={"Exited": "warn"})
    + rec(T1, "--rm ubuntu:26.04 cat /etc/os-release", step=2, head=4, tones={"Ubuntu": "ok"}),
    "bash (recorded)"), [
    S("You can also work inside a container interactively. Dash i keeps input open, dash t gives you a terminal, and "
      "bash is the program to run. You get a prompt inside Ubuntu, even if your computer runs Windows or macOS."),
    S("Type exit, and bash ends. bash was the main process, so the container is Exited. Same rule as before."),
    S("And for a single command, no shell needed: docker run dash dash rm ubuntu cat etc os release. Dash dash rm "
      "deletes the container as soon as it stops, so you do not collect dozens of stopped containers.",
      tts="And for a single command, no shell needed: docker run dash dash R M ubuntu cat etc O S release. Dash dash R M "
          "deletes the container as soon as it stops, so you do not collect dozens of stopped containers."),
])

# ---------------------------------------------------------------- 4. Ports
scene("Port mapping", "Reaching a container from your computer", "-p HOST:CONTAINER", svg(
    box(0, 0, 230, 420, 220, "🌐", "Your browser", ["http://localhost:8080"], "blue")
    + arrow(1, 425, 340, 615, 340, label="port 8080")
    + box(1, 620, 120, 1100, 440, "🖥️", "Your computer", [], "amber", "#111c2e")
    + box(2, 1060, 230, 600, 220, "📦", "container web", ["nginx listens on port 80"], "ok", "#0f2a22")
    + arrow(2, 680, 340, 1055, 340, "ok", label="-p 8080:80")
    + label(3, 860, 650, "Without -p, nothing outside the container can reach it.", 30, "amber", "middle", 800)
), [
    S("The web server is running, but can your browser reach it? Not yet. A container has its own network. To reach it, "
      "you publish a port."),
    S("dash p eight zero eight zero colon eighty means: traffic to port 8080 on your computer goes to port 80 inside the container.",
      tts="dash p eight zero eight zero colon eighty means: traffic to port 8080 on your computer goes to port 80 inside the container."),
    S("The order matters. Host first, container second. nginx listens on 80 inside its container.",
      tts="The order matters. Host first, container second. engine x listens on 80 inside its container."),
    S("Without dash p, nothing outside the container can reach it."),
])

scene(None, "Recorded · tutorial chapter 02", "Publish it, then break it", terminal(
    rec(T2, "curl -s --max-time 3 http://localhost:80", cmd="curl -s --max-time 3 http://localhost:80     # no -p")
    + [(0, "(nothing: curl exit code 7, connection refused)", "bad")]
    + rec(T2, "curl -s http://localhost:8081 | grep title", step=1, tones={"Welcome": "ok"})
    + rec(T2, "docker run -d --name web3 -p 8082:8080", step=2, drop=".")
    + rec(T2, "curl -s --max-time 3 http://localhost:8082", step=2)
    + [(2, "(nothing again: curl exit code 52, empty reply)", "bad")]
    + rec(T2, "docker inspect nginx:1.30-alpine --format", step=3, tones={"80/tcp": "ok"}),
    "bash (recorded)"), [
    S("Without a published port, curl gets connection refused."),
    S("With dash p eight zero eight one colon eighty, here is the nginx welcome page.",
      tts="With dash p eight zero eight one colon eighty, here is the engine x welcome page."),
    S("Now we break it on purpose: dash p eight zero eight two colon eight zero eight zero. The container starts fine, "
      "docker ps says Up, but curl gets an empty reply. Don't guess. Investigate."),
    S("Which port does the image actually use? docker inspect says: 80 slash T C P. We mapped to 8080, where nothing "
      "listens. The container was fine. The mapping was wrong. Fix the mapping, and it works."),
])

scene(None, "In the browser", "http://localhost:8080", shot(0, "nginx-welcome.png", "nginx welcome page", "height:620px;width:auto"), [
    S("And the same page in a browser: localhost, port 8080. Your computer forwards it to port 80 inside the container, "
      "where nginx answers. Your first containerised web server.",
      tts="And the same page in a browser: local host, port 8080. Your computer forwards it to port 80 inside the container, "
          "where engine x answers. Your first containerised web server."),
])

scene(None, "Recorded · a port conflict", "port is already allocated", terminal(
    rec(T2, "docker run -d --name web4 -p 8080:80", drop=r"^[0-9a-f]{64}$|Run 'docker run|^$",
        tones={"already allocated": "bad", "Error": "bad"}, wrap=104)
    + rec(T2, "docker ps --filter publish=8080", step=1, tones={"web": "ok"})
    + rec(T2, "docker ps -a --filter name=web4", step=2, tones={"Created": "warn"}),
    "bash (recorded)"), [
    S("Another classic. A second container on host port 8080. Docker refuses: Bind for 0 point 0 point 0 point 0 port "
      "8080 failed, port is already allocated. One host port can only go to one container."),
    S("Who has it? docker ps, filtered by published port 8080: our first container, web."),
    S("And notice: the failed container still exists, in state Created. Remove it, then pick another host port. "
      "This is exactly the kind of problem you meet on a real server."),
])

# ---------------------------------------------------------------- 5. Environment variables
scene("Environment variables", "One image, many configurations", "-e NAME=value", terminal(
    rec(T2, "curl -s http://localhost:5000", tones={"production": "ok"})
    + rec(T2, "docker run -d --name simple2", step=1, drop=".", width=200)
    + rec(T2, "curl -s http://localhost:5001", step=1, tones={"development": "ok", "Good morning": "ok"}),
    "bash (recorded)"), [
    S("Same image, different configuration. That is what environment variables are for. Here is our small Python app, "
      "simple app, running with its defaults: environment production. The hostname line shows which container answered."),
    S("A second container from the exact same image, with dash e APP_ENV equals development and a different greeting. "
      "Now it greets with Good morning from Docker, environment development. No rebuild. The image did not change, only "
      "its configuration.",
      tts="A second container from the exact same image, with dash e app env equals development and a different greeting. "
          "Now it greets with Good morning from Docker, environment development. No rebuild. The image did not change, only "
          "its configuration."),
])

scene(None, "Recorded · an env file", "Many settings at once: --env-file", terminal(
    rec(T2, "--env-file demo.env", tones={"APP_ENV=staging": "ok", "GREETING": "ok", "HOSTNAME": "dim"}),
    "bash (recorded)"), [
    S("When there are many settings, put them in a file, one name equals value per line, and pass it with dash dash env "
      "file. The env command inside the container shows both variables arrived, next to the ones Docker sets itself, "
      "like the hostname. Never commit env files with real passwords to Git. The repository's dot git ignore file "
      "already excludes them.",
      tts="When there are many settings, put them in a file, one name equals value per line, and pass it with dash dash env "
          "file. The env command inside the container shows both variables arrived, next to the ones Docker sets itself, "
          "like the hostname. Never commit env files with real passwords to Git. The repository's dot git ignore file "
          "already excludes them."),
])

scene(None, "Recorded · a database that refuses to start", "Read the logs first", terminal(
    [(0, "$ docker run --name db postgres:18-alpine", "cmd")]
    + rec(T2, "docker run --name db postgres:18-alpine", out_step=0, grep=r"Error|You must specify|superuser|POSTGRES_PASSWORD",
          cmd="", tones={"Error": "bad"})[1:]
    + rec(T2, "docker ps -a --filter name=db", step=1, tones={"Exited": "bad"})
    + rec(T2, "docker inspect db --format", step=2, width=96, tones={"POSTGRES_PASSWORD": "warn"}),
    "bash (recorded)"), [
    S("Some images refuse to start without configuration, and that is a good thing. Run PostgreSQL without a password: "
      "it prints Database is uninitialized and superuser password is not specified, and tells you exactly which variable to set.",
      tts="Some images refuse to start without configuration, and that is a good thing. Run postgres Q L without a password: "
          "it prints Database is uninitialized and superuser password is not specified, and tells you exactly which variable to set."),
    S("docker ps dash a shows it Exited with code 1. When a container stops, the logs are the first place to look.",
      tts="docker P S dash a shows it Exited with code 1. When a container stops, the logs are the first place to look."),
    S("With dash e POSTGRES_PASSWORD it starts. But look what docker inspect shows: the password, in plain text, for "
      "anyone who can run docker inspect. Remember this. We fix it properly in part two, with secret files.",
      tts="With dash e postgres password it starts. But look what docker inspect shows: the password, in plain text, for "
          "anyone who can run docker inspect. Remember this. We fix it properly in part two, with secret files."),
])

# ---------------------------------------------------------------- 6. Dockerfile
APP = """FROM python:3.14-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
ENV APP_ENV=production
EXPOSE 5000
CMD ["python", "app.py"]"""
scene("Your first Dockerfile", "examples/simple-app/dockerfile-steps/", "Building an image, one instruction at a time",
      code("dockerfile-steps/04.Dockerfile", APP, "docker", 30) + notes([
          (0, "FROM", "start from an official Python image"),
          (1, "WORKDIR, COPY", "put our code into /app"),
          (2, "RUN", "runs while BUILDING: install Flask"),
          (3, "ENV, EXPOSE", "default settings, documented port"),
          (4, "CMD", "runs when the CONTAINER starts"),
      ]), [
    S("So far we used other people's images. Now we build our own, one instruction at a time, the way the tutorial does "
      "it in dockerfile steps one to four. Every Dockerfile starts FROM a base image: here the official slim Python 3.14 image.",
      hl=(1, 1), tts="So far we used other people's images. Now we build our own, one instruction at a time, the way the tutorial does "
                     "it in docker file steps one to four. Every docker file starts from a base image: here the official slim Python 3 point 14 image."),
    S("WORKDIR sets the folder inside the image, and COPY copies our code into it.", hl=(2, 3),
      tts="Work dir sets the folder inside the image, and copy copies our code into it."),
    S("RUN executes a command while the image is being built. Here it installs Flask, the one library the app needs.",
      hl=(4, 4), tts="Run executes a command while the image is being built. Here it installs Flask, the one library the app needs."),
    S("ENV sets a default configuration, and EXPOSE documents the port. EXPOSE alone publishes nothing, you still need dash p.",
      hl=(5, 6), tts="E N V sets a default configuration, and expose documents the port. Expose alone publishes nothing, you still need dash p."),
    S("And CMD is what runs when a container starts. RUN happens at build time, CMD at run time. Mixing them up is one "
      "of the most common beginner mistakes.", hl=(7, 7),
      tts="And C M D is what runs when a container starts. Run happens at build time, C M D at run time. Mixing them up is one "
          "of the most common beginner mistakes."),
], layout="code")

scene(None, "Recorded · step 2 forgot something", "It builds. It does not run.", terminal(
    rec(T3, "docker run --rm simple-app:step2", tones={"ModuleNotFoundError": "bad"})
    + rec(T3, "docker run -d --name step3", step=1, drop=".")
    + rec(T3, "curl -s http://localhost:5000", step=1, tones={"Hello": "ok"})
    + rec(T3, "docker run --rm greeter Docker", step=2, tones={"Hello": "ok"}),
    "bash (recorded)"), [
    S("Step two of the tutorial has no RUN pip install. It builds without any error, but the container crashes: "
      "ModuleNotFoundError, no module named flask. It works on my laptop, because Flask is installed there. The image "
      "only contains what the Dockerfile puts into it.",
      tts="Step two of the tutorial has no run pip install. It builds without any error, but the container crashes: "
          "module not found error, no module named flask. It works on my laptop, because Flask is installed there. The image "
          "only contains what the docker file puts into it."),
    S("Step three adds the install. Build, run with dash p five thousand, and the app answers.",
      tts="Step three adds the install. Build, run with dash p five thousand, and the app answers."),
    S("One more pair you must know: ENTRYPOINT is the fixed program, CMD is its default argument. This little image "
      "has ENTRYPOINT echo Hello, and CMD world. Run it with the word Docker, and the argument replaces only the CMD: "
      "Hello, Docker.",
      tts="One more pair you must know: entry point is the fixed program, C M D is its default argument. This little image "
          "has entry point echo Hello, and C M D world. Run it with the word Docker, and the argument replaces only the C M D: "
          "Hello, Docker."),
])

# ---------------------------------------------------------------- 7. Layers and cache
scene("Layers and the build cache", "Recorded · docker history", "An image is a stack of layers", terminal(
    rec(T3, "docker history simple-app:step4", head=8, width=110,
        tones={"pip install": "warn", "COPY . .": "warn", "WORKDIR /app": "warn", "CMD [\"python\" \"app.py\"]": "warn"}),
    "bash (recorded)"), [
    S("Every instruction in a Dockerfile creates a layer, and docker history shows them, newest on top. Our four "
      "instructions sit on top of the layers of the Python base image. Of our own layers, pip install is the big one."),
    S("Layers are cached. When you rebuild, Docker reuses every layer whose inputs did not change. But as soon as one "
      "layer changes, every layer after it is rebuilt. So the order of the instructions decides how fast your builds are."),
])

scene(None, "Recorded · change one line of app.py, rebuild", "Bad order vs. good order", terminal(
    [(0, "# 03.Dockerfile: COPY . .  THEN  pip install", "dim")]
    + rec(T3, "dockerfile-steps/03.Dockerfile -t simple-app:step3 . 2>&1", nth=0, width=104,
          cmd="docker build -f dockerfile-steps/03.Dockerfile -t simple-app:step3 .", drop="FROM docker.io",
          tones={"Successfully installed": "bad", "RUN pip": "bad", "CACHED": "ok"})
    + [(1, "# 05.Dockerfile: COPY requirements.txt, pip install, THEN COPY app.py", "dim")]
    + rec(T3, "dockerfile-steps/05.Dockerfile -t simple-app:step5 . 2>&1", step=1, width=104,
          cmd="docker build -f dockerfile-steps/05.Dockerfile -t simple-app:step5 .", drop="FROM docker.io",
          tones={"CACHED": "ok", "COPY app.py": "warn"}),
    "bash (recorded, build steps only)"), [
    S("Let's prove it. I changed one comment line in app.py, and rebuilt with step three, which copies all the code "
      "first and installs the libraries after it. The code changed, so the copy layer changed, so pip install runs "
      "again. Successfully installed Flask, for a one line change.",
      tts="Let's prove it. I changed one comment line in app dot py, and rebuilt with step three, which copies all the code "
          "first and installs the libraries after it. The code changed, so the copy layer changed, so pip install runs "
          "again. Successfully installed Flask, for a one line change."),
    S("Step five copies only the requirements file first, installs, and copies the code last. Same change, and now pip "
      "install is CACHED. Only the last, tiny layer is rebuilt. Rule of thumb: things that rarely change go first, your "
      "code goes last. In a real project, that is the difference between a five second build and a five minute build.",
      tts="Step five copies only the requirements file first, installs, and copies the code last. Same change, and now pip "
          "install is cached. Only the last, tiny layer is rebuilt. Rule of thumb: things that rarely change go first, your "
          "code goes last."),
])

# ---------------------------------------------------------------- 8. .dockerignore
scene(".dockerignore", "Recorded · the build context", "What you send to the builder ends up in the image", terminal(
    [(0, "# a 50 MB junk folder and a .env file with a password sit next to the code", "dim")]
    + rec(T3, "mv .dockerignore .dockerignore.off", cmd="docker build -f dockerfile-steps/02.Dockerfile -t simple-app:leaky .    # no .dockerignore",
          tones={"50.02MB": "bad"})
    + rec(T3, "docker run --rm simple-app:leaky cat .env", step=1, tones={"DB_PASSWORD": "bad"})
    + rec(T3, "-t simple-app:clean . 2>&1", step=2, cmd="docker build -f dockerfile-steps/02.Dockerfile -t simple-app:clean .     # with .dockerignore",
          tones={"63B": "ok"})
    + rec(T3, "docker run --rm simple-app:clean ls -a", step=2, tones={"app.py": "ok"}),
    "bash (recorded)"), [
    S("The dot at the end of docker build is the build context: the folder Docker sends to the builder. Watch what "
      "happens without a dot docker ignore file, when a 50 megabyte junk folder and a .env file with a password sit next "
      "to the code. Transferring context: 50 megabytes.",
      tts="The dot at the end of docker build is the build context: the folder Docker sends to the builder. Watch what "
          "happens without a dot docker ignore file, when a 50 megabyte junk folder and a dot E N V file with a password sit next "
          "to the code. Transferring context: 50 megabytes."),
    S("And because the Dockerfile copies everything, the password is now inside the image. Anyone who pulls this image "
      "can read it. This happens in real companies.",
      tts="And because the docker file copies everything, the password is now inside the image. Anyone who pulls this image "
          "can read it. This happens in real companies."),
    S("Put the dot docker ignore file back, and rebuild: 63 bytes of context, and the image contains only the "
      "application files. Faster builds, smaller images, and no secrets shipped by accident.",
      tts="Put the dot docker ignore file back, and rebuild: 63 bytes of context, and the image contains only the "
          "application files. Faster builds, smaller images, and no secrets shipped by accident."),
])

scene(None, "Where you use this at work", "Every DevOps job starts here", grid([
    card(0, "📦", "Images", "the artifact every pipeline builds, scans and ships", "blue"),
    card(0, "📝", "Dockerfiles", "repeatable builds: the same image on every machine", "blue"),
    card(1, "🔌", "Ports and env vars", "the same image in dev, test and production, configured differently", "blue"),
    card(1, "📜", "logs and exec", "the first two commands in every incident", "amber"),
    card(2, "⚡", "Layer order", "the difference between a 5-second and a 5-minute pipeline", "ok"),
    card(2, "🙈", ".dockerignore", "keeps keys and junk out of images you publish", "bad"),
], cols=2), [
    S("Where would you use this as a DevOps engineer? Everywhere. The image is the artifact every pipeline builds, scans "
      "and ships, and the Dockerfile makes that build repeatable.",
      tts="Where would you use this as a dev ops engineer? Everywhere. The image is the artifact every pipeline builds, scans "
          "and ships, and the docker file makes that build repeatable."),
    S("Ports and environment variables let the same image run in development, test and production. And when something "
      "breaks, docker logs and docker exec are the first two commands you type."),
    S("Layer order decides how long every pipeline run takes, and a dot docker ignore file keeps keys and junk out of "
      "the images you publish.",
      tts="Layer order decides how long every pipeline run takes, and a dot docker ignore file keeps keys and junk out of "
          "the images you publish."),
])

# ---------------------------------------------------------------- 9. Wrap up
scene("End of part 1", "What you can do now", "Part 1 complete", grid([
    card(0, "📦", "Images and containers", "pull, run, ps, logs, exec, stop, start, rm", "ok"),
    card(0, "🔄", "The lifecycle", "and why a container stops with its main process", "ok"),
    card(1, "🔌", "Ports and configuration", "-p HOST:CONTAINER, -e, reading errors and logs", "ok"),
    card(1, "📝", "Dockerfiles", "FROM, WORKDIR, COPY, RUN, ENV, EXPOSE, CMD, ENTRYPOINT", "ok"),
    card(2, "⚡", "Layers and cache", "dependencies first, code last", "ok"),
    card(2, "🙈", ".dockerignore", "small context, no secrets in images", "ok"),
    card(3, "▶️", "Part 2", "volumes, networks, Compose, security, optimization, troubleshooting, the capstone", "amber"),
], cols=2), [
    S("Let's recap part one. You can pull and run containers, read their logs, look inside them, and you know why a "
      "container stops when its main process ends."),
    S("You can publish ports, configure containers with environment variables, and you can write a Dockerfile, "
      "instruction by instruction."),
    S("You know how layers and the build cache work, and how a dot docker ignore file keeps your builds fast and your "
      "secrets out of your images.",
      tts="You know how layers and the build cache work, and how a dot docker ignore file keeps your builds fast and your "
          "secrets out of your images."),
    S("In part two: data that survives, networks, Docker Compose, security, image optimization, real troubleshooting, "
      "and the capstone, a complete three container application. Before you continue, do labs one to eight in the "
      "repository. Typing the commands yourself is where the learning happens. See you in part two."),
])
