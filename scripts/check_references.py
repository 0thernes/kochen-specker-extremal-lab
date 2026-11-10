"""check_references.py - print each numbered reference of paper/ks-minimum.md
next to the best match that Crossref returns for it, so that a human can see
at a glance whether the reference exists as cited.  arXiv-only, web and book
entries are looked up by their arXiv number where there is one and are
otherwise marked for manual checking.  Writes results/reference_check.json.

usage: python scripts/check_references.py
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = "ks-extremal-lab-reference-check/1.0 (https://github.com/0thernes/kochen-specker-extremal-lab)"


def get(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def crossref(text):
    q = urllib.parse.quote(text[:300])
    data = json.loads(get(f"https://api.crossref.org/works?query.bibliographic={q}&rows=1"))
    items = data.get("message", {}).get("items", [])
    if not items:
        return None
    it = items[0]
    authors = ", ".join(a.get("family", "") for a in it.get("author", [])[:6])
    year = (it.get("issued", {}).get("date-parts") or [[None]])[0][0]
    return {"title": (it.get("title") or [""])[0], "authors": authors, "year": year,
            "container": (it.get("container-title") or [""])[0], "volume": it.get("volume"),
            "page": it.get("page") or it.get("article-number"), "doi": it.get("DOI"),
            "score": it.get("score")}


def arxiv(num):
    xml = get(f"http://export.arxiv.org/api/query?id_list={num}")
    m = re.search(r"<entry>.*?<title>(.*?)</title>", xml, re.S)
    authors = re.findall(r"<name>(.*?)</name>", xml)
    if not m:
        return None
    return {"title": " ".join(m.group(1).split()), "authors": ", ".join(a.split()[-1] for a in authors[:6])}


def words(s):
    return set(w for w in re.findall(r"[a-z0-9]+", s.lower()) if len(w) > 3)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    text = open(os.path.join(ROOT, "paper", "ks-minimum.md"), encoding="utf-8").read()
    refs = re.findall(r"(?m)^\[(\d+)\] (.+)$", text.split("## References")[1])
    out = []
    for num, ref in refs:
        rec = {"n": int(num), "reference": ref}
        ax = re.search(r"arXiv:([a-z\-]+/\d{7}|\d{4}\.\d{4,5})", ref)
        try:
            if ax:
                rec["arxiv"] = arxiv(ax.group(1))
                time.sleep(3)
            if not re.search(r"https?://", ref) or "doi" in ref.lower() or re.search(r"\(\d{4}\) \d", ref):
                rec["crossref"] = crossref(ref)
        except Exception as e:
            rec["error"] = repr(e)
        best = rec.get("arxiv") or rec.get("crossref")
        if best and best.get("title"):
            overlap = len(words(best["title"]) & words(ref)) / max(1, len(words(best["title"])))
            rec["title_overlap"] = round(overlap, 2)
        verdict = "CHECK BY HAND"
        if rec.get("title_overlap", 0) >= 0.7:
            verdict = "match"
        rec["verdict"] = verdict
        out.append(rec)
        src = "arXiv" if rec.get("arxiv") else ("Crossref" if rec.get("crossref") else "-")
        print(f"[{num}] {verdict:13s} ({src}, overlap {rec.get('title_overlap', '-')}): "
              f"{(best or {}).get('title', '')[:90]} | {(best or {}).get('authors', '')[:60]}", flush=True)
    with open(os.path.join(ROOT, "results", "reference_check.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    n_ok = sum(1 for r in out if r["verdict"] == "match")
    print(f"{n_ok} of {len(out)} references matched automatically; the others need a manual look "
          f"(books, web pages, proceedings titles that differ)")


if __name__ == "__main__":
    main()
