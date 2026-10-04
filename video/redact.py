"""Redaction for everything that ends up in the video, captions or description.

Recorded command output from a real AWS account contains identifying details. Every text that is drawn on a
frame, spoken, or written to youtube/ passes through redact() first, and check() fails the build if anything
identifying is still present.

Blocked words are stored only as SHA-256 hashes, so this file does not itself contain the names it removes.
Add more with REDACT_WORDS=a,b,c (plain words, taken from the environment, never committed).
"""

from __future__ import annotations

import hashlib
import os
import re

# 12-digit AWS account IDs (alone, in ARNs, and in ECR registry hostnames).
_ACCOUNT = re.compile(r"(?<![0-9])[0-9]{12}(?![0-9])")
# E-mail addresses other than the author's public one.
_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PUBLIC_EMAILS = {"sufyanahmad1@gmail.com"}
# SHA-256 of blocked words (lower case), e.g. an organisation name.
_BLOCKED_HASHES = {"b24810587952a34ee9282bc7d43d93d5fec03ab35e423675bbea0ec137dbd163"}
_BLOCKED_HASHES |= {hashlib.sha256(w.strip().lower().encode()).hexdigest()
                    for w in os.environ.get("REDACT_WORDS", "").split(",") if w.strip()}
_WORD = re.compile(r"[A-Za-z0-9]+")


def _blocked(word: str) -> bool:
    return hashlib.sha256(word.lower().encode()).hexdigest() in _BLOCKED_HASHES


def redact(text: str) -> str:
    text = _ACCOUNT.sub("<account-id>", text)
    text = _EMAIL.sub(lambda m: m.group(0) if m.group(0) in _PUBLIC_EMAILS else "<email>", text)
    return _WORD.sub(lambda m: "<org>" if _blocked(m.group(0)) else m.group(0), text)


def check(text: str) -> list[str]:
    """Returns the problems still present in text (empty list = clean)."""
    problems = []
    if _ACCOUNT.search(text):
        problems.append("12-digit account ID")
    if any(_blocked(m.group(0)) for m in _WORD.finditer(text)):
        problems.append("blocked word")
    for m in _EMAIL.finditer(text):
        if m.group(0) not in _PUBLIC_EMAILS:
            problems.append("private e-mail address")
    return problems


if __name__ == "__main__":
    sample = "arn:aws:iam::123456789012:role/x 123456789012.dkr.ecr.eu-central-1.amazonaws.com someone@corp.example"
    out = redact(sample)
    print(out)
    assert not check(out), check(out)
    print("redaction self-test ok")
