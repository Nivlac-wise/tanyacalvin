#!/usr/bin/env python3
"""Health check script for tanyacalvin.com — runs without LLM (no_agent=True)."""
import re, subprocess, sys, pathlib, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
FAIL = []

def check():
    sitemap = ROOT / "sitemap.xml"
    urls = []
    if sitemap.exists():
        for line in sitemap.read_text(encoding="utf-8").splitlines():
            m = re.search(r'<loc>(.*?)</loc>', line)
            if m: urls.append(m.group(1))
    else:
        FAIL.append("sitemap.xml missing")

    for url in urls:
        try:
            req = urllib.request.Request(url, headers={"User-Agent":"Hermes-HealthCheck/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                code = resp.status
        except Exception as e:
            code = f"ERROR:{e}"
        if code != 200:
            FAIL.append(f"{url} -> {code}")

    harness = subprocess.run(
        ["python3", "tools/seo_check.py"],
        cwd=ROOT, capture_output=True, text=True
    )
    # Report harness result; don't fail on it (it's a separate check)
    harness_summary = harness.stdout.strip().splitlines()[-1] if harness.stdout else "harness: no output"
    return urls, harness_summary

if __name__ == "__main__":
    urls, summary = check()
    print(f"HEALTH CHECK — {len(urls)} URLs checked")
    for u in urls:
        status = "OK" if not any(str(u) in f for f in FAIL) else "FAIL"
        print(f"  {status}  {u}")
    for f in FAIL:
        print(f"  FAIL  {f}")
    print(f"  {summary}")
    sys.exit(1 if FAIL else 0)
