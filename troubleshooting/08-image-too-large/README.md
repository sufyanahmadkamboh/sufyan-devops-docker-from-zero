# 08 · Image too large

> A web app with one dependency produces an image of more than a gigabyte. Where does it all come from?
> Time: 25 minutes (the first build downloads a lot) · You need: labs 06, 07 and 16

## Problem

Large images are slow to build, slow to push, slow to pull, use disk everywhere they go, and
contain many more programs that could have security problems. The app here is `simple-app`:
about 40 lines of Python plus Flask. Someone wrote its first Dockerfile in a hurry.

Let's reproduce it. This scenario works directly in the app folder. From the repository root:

```bash
cd examples/simple-app
```

The hurried Dockerfile:

<!-- test: contains=FROM python:3.14 -->
```bash
cat optimization/fat.Dockerfile
```

Build it (this downloads the full Python image and compilers, so it takes a while the first time):

<!-- test: timeout=1500 -->
```bash
docker build -f optimization/fat.Dockerfile -t simple-app:fat .
```

## Symptoms

<!-- test: output; contains=fat -->
```bash
docker images simple-app --format 'table {{.Repository}}:{{.Tag}}\t{{.Size}}'
```

```text
REPOSITORY:TAG     SIZE
simple-app:fat     1.75GB
simple-app:1.0     212MB
simple-app:step4   212MB
simple-app:fixed   212MB
simple-app:step2   189MB
simple-app:step1   189MB
```

More than a gigabyte for a tiny app. Symptom in one sentence: *"The image is huge, compared to what the app needs."*

## Investigation

**Step 1: which instruction added what?** `docker history` lists the layers of an image, newest first,
with the instruction that created each layer and its size:

<!-- test: output=head:12; contains=build-essential -->
```bash
docker history --no-trunc --format 'table {{.Size}}\t{{.CreatedBy}}' simple-app:fat
```

```text
SIZE      CREATED BY
0B        CMD ["python" "app.py"]
18.4MB    RUN /bin/sh -c pip install -r requirements.txt # buildkit
16.4kB    COPY . . # buildkit
8.19kB    WORKDIR /app
74.5MB    RUN /bin/sh -c apt-get update && apt-get install -y build-essential curl vim # buildkit
0B        CMD ["python3"]
16.4kB    RUN /bin/sh -c set -eux;  for src in idle3 pip3 pydoc3 python3 python3-config; do   dst="$(echo "$src" | tr -d 3)";   [ -s "/usr/local/bin/$src" ];   [ ! -e "/usr/local/bin/$dst" ];   ln -svT "$src" "/usr/local/bin/$dst";  done # buildkit
83.3MB    RUN /bin/sh -c set -eux;   savedAptMark="$(apt-mark showmanual)";  apt-get update;  apt-get install -y --no-install-recommends   libzstd-dev  ;   wget -O python.tar.xz "https://www.python.org/ftp/python/${PYTHON_VERSION%%[a-z]*}/Python-$PYTHON_VERSION.tar.xz";  echo "$PYTHON_SHA256 *python.tar.xz" | sha256sum -c -;  mkdir -p /usr/src/python;  tar --extract --directory /usr/src/python --strip-components=1 --file python.tar.xz;  rm python.tar.xz;   cd /usr/src/python;  gnuArch="$(dpkg-architecture --query DEB_BUILD_GNU_TYPE)";  ./configure   --build="$gnuArch"   --enable-loadable-sqlite-extensions   --enable-optimizations   --enable-option-checking=fatal   --enable-shared   $(test "${gnuArch%%-*}" != 'riscv64' && echo '--with-lto')   --with-ensurepip  ;  nproc="$(nproc)";  EXTRA_CFLAGS="$(dpkg-buildflags --get CFLAGS)";  LDFLAGS="$(dpkg-buildflags --get LDFLAGS)";  arch="$(dpkg --print-architecture)"; arch="${arch##*-}";  case "$arch" in   amd64|arm64)    EXTRA_CFLAGS="${EXTRA_CFLAGS:-} -fno-omit-frame-pointer -mno-omit-leaf-frame-pointer";    ;;   i386)    ;;   *)    EXTRA_CFLAGS="${EXTRA_CFLAGS:-} -fno-omit-frame-pointer";    ;;  esac;  make -j "$nproc"   "EXTRA_CFLAGS=${EXTRA_CFLAGS:-}"   "LDFLAGS=${LDFLAGS:-}"  ;  rm python;  make -j "$nproc"   "EXTRA_CFLAGS=${EXTRA_CFLAGS:-}"   "LDFLAGS=${LDFLAGS:-} -Wl,-rpath='\$\$ORIGIN/../lib'"   python  ;  make install;   bin="$(readlink -ve /usr/local/bin/python3)";  dir="$(dirname "$bin")";  mkdir -p "/usr/share/gdb/auto-load/$dir";  cp -vL Tools/gdb/libpython.py "/usr/share/gdb/auto-load/$bin-gdb.py";   cd /;  rm -rf /usr/src/python;   find /usr/local -depth   \(    \( -type d -a \( -name test -o -name tests -o -name idle_test \) \)    -o \( -type f -a \( -name '*.pyc' -o -name '*.pyo' -o -name 'libpython*.a' \) \)   \) -exec rm -rf '{}' +  ;   ldconfig;   apt-mark auto '.*' > /dev/null;  apt-mark manual $savedAptMark;  find /usr/local -type f -executable -not \( -name '*tkinter*' \) -exec ldd '{}' ';'   | awk '/=>/ { so = $(NF-1); if (index(so, "/usr/local/") == 1) { next }; gsub("^/(usr/)?", "", so); printf "*%s\n", so }'   | sort -u   | xargs -rt dpkg-query --search   | awk 'sub(":$", "", $1) { print $1 }'   | sort -u   | xargs -r apt-mark manual  ;  apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false;  apt-get dist-clean;   export PYTHONDONTWRITEBYTECODE=1;  python3 --version;  pip3 --version # buildkit
0B        ENV PYTHON_SHA256=c2215904f02b175596dc49351585104f4bc20341e1c47378b26a2c274360ce73
0B        ENV PYTHON_VERSION=3.14.8
19.9MB    RUN /bin/sh -c set -eux;  apt-get update;  apt-get install -y --no-install-recommends   libbluetooth-dev   tk-dev   uuid-dev  ;  apt-get dist-clean # buildkit
...
```

