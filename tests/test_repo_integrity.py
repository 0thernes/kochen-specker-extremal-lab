"""Repository-wide integrity, version sync, license, doc link, and Lean hygiene checks."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


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
        ]
        hits = [r for r in active if (ROOT / r).is_file() and pat.search((ROOT / r).read_text(encoding="utf-8"))]
        self.assertEqual(hits, [], f"Legacy LLC or verification-licence string found: {hits}")

    def test_docs_internal_links(self) -> None:
        docs = ROOT / "docs"
        broken: list[tuple[str, str, str]] = []
        for hf in sorted(docs.rglob("*.html")):
            txt = hf.read_text(encoding="utf-8", errors="ignore")
            for attr, href in re.findall(r'(href|src)="([^"]+)"', txt):
                if href.startswith(("http://", "https://", "mailto:", "#", "data:", "javascript:")):
                    continue
                clean = href.split("#", 1)[0].split("?", 1)[0]
                if not clean:
                    continue
                if not (hf.parent / clean).resolve().exists():
                    broken.append((hf.relative_to(docs).as_posix(), attr, href))
        self.assertEqual(broken, [], f"Broken local links in docs/: {broken}")

    def test_no_forbidden_lean_tokens(self) -> None:
        forbidden = re.compile(r"\b(sorry|admit|native_decide)\b|^\s*axiom\b|implemented_by|@\[extern")
        hits: list[str] = []
        for lf in sorted((ROOT / "lean").rglob("*.lean")):
            if ".lake" in lf.parts or lf.name == "Challenge.lean":
                continue
            in_block = False
            for lineno, raw in enumerate(lf.read_text(encoding="utf-8").splitlines(), 1):
                s = raw.strip()
                if s.startswith("/-"):
                    in_block = True
                if in_block:
                    if "-/" in s:
                        in_block = False
                    continue
                code = raw.split("--", 1)[0]
                if forbidden.search(code):
                    hits.append(f"{lf.relative_to(ROOT)}:{lineno}: {code.strip()}")
        self.assertEqual(hits, [], f"Forbidden Lean tokens: {hits}")


if __name__ == "__main__":
    unittest.main()
