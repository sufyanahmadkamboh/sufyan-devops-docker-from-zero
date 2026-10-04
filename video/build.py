"""Builds the two-part video course from scenes_part1.py and scenes_part2.py.

    PART=1 python video/build.py [page|frames|audio|video|all]      (default: all)
    PART=2 python video/build.py ...

Steps:
  page    write out/page.html (all scenes; ?sc=<scene>&st=<step> shows one frame)
  frames  screenshot every scene/step with headless Edge (shot.mjs) + the YouTube thumbnail
  audio   narrate every step with the Windows speech engine (tts.ps1), measure it, build one WAV
  video   encode one clip per scene (fade in/out) with ffmpeg in Docker, join, add audio
          and write youtube/captions.srt + youtube/chapters.txt
  post    post-production: voice clean-up, original music bed (ducked under the voice), sound effects,
          loudness -14 LUFS; writes the two final copies:
            docker-from-zero-partN-full.mp4    picture + voice + music + sound effects
            docker-from-zero-partN-silent.mp4  the identical picture stream, no audio at all

Requirements: Python 3 with pygments, Node.js 22+, Microsoft Edge, Windows (System.Speech), Docker.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import wave
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from pygments.formatters import HtmlFormatter  # noqa: E402

from components import SVG_DEFS  # noqa: E402
from production import CSS as PRODUCTION_CSS  # noqa: E402
from redact import check, redact  # noqa: E402
import importlib  # noqa: E402

# PART=1 or PART=2 builds the two-part workshop (scenes_part1.py / scenes_part2.py) into out/partN and youtube/partN;
# without PART, the original single video (scenes.py) is built into out/ and youtube/.
PART = os.environ.get("PART", "1")
SCENES = importlib.import_module(f"scenes_part{PART}").SCENES

OUT = HERE / "out" / f"part{PART}" if PART else HERE / "out"
FRAMES, AUDIO = OUT / "frames", OUT / "audio"
YT = HERE / "youtube" / f"part{PART}" if PART else HERE / "youtube"
THUMBNAIL = HERE / (f"thumbnail_part{PART}.html" if PART else "thumbnail.html")
FPS = 30
LEAD, GAP, TAIL, FADE = 0.5, 0.55, 0.7, 0.3   # seconds
ANIM = [0.488, 0.784, 0.936, 0.992]            # eased build-in of newly revealed elements, one frame each
RATE = 24000                                   # narration WAV: 24 kHz, 16-bit, mono
VOICE = os.environ.get("VOICE", "Microsoft David Desktop")
SPEED = os.environ.get("SPEED", "1")                 # speech engine rate, -10..10
FFMPEG_IMAGE = "linuxserver/ffmpeg@sha256:a7182d4fe498feea393622b43513cfaecb3fd073dcd3c7f38e9d74a10a4e8702"

# How the speech engine should say words it would otherwise mangle (captions keep the real spelling).
PRONOUNCE = [
    (r"\bPostgreSQL\b", "postgres Q L"), (r"\bpsql\b", "P S Q L"), (r"\.dockerignore\b", "dot docker ignore"),
    (r"\bdockerignore\b", "docker ignore"), (r"\bstdout\b", "standard out"), (r"\bstderr\b", "standard error"),
    (r"\btmpfs\b", "temp F S"), (r"\bcgroups\b", "C groups"), (r"\bWSL2\b", "W S L 2"), (r"\bWSL\b", "W S L"),
    (r"\bgunicorn\b", "green unicorn"), (r"\bOOMKilled\b", "O O M killed"), (r"\bOOM\b", "out of memory"),
    (r"\bPID\b", "P I D"), (r"\bUID\b", "U I D"), (r"\bIP\b", "I P"), (r"\bIPs\b", "I Ps"),
    (r"\bDockerfiles\b", "Docker files"), (r"\bDockerfile\b", "Docker file"), (r"\bCMD\b", "C M D"),
    (r"\bENTRYPOINT\b", "entry point"), (r"\bWORKDIR\b", "work dir"), (r"\bENV\b", "E N V"),
    (r"\bCOPY\b", "copy"), (r"\bRUN\b", "run"), (r"\bEXPOSE\b", "expose"), (r"\bUSER\b", "user"),
    (r"\bFROM\b", "from"), (r"\bBuildKit\b", "build kit"), (r"\bsha256\b", "shah 256"), (r"\bexec\b", "exec"),
    (r"\bnginx-unprivileged\b", "engine x unprivileged"), (r"\bMiB\b", "mebibytes"), (r"\bGB\b", "gigabytes"),
    (r"\bMB\b", "megabytes"), (r"\bvs\.?\b", "versus"), (r"\balpine\b", "alpine"), (r"\bhello-world\b", "hello world"),
    (r"\blocalhost\b", "local host"), (r"\bpg_isready\b", "P G is ready"), (r"\bVM\b", "V M"),
    (r"\bKyverno's\b", "Kai-verno's"), (r"\bKyverno\b", "Kai-verno"), (r"\bcosign\b", "co-sign"), (r"\bSBOMs\b", "S-boms"),
    (r"\bSBOM\b", "S-bom"), (r"\bSLSA\b", "S L S A"), (r"\bSyft\b", "Sift"), (r"\bGHCR\b", "G H C R"), (r"\bOIDC\b", "O I D C"),
    (r"\bYAML\b", "yammel"), (r"\.yaml\b", " dot yammel"), (r"\bkubectl\b", "kube control"), (r"\bRekor\b", "Recor"),
    (r"\bFulcio\b", "Fool-see-oh"), (r"\bArgo CD\b", "Argo C D"), (r"\bCVEs\b", "C V Ees"), (r"\bCVE\b", "C V E"),
    (r"\bCI\b", "C I"), (r"\bGitOps\b", "git ops"), (r"\bDevOps\b", "dev ops"), (r"\bKustomize\b", "customize"),
    (r"\bkustomization\b", "customization"), (r"\bnginx\b", "engine x"), (r"\bJSON\b", "jason"), (r"\bAPI\b", "A P I"),
    (r"\bCEL\b", "cel"), (r"\bpromtool\b", "prom tool"), (r"\bactionlint\b", "action lint"), (r"\bCODEOWNERS\b", "code owners"),
    (r"\be2e\b", "e 2 e"), (r"\bSHA\b", "shah"), (r"\bEU\b", "E U"), (r"\bID\b", "I D"),
    (r"\bEKS\b", "E K S"), (r"\bVPC\b", "V P C"), (r"\bIAM\b", "I A M"), (r"\bECR\b", "E C R"), (r"\bALB\b", "A L B"),
    (r"\bKMS\b", "K M S"), (r"\bIMDSv2\b", "I M D S version 2"), (r"\bIMDS\b", "I M D S"), (r"\bCIDR\b", "cider"),
    (r"\bnpm\b", "N P M"), (r"\bVite\b", "veet"), (r"\bgitleaks\b", "git leaks"), (r"\bhadolint\b", "hado lint"),
    (r"\bkubeconform\b", "kube conform"), (r"\bzizmor\b", "zizz-more"), (r"\bHTTPS\b", "H T T P S"), (r"\bHTTP\b", "H T T P"),
    (r"\bDNS\b", "D N S"), (r"\bCDN\b", "C D N"), (r"\bWAF\b", "waff"), (r"\bHPA\b", "H P A"), (r"\bS3\b", "S 3"),
    (r"\bTLS\b", "T L S"), (r"\bCLI\b", "C L I"), (r"\bOIDC\b", "O I D C"), (r"\bACM\b", "A C M"), (r"\bREADME\b", "read me"),
]


def spoken(step: dict) -> str:
    text = redact(step["tts"] or step["say"])
    for pattern, repl in PRONOUNCE:
        text = re.sub(pattern, repl, text)
    return text


def frame_name(sc: int, st: int) -> str:
    return f"s{sc:02d}_{st:02d}"


# ------------------------------------------------------------------------------------------------ page
CSS = """
:root{--bg:#0b1420;--panel:#13233a;--line:#284468;--ink:#f1f6fc;--muted:#a9bbd2;--blue:#3b82d6;--sky:#9cc3f0;--ok:#4cc286;--bad:#ff6b6b;--amber:#ffc94d}
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:1920px;height:1080px;overflow:hidden}
body{background:radial-gradient(1300px 800px at 100% 0%,rgba(59,130,214,.24),transparent 60%),radial-gradient(1000px 700px at 0% 100%,rgba(156,195,240,.09),transparent 60%),var(--bg);
 font-family:Inter,"Segoe UI",sans-serif;color:var(--ink);position:relative}
