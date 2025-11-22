# list_unlicensed_repos

This repository contains a small script to list public GitHub repositories for a user that do not have a license registered.

Files added:

-   `scripts/list_unlicensed_repos.py` - Python script that queries the GitHub API and prints repository URLs that lack a license.
-   `requirements.txt` - Python dependency list (requests).

Quick start (Linux / macOS):

1. Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the script (default user: `linventif`):

```bash
python scripts/list_unlicensed_repos.py linventif --out unlicensed.json
```

You can pass a token via `--token` or by setting the `GITHUB_TOKEN` environment variable to avoid rate limits.

## Add license to repositories

After running `scripts/list_unlicensed_repos.py --out unlicensed.json` you can use
the `scripts/add_license_to_repos.py` tool to clone each repository, copy the
local `LICENSE` file into the repository root, commit the change and optionally
push it back.

The script defaults to a safe mode: it will not push unless you pass `--push`.

Examples:

```bash
# dry-run: show what would happen without making changes
python scripts/add_license_to_repos.py --repos unlicensed.json --dry-run

# actually clone repos into ./repos, commit signed, but do not push
python scripts/add_license_to_repos.py --repos unlicensed.json --workdir repos

# push changes (ensure you have push rights and authentication configured)
python scripts/add_license_to_repos.py --repos unlicensed.json --workdir repos --push

# use HTTPS with a token (non-interactive); token will be included in the remote URL
python scripts/add_license_to_repos.py --repos unlicensed.json --no-ssh --token YOUR_TOKEN --push
```

Notes and cautions

-   The script will attempt a signed commit (`-S`) by default. If your GPG key
    isn't configured locally, use `--no-sign` to avoid commit errors.
-   Only run with `--push` if you are sure you want to push to the target
    repositories and you have the right permissions.
