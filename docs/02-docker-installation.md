# Docker Installation

> Lesson 02 · 20–45 minutes (mostly download time) · you need: a computer with admin rights, about 10 GB of free disk space

## What is it?

Installing Docker gives you two things:

1. the **Docker Engine** (`dockerd`), the background service that builds images and runs containers;
2. the **Docker CLI** (`docker`) and the **Compose plugin** (`docker compose`), the commands you type.

There are two ways to get them:

| Your computer | What to install | What you get |
|---|---|---|
| Windows 10/11 | **Docker Desktop** with the **WSL 2** backend | Engine in a small Linux VM, CLI on Windows and in WSL |
| macOS (Intel or Apple Silicon) | **Docker Desktop** for Mac (pick the matching chip) | Engine in a small Linux VM, CLI in Terminal |
| Linux (Ubuntu, Debian, ...) | **Docker Engine** from Docker's official apt repository | Engine runs directly on your kernel, no VM |

## Why do we need it?

Every lab in this repository talks to a real Docker Engine. A correct installation avoids the
most frustrating beginner problems: "permission denied", "cannot connect to the Docker daemon",
paths that do not work in your terminal, and very old versions from the operating system's own
package list (which miss features this course uses, such as `docker compose`).

## How does it work?

```text
   Linux                                   Windows / macOS (Docker Desktop)
   -----                                   --------------------------------
   terminal                                terminal (WSL 2 / PowerShell / macOS Terminal)
      |  docker CLI                           |  docker CLI
      v                                       v
   /var/run/docker.sock                    Docker Desktop
      |                                       |
      v                                       v
   dockerd  (runs on your own kernel)      small Linux VM  ->  dockerd  ->  containers
      |
      v
   containers
```

The CLI talks to the engine through a **socket** (a special file, `/var/run/docker.sock` on Linux).
Whoever can write to that socket can tell Docker to do anything, including mounting the whole
host filesystem into a container. That is why access to Docker is a powerful permission.

## Prerequisites

- **Windows:** Windows 10 22H2 or Windows 11, 64-bit, virtualization enabled in the BIOS/UEFI
  (Task Manager → Performance → CPU shows "Virtualization: Enabled").
- **macOS:** a currently supported macOS version; know whether you have an Intel or Apple chip
  ( → About This Mac).
- **Linux:** a 64-bit Ubuntu (22.04, 24.04, 26.04) or Debian (12, 13) with `sudo` rights.
- **Git**, to download this repository.

## Hands-on Lab

### Option A · Windows: Docker Desktop + WSL 2 (recommended setup)

1. Open PowerShell **as Administrator** and install WSL 2 with Ubuntu (restart when asked):

<!-- test: skip -->
```bash
wsl --install -d Ubuntu
```

2. Download Docker Desktop from <https://docs.docker.com/desktop/setup/install/windows-install/>,
   run the installer, keep **"Use WSL 2 instead of Hyper-V"** selected.
3. Start Docker Desktop, open **Settings → Resources → WSL integration** and switch on your
   Ubuntu distribution.
4. Open the **Ubuntu** app (this is your WSL terminal). Use it for all labs in this course.

### Option B · macOS: Docker Desktop

1. Download Docker Desktop from <https://docs.docker.com/desktop/setup/install/mac-install/>
   (choose **Apple Silicon** or **Intel chip**).
2. Drag Docker to Applications, start it, wait until the whale icon in the menu bar says
   "Docker Desktop is running".
3. Use the normal **Terminal** app for the labs.

### Option C · Linux (Ubuntu): Docker Engine from Docker's apt repository

These commands follow the official guide at <https://docs.docker.com/engine/install/ubuntu/>.
They change your system, so read each one before running it.

1. Remove old, unofficial packages if they exist (it is fine if apt says none are installed):

<!-- test: skip -->
```bash
for pkg in docker.io docker-doc docker-compose podman-docker containerd runc; do sudo apt-get remove -y $pkg; done
```

2. Add Docker's signing key and repository:

<!-- test: skip -->
```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
```

