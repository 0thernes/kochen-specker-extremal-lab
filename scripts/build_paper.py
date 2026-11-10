#!/usr/bin/env python3
"""
build_paper.py - turns the Markdown paper into one standalone HTML page (MathJax) and, when a
Chromium-based browser is available, a PDF.

  python scripts/build_paper.py                       # paper/ks-minimum.md -> docs/paper.html, docs/ks-minimum.pdf
  python scripts/build_paper.py some/file.md          # any other Markdown file (used to test the tool)
  python scripts/build_paper.py --no-pdf              # HTML only

The Markdown source is the canonical text (GitHub renders it directly). Mathematics is written as
$...$ or $`...`$ inline and as $$...$$ or fenced ```math blocks; all are protected from the Markdown
parser here. GitHub-flavoured pipe tables are converted to HTML tables. Images referenced relatively
(for example figures/x.png) are embedded, so the page is a single file. The title is the first "# "
heading of the Markdown file. Needs the `commonmark` Python package (pip install commonmark).
"""
import argparse, base64, html, mimetypes, os, re, shutil, subprocess, sys, tempfile

import commonmark

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---- metadata (edit here) -------------------------------------------------------------------
TITLE_FALLBACK = "Minimum Kochen-Specker sets inside finite pools of rays"   # used only if the file has no "# " heading
AUTHOR = "Alexander S. Donahue"
AUTHOR_INVERTED = "Donahue, Alexander S."
AFFILIATION = "0thernes LLC, Washington, USA"
EMAIL = "0_0@0thernes.art"
ORCID = "0009-0006-8168-9648"
DATE = "2026-11-10"
SITE = "https://0thernes.github.io/kochen-specker-extremal-lab/"
REPOSITORY = "https://github.com/0thernes/kochen-specker-extremal-lab"
REPORT_SERIES = "Kochen-Specker Extremal Lab"
# ---------------------------------------------------------------------------------------------

DEFAULT_SRC = os.path.join(ROOT, "paper", "ks-minimum.md")
DOCS = os.path.join(ROOT, "docs")
OUT_HTML = os.path.join(DOCS, "paper.html")
OUT_PDF = os.path.join(DOCS, "ks-minimum.pdf")
PDF_NAME = "ks-minimum.pdf"
HTML_NAME = "paper.html"

OPEN, CLOSE = "\ue000", "\ue001"      # private-use delimiters: they survive the Markdown parser untouched

CSS = """
:root{--bg:#fbfaf7;--ink:#1b1f27;--muted:#5b6370;--rule:#d9d6cc;--accent:#0b6b57;--code:#f1efe8;--note:#f3f1e9}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#14171c;--ink:#e6e3da;--muted:#9aa3b0;--rule:#2f353f;--accent:#5ef2c8;--code:#1d2128;--note:#1a1e25}}
:root[data-theme="dark"]{--bg:#14171c;--ink:#e6e3da;--muted:#9aa3b0;--rule:#2f353f;--accent:#5ef2c8;--code:#1d2128;--note:#1a1e25}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.58 "Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif}
.sitenav{max-width:46rem;margin:0 auto;padding:1rem 16px 0;font:.88rem/1.4 system-ui,-apple-system,"Segoe UI",sans-serif;color:var(--muted);display:flex;flex-wrap:wrap;gap:.3rem 1.2rem}
.sitenav a{color:var(--accent)}
main{max-width:46rem;margin:0 auto;padding:1.6rem 16px 5rem}
h1{font-size:2rem;line-height:1.2;margin:0 0 .6rem;letter-spacing:-.01em;text-wrap:balance}
h2{font-size:1.32rem;margin:2.6rem 0 .7rem;padding-top:.9rem;border-top:1px solid var(--rule)}
h3{font-size:1.08rem;margin:1.8rem 0 .5rem}
p{margin:.75rem 0}
a{color:var(--accent);text-decoration-thickness:1px;text-underline-offset:2px}
a:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
blockquote{margin:1.2rem 0;padding:.7rem 1rem;background:var(--note);border-left:3px solid var(--accent);font-size:.95em}
blockquote p{margin:.35rem 0}
code{font:0.86em/1.4 ui-monospace,"Cascadia Mono",Consolas,Menlo,monospace;background:var(--code);padding:.08em .3em;border-radius:3px;overflow-wrap:anywhere}
pre{background:var(--code);padding:.8rem 1rem;border-radius:6px;overflow-x:auto;font-size:.84rem;line-height:1.45}
pre code{background:none;padding:0;font-size:inherit;overflow-wrap:normal}
.tablewrap{overflow-x:auto;margin:1rem 0}
table{border-collapse:collapse;font-size:.88rem;line-height:1.35;min-width:100%;font-variant-numeric:tabular-nums}
th,td{padding:.38rem .6rem;border-bottom:1px solid var(--rule);text-align:left;vertical-align:top}
th{font-weight:600;border-bottom:2px solid var(--ink)}
img{max-width:100%;height:auto;display:block;margin:1.2rem auto .3rem;background:#fff;border-radius:4px}
.MathJax{font-size:1em!important}
mjx-container[display="true"]{overflow-x:auto;overflow-y:hidden;padding:.2rem 0}
ul,ol{padding-left:1.3rem}
li{margin:.3rem 0}
hr{border:0;border-top:1px solid var(--rule);margin:2rem 0}
@media print{:root:not([data-theme="dark"]):not(.x){--bg:#fff;--ink:#000;--muted:#444;--rule:#bbb;--accent:#0b5c4a;--code:#f3f3f1;--note:#f6f5f0}body{font-size:11pt;background:#fff;color:#000}.sitenav{display:none}main{max-width:none;padding:0}h2{break-after:avoid}h3{break-after:avoid}pre,tr,blockquote,img{break-inside:avoid}a{color:#000}}
"""

