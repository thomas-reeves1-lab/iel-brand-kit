#!/usr/bin/env python3
"""Block real secrets and hardcoded participant/staff PII from being committed.
Runs as a pre-commit hook and stands alone for a whole-repo sweep.

Estate-wide secret + PII pre-commit guard, rolled out 20/08/2026.

It matches high-confidence shapes only, so a block means a block - the hook is
worth trusting, not routing around. Placeholder/redacted/example values do not
trip it.

Usage:
    python scripts/secret_scan.py --staged   # only files staged for commit (hook)
    python scripts/secret_scan.py            # every tracked file (audit sweep)
Exit 0 = clean, 1 = secret/PII found (commit blocked), 2 = usage error.
"""

import re
import subprocess
import sys

SECRET_PATTERNS = {
    "Google API key": re.compile(r"AIza[0-9A-Za-z_\-]{35}"),
    "Google OAuth client secret": re.compile(r"GOCSPX-[0-9A-Za-z_\-]{20,}"),
    "GitHub token": re.compile(r"gh[pousr]_[0-9A-Za-z]{36,}"),
    "GitHub fine-grained PAT": re.compile(r"github_pat_[0-9A-Za-z_]{60,}"),
    "AWS access key id": re.compile(r"AKIA[0-9A-Z]{16}"),
    "Slack token": re.compile(r"xox[baprs]-[0-9A-Za-z\-]{10,}"),
    "Private key block": re.compile(
        r"-----BEGIN (?:RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----[^-]{100,}"),
}

# any line containing one of these is treated as a deliberate placeholder
ALLOW = re.compile(r"REDACTED|ROTATE|YOUR_|<[^>]+>|xxxx|EXAMPLE|placeholder|dummy|sample",
                   re.IGNORECASE)

# NDIS participant numbers are 9 digits. Only block when a bare 9-digit token
# sits on a line that also names participant/payer data - avoids flagging
# invoice numbers, phone numbers, timestamps.
PII_CONTEXT = re.compile(
    r"ndis|participant|payer|client_registry|registry", re.IGNORECASE)
NINE_DIGIT = re.compile(r"(?<!\d)\d{9}(?!\d)")

SENSITIVE_FILENAME = re.compile(
    r"participant_registry|worker_aliases|client_registry|payer_map"
    r"|credentials|_tokens?\.|secrets?\.|api_key", re.IGNORECASE)
SAFE_FILENAME = re.compile(r"example|template|sample|\.md$", re.IGNORECASE)


def tracked_files(staged):
    args = (["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"]
            if staged else ["git", "ls-files"])
    out = subprocess.run(args, capture_output=True, text=True).stdout
    return [f for f in out.splitlines() if f.strip()]


def read_text(f):
    try:
        with open(f, "r", encoding="utf-8", errors="ignore") as fh:
            return fh.read()
    except (OSError, UnicodeError):
        return None


def scan_secrets(f, text):
    hits = []
    for name, pat in SECRET_PATTERNS.items():
        for m in pat.finditer(text):
            line_start = text.rfind("\n", 0, m.start()) + 1
            line_end = text.find("\n", m.end())
            line = text[line_start:line_end if line_end != -1 else None]
            if ALLOW.search(line):
                continue
            lineno = text.count("\n", 0, m.start()) + 1
            hits.append((f, lineno, name, m.group()[:24]))
    return hits


def scan_pii(f, text):
    hits = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        if not PII_CONTEXT.search(line):
            continue
        if ALLOW.search(line):
            continue
        for m in NINE_DIGIT.finditer(line):
            hits.append((f, lineno, "Possible NDIS number", m.group()))
    return hits


def scan_filenames(files):
    hits = []
    for f in files:
        base = f.rsplit("/", 1)[-1]
        if SENSITIVE_FILENAME.search(base) and not SAFE_FILENAME.search(base):
            hits.append((f, 0, "Sensitive filename staged", base))
    return hits


def scan(files):
    hits = []
    hits += scan_filenames(files)
    for f in files:
        text = read_text(f)
        if text is None:
            continue
        hits += scan_secrets(f, text)
        hits += scan_pii(f, text)
    return hits


def main():
    staged = "--staged" in sys.argv
    hits = scan(tracked_files(staged))
    if not hits:
        return 0
    print("BLOCKED: possible secret or participant/staff PII detected:\n", file=sys.stderr)
    for f, ln, name, sample in hits:
        loc = f"{f}:{ln}" if ln else f
        print(f"  {loc}  {name}  ({sample}...)", file=sys.stderr)
    print("\nSecrets: redact to a placeholder, keep the real value in Bitwarden Secrets Manager.\n"
          "PII: move real names/NDIS numbers to a gitignored config file, keep only a synthetic\n"
          "example in git. If this is a false positive, add REDACTED/EXAMPLE to the line or\n"
          "refine scripts/secret_scan.py. Do not bypass with --no-verify for a real hit.",
          file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
