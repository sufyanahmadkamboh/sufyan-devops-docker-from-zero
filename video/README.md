# Video course

A two-part narrated walkthrough of this repository, built from code. **Every terminal in the video shows real output**:
the commands were recorded while `tests/mdrun.py --record` ran the tutorial chapters on a fresh Docker engine, and the
scenes look them up by command (`recordings.py`). Nothing on screen is typed by hand.

| Part | Covers | Script |
|---|---|---|
| 1 · Containers and images | Docker's architecture, image vs. container, run/ps/logs/exec, the lifecycle and why containers stop, ports, environment variables, Dockerfiles step by step, layers and the build cache, .dockerignore | `scenes_part1.py` |
| 2 · Data, networks, Compose, troubleshooting and the capstone | volumes, bind mounts, networking and DNS, the multi-container app by hand and with Compose, limits and OOM kills, security basics, image optimization, registries, three troubleshooting scenarios, the capstone and its 18 checks, safe cleanup | `scenes_part2.py` |

## Files

| File | What it is |
|---|---|
| `scenes_part1.py`, `scenes_part2.py` | the scripts: scenes, narration steps, and the visuals for each step |
| `recordings.py` + `recordings/` | the recorded commands and outputs, and `rec()` to show them in a scene |
| `components.py` | building blocks: cards, tiles, diagrams, highlighted code, terminals |
| `build.py` | page → frames → narration → encode → captions, chapters and description |
| `shot.mjs` | screenshots every frame with one headless Edge/Chrome (no extensions, no sync) |
| `tts.ps1` | narration with the Windows speech engine (`System.Speech`) |
| `redact.py` | removes identifying data from everything that reaches the video; the build fails if any remains |
| `thumbnail_part1.html`, `thumbnail_part2.html` | YouTube thumbnails (1280×720) |
| `assets/` | browser screenshots used in the video |
| `youtube/part1/`, `youtube/part2/` | upload packages: titles, description with chapters, tags, captions (SRT), thumbnail, pinned comment |

## Build

Requirements: Windows (for `System.Speech`), Python 3 with `pygments`, Node.js 22+, Microsoft Edge (or set `BROWSER`),
and Docker (ffmpeg runs in a container pinned by digest).

```text
MDRUN_ALLOW_CLEANUP=1 python tests/mdrun.py --record tests/out tutorial/*.md capstone/README.md   # record
python video/recordings.py                                                                       # copy them here
PART=1 python video/build.py          # output: video/out/part1/video.mp4
PART=2 python video/build.py          # output: video/out/part2/video.mp4
```

## Upload checklist

1. Upload `out/partN/video.mp4`; use the first title in `youtube/partN/title.txt`.
2. Paste `youtube/partN/description.md` (its chapter list becomes YouTube chapters). Replace `{{PART1_LINK}}` /
   `{{PART2_LINK}}` with the video links after uploading both, and add them to one playlist.
3. Thumbnail `youtube/partN/thumbnail.png`; tags from `youtube/partN/tags.txt`.
4. Subtitles: upload `youtube/partN/captions.srt` (English).
5. Pin the comment in `youtube/partN/pinned-comment.txt`.