MATHJAX = """<script>
window.MathJax = {tex: {inlineMath: [['\\\\(', '\\\\)']], displayMath: [['\\\\[', '\\\\]']]}, options: {skipHtmlTags: ['script','noscript','style','textarea','pre','code']},
  startup: {pageReady: () => MathJax.startup.defaultPageReady().then(() => { document.documentElement.setAttribute('data-math', 'ready'); })}};
</script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.2/es5/tex-chtml-full.min.js"
  integrity="sha384-dCtf/9Xgzj8edI30iIEsxNfjUQ0zj2AXa3eUdgjsx8odUmpURZx5Z7aDZmV781et" crossorigin="anonymous"></script>"""

FENCE = re.compile(r"(^(?:```|~~~).*?^(?:```|~~~)[ \t]*$)", flags=re.S | re.M)


def protect_math(text):
    """Replace mathematics by placeholders; returns (text, store)."""
    store = []

    def keep(tex, display):
        store.append((tex, display))
        return "%s%d%s" % (OPEN, len(store) - 1, CLOSE)

    out = []
    for part in FENCE.split(text):
        if part.startswith("```") or part.startswith("~~~"):
            first, rest = part.split("\n", 1)
            if first.strip() == "```math":
                body = rest.rsplit("```", 1)[0]
                out.append("\n" + keep(body.strip(), True) + "\n")
            else:
                out.append(part)          # ordinary code block: untouched
            continue
        # GitHub's code form of inline math, $`...`$, which its renderer passes through verbatim; sources
        # use it wherever plain $...$ would be damaged there (backslash-punctuation such as \, \{ \#,
        # a formula ending in ")" before ")", math after a quote or inside *emphasis*)
        part = re.sub(r"\$`([^`\n]+)`\$", lambda m: keep(m.group(1), False), part)
        # inline code spans must not be searched for math
        pieces = re.split(r"(`[^`\n]+`)", part)
        for i, piece in enumerate(pieces):
            if piece.startswith("`"):
                continue
            piece = re.sub(r"\$\$(.+?)\$\$", lambda m: keep(m.group(1).strip(), True), piece, flags=re.S)
            piece = re.sub(r"(?<![\\$])\$(?!\s)([^$\n]+?)(?<!\s)\$", lambda m: keep(m.group(1), False), piece)
            pieces[i] = piece
        out.append("".join(pieces))
    return "".join(out), store


def restore_math(htmltext, store):
    def put(m):
        tex, display = store[int(m.group(1))]
        tex = html.escape(tex, quote=False)
        return ("\\[" + tex + "\\]") if display else ("\\(" + tex + "\\)")
    return re.sub(OPEN + r"(\d+)" + CLOSE, put, htmltext)


