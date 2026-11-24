"""Repository-wide integrity, version sync, license, doc link, CRLF, and Lean hygiene checks."""
from __future__ import annotations

import hashlib
import json
import os
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def strip_lean_comments(src: str) -> str:
    """Remove nested /- ... -/ block comments, -- line comments, and string literals."""
    out: list[str] = []
    i, n, depth, in_str = 0, len(src), 0, False
    while i < n:
        if depth > 0:
            if src[i : i + 2] == "/-":
                depth += 1
                i += 2
            elif src[i : i + 2] == "-/":
                depth -= 1
                i += 2
            else:
                if src[i] == "\n":
                    out.append("\n")
                i += 1
        elif in_str:
            if src[i] == "\\" and i + 1 < n:
                i += 2
            elif src[i] == '"':
                in_str = False
                i += 1
            else:
                if src[i] == "\n":
                    out.append("\n")
                i += 1
        else:
            if src[i : i + 2] == "/-":
                depth = 1
                i += 2
            elif src[i : i + 2] == "--":
                while i < n and src[i] != "\n":
                    i += 1
            elif src[i] == '"':
                in_str = True
                i += 1
            else:
                out.append(src[i])
                i += 1
    return "".join(out)


def path_exists_case_exact(root: Path, target: Path) -> bool:
    if not target.exists():
        return False
    norm_target = Path(os.path.normpath(str(target)))
    norm_root = Path(os.path.normpath(str(root)))
    try:
        rel_parts = norm_target.relative_to(norm_root).parts
    except ValueError:
        return True
    cur = norm_root
    for part in rel_parts:
        names = {entry.name for entry in cur.iterdir()}
        if part not in names:
            return False
        cur = cur / part
    return True


