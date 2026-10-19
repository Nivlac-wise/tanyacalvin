#!/usr/bin/env python3
"""Audit mingguan untuk tanyacalvin.com — tanpa LLM (cron no_agent=True).

Script ini residing di ~/.hermes/scripts/, jadi root repo HARUS dicari,
tidak boleh diasumsikan dari lokasi script.
"""
import subprocess
import pathlib
import sys
import time

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent


def find_repo_root():
    """Cari root repo tanyacalvin: prefer cwd (cron workdir), lalu lokasi script."""
    candidates = [pathlib.Path.cwd(), SCRIPT_DIR.parent, SCRIPT_DIR.parent.parent]
    for c in candidates:
        if (c / "tools" / "seo_check.py").exists() and (c / "index.html").exists():
            return c
    return pathlib.Path.cwd()


ROOT = find_repo_root()

ARTICLE_FOLDERS = [
    "tabungan-masa-tua", "warisan-anak", "dana-pendidikan-anak",
    "dana-kuliah-anak", "kesehatan", "masuk-rumah-sakit",
]


def git_last_commit_ts():
    try:
        out = subprocess.check_output(
            ["git", "log", "-1", "--pretty=format:%ct"], cwd=ROOT, text=True
        ).strip()
        return int(out) if out else 0
    except Exception:
        return 0


def count_articles():
    return sum(1 for f in ARTICLE_FOLDERS if (ROOT / f / "index.html").exists())


def run_harness():
    harness = ROOT / "tools" / "seo_check.py"
    if not harness.exists():
        return ["harness tidak ditemukan di " + str(harness)]
    res = subprocess.run(
        [sys.executable, str(harness)], cwd=ROOT, capture_output=True, text=True
    )
    return res.stdout.strip().splitlines()


def main():
    last = git_last_commit_ts()
    days = (time.time() - last) / 86400 if last else 999
    articles = count_articles()
    total = len(ARTICLE_FOLDERS)

    print("AUDIT MINGGUAN tanyacalvin.com")
    print(f"  Repo: {ROOT}")
    print(f"  Artikel: {articles}/{total} folder aktif")
    print(f"  Commit terakhir: {days:.0f} hari lalu")

    if days > 7:
        print("  [REMINDER] Sudah lebih dari 7 hari tanpa deploy artikel baru. "
              "Cek job 'Terbitkan Artikel Mingguan' dan antrean content-queue.json.")

    for line in run_harness():
        print(f"  {line}")


if __name__ == "__main__":
    main()
