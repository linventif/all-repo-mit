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
