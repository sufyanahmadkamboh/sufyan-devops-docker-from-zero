#!/usr/bin/env python3
"""mdrun: run the commands in the Markdown lessons, exactly as a learner would type them.

Every ```bash block in a lesson is executed in order, in one working directory that
carries over from block to block (so a `cd` in one block applies to the next).
A block passes when it exits with status 0, unless it is marked as an expected failure.

Annotations are HTML comments on the line right before a block (invisible on GitHub):

    <!-- test: skip -->                 do not run (interactive or long-running commands)
    <!-- test: fail -->                 the block MUST fail (we break things on purpose)
    <!-- test: contains=TEXT -->        the output must contain TEXT (repeatable, separated by ;)
    <!-- test: absent=TEXT -->          the output must NOT contain TEXT
    <!-- test: retry=N -->              retry up to N times, 1 s apart (e.g. waiting for a server)
    <!-- test: timeout=S -->            seconds before the block is killed (default 300)
    <!-- test: output -->               with --update: write the real output into the ```text block below
    <!-- test: output=head:N -->        ... only the first N lines (also tail:N)

Hidden steps that run but are not shown to readers (setup, cleanup, waiting):

    <!-- test-run: docker rm -f web -->

Usage:
    python tests/mdrun.py labs/01-first-container/README.md     run one lesson
    python tests/mdrun.py --update labs/*/README.md            run and refresh the shown outputs
    python tests/mdrun.py --record out/ ...                    also save every command + output

WARNING: before and after each file, mdrun removes ALL containers, unused networks and unused
volumes on this Docker engine, so every lesson starts from a clean state. Images are kept.
Run it in CI or on a machine where that is fine; it refuses to run otherwise unless
MDRUN_ALLOW_CLEANUP=1 is set.
"""
from __future__ import annotations

import argparse
import os
import re
import shlex
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FENCE = re.compile(r"^(\s*)```(\w*)\s*$")
ANNOT = re.compile(r"^\s*<!--\s*test:\s*(.*?)\s*-->\s*$")
HIDDEN_ONE = re.compile(r"^\s*<!--\s*test-run:\s*(.*?)\s*-->\s*$")
ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
WINDOWS = os.name == "nt"


@dataclass
class Block:
    line: int                      # 1-based line of the opening fence
    code: str
    hidden: bool = False
    opts: dict = field(default_factory=dict)
    contains: list = field(default_factory=list)
    absent: list = field(default_factory=list)
    out_start: int | None = None   # line index range of the ```text block to refresh
    out_end: int | None = None


def parse_annotation(text: str, block: Block) -> None:
    for part in [p.strip() for p in text.split(";") if p.strip()]:
        key, _, val = part.partition("=")
        key = key.strip()
        val = val.strip().strip('"')
        if key == "contains":
            block.contains.append(val)
        elif key == "absent":
            block.absent.append(val)
        else:
            block.opts[key] = val or True


def parse(path: Path) -> tuple[list[str], list[Block]]:
    lines = path.read_text(encoding="utf-8").split("\n")
    blocks: list[Block] = []
    i = 0
    while i < len(lines):
        hidden = HIDDEN_ONE.match(lines[i])
        if hidden:
            blocks.append(Block(line=i + 1, code=hidden.group(1), hidden=True))
            i += 1
            continue
        m = FENCE.match(lines[i])
        if m and m.group(2) in ("bash", "sh"):
            start = i
            j = i + 1
            while j < len(lines) and not FENCE.match(lines[j]):
                j += 1
            block = Block(line=start + 1, code="\n".join(lines[start + 1:j]))
            k = start - 1
            while k >= 0 and ANNOT.match(lines[k]):        # one or more annotation lines
                parse_annotation(ANNOT.match(lines[k]).group(1), block)
                k -= 1
            # an output block directly below (only blank lines in between)
            n = j + 1
            while n < len(lines) and not lines[n].strip():
                n += 1
            if n < len(lines) and FENCE.match(lines[n]) and FENCE.match(lines[n]).group(2) == "text":
                e = n + 1
                while e < len(lines) and not FENCE.match(lines[e]):
                    e += 1
                block.out_start, block.out_end = n, e
            blocks.append(block)
            i = j + 1
            continue
        elif m:                                              # skip other fenced blocks entirely
            j = i + 1
            while j < len(lines) and not FENCE.match(lines[j]):
                j += 1
            i = j + 1
            continue
        i += 1
    return lines, blocks


