"""Real terminal output for the video, taken from the test run of the lessons.

`python tests/mdrun.py --record tests/out ...` saves every command and its output while the lessons run on a fresh
Docker engine. `python video/recordings.py` copies the recordings the video uses into video/recordings/ (committed,
so the video can be rebuilt), and the scenes call rec() to show them. Nothing in the video's terminals is typed by hand.
"""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REC = HERE / "recordings"
SOURCES = ["tutorial", "labs", "troubleshooting", "capstone"]


def _load(src: str) -> list[tuple[str, str]]:
    """All (command, output) pairs recorded for one lesson file, in order."""
    folder = REC / src.replace("/", "__").removesuffix(".md")
    if not folder.is_dir():
        raise SystemExit(f"no recordings for {src}: run tests/mdrun.py --record tests/out, then python video/recordings.py")
    pairs = []
    for f in sorted(folder.glob("*.txt"), key=lambda p: int(p.name.split("-")[0])):
        text = f.read_text(encoding="utf-8")
        cmd, _, rest = text.partition("\n---\n")
        out = re.sub(r"\n# exit -?\d+\n?$", "", rest)
        pairs.append((cmd.strip("\n"), out.rstrip("\n")))
    return pairs


def rec(src: str, match: str, step: int = 0, out_step: int | None = None, nth: int = 0, head: int | None = None,
        tail: int | None = None, grep: str | None = None, drop: str | None = None, cmd: str | None = None,
        tones: dict | None = None, width: int = 118) -> list[tuple[int, str, str]]:
    """Terminal lines for the nth recorded block of `src` whose command contains `match`.

    head/tail/grep/drop select output lines; tones maps a substring to a line style (ok, bad, warn, dim);
    cmd replaces the shown command (e.g. to show only the interesting line of a multi-line block)."""
    hits = [(c, o) for c, o in _load(src) if match in c]
    if len(hits) <= nth:
        raise SystemExit(f"{src}: no recorded command containing {match!r}")
    command, output = hits[nth]
    lines = [x for x in output.split("\n")]
    if grep:
        lines = [x for x in lines if re.search(grep, x)]
    if drop:
        lines = [x for x in lines if not re.search(drop, x)]
    if head is not None and len(lines) > head:
        lines = lines[:head] + ["..."]
    if tail is not None and len(lines) > tail:
        lines = ["..."] + lines[-tail:]
    o = step if out_step is None else out_step
    shown = []
    for c in (cmd if cmd is not None else command).split("\n"):
        shown.append((step, "$ " + c if c.strip() else "", "cmd"))
    for x in lines:
        kind = "out"
        for key, tone in (tones or {}).items():
            if key in x:
                kind = tone
        if len(x) > width:
            x = x[:width - 1] + "…"
        shown.append((o, x, kind))
    return shown


def collect(out_dir: Path) -> None:
    """Copy the recordings of the lesson folders the video uses into video/recordings/."""
    if REC.exists():
        shutil.rmtree(REC)
    REC.mkdir()
    n = 0
    for folder in sorted(out_dir.iterdir()):
        if folder.is_dir() and folder.name.split("__")[0] in SOURCES:
            shutil.copytree(folder, REC / folder.name)
            n += len(list(folder.glob("*.txt")))
    print(f"copied {n} recordings into {REC.relative_to(HERE.parent)}")


if __name__ == "__main__":
    collect(Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.parent / "tests" / "out")
