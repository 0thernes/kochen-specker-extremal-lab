"""fix_paper_math.py - rewrite the plain-text formulas of paper/ks-minimum.md
that contain subscripts or superscripts into the "code form" of inline math
($`...`$), which GitHub, pandoc and the HTML build all typeset.  Text inside
fenced code blocks and inside existing back-ticked spans is left alone.
Idempotent: a second run changes nothing.
"""
from __future__ import annotations

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "paper", "ks-minimum.md")

# (plain text, TeX) - longest patterns first
RULES = [
    ("(e₀ + e_j, e₀ − e_j)", r"(e_0 + e_j,\ e_0 - e_j)"),
    ("{e₀, e₁, e₂, e₃}", r"\{e_0, e_1, e_2, e_3\}"),
    ("{e₀, e₁, e₂}", r"\{e_0, e_1, e_2\}"),
    ("e₀ − e_j", r"e_0 - e_j"),
    ("e₀ + e_j", r"e_0 + e_j"),
    ("{0} ∪ μ_N", r"\{0\} \cup \mu_N"),
    ("μ_N", r"\mu_N"),
    ("{0, ±1}⁵", r"\{0, \pm 1\}^5"),
    ("2·10⁻¹⁵", r"2 \times 10^{-15}"),
    ("Zᵈ", r"\mathbb{Z}^d"),
    ("Cᵈ", r"\mathbb{C}^d"),
    ("x_v", r"x_v"),
    ("y_b", r"y_b"),
    ("j = 1, …, d − 1", r"j = 1, \dots, d-1"),
]


def convert(segment):
    for plain, tex in RULES:
        segment = segment.replace(plain, "$`" + tex + "`$")
    return segment


def main():
    text = open(PATH, encoding="utf-8").read()
    out = []
    in_fence = False
    for line in text.split("\n"):
        if line.startswith("```"):
            in_fence = not in_fence
            out.append(line)
            continue
        if in_fence:
            out.append(line)
            continue
        # split on existing code spans and code-form math; convert only the plain parts
        parts = re.split(r"(\$`[^`]*`\$|`[^`]*`)", line)
        out.append("".join(p if (p.startswith("`") or p.startswith("$`")) else convert(p) for p in parts))
    new = "\n".join(out)
    if new != text:
        open(PATH, "w", encoding="utf-8", newline="\n").write(new)
    n = len(re.findall(r"\$`[^`]*`\$", new))
    print(f"{PATH}: {n} inline formulas in code form; changed={new != text}")


if __name__ == "__main__":
    main()
