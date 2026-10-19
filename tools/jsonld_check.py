#!/usr/bin/env python3
"""RED test: validasi JSON-LD + datePublished/dateModified + lastmod sinkron.
Dipakai sebagai harness tambahan sebelum/ sesudah perubahan item 1 & 2.
"""
import json, pathlib, re, sys

REPO = pathlib.Path("/Users/Hau/WORK/Tanyacalvin/tanyacalvin")
PAGES = [
    "tabungan-masa-tua", "warisan-anak", "dana-pendidikan-anak", "dana-kuliah-anak",
    "kesehatan", "masuk-rumah-sakit", "asuransi-jiwa-medan", "asuransi-pendidikan",
]
fails, ok = [], []

def load_ld(path):
    """Ambil semua blok <script type=application/ld+json> sebagai objek Python."""
    html = path.read_text(encoding="utf-8")
    blocks = re.findall(r'(?is)<script[^>]+application/ld\+json[^>]*>(.*?)</script>', html)
    out = []
    for raw in blocks:
        try:
            out.append(json.loads(raw))
        except Exception as e:
            out.append({"__parse_error__": str(e), "__raw_head__": raw[:200]})
    return out, html

# ---- baca sitemap lastmod ----
sm = (REPO / "sitemap.xml").read_text(encoding="utf-8")
lastmod = dict(re.findall(r"<loc>https://tanyacalvin\.com/(?:([^<]*?))?</loc>\s*<lastmod>([^<]+)</lastmod>", sm))

for slug in PAGES:
    f = REPO / slug / "index.html"
    if not f.exists():
        fails.append(f"FAIL {slug}: index.html tidak ada")
        continue
    data, html = load_ld(f)
    problems = []

    for d in data:
        if "__parse_error__" in d:
            problems.append(f"JSON-LD parse error: {d['__parse_error__']}")
            continue
        # sensor/corruption check: '@graph' harus ada sebagai key, context harus schema.org
        ctx = d.get("@context")
        if isinstance(ctx, str) and "schema.org" not in ctx:
            problems.append(f"@context rusak/tersensor: {ctx!r}")
        graph = d.get("@graph")
        if not isinstance(graph, list):
            problems.append("tidak ada @graph list")
            continue
        arts = [g for g in graph if g.get("@type") == "Article"]
        for a in arts:
            for key in ("datePublished", "dateModified"):
                v = a.get(key)
                if not v:
                    problems.append(f"Article.{key} hilang")
                elif not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(v)):
                    problems.append(f"Article.{key} format salah: {v!r}")
            pub = a.get("datePublished")
            mod = a.get("dateModified")
            if pub and mod and str(mod) < str(pub):
                problems.append(f"dateModified ({mod}) lebih tua dari datePublished ({pub})")
            # author harus punya url
            au = a.get("author") or {}
            if isinstance(au, dict) and not au.get("url"):
                problems.append("author.url hilang")
            # sinkron dengan sitemap lastmod
            lm = lastmod.get(slug) or lastmod.get(slug + "/")
            if lm and mod and str(lm) != str(mod):
                problems.append(f"lastmod sitemap ({lm}) != dateModified ({mod})")
            if lm and not mod:
                problems.append(f"tidak ada dateModified untuk dicocokkan dgn lastmod {lm}")

    if problems:
        fails.append(f"FAIL {slug}: " + "; ".join(problems))
    else:
        ok.append(f"PASS {slug}")

print("\n".join(ok))
print()
if fails:
    print("\n".join(fails))
print(f"\n{len(ok)}/{len(PAGES)} halaman lolos cek JSON-LD+date")
sys.exit(1 if fails else 0)