3. Install the engine, the CLI, Buildx and the Compose plugin:

<!-- test: skip -->
```bash
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

On **Debian**, replace `ubuntu` with `debian` in both URLs.

**Alternative: the convenience script.** Docker also publishes a script that does all of the
above in one go. It is fine for a personal learning VM, but it runs as root and you do not see
what it changes, so do not use it on servers you share with others:

<!-- test: skip -->
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

4. **Run Docker without `sudo`** (optional, but every lab here assumes it). Add yourself to the
   `docker` group, then log out and back in:

<!-- test: skip -->
```bash
sudo usermod -aG docker "$USER"
```

> **Security note:** members of the `docker` group can start a container that mounts `/` from
> the host and changes any file as root. Being in the `docker` group is effectively the same as
> having root on that machine. That is acceptable on your own learning machine. On shared
> servers, only trusted administrators should be in this group.

### Everyone: get Git and this repository

Check Git (install it from <https://git-scm.com/downloads> or `sudo apt-get install -y git` if
the command is missing):

<!-- test: contains=git version -->
```bash
git --version
```

Clone the course and go into it (in WSL on Windows):

<!-- test: skip -->
```bash
git clone https://github.com/sufyanahmadkamboh/sufyan-devops-docker-from-zero.git
cd sufyan-devops-docker-from-zero
```

### Everyone: verify the installation

The client and the server should both answer:

<!-- test: contains=Client; contains=Server; output=head:14 -->
```bash
docker version
```

```text
Client:
 Version:           29.4.3
 API version:       1.54
 Go version:        go1.26.2
 Git commit:        055a478
 Built:             Wed May  6 17:10:36 2026
 OS/Arch:           windows/amd64
 Context:           desktop-linux

Server: Docker Desktop 4.74.0 (227015)
 Engine:
  Version:          29.4.3
  API version:      1.54 (minimum version 1.40)
  Go version:       go1.26.2
...
```

Compose is a plugin of the CLI (two words, `docker compose`, not the old `docker-compose`):

<!-- test: contains=Docker Compose version; output -->
```bash
docker compose version
```

```text
Docker Compose version v5.1.4
```

And the classic smoke test:

<!-- test: contains=Hello from Docker -->
```bash
docker run hello-world
```

### Which terminal should I use?

| System | Recommended terminal | Folder of the current directory in commands |
|---|---|---|
| Windows | **WSL 2 (Ubuntu app)** | `"$(pwd)"` |
| Windows | PowerShell (works for most labs) | `${PWD}` instead of `"$(pwd)"` |
| Windows | Git Bash (works, with one setting) | `"$(pwd)"`, after `export MSYS_NO_PATHCONV=1` |
| macOS / Linux | the normal Terminal | `"$(pwd)"` |

Why the Git Bash setting? Git Bash "helpfully" converts anything that looks like a Unix path into
a Windows path. `docker exec web ls /usr/share/nginx/html` silently becomes
`ls C:/Program Files/Git/usr/share/nginx/html`, which does not exist inside the container.
`export MSYS_NO_PATHCONV=1` switches that conversion off for the current terminal.

## Expected Result

- `git --version` prints `git version 2.x`.
- `docker version` shows **Client** and **Server** sections without errors.
- `docker compose version` prints `Docker Compose version v2.x` or newer.
- `docker run hello-world` prints `Hello from Docker!`.

## Experiment

`docker info` shows how your engine is set up. Look for `Server Version`, `Operating System`
(on Docker Desktop it says "Docker Desktop"), `CPUs`, `Total Memory` and `Docker Root Dir`
(where images and volumes are stored):

It prints a long report. For now, ask only for the fields that matter here, with `--format`:

<!-- test: contains=Server Version; output -->
```bash
docker info --format 'Server Version: {{.ServerVersion}}
Operating System: {{.OperatingSystem}}
CPUs: {{.NCPU}}
Total Memory: {{.MemTotal}} bytes
Docker Root Dir: {{.DockerRootDir}}'
```

```text
Server Version: 29.4.3
Operating System: Docker Desktop
CPUs: 14
Total Memory: 16486322176 bytes
Docker Root Dir: /var/lib/docker
```

Run plain `docker info` too and scroll through it: the same fields are in there, together with the plugins your
installation includes, the storage driver and the number of containers and images.

## Break It

On Linux, stop the engine and try a command (skip this on Docker Desktop: there you would quit
Docker Desktop from its menu instead):

<!-- test: skip -->
```bash
sudo systemctl stop docker docker.socket
docker ps
```

## Troubleshoot It

| Message | What it means | Fix |
|---|---|---|
| `Cannot connect to the Docker daemon at unix:///var/run/docker.sock. Is the docker daemon running?` | The CLI works, the engine is not running | Linux: `sudo systemctl start docker` · Desktop: start Docker Desktop and wait for "running" |
| `permission denied while trying to connect to the Docker daemon socket` | You are not in the `docker` group (or did not log out/in after adding yourself) | `sudo usermod -aG docker "$USER"`, then log out and back in, then `docker ps` |
| `docker: command not found` in WSL | WSL integration is off for this distribution | Docker Desktop → Settings → Resources → WSL integration → switch it on |
| `docker-compose: command not found` | You typed the old v1 command | Use `docker compose` (with a space) |
| `ls: cannot access 'C:/Program Files/Git/...'` | Git Bash path conversion | `export MSYS_NO_PATHCONV=1`, or use WSL |

