#!/usr/bin/env python3
"""Audit mingguan untuk tanyacalvin.com — tanpa LLM (cron no_agent=True).

Script ini residing di ~/.hermes/scripts/, jadi root repo HARUS dicari,
tidak boleh diasumsikan dari lokasi script.
"""
import subprocess
import pathlib
import re
import sys
import time

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent


KNOWN_REPO = pathlib.Path("/Users/Hau/WORK/Tanyacalvin/tanyacalvin")


def find_repo_root():
    """Cari root repo tanyacalvin: prefer cwd (cron workdir), lalu lokasi script,
    lalu path absolut yang diketahui. Fallback terakhir penting supaya audit tidak
    pernah menghitung '0/0 artikel' di direktori yang salah — kesalahan itu dulu
    memicu REMINDER palsu yang menuduh tidak ada deploy padahal ada."""
    candidates = [
        pathlib.Path.cwd(),
        SCRIPT_DIR.parent,
        SCRIPT_DIR.parent.parent,
        KNOWN_REPO,
    ]
    for c in candidates:
        if (c / "tools" / "seo_check.py").exists() and (c / "index.html").exists():
            return c
    return pathlib.Path.cwd()


ROOT = find_repo_root()
REPO_OK = (ROOT / "tools" / "seo_check.py").exists() and (ROOT / "index.html").exists()

def article_folders():
    """Sumber kebenaran = sitemap.xml, bukan daftar hardcoded.
    Daftar manual akan salah hitung tiap kali artikel baru terbit (dan dulu
    memang salah: tertulis 6 padahal sudah 8)."""
    sm = ROOT / "sitemap.xml"
    if not sm.exists():
        return []
    urls = re.findall(r"<loc>https://tanyacalvin\.com/([^<>/]+)/</loc>", sm.read_text(encoding="utf-8"))
    return sorted(set(urls))


def git_last_commit_ts():
    try:
        out = subprocess.check_output(
            ["git", "log", "-1", "--pretty=format:%ct"], cwd=ROOT, text=True
        ).strip()
        return int(out) if out else 0
    except Exception:
        return 0


def count_articles():
    folders = article_folders()
    return sum(1 for f in folders if (ROOT / f / "index.html").exists())


def run_harness():
    """Jalankan SEMUA checker di tools/. Kalau ada yang exit non-zero, tandai jelas
    supaya laporan mingguan tidak pernah bilang 'lolos' padahal checker baru gagal."""
    checkers = ["seo_check.py", "title_check.py", "jsonld_check.py"]
    lines = []
    for name in checkers:
        path = ROOT / "tools" / name
        if not path.exists():
            lines.append(f"CHECKER TIDAK ADA: tools/{name}")
            continue
        res = subprocess.run(
            [sys.executable, str(path)], cwd=ROOT, capture_output=True, text=True
        )
        tail = [l for l in res.stdout.strip().splitlines() if l.strip()]
        label = tail[-1] if tail else "(tanpa output)"
        status = "OK" if res.returncode == 0 else "GAGAL"
        lines.append(f"[{status}] {name} — {label}")
        if res.returncode != 0:
            for l in tail:
                if l.startswith("FAIL"):
                    lines.append(f"    {l}")
    return lines


def main():
    print("AUDIT MINGGUAN tanyacalvin.com")
    if not REPO_OK:
        # Jangan pernah keluar dengan angka '0/0' + REMINDER palsu. Sebut jelas
        # bahwa root repo tidak ketemu, supaya penyebabnya tidak disalahartikan.
        print(f"  [GAGAL] Root repo tidak ditemukan. cwd={pathlib.Path.cwd()} "
              f"script={SCRIPT_DIR}. Perbaiki workdir job cron atau KNOWN_REPO.")
        return

    last = git_last_commit_ts()
    days = (time.time() - last) / 86400 if last else 999
    articles = count_articles()
    total = len(article_folders())

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
