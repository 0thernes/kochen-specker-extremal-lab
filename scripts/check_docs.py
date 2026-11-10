"""check_docs.py - consistency checks of the documents before a release.

  1. every relative link in a Markdown file points to an existing file;
  2. the results table of README.md repeats section A of results/RESULTS.md row for row;
  3. no document contains a phrase from the list STALE (statements that were true in an earlier
     state of the work and are wrong now), a placeholder, or a path of the development machine;
  4. the word PENDING occurs only where the register itself uses it.

usage: python scripts/check_docs.py        exit status 0 if nothing is found
"""
from __future__ import annotations

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {".git", ".lake", "node_modules", "__pycache__", "third_party", "logs", "results", "data"}
DOC_EXT = {".md", ".cff", ".txt", ".html", ".bib", ".tex"}

# phrases that must not appear any more (lower case); extend when a statement is withdrawn
STALE = [
    "may be empty for structural reasons",
    "58 684",
    "first exact minimum in a pool",
    "26 to 7",
    "from 26 to",
    "56/56",
    "56 of 56",
    "four theorems",
    "lake build ks.box3h2 ks.box4h1",
    "_placeholder",
    "fouraxisglucose",
    "cubesverdict",
    "fiveaxis30",
    "ever contain all five",
    "known record (31, 33, 18 or 29",
    "two smallest pools in dimension three were reported",
]
LOCAL_PATH = re.compile(r"(?i)\b[a-z]:\\\\?(users|tools|vibe)|\bK:[\\/]|Users[\\/]Alexa")
LINK = re.compile(r"\[[^\]\n]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")


def documents():
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            if os.path.splitext(name)[1].lower() in DOC_EXT:
                yield os.path.join(dirpath, name)


def register_rows():
    rows = []
    with open(os.path.join(ROOT, "results", "RESULTS.md"), encoding="utf-8") as f:
        for line in f:
            if re.match(r"\|\s*A\d+\s*\|", line):
                rows.append(re.sub(r"\s+", " ", line.strip()))
    return rows


def main():
    problems = []
    reg = register_rows()
    marker_re = re.compile(r"\b[A-Z0-9]{3,}(?:LEMMAS|VERDICT)\b|\bFOURAXISGLUCOSE\b|\bFIVEAXIS30\b")
    readme = re.sub(r"[ \t]+", " ", open(os.path.join(ROOT, "README.md"), encoding="utf-8").read())
    for row in reg:
        if row not in readme:
            problems.append("README.md: results table lacks the register row: " + row[:90] + " ...")
    for path in documents():
        rel = os.path.relpath(path, ROOT).replace("\\", "/")
        text = open(path, encoding="utf-8", errors="replace").read()
        low = text.lower()
        if rel != "scripts/check_docs.py":
            for marker in sorted(set(marker_re.findall(text))):
                problems.append(f"{rel}: unfilled marker {marker}")
        for phrase in STALE:
            # docs/REVIEW.md quotes the withdrawn statements on purpose
            if phrase in low and rel not in ("scripts/check_docs.py", "docs/REVIEW.md"):
                problems.append(f"{rel}: stale phrase {phrase!r}")
        if LOCAL_PATH.search(text):
            problems.append(f"{rel}: path of the development machine: {LOCAL_PATH.search(text).group(0)!r}")
        if "PENDING" in text and rel not in ("results/RESULTS.md", "docs/REVIEW.md", "publication/README.md"):
            n_reg = open(os.path.join(ROOT, "results", "RESULTS.md"), encoding="utf-8").read().count("PENDING")
            if n_reg == 0:
                problems.append(f"{rel}: says PENDING but the register has no pending row")
        if path.endswith(".md"):
            base = os.path.dirname(path)
            for m in LINK.finditer(text):
                target = m.group(1)
                if re.match(r"(?i)^(https?:|mailto:|#)", target):
                    continue
                target = target.split("#")[0]
                if target and not os.path.exists(os.path.normpath(os.path.join(base, target))):
                    problems.append(f"{rel}: broken link {m.group(1)}")
    for p in problems:
        print("PROBLEM", p)
    print(f"{len(problems)} problem(s); register rows checked: {len(reg)}")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