def inline_html(md):
    out = commonmark.commonmark(md).strip()
    if out.startswith("<p>") and out.endswith("</p>"):
        out = out[3:-4]
    return out


def split_row(row):
    """Cells of one pipe-table row. A pipe inside a code span or written as \\| does not end a cell."""
    row = row.strip()
    if row.startswith("|"):
        row = row[1:]
    cells, cur, in_code, i = [], [], False, 0
    while i < len(row):
        ch = row[i]
        if ch == "\\" and i + 1 < len(row) and row[i + 1] == "|":
            cur.append("|"); i += 2; continue
        if ch == "`":
            in_code = not in_code
        if ch == "|" and not in_code:
            cells.append("".join(cur).strip()); cur = []
        else:
            cur.append(ch)
        i += 1
    last = "".join(cur).strip()
    if last:
        cells.append(last)
    return cells


def convert_tables(text):
    """GitHub-flavoured pipe tables -> HTML (commonmark itself has no tables). Code fences are skipped."""
    delim = re.compile(r"^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)*\|?\s*$")
    lines = text.split("\n")
    res, i, fence = [], 0, None
    while i < len(lines):
        line = lines[i]
        mark = line.lstrip()[:3]
        if fence is None and mark in ("```", "~~~"):
            fence = mark
        elif fence is not None and mark == fence:
            fence = None
        is_table = (fence is None and line.lstrip().startswith("|") and i + 1 < len(lines)
                    and "-" in lines[i + 1] and delim.match(lines[i + 1]))
        if not is_table:
            res.append(line); i += 1
            continue
        block = []
        while i < len(lines) and lines[i].lstrip().startswith("|"):
            block.append(lines[i]); i += 1
        head = split_row(block[0])
        aligns = []
        for c in split_row(block[1]):
            left, right = c.startswith(":"), c.endswith(":")
            aligns.append("center" if left and right else "right" if right else "left" if left else "")
        aligns += [""] * (len(head) - len(aligns))

        def cell(tag, k, c):
            style = ' style="text-align:%s"' % aligns[k] if k < len(aligns) and aligns[k] else ""
            return "<%s%s>%s</%s>" % (tag, style, inline_html(c), tag)

        h = ['<div class="tablewrap" tabindex="0" role="region" aria-label="table"><table><thead><tr>']
        h += [cell("th", k, c) for k, c in enumerate(head)]
        h.append("</tr></thead><tbody>")
        for r in block[2:]:
            cells = split_row(r)
            cells = (cells + [""] * len(head))[:len(head)]
            h.append("<tr>" + "".join(cell("td", k, c) for k, c in enumerate(cells)) + "</tr>")
        h.append("</tbody></table></div>")
        res += ["", "".join(h), ""]
    return "\n".join(res)


def embed_images(body, src_dir):
    def emb(m):
        ref = m.group(1)
        if re.match(r"^(?:[a-z]+:|//|#)", ref):
            return m.group(0)
        path = os.path.join(src_dir, ref.replace("/", os.sep))
        if not os.path.exists(path):
            print("warning: image not found, left as a link:", ref)
            return m.group(0)
        mime = mimetypes.guess_type(path)[0] or "application/octet-stream"
        data = base64.b64encode(open(path, "rb").read()).decode()
        return 'src="data:%s;base64,%s"' % (mime, data)
    return re.sub(r'src="([^"]+)"', emb, body)


