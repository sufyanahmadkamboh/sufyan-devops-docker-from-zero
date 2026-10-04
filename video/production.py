"""Production layer shared by both parts: the title sting, the end card and the sound-effect cues.

The scene scripts stay focused on teaching; this module adds the packaging around them:
  * an animated title card at the start (with the intro sound) and an end card at the finish
  * cues for the sound effects: an error tone when something breaks on screen, a chime when it is fixed or proven
Silent steps ("say": "") are held for "hold" seconds; build.py gives them silence instead of narration.
"""

from __future__ import annotations

from components import card, grid


def _intro(part: int, subtitle: str, chips: list[str]) -> dict:
    chip_html = "".join(f'<span class="chip st" data-s="1">{c}</span>' for c in chips)
    body = (
        '<div class="titlecard">'
        '<div class="tc-logo st" data-s="0">🐳</div>'
        '<div class="tc-name st" data-s="0">Docker From Zero</div>'
        f'<div class="tc-part st" data-s="1">Part {part} of 2 · {subtitle}</div>'
        f'<div class="tc-chips">{chip_html}</div>'
        '</div>')
    return {"chapter": None, "kicker": "A hands-on course for complete beginners", "title": "&nbsp;", "body": body,
            "layout": "full", "steps": [{"say": "", "hl": None, "tts": None, "hold": 1.9, "sfx": "intro"},
                                        {"say": "", "hl": None, "tts": None, "hold": 2.3, "sfx": "pop"}]}


def _outro(part: int) -> dict:
    nxt = (card(1, "▶️", "Next: part 2", "volumes, networks, Compose, security, troubleshooting and the capstone", "amber")
           if part == 1 else
           card(1, "🏁", "Your turn", "do the labs, solve the challenges, build and break the capstone", "amber"))
    body = grid([
        card(0, "💻", "The free lab", "github.com/sufyanahmadkamboh/sufyan-devops-docker-from-zero", "ok"),
        nxt,
        card(1, "📚", "Study guide (PDF)", "23 lessons, a glossary and 25 interview questions", "blue"),
        card(1, "🐳", "Ready-made images", "sufibaba6629/docker-from-zero-web and -api on Docker Hub", "blue"),
    ], cols=2)
    return {"chapter": None, "kicker": "Docker From Zero", "title": "Thanks for watching", "body": body, "layout": "full",
            "steps": [{"say": "", "hl": None, "tts": None, "hold": 2.2, "sfx": "outro"},
                      {"say": "", "hl": None, "tts": None, "hold": 5.0}]}


CSS = """
.titlecard{height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:18px;margin-top:-40px}
.tc-logo{font-size:150px;line-height:1}
.tc-name{font-size:118px;font-weight:900;letter-spacing:-3px;color:#f1f6fc}
.tc-part{font-size:44px;font-weight:800;color:#ffc94d}
.tc-chips{display:flex;gap:16px;margin-top:18px}
.chip{background:#13233a;border:3px solid #2496ed;border-radius:40px;padding:10px 26px;font-size:30px;font-weight:800;color:#f1f6fc}
"""


def package(scenes: list[dict], part: int, subtitle: str, chips: list[str], cues: dict[str, dict[int, str]]) -> None:
    """Add the title card and end card, and mark sound-effect cues (title fragment -> {step: kind})."""
    for frag, marks in cues.items():
        hits = [s for s in scenes if frag in s["title"]]
        if len(hits) != 1:
            raise SystemExit(f"sound cue: {frag!r} matches {len(hits)} scenes")
        for k, kind in marks.items():
            hits[0]["steps"][k]["sfx"] = kind
    intro = _intro(part, subtitle, chips)
    intro["chapter"], scenes[0]["chapter"] = scenes[0]["chapter"], None   # YouTube chapters must start at 0:00
    scenes.insert(0, intro)
    scenes.append(_outro(part))