def sanitize(text: str) -> str:
    text = ANSI.sub("", text.replace("\r\n", "\n"))
    # docker pull / build progress lines rewrite themselves with \r: keep the final state
    text = "\n".join(line.split("\r")[-1] for line in text.split("\n"))
    # Docker 29 prints this only when the output is not a terminal; learners at a terminal never see it
    text = text.replace("WARNING: This output is designed for human readability. For machine-readable output, "
                        "please use --format.\n", "")
    root = str(ROOT)
    for form in {root, root.replace("\\", "/"), "/" + root[0].lower() + root[2:].replace("\\", "/")}:
        text = text.replace(form, "~/sufyan-devops-docker-from-zero")
    return text.rstrip("\n")


def shell() -> list[str]:
    if WINDOWS:
        for candidate in (r"C:\Program Files\Git\bin\bash.exe", r"C:\Program Files\Git\usr\bin\bash.exe"):
            if Path(candidate).exists():
                return [candidate]
    return ["bash"]


ENV = {**os.environ, "DOCKER_CLI_HINTS": "false", "NO_COLOR": "1", "BUILDKIT_PROGRESS": "plain",
       "COMPOSE_PROGRESS": "plain", "COMPOSE_ANSI": "never", "MSYS_NO_PATHCONV": "1", "TERM": "dumb"}
PROBE = re.compile(r"\s*(curl|wget|docker exec|docker run --rm|docker logs|docker compose exec)\b")
STARTS = re.compile(r"docker (run|create|rm|compose (up|start|run)|network (create|connect|disconnect)|volume create)\b|"
                    r"^\s*(printf|echo|cat)\b.*>", re.M)
# Git Bash on Windows only: its curl cannot write to "/dev/null" when path conversion is off (exit 23)
CURL_SHIM = ('curl() { local a=() x; for x in "$@"; do [ "$x" = /dev/null ] && x=NUL; a+=("$x"); done; '
             'command curl "${a[@]}"; }')