def plain(text):
    """Markdown/TeX-free one-line version of a heading, for <title> and meta tags."""
    text = re.sub(r"\$`?([^$`]*)`?\$", r"\1", text)
    text = re.sub(r"[*_`]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def build(src_path):
    src = open(src_path, encoding="utf-8").read()
    m = re.search(r"^# (.+)$", src, flags=re.M)
    title = plain(m.group(1)) if m else TITLE_FALLBACK
    text, store = protect_math(src)
    text = convert_tables(text)
    body = commonmark.commonmark(text)
    body = restore_math(body, store)
    body = embed_images(body, os.path.dirname(os.path.abspath(src_path)))
    # bibliographic metadata for indexing services (Highwire Press and Dublin Core tags, as read by Google Scholar)
    slash_date = DATE.replace("-", "/")
    version = re.search(r"[Vv]ersion ([0-9][0-9.]*[0-9])", src)
    report_no = REPORT_SERIES + (", version " + version.group(1) if version else "")
    institution = AFFILIATION.split(",")[0]
    tags = [("citation_title", title), ("citation_author", AUTHOR_INVERTED),
            ("citation_author_institution", AFFILIATION), ("citation_author_email", EMAIL),
            ("citation_author_orcid", "https://orcid.org/" + ORCID),
            ("citation_publication_date", slash_date), ("citation_online_date", slash_date),
            ("citation_technical_report_institution", institution),
            ("citation_technical_report_number", report_no),
            ("citation_pdf_url", SITE + PDF_NAME), ("citation_abstract_html_url", SITE + HTML_NAME),
            ("citation_fulltext_html_url", SITE + HTML_NAME), ("citation_language", "en"),
            ("DC.title", title), ("DC.creator", AUTHOR_INVERTED), ("DC.publisher", institution), ("DC.date", DATE),
            ("DC.type", "Text"), ("DC.format", "text/html"), ("DC.language", "en"), ("DC.source", REPOSITORY),
            ("author", "%s (%s)" % (AUTHOR, AFFILIATION))]
    meta = "\n".join('<meta name="%s" content="%s">' % (k, html.escape(v, quote=True)) for k, v in tags)
    nav = ('<nav class="sitenav" aria-label="Site"><a href="./">Kochen-Specker Extremal Lab: explorer and results</a>'
           '<a href="%s">PDF</a><a href="%s">Repository</a></nav>' % (PDF_NAME, html.escape(REPOSITORY, quote=True)))
    page = ("<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
            "<title>%s</title>\n"
            "<meta name=\"description\" content=\"%s\">\n<link rel=\"canonical\" href=\"%s\">\n%s\n<style>%s</style>\n%s\n"
            "</head>\n<body>\n%s\n<main>\n%s\n</main>\n</body>\n</html>\n"
            % (html.escape(title), html.escape(title + ". " + AUTHOR + ", " + AFFILIATION + ".", quote=True),
               SITE + HTML_NAME, meta, CSS, MATHJAX, nav, body))
    return page, title


def find_browser():
    for cand in (r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                 r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
                 r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                 "/usr/bin/chromium", "/usr/bin/chromium-browser", "/usr/bin/google-chrome"):
        if os.path.exists(cand):
            return cand
    return shutil.which("chromium") or shutil.which("google-chrome") or shutil.which("msedge")


def main():
    ap = argparse.ArgumentParser(description="Markdown paper -> docs/paper.html and docs/ks-minimum.pdf")
    ap.add_argument("source", nargs="?", default=DEFAULT_SRC, help="Markdown file (default: paper/ks-minimum.md)")
    ap.add_argument("--no-pdf", action="store_true", help="write the HTML page only")
    args = ap.parse_args()
    if not os.path.exists(args.source):
        sys.exit("source not found: %s\n(give the path of a Markdown file)" % args.source)
    page, title = build(args.source)
    os.makedirs(DOCS, exist_ok=True)
    with open(OUT_HTML, "w", encoding="utf-8", newline="\n") as f:
        f.write(page)
    nojekyll = os.path.join(DOCS, ".nojekyll")
    if not os.path.exists(nojekyll):
        open(nojekyll, "w").close()
    print("title:", title)
    print("wrote", OUT_HTML, "(%d bytes)" % len(page.encode("utf-8")))
    browser = find_browser()
    if args.no_pdf or not browser:
        print("PDF not built (--no-pdf or no Chromium-based browser found)")
        return
    url = "file:///" + OUT_HTML.replace("\\", "/").replace(" ", "%20")
    profile = tempfile.mkdtemp(prefix="ks-paper-pdf-")
    if os.path.exists(OUT_PDF):
        os.remove(OUT_PDF)
    cmd = [browser, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--user-data-dir=" + profile,
           "--virtual-time-budget=45000", "--run-all-compositor-stages-before-draw", "--print-to-pdf=" + OUT_PDF, url]
    try:
        subprocess.run(cmd, check=False, timeout=180, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        print("browser timed out")
    shutil.rmtree(profile, ignore_errors=True)
    if os.path.exists(OUT_PDF):
        print("wrote", OUT_PDF, os.path.getsize(OUT_PDF), "bytes")
    else:
        print("PDF was not produced")


if __name__ == "__main__":
    main()
