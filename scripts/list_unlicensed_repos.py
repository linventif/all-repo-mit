#!/usr/bin/env python3
"""List public GitHub repos for a user that have no license registered.

Writes to stdout a list of repo URLs and can optionally save JSON to a file.

Usage:
  python scripts/list_unlicensed_repos.py [user] [--token TOKEN] [--out file.json]

If --token is omitted the script will try the GITHUB_TOKEN environment variable.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import Dict, List, Optional

import requests

API = "https://api.github.com"


def list_unlicensed_repos(user: str, token: Optional[str] = None, per_page: int = 100) -> List[Dict]:
    """Return list of public repos for `user` that have no license registered.

    Each returned dict contains at least: name, html_url, full_name
    Raises SystemExit on unrecoverable HTTP errors.
    """
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    page = 1
    out: List[Dict] = []

    while True:
        params = {"per_page": per_page, "page": page, "type": "public", "sort": "full_name"}
        resp = requests.get(f"{API}/users/{user}/repos", headers=headers, params=params, timeout=15)

        if resp.status_code == 403:
            # possibly rate limited. attempt to surface the message and retry once after waiting if Retry-After set
            reset = resp.headers.get("X-RateLimit-Reset")
            if reset:
                wait = max(0, int(reset) - int(time.time()))
                raise SystemExit(f"Rate limited. Retry after {wait} seconds. Response: {resp.text}")
            raise SystemExit(f"GitHub API 403: {resp.text}")

        if resp.status_code != 200:
            raise SystemExit(f"GitHub API error {resp.status_code}: {resp.text}")

        items = resp.json()
        if not items:
            break

        for r in items:
            # skip private repos (we asked for public but be defensive)
            if r.get("private"):
                continue
            if r.get("license") is None:
                out.append({"name": r.get("name"), "full_name": r.get("full_name"), "html_url": r.get("html_url")})

        page += 1

    return out


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description="List public GitHub repos without a license")
    p.add_argument("user", nargs="?", default="linventif", help="GitHub username (default: linventif)")
    p.add_argument("--token", help="GitHub token or set GITHUB_TOKEN env var", default=os.environ.get("GITHUB_TOKEN"))
    p.add_argument("--out", help="Write JSON output to file")
    p.add_argument("--quiet", help="Only output machine-friendly results (no status lines)", action="store_true")
    args = p.parse_args(argv)

    try:
        repos = list_unlicensed_repos(args.user, token=args.token)
    except SystemExit as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2

    if not args.quiet:
        print(f"Found {len(repos)} unlicensed public repo(s) for user: {args.user}")

    for r in repos:
        print(r["html_url"])

    if args.out:
        try:
            with open(args.out, "w", encoding="utf-8") as f:
                json.dump(repos, f, indent=2)
        except OSError as e:
            print(f"Failed to write {args.out}: {e}", file=sys.stderr)
            return 3

    if not repos:
        # keep exit code 0 but write a message to stderr when nothing found
        if not args.quiet:
            print("No unlicensed public repos found.", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