class KSRepoIntegrityTests(unittest.TestCase):
    def test_single_version_source_consistency(self) -> None:
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        self.assertRegex(version, r"^\d+\.\d+\.\d+$")
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertRegex(changelog, re.compile(rf"^## \[?v?{re.escape(version)}\]?", re.M))
        citation = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
        self.assertRegex(citation, re.compile(rf'^version:\s*"{re.escape(version)}"$', re.M))
        formal = (ROOT / "formalization.yaml").read_text(encoding="utf-8")
        self.assertRegex(formal, re.compile(rf'^version:\s*"{re.escape(version)}"$', re.M))
        lakefile = (ROOT / "lean" / "lakefile.toml").read_text(encoding="utf-8")
        self.assertRegex(lakefile, re.compile(rf'^version\s*=\s*"{re.escape(version)}"$', re.M))
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn(f"Version {version}", readme)
        self.assertIn(f"version {version}", readme)
        zenodo = json.loads((ROOT / "publication" / "zenodo-metadata.json").read_text(encoding="utf-8"))
        self.assertEqual(zenodo["metadata"]["version"], version)

    def test_open_dual_license_and_independent_affiliation(self) -> None:
        lic = (ROOT / "LICENSE").read_text(encoding="utf-8")
        self.assertIn("Apache License", lic)
        self.assertNotIn("0thernes LLC", lic)
        docs_lic = (ROOT / "LICENSE-DOCS").read_text(encoding="utf-8")
        self.assertIn("CC-BY-4.0", docs_lic)
        pat = re.compile(r"0thernes\s+LLC|verification\s+licen[cs]e", re.I)
        active = [
            "README.md", "CONTRIBUTING.md", "CITATION.cff", "LEGAL.md",
            "docs/index.html", "docs/paper.html", "docs/SUMMARY.md",
            "paper/ks-minimum.md", "publication/ks-minimum/ks-minimum.tex",
            "publication/orcid-work.bib", "publication/arxiv-metadata.txt",
            "publication/zenodo-metadata.json",
        ]
        hits = [r for r in active if (ROOT / r).is_file() and pat.search((ROOT / r).read_text(encoding="utf-8"))]
        self.assertEqual(hits, [], f"Legacy LLC or verification-licence string found: {hits}")

    def test_docs_internal_links_and_case_exact_markdown(self) -> None:
        docs = ROOT / "docs"
        broken_html: list[tuple[str, str, str]] = []
        for hf in sorted(docs.rglob("*.html")):
            txt = hf.read_text(encoding="utf-8", errors="ignore")
            for attr, href in re.findall(r'(href|src)="([^"]+)"', txt):
                if href.startswith(("http://", "https://", "mailto:", "#", "data:", "javascript:")):
                    continue
                clean = href.split("#", 1)[0].split("?", 1)[0]
                if not clean:
                    continue
                if not path_exists_case_exact(ROOT, hf.parent / clean):
                    broken_html.append((hf.relative_to(docs).as_posix(), attr, href))
        self.assertEqual(broken_html, [], f"Broken local links in docs/: {broken_html}")

        skip = {".git", ".lake", ".venv", "node_modules", "third_party", "build"}
        md_link_re = re.compile(r"\[[^\]]*\]\(([^)#\s]+)")
        broken_md: list[tuple[str, str]] = []
        for md in sorted(ROOT.rglob("*.md")):
            if any(part in skip for part in md.parts) or md.name == "build-standard.md":
                continue
            txt = re.sub(r"```.*?```", "", md.read_text(encoding="utf-8", errors="replace"), flags=re.S)
            for m in md_link_re.finditer(txt):
                target = m.group(1)
                if target.startswith(("http://", "https://", "mailto:", "data:", "javascript:")):
                    continue
                if not path_exists_case_exact(ROOT, md.parent / target):
                    broken_md.append((md.relative_to(ROOT).as_posix(), target))
        self.assertEqual(broken_md, [], f"Broken/wrong-case Markdown links: {broken_md}")
        for rel in ("docs/INDEX.md", "docs/SUMMARY.md"):
            self.assertNotIn("GLOSSARY.md", (ROOT / rel).read_text(encoding="utf-8"))

    def test_no_crlf_in_code_and_lean_sources(self) -> None:
        skip = {".git", ".lake", ".venv", "node_modules", "third_party", "build"}
        crlf: list[str] = []
        for p in sorted(ROOT.rglob("*")):
            if not p.is_file() or any(part in skip for part in p.parts):
                continue
            if p.suffix.lower() in {".lean", ".py", ".c", ".h", ".sh", ".yml", ".yaml", ".toml", ".js", ".mjs", ".css", ".html"}:
                if b"\r\n" in p.read_bytes():
                    crlf.append(p.relative_to(ROOT).as_posix())
        self.assertEqual(crlf, [], f"CRLF line endings found: {crlf}")

    def test_no_forbidden_lean_tokens(self) -> None:
        forbidden = re.compile(r"\b(sorry|admit|native_decide|unsafe)\b|^\s*(?:private\s+|protected\s+)?axiom\b|implemented_by|@\[extern")
        hits: list[str] = []
        for lf in sorted((ROOT / "lean").rglob("*.lean")):
            if ".lake" in lf.parts or lf.name == "Challenge.lean":
                continue
            cleaned = strip_lean_comments(lf.read_text(encoding="utf-8"))
            for lineno, line in enumerate(cleaned.splitlines(), 1):
                if forbidden.search(line):
                    hits.append(f"{lf.relative_to(ROOT)}:{lineno}: {line.strip()}")
        self.assertEqual(hits, [], f"Forbidden Lean tokens: {hits}")

    def test_data_manifest_and_docs_manifest_sha256(self) -> None:
        manifest = ROOT / "data" / "MANIFEST.sha256"
        self.assertTrue(manifest.is_file())
        count = 0
        for line in manifest.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            expected, rel = line.split(None, 1)
            target = ROOT / rel.strip().lstrip("*")
            self.assertTrue(target.is_file(), f"Missing manifest file: {rel}")
            self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(), expected.lower(), f"Hash mismatch: {rel}")
            count += 1
        self.assertGreaterEqual(count, 8)

        docs_manifest = json.loads((ROOT / "docs" / "data" / "manifest.json").read_text(encoding="utf-8"))
        for fname, info in docs_manifest["files"].items():
            target = ROOT / "docs" / "data" / fname
            self.assertTrue(target.is_file(), f"Missing docs/data/{fname}")
            raw = target.read_bytes()
            self.assertEqual(len(raw), info["bytes"], f"Byte-length mismatch: docs/data/{fname}")
            self.assertEqual(hashlib.sha256(raw).hexdigest(), info["sha256"].lower(), f"Hash mismatch: docs/data/{fname}")


if __name__ == "__main__":
    unittest.main()
