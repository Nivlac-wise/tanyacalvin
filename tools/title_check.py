#!/usr/bin/env python3
"""Item 3 & 4: title harus geo-lokal + intent tiap halaman harus terkunci.

Aturan yang dijaga:
 1. Semua 8 halaman: <title> memuat "Medan", 30-65 karakter.
 2. <h1> tetap memuat kata kunci inti halaman itu (sama dgn seo_check.py).
 3. Anti-kannibalisasi untuk trio pendidikan:
      - dana-pendidikan-anak  => membahas SD/SMP/SMA, TIDAK boleh memuat "kuliah"
                                 di title maupun H1 (itu wilayah dana-kuliah-anak)
      - dana-kuliah-anak      => wajib memuat "kuliah"
      - asuransi-pendidikan    => wajib memuat "asuransi pendidikan"
 4. Tidak ada dua halaman yang punya <title> identik.
Keluaran: PASS/FAIL per halaman. Exit 0 bila semua lolos.
"""
import pathlib, re, sys

ROOT = pathlib.Path("/Users/Hau/WORK/Tanyacalvin/tanyacalvin")

SPEC = {
    "tabungan-masa-tua":   {"h1_kw": "tabungan masa tua",  "ban_in_title_h1": []},
    "warisan-anak":        {"h1_kw": "warisan",            "ban_in_title_h1": []},
    "dana-pendidikan-anak":{"h1_kw": "pendidikan",         "ban_in_title_h1": ["kuliah"]},
    "dana-kuliah-anak":    {"h1_kw": "kuliah",             "ban_in_title_h1": []},
    "kesehatan":           {"h1_kw": "kesehatan",           "ban_in_title_h1": []},
    "masuk-rumah-sakit":   {"h1_kw": "rumah sakit",         "ban_in_title_h1": []},
    "asuransi-jiwa-medan": {"h1_kw": "asuransi jiwa medan", "ban_in_title_h1": []},
    "asuransi-pendidikan": {"h1_kw": "asuransi pendidikan", "ban_in_title_h1": []},
    "tentang-calvin":    {"h1_kw": "life planner",         "ban_in_title_h1": []},
}

def title_of(h):
    m = re.search(r"(?is)<title\b[^>]*>(.*?)</title>", h)
    return m.group(1).strip() if m else ""

def h1_of(h):
    m = re.search(r"(?is)<h1\b[^>]*>(.*?)</h1>", h)
    return re.sub(r"(?s)<[^>]+>", "", m.group(1)).strip() if m else ""

fails, ok, titles = [], [], {}
for slug, spec in SPEC.items():
    p = ROOT / slug / "index.html"
    if not p.exists():
        fails.append(f"FAIL {slug}: file tidak ada"); continue
    h = p.read_text(encoding="utf-8")
    t, x = title_of(h), h1_of(h)
    titles[slug] = t
    probs = []

    if "medan" not in t.lower():
        probs.append(f'title tidak memuat "Medan": {t!r}')
    if not (30 <= len(t) <= 65):
        probs.append(f"title {len(t)} karakter (30-65): {t!r}")
    if spec["h1_kw"] not in x.lower():
        probs.append(f"H1 tidak memuat {spec['h1_kw']!r}: {x!r}")
    for banned in spec["ban_in_title_h1"]:
        if banned in t.lower() or banned in x.lower():
            probs.append(f'KANNIBAL: "{banned}" ada di title/H1 {slug} '
                         f'(wilayah dana-kuliah-anak)')
    # 5. konsistensi sinyal: og:title harus sama persis dengan <title>
    og = re.search(r'(?is)<meta property="og:title" content="(.*?)"', h)
    og_t = og.group(1).strip() if og else ""
    if not og_t:
        probs.append("og:title tidak ada")
    elif og_t != t:
        probs.append(f"og:title != <title> (sinyal inkonsisten): og={og_t!r}")
    if "medan" not in og_t.lower() and og_t:
        probs.append(f'og:title tidak memuat "Medan": {og_t!r}')

    (fails.append(f"FAIL {slug}: " + "; ".join(probs)) if probs else ok.append(f"PASS {slug}"))

dupes = {t: [s for s in titles if titles[s] == t] for t in titles}
for t, slugs in dupes.items():
    if len(slugs) > 1:
        fails.append(f"FAIL duplicate title {t!r} dipakai {slugs}")

print("\n".join(ok)); print()
print("\n".join(fails) if fails else "tidak ada duplikat title")
print(f"\n{len(ok)}/{len(SPEC)} halaman lolos cek title-lokal + anti-kannibalisasi")
sys.exit(1 if fails else 0)
