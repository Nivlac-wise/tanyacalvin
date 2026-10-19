#!/usr/bin/env python3
"""seo_check.py — cek halaman tanyacalvin.com sebelum push.

Stdlib saja, tanpa dependensi. Jalankan dari root repo:
    python3 tools/seo_check.py
Exit code 0 = semua halaman lolos, 1 = ada yang gagal.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# nama -> (path relatif, kata kunci WAJIB di <h1>, jumlah kata terlihat minimum)
PAGES = {
    "index.html": ("index.html", "", 0),
    "tabungan-masa-tua": ("tabungan-masa-tua/index.html", "tabungan masa tua", 600),
    "warisan-anak": ("warisan-anak/index.html", "warisan", 600),
    "dana-pendidikan-anak": ("dana-pendidikan-anak/index.html", "pendidikan", 600),
    "dana-kuliah-anak": ("dana-kuliah-anak/index.html", "kuliah", 600),
    "kesehatan": ("kesehatan/index.html", "kesehatan", 600),
    "masuk-rumah-sakit": ("masuk-rumah-sakit/index.html", "rumah sakit", 600),
    "asuransi-jiwa-medan": ("asuransi-jiwa-medan/index.html", "asuransi jiwa medan", 600),
    "asuransi-pendidikan": ("asuransi-pendidikan/index.html", "asuransi pendidikan", 600),
    "tentang-calvin": ("tentang-calvin/index.html", "life planner", 500),
}

FOLDERS = [k for k in PAGES if k != "index.html"]
BAD_TOKENS = ("TODO", "PLACEHOLDER", "Lorem ipsum", "[kata kunci", "XXXX")


def strip_noise(html):
    return re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", html)


def visible_text(html):
    return re.sub(r"(?s)<[^>]+>", " ", strip_noise(html))


def title_of(html):
    m = re.search(r"(?is)<title\b[^>]*>(.*?)</title>", html)
    return m.group(1).strip() if m else ""


def meta_content(html, name):
    m = re.search(r'(?is)<meta[^>]+(?:name|property)=["\']' + re.escape(name) + r'["\'][^>]*>', html)
    if not m:
        return ""
    c = re.search(r'(?is)content=["\'](.*?)["\']', m.group(0))
    return c.group(1) if c else ""


def tag_attr(html, tag, attr):
    m = re.search(r"(?is)<" + tag + r"\b[^>]*>", html)
    if not m:
        return ""
    a = re.search(r'(?is)\b' + attr + r'=["\'](.*?)["\']', m.group(0))
    return a.group(1) if a else ""


def check(page, rel, keyword, min_words):
    path = ROOT / rel
    if not path.exists():
        return [f"file tidak ada: {rel}"]
    html = path.read_text(encoding="utf-8")
    problems = []

    for token in BAD_TOKENS:
        if token.lower() in html.lower():
            problems.append(f"masih ada teks cadangan: {token!r}")

    title = title_of(html)
    if not (30 <= len(title) <= 65):
        problems.append(f"title {len(title)} karakter (target 30-65): {title!r}")

    desc = meta_content(html, "description")
    if not (120 <= len(desc) <= 160):
        problems.append(f"meta description {len(desc)} karakter (target 120-160)")

    h1s = re.findall(r"(?is)<h1\b[^>]*>(.*?)</h1>", html)
    if len(h1s) != 1:
        problems.append(f"jumlah <h1> = {len(h1s)} (harus tepat 1)")
    elif keyword and keyword not in re.sub(r"(?s)<[^>]+>", "", h1s[0]).lower():
        problems.append(f"<h1> tidak memuat kata kunci {keyword!r}")

    if not re.search(r'(?is)<link[^>]+rel=["\']canonical["\'][^>]*>', html):
        problems.append("canonical tidak ada")

    if not re.search(r'(?is)<link[^>]+rel=["\']stylesheet["\'][^>]*>', html):
        problems.append("tidak memuat stylesheet")

    words = len(visible_text(html).split())
    if min_words and words < min_words:
        problems.append(f"hanya {words} kata terlihat (target >= {min_words})")

    if len(re.findall(r"(?is)<h2\b", html)) < 3:
        problems.append("kurang dari 3 <h2> (kedalaman konten)")

    if page != "index.html":
        links = re.findall(r'(?is)<a\b[^>]*href=["\']([^"\']+)["\']', html)
        internal = [l for l in links if not l.startswith(("http", "mailto:", "tel:", "#", "javascript:"))]
        if len(internal) < 2:
            problems.append(f"hanya {len(internal)} tautan internal (target >= 2)")

    return problems


def main():
    failed = 0
    for page, (rel, keyword, min_words) in PAGES.items():
        problems = check(page, rel, keyword, min_words)
        if problems:
            failed += 1
            print(f"FAIL  {page}")
            for p in problems:
                print(f"        - {p}")
        else:
            print(f"PASS  {page}")

    idx = (ROOT / "index.html")
    if idx.exists():
        html = idx.read_text(encoding="utf-8")
        missing = [f for f in FOLDERS if f'href="{f}/"' not in html]
        if missing:
            failed += 1
            print("FAIL  index.html — belum menautkan:")
            for m in missing:
                print(f"        - {m}/")
        else:
            print(f"PASS  index.html — menautkan ke {len(FOLDERS)} halaman konten")

    for name, needle in (("sitemap.xml", "https://tanyacalvin.com/tabungan-masa-tua/"),
                         ("robots.txt", "Sitemap: https://tanyacalvin.com/sitemap.xml")):
        p = ROOT / name
        if not p.exists() or needle not in p.read_text(encoding="utf-8"):
            failed += 1
            print(f"FAIL  {name} — belum ada / belum memuat {needle!r}")
        else:
            print(f"PASS  {name}")

    total = len(PAGES) + 3
    print(f"\n{total - failed}/{total} pemeriksaan lolos")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
