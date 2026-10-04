# Lab 05 · Environment Variables

> **Goal:** configure containers from the outside, without changing the image.
> **Time:** about 35 minutes · **You need:** [Lab 04](../04-port-mapping/README.md)

## What you will learn

- What environment variables are and why containers are configured with them
- `-e NAME=value`, `-e NAME` (copy from your shell) and `--env-file`
- How to see a container's variables with `docker exec` and `docker inspect`
- Why you must re-create a container to change its configuration
- How a missing variable stops a real application (PostgreSQL), and how to fix it

```text
         same image                       different configuration
   +------------------+   -e APP_ENV=development   -> container "dev"
   |  postgres:18     |   -e APP_ENV=production    -> container "prod"
   |  (never changes) |   -e POSTGRES_PASSWORD=... -> required by this image
   +------------------+
```

An **environment variable** is a `NAME=value` pair that a process can read. Every program on Linux gets a list of them when it starts. Images are built once and run everywhere; environment variables are how the *same* image behaves differently in development, testing and production.

## Step 1 · Pass a variable with `-e`

From the repository root:

```bash
cd labs/05-environment-variables
```

`env` prints all environment variables of the process. Let's run it in a tiny Alpine container with one extra variable:

<!-- test: output; contains=APP_ENV=development -->
```bash
docker run --rm -e APP_ENV=development alpine:3.24 env
```

```text
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
HOSTNAME=77d7d8d123e5
APP_ENV=development
HOME=/root
```

**What you see:** `PATH` and `HOSTNAME` (set by Docker and the image), `HOME`, and our `APP_ENV=development`. The container ends right away because `env` is a short command; `--rm` deletes it afterwards.

Several variables, values with spaces (use quotes), and `printenv` to print just one:

<!-- test: output; contains=Hello from lab 05 -->
```bash
docker run --rm -e APP_ENV=testing -e GREETING="Hello from lab 05" alpine:3.24 printenv GREETING
```

```text
Hello from lab 05
```

## Step 2 · Copy a variable from your own shell

`-e NAME` without `=value` takes the value from the shell where you type the command:

<!-- test: output; contains=blue -->
```bash
export LAB_COLOR=blue
docker run --rm -e LAB_COLOR alpine:3.24 printenv LAB_COLOR
```

```text
blue
```

Useful in scripts: the value never appears in the command itself.

## Step 3 · Many variables: `--env-file`

Typing ten `-e` options gets old quickly. Put them in a file instead. Create `lab.env` in this lab's folder:

```bash
printf 'APP_ENV=staging\nGREETING=Hello from an env file\nLOG_LEVEL=debug\n' > lab.env
cat lab.env
```

The format is one `NAME=value` per line, no `export`, no quotes needed. Now use it:

<!-- test: output; contains=APP_ENV=staging; contains=LOG_LEVEL=debug -->
```bash
docker run --rm --env-file lab.env alpine:3.24 env
```

```text
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
HOSTNAME=a67e16e72e71
APP_ENV=staging
GREETING=Hello from an env file
LOG_LEVEL=debug
HOME=/root
```

> Real projects keep a `.env.example` in git and the real `.env` **out** of git (`.gitignore`), because it often contains passwords. You will see this in the capstone.

## Step 4 · Look at the variables of a running container

Start a container that stays alive (`sleep 300` keeps the main process busy for 5 minutes):

```bash
docker run -d --name demo -e APP_ENV=development -e GREETING="Hi there" alpine:3.24 sleep 300
```

From the inside, with `docker exec`:

<!-- test: output; contains=development -->
```bash
docker exec demo printenv APP_ENV
```

```text
development
```

From the outside, with `docker inspect` (works even when the container is stopped):

<!-- test: output; contains=APP_ENV=development -->
```bash
docker inspect demo --format '{{json .Config.Env}}'
```

```text
["APP_ENV=development","GREETING=Hi there","PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"]
```

**What you see:** a JSON list with every variable, including the ones that come from the image (`PATH`). Remember this: **anyone who can run `docker inspect` can read every environment variable**. That matters for passwords (Lab 15).

## Step 5 · Can you change a variable of a running container?

Try it with `exec -e`:

<!-- test: output; contains=changed -->
```bash
docker exec -e APP_ENV=changed demo printenv APP_ENV
docker exec demo printenv APP_ENV
```

```text
changed
development
```

The first command prints `changed`, the second still `development`. `exec -e` only sets the variable for that one extra command. The main process got its environment when it started, and that never changes.

**The rule:** to change configuration, you **re-create** the container:

<!-- test: contains=production -->
```bash
docker rm -f demo
docker run -d --name demo -e APP_ENV=production alpine:3.24 sleep 300
docker exec demo printenv APP_ENV
```

This sounds annoying, but it is a feature: containers are **disposable**. You throw one away and create a new one from the same image with new settings. Nothing is lost, as long as important data lives in volumes (Lab 09).

## Break it · A database that refuses to start

The official PostgreSQL image *requires* a password variable. Let's start it without one, in the foreground so we see what happens:

<!-- test: fail; contains=superuser password is not specified -->
```bash
docker run --name db postgres:18-alpine
```

The command ends almost immediately with an error. Don't fix it yet. Let's investigate like an engineer.

## Troubleshoot it

**Observe.** Is the container running?

<!-- test: output; contains=Exited (1) -->
```bash
docker ps -a --filter name=db --format '{{.Names}}: {{.Status}}'
```

```text
db: Exited (1) Less than a second ago
```

`Exited (1)`: the main process failed.

**Investigate.** The logs keep what it printed, even after the container stopped:

<!-- test: output; contains=POSTGRES_PASSWORD -->
```bash
docker logs db
```

```text
Error: Database is uninitialized and superuser password is not specified.
       You must specify POSTGRES_PASSWORD to a non-empty value for the
       superuser. For example, "-e POSTGRES_PASSWORD=password" on "docker run".

       You may also use "POSTGRES_HOST_AUTH_METHOD=trust" to allow all
       connections without a password. This is *not* recommended.

       See PostgreSQL documentation about "trust":
       https://www.postgresql.org/docs/current/auth-trust.html
```

**Root cause.** The message is explicit: the database is new (*uninitialized*), and the image needs `POSTGRES_PASSWORD` to create the administrator ("superuser") account. Good images fail fast with a clear message like this instead of starting in an insecure state.

**Fix.** A container's configuration cannot be changed, so remove it and create it again, this time with the variable (and `-d`, because a database is a server):

```bash
docker rm db
docker run -d --name db -e POSTGRES_PASSWORD=lab-password postgres:18-alpine
```

**Verify.** The database needs a few seconds to initialise. Then ask it for its version:

<!-- test: retry=20; contains=PostgreSQL 18 -->
```bash
docker exec db psql -U postgres -c 'SELECT version();'
```

And notice what `inspect` shows:

<!-- test: contains=POSTGRES_PASSWORD=lab-password -->
```bash
docker inspect db --format '{{json .Config.Env}}'
```

The password is visible in plain text. For a lab that is fine. Lab 15 and the capstone show a better way (secret files).

## Challenge

**Task:** configure the same image two different ways at the same time.

**Requirements:**
- Two Alpine containers, `dev` and `prod`, both running `sleep 300`, both using `lab.env`.
- `prod` must override `APP_ENV` to `production` on the command line; `dev` keeps the value from the file.
- Prove the result for both containers with one command each.

**Hints:** `--env-file` and `-e` can be combined. Which one wins when both set the same name?

**Expected result:** `dev` prints `staging`, `prod` prints `production`.

<details>
<summary>Solution</summary>

<!-- test: output; contains=staging; contains=production -->
```bash
docker run -d --name dev --env-file lab.env alpine:3.24 sleep 300
docker run -d --name prod --env-file lab.env -e APP_ENV=production alpine:3.24 sleep 300
docker exec dev printenv APP_ENV
docker exec prod printenv APP_ENV
```

```text
1c4d192e40f684e71f9c1c79a2bcda282174f6ee60395362de7a9ef6ba03d70f
efef7b62c00d580fd81e59ec449ac8be393e5347c402f461c55196be62b9d046
staging
production
```

**Explanation:** the file gives defaults; a value passed with `-e` on the command line takes precedence over the same name from `--env-file`. This is the typical pattern: shared settings in a file, the few differences on the command line.

</details>

## Verify

You can now:

- [ ] pass variables with `-e NAME=value`, `-e NAME` and `--env-file`
- [ ] read a container's variables with `docker exec ... printenv` and `docker inspect`
- [ ] explain why changing configuration means re-creating the container
- [ ] read an image's error message about a missing variable and fix it
- [ ] explain why environment variables are not a safe place for real passwords

## Clean up

```bash
docker rm -f demo db dev prod
rm -f lab.env
```

## Next

➡️ [Lab 06 · Your first Dockerfile](../06-first-dockerfile/README.md) · 📖 Concepts: [docs/08-environment-variables.md](../../docs/08-environment-variables.md)
