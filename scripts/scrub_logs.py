"""scrub_logs.py - replace local user paths in logs/ by a placeholder before the
logs are committed.  Only the path prefix up to and including the user name is
replaced (by "<home>"); nothing else is touched.  Prints the files changed.

usage: python scripts/scrub_logs.py [--check]     (--check: exit 1 if a local path is present)
"""
from __future__ import annotations

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAT = re.compile(r"(?i)(?:[A-Z]:)?[\\/]+Users[\\/]+[^\\/\s\"']+")
SKIP_DIRS = {".git", ".lake", "node_modules", "__pycache__"}
TEXT_EXT = {".log", ".out", ".txt", ".json", ".md", ".err"}


def main():
    check = "--check" in sys.argv
    hits = []
    for base in ("logs", "results", "docs", "publication"):
        for dirpath, dirnames, filenames in os.walk(os.path.join(ROOT, base)):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for name in filenames:
                if os.path.splitext(name)[1].lower() not in TEXT_EXT:
                    continue
                path = os.path.join(dirpath, name)
                try:
                    text = open(path, encoding="utf-8", errors="surrogateescape").read()
                except OSError:
                    continue
                new = PAT.sub("<home>", text)
                if new != text:
                    hits.append(os.path.relpath(path, ROOT))
                    if not check:
                        with open(path, "w", encoding="utf-8", errors="surrogateescape", newline="") as f:
                            f.write(new)
    for h in hits:
        print(("local path found: " if check else "scrubbed: ") + h)
    print(f"{len(hits)} file(s) " + ("contain local paths" if check else "changed"))
    sys.exit(1 if (check and hits) else 0)


if __name__ == "__main__":
    main()
