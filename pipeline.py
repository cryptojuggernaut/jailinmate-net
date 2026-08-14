"""
pipeline.py — Full pipeline: generate county data → enrich pages → deploy → IndexNow submit.

Run this after county_data_builder.py finishes, or chain them:
    python county_data_builder.py --batch 50 && python pipeline.py

Or just run pipeline.py standalone to enrich + deploy whatever data exists.
"""

import os
import subprocess
import sys


def run(cmd: list[str], cwd: str = ".") -> int:
    print(f"\n>>> {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd)
    return result.returncode


def main():
    base = os.path.dirname(os.path.abspath(__file__))

    # Step 0: SEO validation gate — must pass before any deploy
    print("\n[pipeline] Running SEO validation gate...")
    rc = run([sys.executable, "seo_validator.py"], cwd=base)
    if rc != 0:
        print("\n[pipeline] BLOCKED: SEO validation failed. Fix issues before deploying.")
        sys.exit(rc)
    print("[pipeline] SEO gate passed.\n")

    # Step 1: Enrich pages with whatever data is in county_data.json
    rc = run([sys.executable, "enrich_pages.py"], cwd=base)
    if rc != 0:
        print("enrich_pages.py failed, stopping.")
        sys.exit(rc)

    # Step 1b: Never deploy Google-search "official" links
    rc = run([sys.executable, "quality_gate.py"], cwd=base)
    if rc != 0:
        print("\n[pipeline] BLOCKED: quality_gate failed (google.com/search in county pages).")
        sys.exit(rc)

    # Step 2: Deploy to Cloudflare Pages
    env = os.environ.copy()
    env["CLOUDFLARE_API_TOKEN"]  = env.get("CLOUDFLARE_API_TOKEN", "")
    env["CLOUDFLARE_ACCOUNT_ID"] = env.get("CLOUDFLARE_ACCOUNT_ID", "")
    wrangler_cmd = "wrangler.cmd" if os.name == "nt" else "wrangler"
    result = subprocess.run(
        [wrangler_cmd, "pages", "deploy", "dist/", "--project-name", "jailinmate-net", "--branch", "main"],
        cwd=base, env=env
    )
    if result.returncode != 0:
        print("Wrangler deploy failed.")
        sys.exit(1)

    # Step 3: Submit to IndexNow
    run([sys.executable, "indexnow_submit.py"], cwd=base)

    print("\n✅ Pipeline complete.")


if __name__ == "__main__":
    main()
