# .dockerignore

> Lesson 11 · about 30 minutes · you need: [10 · Image Layers](10-image-layers.md)

## What is it?

`.dockerignore` is a file next to your Dockerfile that lists files and folders Docker must **not**
send to the build. It uses the same idea as `.gitignore`.

```text
   examples/simple-app/                      sent to the engine (build context)
   ├── app.py                       ------>  app.py
   ├── requirements.txt             ------>  requirements.txt
   ├── .env            (secrets!)       X    (ignored)
   ├── junk/           (60 MB)          X    (ignored)
   ├── dockerfile-steps/                X    (ignored)
   └── .dockerignore                         (read by docker build, not sent)
```

## Why do we need it?

Before the first instruction runs, `docker build` packs up the **whole build context** folder and
sends it to the engine. Without `.dockerignore`:

- **builds are slow:** large folders (`.git`, `node_modules`, test data, logs) are transferred every time;
- **secrets leak:** `COPY . .` copies your `.env`, SSH keys or credentials **into the image**,
  where anyone who gets the image can read them;
- **the cache breaks more often:** an unrelated file changing (a log file) invalidates `COPY . .`.

## How does it work?

`docker build -t name .` → the CLI reads `./.dockerignore`, leaves out every match, and sends the
rest. Patterns:

| Pattern | Matches |
|---|---|
| `.env` | the file `.env` in the context root |
| `*.log` | every `.log` file in the root |
| `**/*.log` | `.log` files in any folder |
| `junk/` | the folder `junk` and everything in it |
| `!keep.log` | exception: do send `keep.log` after all |

This repository's `examples/simple-app/.dockerignore`:

```text
.git
.env
*.log
__pycache__/
*.pyc
junk/
dockerfile-steps/
optimization/
Dockerfile*
.dockerignore
```

`docker build -f dockerfile-steps/03.Dockerfile .` still works although `dockerfile-steps/` is
ignored: the CLI always sends the Dockerfile you name with `-f` separately.

## Prerequisites

- `examples/simple-app/` and the step 02 Dockerfile (`COPY . .`) from lesson 09.

## Hands-on Lab

We create the two kinds of files that cause trouble: a big folder and a fake secret.

```bash
cd examples/simple-app
mkdir -p junk
head -c 60000000 /dev/zero > junk/big-test-data.bin
echo "DB_PASSWORD=super-secret-do-not-ship" > .env
```

**Before:** switch the `.dockerignore` off by renaming it, and build with `COPY . .`:

<!-- test: timeout=600; contains=transferring context; output -->
```bash
mv .dockerignore dockerignore.off
docker build --progress=plain -f dockerfile-steps/02.Dockerfile -t ignore-test:before . 2>&1 | grep 'transferring context'
```

```text
#3 transferring context: 2B done
#4 transferring context: 60.02MB 2.4s done
```

Look inside the image:

<!-- test: contains=super-secret; contains=junk; output -->
```bash
docker run --rm ignore-test:before ls -a /app
docker run --rm ignore-test:before cat /app/.env
```

```text
.
..
.env
Dockerfile
app.py
dockerfile-steps
dockerignore.off
junk
optimization
requirements.txt
DB_PASSWORD=super-secret-do-not-ship
```

**After:** switch the `.dockerignore` back on and build again:

<!-- test: timeout=600; contains=transferring context; output -->
```bash
mv dockerignore.off .dockerignore
docker build --progress=plain -f dockerfile-steps/02.Dockerfile -t ignore-test:after . 2>&1 | grep 'transferring context'
```

```text
#3 transferring context: 295B done
#4 transferring context: 63B 0.0s done
```

<!-- test: absent=junk; absent=.env; output -->
```bash
docker run --rm ignore-test:after ls -a /app
```

```text
.
..
app.py
requirements.txt
```

The guided lab is [labs/08-dockerignore](../labs/08-dockerignore/README.md).

## Expected Result

- **Before:** `transferring context` shows tens of MB; the image contains `.env` (with the
  "password") and `junk/`.
- **After:** the context is a few kB; `/app` contains only the app files.

Compare the image sizes too:

<!-- test: output -->
```bash
docker images ignore-test --format 'table {{.Tag}}\t{{.Size}}'
```

```text
TAG       SIZE
before    250MB
after     189MB
```

## Experiment

`docker history` shows that the 60 MB came in with the `COPY . .` layer:

<!-- test: contains=COPY -->
```bash
docker history ignore-test:before --format '{{.Size}}\t{{.CreatedBy}}' | head -3
```

## Break It

Ignore rules can also be **too greedy**. Scenario
[05 · Dockerfile build fails](../troubleshooting/05-dockerfile-build-fails/README.md) has a
`.dockerignore` with `*.txt` in it. Build it:

<!-- test: fail; contains=requirements.txt -->
```bash
docker build -t ts05 ../../troubleshooting/05-dockerfile-build-fails
```

## Troubleshoot It

- **Observe:** the build fails at `COPY requirements.txt .` with
  `failed to compute cache key: ... "/requirements.txt": not found`.
- **Investigate:** the file **does** exist on disk (`ls ../../troubleshooting/05-dockerfile-build-fails`).
  "Not found" means "not in the build context". Read that folder's `.dockerignore`:

<!-- test: contains=*.txt -->
```bash
cat ../../troubleshooting/05-dockerfile-build-fails/.dockerignore
```

- **Root cause:** `*.txt` excludes `requirements.txt` from the context.
- **Fix and verify:** the scenario's README walks through the fix. In short: be specific
  (`notes.txt`, or `*.log` only), or add an exception line `!requirements.txt`.

## Common Mistakes

- No `.dockerignore` at all, together with `COPY . .`.
- Putting `.dockerignore` in the wrong folder: it must be in the **root of the build context**
  (the folder you pass to `docker build`), not next to a Dockerfile in a subfolder.
- Believing `.env` is safe because it is in `.gitignore`. Git and Docker read different ignore files.
- Patterns that are too broad (`*.txt`, `*.json`) and exclude files the build needs.

## Best Practices

- Create `.dockerignore` together with the Dockerfile, always.
- Start with: `.git`, `.env`, `*.log`, dependency folders (`node_modules`, `__pycache__`), test data.
- Prefer copying only what you need (`COPY app.py .`) over `COPY . .`.
- Never rely on `.dockerignore` alone for secrets: keep secrets out of the project folder, or pass
  them at run time (lesson [19 · Security Basics](19-security-basics.md)).

## Challenge

Without renaming any file, prove that `.env` and `junk/` are **not** sent with the current
`.dockerignore`, using a throw-away Dockerfile piped into `docker build`. Hint: a Dockerfile can
`COPY . /ctx` and list `/ctx`.

## Solution

<details><summary>Show the solution</summary>

`-f -` reads the Dockerfile from standard input while `.` is still the build context:

<!-- test: timeout=600; contains=app.py; absent=junk; absent=.env -->
```bash
printf 'FROM alpine:3.24\nCOPY . /ctx\nCMD ["ls", "-a", "/ctx"]\n' | docker build -q -t context-check -f - .
docker run --rm context-check
```

</details>

## Verification

- [ ] You can explain what the build context is and when it is sent.
- [ ] You can write `.dockerignore` patterns.
- [ ] You proved that a missing `.dockerignore` puts secrets into an image.
- [ ] You can recognise a build failure caused by an over-eager ignore rule.

Clean up (delete the test data and return to the repository root):

```bash
rm -rf junk .env
docker rmi ignore-test:before ignore-test:after context-check
cd ../..
```

## Real-World Usage

- Leaked credentials inside public images are a real, recurring security incident; a
  `.dockerignore` is the cheapest protection.
- Large monorepos can have gigabytes in the build context; ignoring them turns minute-long
  "sending context" phases into seconds.
- Security reviews check `.dockerignore` next to every Dockerfile.

## Key Takeaways

- The build context is sent before the build; `.dockerignore` decides what is in it.
- Without it, builds are slower and secrets can end up inside images.
- "not found" in `COPY` usually means "excluded from or outside the context".
- Next: [12 · Volumes](12-volumes.md).