def execute(code: str, cwd: str, timeout: int) -> tuple[str, int, str]:
    """Run code with bash -e in cwd. Returns (output, exit status, working directory at the end)."""
    state = tempfile.NamedTemporaryFile(delete=False, suffix=".cwd")
    state.close()
    script = "\n".join(["set -eo pipefail", CURL_SHIM if WINDOWS else "", f"cd {shlex.quote(cwd)}", code,
                        f"pwd > {shlex.quote(Path(state.name).as_posix())}", ""])
    try:
        p = subprocess.run(shell() + ["-c", script], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout, env=ENV)
        out, rc = p.stdout, p.returncode
    except subprocess.TimeoutExpired as e:
        partial = e.stdout.decode(errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
        out, rc = partial + f"\n[timed out after {timeout}s]", 124
    new_cwd = Path(state.name).read_text(encoding="utf-8").strip() or cwd
    os.unlink(state.name)
    if WINDOWS and re.match(r"^/[a-z]/", new_cwd):                 # /c/Users/... -> C:/Users/...
        new_cwd = new_cwd[1].upper() + ":" + new_cwd[2:]
    return out, rc, new_cwd


def run_block(block: Block, cwd: str, record_to: Path | None) -> tuple[bool, str, str, str]:
    timeout = int(block.opts.get("timeout", 300))
    tries = int(block.opts.get("retry", 1))
    expect_fail = "fail" in block.opts
    code, setup_out = block.code, ""
    if tries > 1:
        # A retried block often starts something ("docker run -d --name web ...") and then probes it ("curl ...").
        # Repeating the start would fail (the name is taken), so the setup part runs once and only the probe
        # (from the first curl / wget / docker exec / docker run --rm / docker logs line on) is retried.
        lines = block.code.split("\n")
        at = next((i for i, line in enumerate(lines) if PROBE.match(line)), 0)
        setup = "\n".join(lines[:at])
        # split only when the setup starts something that cannot simply run twice, and sets no shell variables
        # (the probe runs in a new shell, so variables would be lost)
        if at > 0 and STARTS.search(setup) and not re.search(r"^\s*[A-Za-z_]\w*=", setup, re.M):
            setup_out, rc, cwd = execute("\n".join(lines[:at]), cwd, timeout)
            if rc != 0 and not expect_fail:
                out = sanitize(setup_out)
                return False, f"exit status {rc} (before the retried part)\n{out[-2500:]}", out, cwd
            code = "\n".join(lines[at:])
    for attempt in range(tries):
        raw, rc, new_cwd = execute(code, cwd, timeout)
        out = sanitize(setup_out + raw)
        problems = []
        if expect_fail and rc == 0:
            problems.append("expected this block to fail, but it succeeded")
        if not expect_fail and rc != 0:
            problems.append(f"exit status {rc}")
        problems += [f"output does not contain {t!r}" for t in block.contains if t not in out]
        problems += [f"output contains {t!r}" for t in block.absent if t in out]
        if not problems or attempt == tries - 1:
            break
        time.sleep(1)
    if record_to is not None and not block.hidden:
        record_to.write_text(f"{block.code}\n---\n{out}\n# exit {rc}\n", encoding="utf-8")
    why = "; ".join(problems) + ("\n" + out[-2500:] if problems else "")
    return not problems, why, out, new_cwd


def cleanup() -> None:
    """Every lesson starts from a clean engine: no containers, no unused networks or volumes."""
    ids = subprocess.run(["docker", "ps", "-aq"], capture_output=True, text=True).stdout.split()
    if ids:
        subprocess.run(["docker", "rm", "-f", *ids], capture_output=True)
    subprocess.run(["docker", "network", "prune", "-f"], capture_output=True)
    subprocess.run(["docker", "volume", "prune", "-af"], capture_output=True)


def shown_output(out: str, spec) -> list[str]:
    lines = out.split("\n") if out else []
    if isinstance(spec, str) and ":" in spec:
        kind, n = spec.split(":", 1)
        n = int(n)
        if kind == "head" and len(lines) > n:
            lines = lines[:n] + ["..."]
        elif kind == "tail" and len(lines) > n:
            lines = ["..."] + lines[-n:]
    return lines


def run_file(path: Path, update: bool, record: Path | None) -> tuple[int, int]:
    lines, blocks = parse(path)
    cwd = str(ROOT).replace("\\", "/")
    rel = path.resolve().relative_to(ROOT).as_posix()
    print(f"\n=== {rel}")
    cleanup()
    passed = failed = 0
    edits = []                                      # (start, end, new lines) for --update
    rec_dir = None
    if record:
        rec_dir = record / rel.replace("/", "__").removesuffix(".md")
        rec_dir.mkdir(parents=True, exist_ok=True)
    shown = 0
    for b in blocks:
        if "skip" in b.opts:
            print(f"  skip  line {b.line}")
            continue
        rec_file = None
        if rec_dir and not b.hidden:
            shown += 1
            rec_file = rec_dir / f"{shown:02d}-line{b.line}.txt"
        ok, why, out, cwd = run_block(b, cwd, rec_file)
        label = "hidden" if b.hidden else "block"
        if ok:
            passed += 1
            print(f"  ok    line {b.line} {label}")
        else:
            failed += 1
            print(f"  FAIL  line {b.line} {label}: {why}")
        if update and "output" in b.opts and b.out_start is not None and ok:
            edits.append((b.out_start + 1, b.out_end, shown_output(out, b.opts["output"])))
    cleanup()
    if update and edits:
        for start, end, new in sorted(edits, reverse=True):
            lines[start:end] = new
        path.write_text("\n".join(lines), encoding="utf-8", newline="\n")
        print(f"  updated {len(edits)} output block(s)")
    return passed, failed


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+")
    ap.add_argument("--update", action="store_true", help="refresh ```text output blocks marked with output")
    ap.add_argument("--record", type=Path, help="save every command and its output into this folder")
    args = ap.parse_args()
    if not (os.environ.get("CI") or os.environ.get("MDRUN_ALLOW_CLEANUP") == "1"):
        print("mdrun removes all containers, unused networks and unused volumes before each lesson.\n"
              "Set MDRUN_ALLOW_CLEANUP=1 to confirm this is fine on this machine.", file=sys.stderr)
        return 2
    total_ok = total_fail = 0
    for f in args.files:
        ok, bad = run_file(Path(f), args.update, args.record)
        total_ok += ok
        total_fail += bad
    print(f"\n{total_ok} passed, {total_fail} failed")
    return 1 if total_fail else 0


if __name__ == "__main__":
    sys.exit(main())
