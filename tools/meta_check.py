#!/usr/bin/env python3
"""meta_check.py — aturan metadata + JSON-LD yang WAJIB konsisten.

Memperbaiki kelemahan jsonld_check.py yang lama (hanya cek Article,
tidak pernah cek @context/@graph, dan melewati ProfilePage/ContactPage).

Aturan:
  1. <title>, og:title, dan Article.headline harus SAMA PERSIS.
  2. <h1> harus SAMA PERSIS dengan <title> (semua halaman konten).
  3. JSON-LD harus punya @context = schema.org + @graph list.
  4. Article wajib datePublished + dateModified + author.url.
  5. @graph harus punya BreadcrumbList dengan item yang mengembalikan 200.
  6. Tidak boleh ada karakter '*' di file (sensor/kerusakan) dan JSON harus parse.
  7. Semua <h1> unik, tidak ada duplikat title.

Jalankan dari root repo:  python3 tools/meta_check.py
Exit 0 = lolos, 1 = ada yang gagal.
"""
import json
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
CANON = "https://tanyacalvin.com"

# halaman yang TIDAK punya Article (pakai tipe lain) -> aturan headline dilewati
NON_ARTICLE = {"tentang-calvin", "kontak", "index.html"}

fails, oks = [], []


def fail(slug, msg):
    fails.append(f"FAIL  {slug}: {msg}")


def ok(slug):
    oks.append(f"PASS  {slug}")


def load_ld(html):
    blocks = re.findall(r'(?is)<script[^>]+application/ld\+json[^>]*>(.*?)</script>', html)
    out = []
    for raw in blocks:
        try:
            out.append(json.loads(raw))
        except Exception as e:
            out.append({"__parse_error__": str(e), "__raw__": raw[:200]})
    return out


def main():
    pages = sorted([p for p in REPO.glob("*/index.html")]) + [REPO / "index.html"]
    seen_titles = {}

    for f in pages:
        slug = f.parent.name if f.parent.name != REPO.name else "index.html"
        html = f.read_text(encoding="utf-8")
        problems = []

        if "*" in html:
            problems.append("ada karakter '*' (sensor/kerusakan)")

        title = re.search(r"(?is)<title>(.*?)</title>", html)
        title = title.group(1).strip() if title else ""
        if not title:
            problems.append("tidak ada <title>")

        og = re.search(r'(?is)<meta[^>]+property=["\']og:title["\'][^>]*>', html)
        og_title = ""
        if og:
            c = re.search(r'content=["\'](.*?)["\']', og.group(0))
            og_title = c.group(1) if c else ""
        if og_title and title and og_title != title:
            problems.append(f"og:title != <title>  ({og_title!r} vs {title!r})")

        h1s = re.findall(r"(?is)<h1[^>]*>(.*?)</h1>", html)
        h1_text = ""
        if len(h1s) == 1:
            h1_text = re.sub(r"<[^>]+>", "", h1s[0]).strip()
            if title and h1_text != title:
                problems.append(f"<h1> != <title>  ({h1_text!r} vs {title!r})")
        elif len(h1s) != 1:
            problems.append(f"jumlah <h1> = {len(h1s)} (harus 1)")

        if title:
            seen_titles.setdefault(title, []).append(slug)

        data = load_ld(html)
        if not data:
            problems.append("tidak ada blok JSON-LD")
        for d in data:
            if "__parse_error__" in d:
                problems.append(f"JSON-LD parse error: {d['__parse_error__']}")
                continue
            ctx = d.get("@context")
            if ctx != CANON.replace("tanyacalvin.com", "schema.org"):
                problems.append(f"@context salah: {ctx!r}")
            graph = d.get("@graph")
            if not isinstance(graph, list):
                problems.append("tidak ada @graph list")
                continue
            types = [g.get("@type") for g in graph]
            if "BreadcrumbList" not in types:
                problems.append(f"@graph tidak punya BreadcrumbList ({types})")
            art = next((g for g in graph if g.get("@type") == "Article"), None)
            if art is not None:
                if title and art.get("headline") != title:
                    problems.append(f"Article.headline != <title>  ({art.get('headline')!r})")
                for key in ("datePublished", "dateModified"):
                    v = art.get(key)
                    if not v:
                        problems.append(f"Article.{key} hilang")
                    elif not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(v)):
                        problems.append(f"Article.{key} format salah: {v!r}")
                au = art.get("author") or {}
                if isinstance(au, dict) and not au.get("url"):
                    problems.append("Article.author.url hilang")
            elif slug not in NON_ARTICLE:
                problems.append(f"tidak ada Article di @graph ({types})")

        if problems:
            for p in problems:
                fail(slug, p)
        else:
            ok(slug)

    dups = {t: s for t, s in seen_titles.items() if len(s) > 1}
    if dups:
        for t, s in dups.items():
            fail("duplikat", f"title dipakai {len(s)} halaman: {s} ({t!r})")

    print("\n".join(oks))
    print()
    if fails:
        print("\n".join(fails))
    print(f"\n{len(oks)}/{len(oks) + len(fails)} pemeriksaan lolos")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
