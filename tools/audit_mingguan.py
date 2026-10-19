#!/usr/bin/env python3
"""Audit mingguan untuk tanyacalvin.com — tanpa LLM."""
import subprocess, pathlib, time, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

def git_last_commit():
    try:
        out = subprocess.check_output(
            ["git", "log", "-1", "--pretty=format:%ct", "--date=unix"], cwd=ROOT, text=True
        ).strip()
        return int(out) if out else 0
    except Exception:
        return 0

def count_articles():
    folders = ["tabungan-masa-tua", "warisan-anak", "dana-pendidikan-anak",
               "dana-kuliah-anak", "kesehatan", "masuk-rumah-sakit"]
    return sum(1 for f in folders if (ROOT / f / "index.html").exists())

def main():
    last_commit = git_last_commit()
    now = time.time()
    days_since = (now - last_commit) / 86400 if last_commit else 999
    articles = count_articles()
    msg = f"AUDIT MINGGUAN — Artikel: {articles}/6 aktif. Commit terakhir: {days_since:.0f} hari lalu."
    if days_since > 7 and articles == 0:
        msg += " [REMINDER] Tidak ada artikel baru minggu ini — belum ada deploy konten baru."
    elif days_since > 7:
        msg += " [REMINDER] Sudah lebih dari 7 hari tanpa deploy artikel baru."
    print(msg)
    # Also run harness
    harness = subprocess.run(
        [sys.executable, "tools/seo_check.py"], cwd=ROOT, capture_output=True, text=True
    )
    for line in harness.stdout.strip().splitlines():
        print(f"  {line}")

if __name__ == "__main__":
    main()
