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
        forbidden = re.compile(
            r"\b(sorry|admit|native_decide|unsafe)\b|"
            r"^\s*(?:(?:private|protected|noncomputable|scoped|local)\s+)*axiom\b|"
            r"implemented_by|@\[extern"
        )
        hits: list[str] = []
        for lf in sorted((ROOT / "lean").rglob("*.lean")):
            if ".lake" in lf.parts or lf.name == "Challenge.lean":
                continue
            cleaned = strip_lean_comments(lf.read_text(encoding="utf-8"))
            for lineno, line in enumerate(cleaned.splitlines(), 1):
                if forbidden.search(line):
                    hits.append(f"{lf.relative_to(ROOT)}:{lineno}: {line.strip()}")
        self.assertEqual(hits, [], f"Forbidden Lean tokens: {hits}")

    def test_build_standard_v12_manifest_and_ten_finding_classes(self) -> None:
        schema = json.loads((ROOT / "repo-standard.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["$id"], "urn:0thernes:build-standard:repo-manifest-schema:1.2.0")
        try:
            import yaml
            manifest = yaml.safe_load((ROOT / "repo.yaml").read_text(encoding="utf-8"))
            self.assertEqual(manifest["standard"], "1.2.0")
            allowed_stacks = set(schema["properties"]["stack"]["items"]["enum"])
            for entry in manifest["stack"]:
                self.assertIn(entry, allowed_stacks, f"Invalid stack value in repo.yaml: {entry!r}")
            try:
                import jsonschema
                jsonschema.validate(instance=manifest, schema=schema)
            except ImportError:
                pass
        except ImportError:
            self.assertIn('standard: "1.2.0"', (ROOT / "repo.yaml").read_text(encoding="utf-8"))

        ten_classes = [
            "bug", "error", "issue", "problem", "concern",
            "dilemma", "conflict", "gap", "hole", "blindspot",
        ]
        labels_txt = (ROOT / ".github" / "labels.tsv").read_text(encoding="utf-8")
        bug_form_txt = (ROOT / ".github" / "ISSUE_TEMPLATE" / "bug.yml").read_text(encoding="utf-8")
        glossary_txt = (ROOT / "docs" / "glossary.md").read_text(encoding="utf-8")
        for cls in ten_classes:
            self.assertRegex(labels_txt, re.compile(rf"^{cls}\t", re.M), f"Missing label '{cls}' in .github/labels.tsv")
            self.assertIn(f'"{cls}:', bug_form_txt, f"Missing finding class '{cls}' in .github/ISSUE_TEMPLATE/bug.yml")
            self.assertIn(f"**{cls}**", glossary_txt, f"Missing finding class '{cls}' in docs/glossary.md")

    def test_playbook_v13_errata_mega_atlas_palomar_and_cdn_sri(self) -> None:
        errata = (ROOT / "ERRATA.md").read_text(encoding="utf-8")
        self.assertIn("Withdrawal Plan", errata)
        self.assertIn("version-specific DOI", errata)
        mega = (ROOT / "docs" / "mega-atlas-cross-reference.md").read_text(encoding="utf-8")
        self.assertIn("0 / 1,900", mega)
        self.assertIn("QM-011", mega)

        # Palomar size caps & symlink guard (Playbook v1.3 H14)
        ch = ROOT / "lean" / "Challenge.lean"
        self.assertLessEqual(len(ch.read_text(encoding="utf-8").splitlines()), 1000)
        self.assertLessEqual(ch.stat().st_size, 102400)
        for lf in (ROOT / "lean").rglob("*.lean"):
            if ".lake" in lf.parts:
                continue
            self.assertFalse(lf.is_symlink(), f"Lean file must not be a symlink: {lf}")
            self.assertLessEqual(len(lf.read_text(encoding="utf-8").splitlines()), 10000)

        # Verify all external CDN <script> tags carry sha384 SRI and crossorigin
        skip = {".git", ".lake", ".venv", "node_modules", "third_party", "build"}
        cdn_re = re.compile(r"<script[^>]+src=[\"'](https?://[^\"']*(?:cdn\.|jsdelivr|cdnjs|unpkg)[^\"']*)[\"'][^>]*>", re.I)
        missing_sri: list[str] = []
        for ext in ("*.html", "*.py", "*.js", "*.mjs"):
            for fp in sorted(ROOT.rglob(ext)):
                if any(part in skip for part in fp.parts):
                    continue
                txt = fp.read_text(encoding="utf-8", errors="ignore")
                for m in cdn_re.finditer(txt):
                    tag = m.group(0)
                    if 'integrity="sha384-' not in tag or 'crossorigin="anonymous"' not in tag:
                        missing_sri.append(f"{fp.relative_to(ROOT).as_posix()}: {m.group(1)}")
        self.assertEqual(missing_sri, [], f"External CDN <script> missing sha384 SRI or crossorigin: {missing_sri}")

    def test_rfc3161_opentimestamps_and_lrat_script(self) -> None:
        import importlib.util

        self.assertTrue((ROOT / "scripts" / "verify_lrat.sh").is_file())
        self.assertTrue((ROOT / "docs" / "submission-packet.md").is_file())
        spec = importlib.util.spec_from_file_location("stamp_timestamps", ROOT / "scripts" / "stamp_timestamps.py")
        assert spec is not None and spec.loader is not None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.assertEqual(mod.verify_timestamps(), 0, "RFC 3161 TSA or OpenTimestamps proof failed verification")

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
