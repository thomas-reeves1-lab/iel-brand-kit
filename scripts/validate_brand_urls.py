#!/usr/bin/env python3
"""Verify gate for iel-brand-kit.

brand_urls.json is the contract every consumer relies on: the app, welcome
emails and Notion all hotlink these raw GitHub URLs. A push that renames or
deletes an asset, or that leaves brand_urls.json pointing at a file that no
longer exists, silently breaks images everywhere at once.

This check fails (non-zero exit) if:
  - brand_urls.json is not valid JSON, or is missing "base"/"files";
  - any path listed under "files" (or "by_name") does not exist on disk;
  - any listed URL does not resolve to base + path;
  - any image asset on disk is missing from "files" — drift the other way,
    where an asset ships but never makes it into the map, so no consumer can
    find it. (IEL_Brand_Strip1/2.png sat unmapped this way.)

No third-party dependencies — standard library only.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP = ROOT / "brand_urls.json"
ASSET_SUFFIXES = {".png", ".jpg", ".jpeg", ".svg", ".ico", ".webp"}


def main() -> int:
    if not MAP.exists():
        print(f"FAIL: {MAP.name} not found")
        return 1
    try:
        data = json.loads(MAP.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"FAIL: {MAP.name} is not valid JSON: {exc}")
        return 1

    if not isinstance(data, dict) or "base" not in data or "files" not in data:
        print("FAIL: brand_urls.json must be an object with 'base' and 'files'")
        return 1

    base = str(data["base"]).rstrip("/") + "/"
    errors: list[str] = []
    checked = 0

    def check_entry(rel_path: str, url: str, section: str) -> None:
        nonlocal checked
        checked += 1
        if not (ROOT / rel_path).exists():
            errors.append(f"[{section}] file missing on disk: {rel_path}")
        expected = base + rel_path
        if url != expected:
            errors.append(
                f"[{section}] url mismatch for {rel_path}: expected {expected}, got {url}"
            )

    for rel_path, url in (data.get("files") or {}).items():
        check_entry(rel_path, url, "files")

    # by_name is keyed by bare filename but its values are the same raw URLs;
    # confirm each resolves to a file that actually exists under the repo.
    for name, url in (data.get("by_name") or {}).items():
        checked += 1
        if not str(url).startswith(base):
            errors.append(f"[by_name] {name}: url not under base: {url}")
            continue
        rel = str(url)[len(base):]
        if not (ROOT / rel).exists():
            errors.append(f"[by_name] {name}: file missing on disk: {rel}")

    # Reverse direction: every image asset on disk must be in the files map.
    mapped = set(data.get("files") or {})
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in ASSET_SUFFIXES:
            continue
        rel = path.relative_to(ROOT).as_posix()
        if ".git/" in rel + "/" or rel.startswith(".git/"):
            continue
        checked += 1
        if rel not in mapped:
            errors.append(
                f"[disk] asset is not in brand_urls.json, so nothing can link it: {rel}"
            )

    if errors:
        print(f"FAIL: {len(errors)} problem(s) in brand_urls.json:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(f"OK: brand_urls.json is consistent ({checked} entries checked).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
