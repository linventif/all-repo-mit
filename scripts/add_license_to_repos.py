#!/usr/bin/env python3
"""Copy local LICENSE into repositories and commit (optionally push).

This script operates on a list of repositories (JSON file with items containing
`full_name` and `html_url`, like the output of `list_unlicensed_repos.py`).

It will:
- clone each repo into a workdir if the directory doesn't already exist
- copy the local LICENSE file into the repo root
- git add && git commit (signed with -S by default)
- optionally git push

IMPORTANT: pushing requires that you have permission to push to the target
repositories and an authentication method available (SSH key or HTTPS token).
By default the script will NOT push unless `--push` is passed.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from typing import Dict, Iterable, List


def run(cmd: List[str], cwd: str | None = None, check: bool = True) -> subprocess.CompletedProcess:
    print(f"$ {' '.join(cmd)}" + (f"  (cwd={cwd})" if cwd else ""))
    return subprocess.run(cmd, cwd=cwd, check=check)


def load_repos_from_json(path: str) -> List[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def repo_clone_url(full_name: str, use_ssh: bool = True, token: str | None = None) -> str:
    # full_name is like owner/repo
    if use_ssh:
        return f"git@github.com:{full_name}.git"
    # HTTPS: we can include token for non-interactive pushes (if provided)
    if token:
        # token in URL: https://{token}@github.com/owner/repo.git
        return f"https://{token}@github.com/{full_name}.git"
    return f"https://github.com/{full_name}.git"


def process_repo(repo: Dict, license_file: str, workdir: str, use_ssh: bool, token: str | None, commit_msg: str, sign: bool, do_push: bool, dry_run: bool) -> None:
    full_name = repo.get("full_name") or repo.get("name")
    if not full_name:
        print("Skipping repo with no full_name/name", repo)
        return

    repo_name = full_name.split("/", 1)[-1]
    dest = os.path.join(workdir, repo_name)

    if not os.path.exists(dest):
        clone_url = repo_clone_url(full_name, use_ssh=use_ssh, token=token)
        if dry_run:
            print(f"DRY RUN: would clone {clone_url} into {dest}")
        else:
            os.makedirs(workdir, exist_ok=True)
            run(["git", "clone", clone_url, dest])
    else:
        print(f"Repo directory exists, skipping clone: {dest}")

    # copy license
    target_license = os.path.join(dest, "LICENSE")
    print(f"Copying {license_file} -> {target_license}")
    if dry_run:
        print("DRY RUN: copy skipped")
    else:
        shutil.copy(license_file, target_license)

    # git add
    if dry_run:
        print("DRY RUN: git add LICENSE")
    else:
        run(["git", "add", "LICENSE"], cwd=dest)

    # git commit
    commit_cmd = ["git", "commit", "-m", commit_msg]
    if sign:
        commit_cmd.insert(2, "-S")  # git commit -S -m msg

    try:
        if dry_run:
            print(f"DRY RUN: would run: {' '.join(commit_cmd)} (cwd={dest})")
        else:
            run(commit_cmd, cwd=dest)
    except subprocess.CalledProcessError:
        print("Commit failed (maybe no changes or signing not configured). Continuing.")

    # push
    if do_push:
        if dry_run:
            print("DRY RUN: git push")
        else:
            try:
                run(["git", "push", "origin", "HEAD"], cwd=dest)
            except subprocess.CalledProcessError as e:
                print(f"Push failed for {full_name}: {e}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Add LICENSE to repositories and commit/push it")
    p.add_argument("--repos", help="JSON file with repo list (default: unlicensed.json)", default="unlicensed.json")
    p.add_argument("--workdir", help="Directory to clone repos into", default="repos")
    p.add_argument("--license-file", help="Local license file to copy", default="LICENSE")
    p.add_argument("--no-ssh", help="Use HTTPS instead of SSH for cloning/pushing", action="store_true")
    p.add_argument("--token", help="GitHub token to use in HTTPS URL (if not using SSH)")
    p.add_argument("--message", help="Commit message", default="feat: add licence")
    p.add_argument("--no-sign", help="Do not sign commits with -S", action="store_true")
    p.add_argument("--push", help="Push commits to origin (disabled by default)", action="store_true")
    p.add_argument("--dry-run", help="Show actions without performing them", action="store_true")
    args = p.parse_args(argv)

    if not os.path.exists(args.license_file):
        print(f"License file not found: {args.license_file}", file=sys.stderr)
        return 2

    try:
        repos = load_repos_from_json(args.repos)
    except Exception as e:
        print(f"Failed to load repos from {args.repos}: {e}", file=sys.stderr)
        return 3

    for repo in repos:
        process_repo(repo, args.license_file, args.workdir, not args.no_ssh, args.token, args.message, not args.no_sign, args.push, args.dry_run)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