body::before{content:"";position:absolute;inset:0;background-image:linear-gradient(rgba(156,195,240,.045) 1px,transparent 1px),linear-gradient(90deg,rgba(156,195,240,.045) 1px,transparent 1px);background-size:60px 60px}
.scene{display:none;position:absolute;inset:0}
.scene.on{display:block}
.kicker{position:absolute;left:100px;top:58px;color:var(--sky);font-weight:800;font-size:24px;letter-spacing:3px;text-transform:uppercase}
h1{position:absolute;left:100px;right:100px;top:96px;font-size:58px;line-height:1.08;font-weight:900;letter-spacing:-1px}
.content{position:absolute;left:100px;right:100px;top:215px;bottom:115px;display:flex;flex-direction:column;align-items:center;justify-content:center}
.content.split{display:grid;grid-template-columns:minmax(0,1.62fr) minmax(0,1fr);gap:40px;align-items:center}
.st{opacity:0;transition:none}
.st.on{opacity:1}
.grid{display:grid;width:100%}
.card{display:flex;gap:22px;align-items:flex-start;background:var(--panel);border:3px solid var(--line);border-left:10px solid var(--tone);border-radius:22px;padding:24px 26px;min-height:120px}
.card.now{box-shadow:0 0 0 4px var(--tone),0 0 40px rgba(255,255,255,.12);background:#182c49}
.card-icon{font-size:46px;line-height:1}
.card-title{font-size:29px;font-weight:800;margin-bottom:8px}
.card-text{font-size:22px;color:var(--muted);line-height:1.35}
.tile{background:var(--panel);border:3px solid var(--line);border-top:10px solid var(--tone);border-radius:22px;padding:22px 24px;min-height:250px}
.tile.now{box-shadow:0 0 0 4px var(--tone);background:#182c49}
.tile-icon{font-size:44px}.tile-label{font-size:24px;font-weight:700;margin:10px 0 8px;min-height:62px}
.tile-value{font-size:52px;font-weight:900;color:var(--tone)}.tile-note{font-size:20px;color:var(--muted);margin-top:6px}
.compact .tile{min-height:0;padding:16px 22px}.compact .tile-icon{font-size:36px}.compact .tile-label{min-height:0;margin:6px 0 4px}.compact .tile-value{font-size:40px}
.notes{list-style:none;display:flex;flex-direction:column;gap:18px}
.notes li{background:var(--panel);border:3px solid var(--line);border-radius:18px;padding:18px 22px}
.notes li.now{border-color:var(--amber);background:#2b2410}
.notes b{display:block;font-size:28px;margin-bottom:6px}.notes span{font-size:22px;color:var(--muted)}
.checklist{list-style:none;width:100%;display:flex;flex-direction:column;gap:16px}
.checklist li{display:flex;gap:26px;align-items:center;background:var(--panel);border:3px solid var(--line);border-radius:20px;padding:16px 26px}
.checklist li.now{border-color:var(--ok);background:#0f2a22}
.checklist .num{flex:0 0 64px;height:64px;border-radius:50%;background:var(--blue);display:flex;align-items:center;justify-content:center;font-size:30px;font-weight:900}
.checklist b{display:block;font-size:30px}.checklist span{font-size:23px;color:var(--muted)}
.code{background:#0a0f18;border:3px solid var(--line);border-radius:20px;overflow:hidden;width:100%}
.code-bar{display:flex;gap:10px;align-items:center;padding:14px 20px;background:#101b2c;border-bottom:2px solid var(--line)}
.code-bar i{width:14px;height:14px;border-radius:50%;background:#ff6b6b}.code-bar i:nth-child(2){background:#ffc94d}.code-bar i:nth-child(3){background:#4cc286}
.code-bar span{margin-left:14px;font:600 20px "JetBrains Mono",Consolas,monospace;color:var(--muted)}
.code pre{font:500 var(--fs) / 1.45 "JetBrains Mono",Consolas,monospace;padding:18px 0;white-space:pre;font-variant-ligatures:none;overflow:hidden}
.code pre > span[id]{display:block;padding:0 24px;border-left:6px solid transparent}
.code.hlon pre > span[id]{opacity:.42}
.code.hlon pre > span.hl{opacity:1;background:rgba(255,201,77,.13);border-left-color:var(--amber)}
.term{background:#0a0f18;border:3px solid var(--line);border-radius:20px;overflow:hidden;width:100%;padding-bottom:14px}
.tl{font:500 24px/1.72 "JetBrains Mono",Consolas,monospace;padding:0 24px;white-space:pre;overflow:hidden;color:#c9d6e6;font-variant-ligatures:none}
.tl.cmd{color:#9cc3f0;font-weight:700}.tl.ok{color:#4cc286}.tl.bad{color:#ff8a8a}.tl.warn{color:#ffc94d}.tl.dim{color:#7f93ad;font-style:italic}
.tl.now{background:rgba(255,201,77,.10)}
.term{padding-top:0}.term .code-bar{margin-bottom:12px}
svg.dia{max-width:100%;height:auto}
svg text{font-family:Inter,"Segoe UI",sans-serif}
svg g.now rect{filter:drop-shadow(0 0 18px rgba(255,255,255,.35))}
img.shot{max-width:100%;max-height:745px;border-radius:16px;border:3px solid var(--line);box-shadow:0 20px 60px rgba(0,0,0,.5)}
.bottom{position:absolute;left:100px;right:100px;bottom:40px;display:flex;align-items:center;gap:28px;font-size:22px;color:var(--muted)}
.bottom b{color:var(--ink)}
.bar{flex:1;display:flex;gap:6px}
.bar i{flex:1;height:8px;border-radius:4px;background:#22344f}
.bar i.done{background:#3b6fb0}.bar i.cur{background:var(--amber)}
.chap{color:var(--amber);font-weight:800}
"""

JS = """
const q = new URLSearchParams(location.search);
const sc = +(q.get("sc") || 0), st = +(q.get("st") || 0), p = q.has("p") ? +q.get("p") : 1;
const scene = document.querySelector(`.scene[data-i="${sc}"]`);
scene.classList.add("on");
scene.querySelectorAll("[data-s]").forEach(e => {
  const s = +e.dataset.s;
  if (s <= st) e.classList.add("on");
  if (s === st) {
    e.classList.add("now");
    if (p < 1) { e.style.opacity = p; e.style.transform = `translateY(${((1 - p) * 18).toFixed(1)}px)`; }
  }
});
const hl = JSON.parse(scene.dataset.hl)[st];
const code = scene.querySelector("div.code");
if (code && hl) { code.classList.add("hlon"); for (let n = hl[0]; n <= hl[1]; n++) { const l = code.querySelector(`#L-${n}`); if (l) l.classList.add("hl"); } }
window.__ready = true;
"""


def chapters() -> list[tuple[int, str]]:
    return [(i, s["chapter"]) for i, s in enumerate(SCENES) if s["chapter"]]


def write_page() -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    YT.mkdir(parents=True, exist_ok=True)
    chaps = chapters()
    style = HtmlFormatter(style="github-dark").get_style_defs(".code pre")
    parts = []
    for i, s in enumerate(SCENES):
        cur = max(k for k, (start, _) in enumerate(chaps) if start <= i)
        bar = "".join(f'<i class="{"cur" if k == cur else "done" if k < cur else ""}"></i>' for k in range(len(chaps)))
        hl = json.dumps([st["hl"] for st in s["steps"]])
        layout = "split" if s["layout"] == "code" else ""
        parts.append(
            f'<section class="scene" data-i="{i}" data-hl=\'{hl}\'><div class="kicker">{s["kicker"]}</div><h1>{s["title"]}</h1>'
            f'<div class="content {layout}">{s["body"]}</div>'
            f'<div class="bottom"><span><b>Sufyan Ahmad</b> · DevOps Engineer</span><div class="bar">{bar}</div>'
            f'<span class="chap">{chaps[cur][1]}</span></div></section>')
    page = OUT / "page.html"
    html_out = redact(

        '<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Docker From Zero: video</title>'
        '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@500;600;700&display=swap" rel="stylesheet">'
        f"<style>{CSS}{PRODUCTION_CSS}{style}.code pre{{background:transparent}}</style></head><body>{SVG_DEFS}{''.join(parts)}<script>{JS}</script></body></html>")
    problems = check(re.sub(r"<[^>]+>", " ", html_out))
    if problems:
        raise SystemExit(f"redaction check failed for the page: {problems}")
    page.write_text(html_out, encoding="utf-8", newline="\n")
    return page


# ------------------------------------------------------------------------------------------------ frames
def shoot(jobs: list[dict], profile: str) -> None:
    jf = OUT / "jobs.json"
    jf.write_text(json.dumps(jobs), encoding="utf-8")
    subprocess.run(["node", str(HERE / "shot.mjs"), str(jf), str(OUT / profile)], check=True)


def frames() -> None:
    page = write_page()
    FRAMES.mkdir(exist_ok=True)
    for old in FRAMES.glob("*.png"):
        old.unlink()
    url = page.as_uri()
    jobs = [{"url": f"{url}?sc={i}&st={k}", "out": str(FRAMES / f"{frame_name(i, k)}.png")}
            for i, s in enumerate(SCENES) for k in range(len(s["steps"]))]
    jobs += [{"url": f"{url}?sc={i}&st={k}&p={p}", "out": str(FRAMES / f"{frame_name(i, k)}_a{j}.png")}
             for i, s in enumerate(SCENES) for k in range(len(s["steps"])) for j, p in enumerate(ANIM)]
    jobs.append({"url": THUMBNAIL.as_uri(), "out": str(YT / "thumbnail.png"), "w": 1280, "h": 720})
    shoot(jobs, "browser-profile")


# ------------------------------------------------------------------------------------------------ audio
def audio() -> None:
    AUDIO.mkdir(exist_ok=True)
    for old in AUDIO.glob("*.wav"):
        old.unlink()
    items = [{"text": spoken(st), "out": str(AUDIO / f"{frame_name(i, k)}.wav")}
             for i, s in enumerate(SCENES) for k, st in enumerate(s["steps"]) if st["say"]]
    for i, s in enumerate(SCENES):
        for k, st in enumerate(s["steps"]):
            if not st["say"]:                                   # a silent step: hold the picture
                with wave.open(str(AUDIO / f"{frame_name(i, k)}.wav"), "wb") as w:
                    w.setnchannels(1)
                    w.setsampwidth(2)
                    w.setframerate(RATE)
                    w.writeframes(b"\0\0" * round(st.get("hold", 2.0) * RATE))
    (OUT / "tts.json").write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
    subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(HERE / "tts.ps1"),
                    str(OUT / "tts.json"), VOICE, str(RATE), SPEED], check=True)


def wav_seconds(path: Path) -> float:
    with wave.open(str(path)) as w:
        return w.getnframes() / w.getframerate()


def frames_for(seconds: float) -> int:
    return max(1, round(seconds * FPS))


def timeline() -> list[dict]:
    """Per scene: list of steps with frame counts; audio positions in samples."""
    plan = []
    for i, s in enumerate(SCENES):
        steps = []
        for k, st in enumerate(s["steps"]):
            speech = wav_seconds(AUDIO / f"{frame_name(i, k)}.wav")
            if st["say"]:
                n = frames_for(speech + GAP + (LEAD if k == 0 else 0) + (TAIL if k == len(s["steps"]) - 1 else 0))
            else:
                n, speech = frames_for(speech), 0.0
            steps.append({"k": k, "frames": n, "speech": speech, "say": st["say"], "sfx": st.get("sfx")})
        plan.append({"i": i, "steps": steps, "chapter": s["chapter"], "title": s["title"]})
    return plan


def build_audio(plan: list[dict]) -> Path:
    out = OUT / "narration.wav"
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        for sc in plan:
            for st in sc["steps"]:
                total = round(st["frames"] / FPS * RATE)
                lead = round(LEAD * RATE) if st["k"] == 0 and st["say"] else 0
                with wave.open(str(AUDIO / f"{frame_name(sc['i'], st['k'])}.wav")) as r:
                    assert r.getframerate() == RATE and r.getsampwidth() == 2 and r.getnchannels() == 1
                    data = r.readframes(r.getnframes())
                speech = len(data) // 2
                w.writeframes(b"\0\0" * lead + data + b"\0\0" * max(0, total - lead - speech))
    return out


# ------------------------------------------------------------------------------------------------ video
def stamp(t: float, srt: bool = False) -> str:
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    if srt:
        return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s - int(s)) * 1000)) % 1000:03d}"
    return f"{int(h)}:{int(m):02d}:{int(s):02d}" if h else f"{int(m)}:{int(s):02d}"


def sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.?!:])\s+", text.strip())
    out: list[str] = []
    for p in parts:   # keep captions short: split long sentences at commas
        while len(p) > 110 and ", " in p[40:]:
            cut = p.index(", ", 40) + 1
            out.append(p[:cut])
            p = p[cut:].strip()
        out.append(p)
    return [p for p in out if p]


def captions_and_chapters(plan: list[dict]) -> None:
    YT.mkdir(exist_ok=True)
    cues, chaps, t = [], [], 0.0
    for sc in plan:
        if sc["chapter"]:
            chaps.append(f"{stamp(t)} {sc['chapter']}")
        for st in sc["steps"]:
            start = t + (LEAD if st["k"] == 0 else 0)
            parts = sentences(st["say"])
            total_chars = sum(len(p) for p in parts)
            for p in parts:
                d = st["speech"] * len(p) / total_chars
                cues.append((start, start + d, redact(p)))
                start += d
            t += st["frames"] / FPS
    srt = "\n".join(f"{n}\n{stamp(a, True)} --> {stamp(b, True)}\n{text}\n" for n, (a, b, text) in enumerate(cues, 1))
    for name, text in (("captions", srt), ("chapters", "\n".join(chaps))):
        if check(text):
            raise SystemExit(f"redaction check failed for {name}: {check(text)}")
    (YT / "captions.srt").write_text(srt, encoding="utf-8", newline="\n")
    (YT / "chapters.txt").write_text("\n".join(chaps) + "\n", encoding="utf-8", newline="\n")
    tpl = (YT / "description.template.md").read_text(encoding="utf-8")
    description = redact(tpl.replace("{{CHAPTERS}}", "\n".join(chaps)))
    if check(description):
        raise SystemExit(f"redaction check failed for the description: {check(description)}")
    (YT / "description.md").write_text(description, encoding="utf-8", newline="\n")
    print(f"duration {stamp(t)} · {len(cues)} captions · {len(chaps)} chapters")


def video() -> None:
    plan = timeline()
    build_audio(plan)
    clips = OUT / "clips"
    clips.mkdir(exist_ok=True)
    script = ["set -e", "cd /work"]
    joined = []
    for sc in plan:
        lst = clips / f"scene{sc['i']:02d}.txt"
        lines = ["ffconcat version 1.0"]
        for st in sc["steps"]:
            name = frame_name(sc['i'], st['k'])
            for j in range(len(ANIM)):                  # the new elements ease in, one frame each
                lines += [f"file '../frames/{name}_a{j}.png'", f"duration {1 / FPS:.6f}"]
            lines += [f"file '../frames/{name}.png'", f"duration {(st['frames'] - len(ANIM)) / FPS:.6f}"]
        lines.append(f"file '../frames/{frame_name(sc['i'], sc['steps'][-1]['k'])}.png'")   # concat demuxer needs the last file twice
        lst.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
        total = sum(st["frames"] for st in sc["steps"]) / FPS
        vf = f"fps={FPS},format=yuv420p,fade=t=in:st=0:d={FADE},fade=t=out:st={total - FADE:.3f}:d={FADE}"
        script.append(f"ffmpeg -y -loglevel error -f concat -safe 0 -i clips/{lst.name} -vf '{vf}' -frames:v {sum(st['frames'] for st in sc['steps'])} "
                      f"-c:v libx264 -preset slow -crf 18 -tune stillimage -r {FPS} clips/scene{sc['i']:02d}.mp4")
        joined.append(f"file 'scene{sc['i']:02d}.mp4'")
    (clips / "all.txt").write_text("\n".join(joined) + "\n", encoding="utf-8", newline="\n")
    script.append("ffmpeg -y -loglevel error -f concat -safe 0 -i clips/all.txt -i narration.wav -map 0:v -map 1:a "
                  "-af acompressor=threshold=-30dB:ratio=6:attack=5:release=120:makeup=22dB,alimiter=limit=0.89:level=false -c:v copy -c:a aac -b:a 160k -ar 48000 -ac 2 -shortest -movflags +faststart video.mp4")
    (OUT / "encode.sh").write_text("\n".join(script) + "\n", encoding="utf-8", newline="\n")
    subprocess.run(["docker", "run", "--rm", "-v", f"{OUT}:/work", "--entrypoint", "bash", FFMPEG_IMAGE, "/work/encode.sh"], check=True)
    captions_and_chapters(plan)


# ------------------------------------------------------------------------------------------------ post-production
def post() -> None:
    """Mix voice, music and sound effects, then write the full and the silent copy (identical picture)."""
    import audio_assets
    plan = timeline()
    events, t = [], 0.0
    for n, sc in enumerate(plan):
        if n > 0:
            events.append((t, "chapter" if sc["chapter"] else "scene"))
        for st in sc["steps"]:
            if st["sfx"]:
                when = t + (LEAD if st["k"] == 0 and st["say"] else 0)
                events.append((when, st["sfx"]))
            t += st["frames"] / FPS
    total = t
    mix = OUT / "mix"
    mix.mkdir(exist_ok=True)
    # 1. voice clean-up: rumble filter, a little presence, gentle compression, consistent level
    subprocess.run(["docker", "run", "--rm", "-v", f"{OUT}:/work", "--entrypoint", "ffmpeg", FFMPEG_IMAGE, "-y",
                    "-loglevel", "error", "-i", "/work/narration.wav", "-af",
                    "highpass=f=80,equalizer=f=3200:t=q:w=1.2:g=2.5,equalizer=f=250:t=q:w=1:g=-1.5,"
                    "acompressor=threshold=-26dB:ratio=3:attack=5:release=160:makeup=4dB,"
                    "loudnorm=I=-17:TP=-2:LRA=9,aresample=48000", "-ac", "1", "/work/mix/voice.wav"], check=True)
    # 2. music + sound effects + ducking, rendered by audio_assets (all original, generated here)
    audio_assets.render_mix(mix / "voice.wav", mix / "mix.wav", total, events, seed=int(PART or 1))
    # 3. final loudness for YouTube (two-pass loudnorm), then the two copies
    def ff(*args, capture=False):
        r = subprocess.run(["docker", "run", "--rm", "-v", f"{OUT}:/work", "-w", "/work", "--entrypoint", "ffmpeg",
                            FFMPEG_IMAGE, "-hide_banner", "-y", *args], check=True, capture_output=capture, text=True)
        return r.stderr if capture else ""
    measured = json.loads(re.search(r"\{[^{}]*\}", ff("-nostats", "-i", "mix/mix.wav", "-af",
                          "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-", capture=True)).group(0))
    ff("-loglevel", "error", "-i", "mix/mix.wav", "-af",
       "loudnorm=I=-14:TP=-1.5:LRA=11:linear=true:"
       f"measured_I={measured['input_i']}:measured_TP={measured['input_tp']}:measured_LRA={measured['input_lra']}:"
       f"measured_thresh={measured['input_thresh']}:offset={measured['target_offset']},aresample=48000", "mix/final.wav")
    ff("-loglevel", "error", "-i", "video.mp4", "-i", "mix/final.wav", "-map", "0:v", "-map", "1:a", "-c:v", "copy",
       "-c:a", "aac", "-b:a", "320k", "-ar", "48000", "-ac", "2", "-shortest", "-movflags", "+faststart",
       f"docker-from-zero-part{PART}-full.mp4")
    ff("-loglevel", "error", "-i", "video.mp4", "-map", "0:v", "-c:v", "copy", "-an", "-movflags", "+faststart",
       f"docker-from-zero-part{PART}-silent.mp4")
    print(f"post: {len(events)} sound effects, {stamp(total)} -> docker-from-zero-part{PART}-full.mp4 and -silent.mp4")


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    if what in ("page", "all"):
        print("page:", write_page())
    if what in ("frames", "all"):
        frames()
    if what in ("audio", "all"):
        audio()
    if what in ("video", "all"):
        video()
    if what in ("post", "all"):
        post()