(`--no-trunc` shows the full instruction instead of cutting it after a few words.)
Read the SIZE column from top to bottom and compare it with your own output:

- the `apt-get install -y build-essential curl vim` layer: tools and an editor the app never uses,
  plus the apt package lists that were downloaded and left behind;
- the `pip install` layer: Flask, plus pip's download cache, which stays in the image;
- further down, the layers of the base image `python:3.14` itself. They are by far the biggest part:
  the full image is a complete Debian system with compilers and development files.

**Step 2: what does the app really need at run time?** Only a Python interpreter and Flask:

<!-- test: contains=flask -->
```bash
cat requirements.txt
```

**Step 3: is there junk in `/app`?** `COPY . .` copies everything in the build context:

<!-- test: output -->
```bash
docker run --rm simple-app:fat ls -la /app
```

```text
total 16
drwxr-xr-x 1 root root 4096 Oct  4 04:11 .
drwxr-xr-x 1 root root 4096 Oct  4 04:12 ..
-rwxr-xr-x 1 root root 1087 Oct  4 04:02 app.py
-rwxr-xr-x 1 root root   13 Oct  4 04:03 requirements.txt
```

`.dockerignore` keeps the worst out here, but without it `COPY . .` would copy every file in the folder.

## Commands

| Command | What it told us |
|---|---|
| `docker images` | the image size |
| `docker history --no-trunc --format 'table {{.Size}}\t{{.CreatedBy}}' <image>` | which instruction made which layer, and how big |
| `cat requirements.txt` | what the app really needs |
| `docker run --rm <image> ls -la /app` | what got copied into the image |

## Root Cause

Four habits add up:

1. `FROM python:3.14`: the full image with compilers and headers, instead of `python:3.14-slim`.
2. `apt-get install build-essential curl vim`: tools that are never used at run time (and the apt lists stay in the layer).
3. `pip install` without `--no-cache-dir`: the download cache is kept in the image.
4. `COPY . .` before `pip install`: everything is copied, and every code change re-runs pip (slow builds, see lab 07).

## Fix

The project already has two better Dockerfiles. Build both and compare.

The standard one (`Dockerfile`): slim base image, dependencies first, no pip cache, only `app.py` copied, non-root user:

```bash
docker build -t simple-app:1.0 .
```

The multi-stage one: build tools only in a first stage, a small Alpine-based runtime stage:

<!-- test: timeout=900 -->
```bash
docker build -f optimization/multistage.Dockerfile -t simple-app:multistage .
```

## Verification

<!-- test: output; contains=multistage -->
```bash
docker images simple-app --format 'table {{.Repository}}:{{.Tag}}\t{{.Size}}'
```

```text
REPOSITORY:TAG          SIZE
simple-app:multistage   108MB
simple-app:fat          1.75GB
simple-app:1.0          212MB
simple-app:step4        212MB
simple-app:fixed        212MB
simple-app:step2        189MB
simple-app:step1        189MB
```

The fat image is many times larger than the other two. The optimized images still run the same app:

```bash
docker run -d --name simple -p 5000:5000 simple-app:multistage
```

<!-- test: retry=15; contains=Hello from simple-app -->
```bash
curl -s http://localhost:5000
```

And the compilers are really gone from the multi-stage image:

<!-- test: fail -->
```bash
docker run --rm simple-app:multistage which gcc
```

`which` finds nothing and returns an error: there is no `gcc` in the final image, even though the
builder stage installed it.

## Clean up

```bash
docker rm -f simple
docker rmi simple-app:fat simple-app:multistage
cd ../..
```

We keep `simple-app:1.0`: other labs use it.

## Lesson Learned

- `docker history` shows exactly which Dockerfile line made an image big.
- Start from a slim base image, install only what runs, and clean up in the **same** `RUN` (or use `--no-cache-dir`).
- Order matters: dependencies first, code last.
- Multi-stage builds keep build tools out of the final image: compile in stage 1, copy only the result to stage 2.

Next: [09 · Host changes not reflected](../09-host-changes-not-reflected/README.md)