Restart after the Break It step:

<!-- test: skip -->
```bash
sudo systemctl start docker
docker ps
```

## Common Mistakes

- Installing `docker.io` from Ubuntu's own repository and then following a guide for Docker's
  official packages. Pick one source; this course assumes Docker's official repository.
- Forgetting to log out and back in after `usermod -aG docker`: group changes only apply to new logins.
- Running every command with `sudo` "to be safe": files created by root inside bind mounts then
  become hard to edit, and you get used to giving everything root.
- On Windows, cloning the repository into `C:\...` and working in WSL: it works, but file access
  across the boundary is slow. Clone it inside WSL (`~/`) instead.

## Best Practices

- Keep Docker Desktop / Docker Engine updated; security fixes ship regularly.
- Give Docker Desktop enough resources (Settings → Resources): 2 CPUs and 4 GB RAM are plenty
  for this course.
- Treat the `docker` group like `sudo`: only for people who should have root.
- Use WSL 2 on Windows: the labs use Linux commands, and they behave exactly as written.

## Challenge

Find out, with commands only, **where your engine stores its data** and **how many CPUs** it
can use.

## Solution

<details><summary>Show the solution</summary>

Both values are in `docker info`. A Go template prints just those fields:

<!-- test: output -->
```bash
docker info --format 'Docker Root Dir: {{.DockerRootDir}} · CPUs: {{.NCPU}}'
```

```text
Docker Root Dir: /var/lib/docker · CPUs: 14
```

On Docker Desktop the root directory is inside the Linux VM, not a folder you can open in
Windows Explorer or Finder.

</details>

## Verification

- [ ] `docker version` shows a Server section.
- [ ] `docker compose version` works.
- [ ] `docker run hello-world` works **without** `sudo`.
- [ ] You cloned this repository and you are inside its folder.
- [ ] You know which terminal you will use for the labs.

## Real-World Usage

- Every developer workstation and CI runner in a container-based team has Docker (or a
  compatible engine) installed in exactly this way.
- On servers, engineers install Docker Engine from the official repository, keep it patched, and
  restrict who can reach the socket, because socket access means root access.
- `docker info` is one of the first commands to run when a build machine "behaves strangely":
  it shows the engine version, storage location, and resources.

## Key Takeaways

- Windows/macOS: Docker Desktop (WSL 2 on Windows). Linux: Docker Engine from Docker's repository.
- Verify with `docker version`, `docker compose version` and `docker run hello-world`.
- The `docker` group is equivalent to root on that machine.
- Use WSL 2 on Windows; in Git Bash set `MSYS_NO_PATHCONV=1`; in PowerShell use `${PWD}`.
- Next: [03 · Images](03-images.md).
