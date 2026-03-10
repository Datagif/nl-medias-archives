# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Archives of the **Médias** newsletter by [Datagif](https://datagif.fr), auto-synced from Mailchimp. The repo stores newsletter campaigns as both raw HTML and converted Markdown text.

## Commands

### Run the sync script locally

```bash
pip install requests html2text python-dotenv
cp .env.example .env
# Edit .env with real values
python fetch_archives.py
```

### Deploy the Cloudflare Worker

```bash
cd cloudflare
wrangler deploy
# Set secrets:
wrangler secret put GITHUB_TOKEN
wrangler secret put SECRET_KEY
```

## Architecture

Two automation paths keep `archives/` in sync:

1. **`fetch_archives.py`** (Python) — fetches all sent campaigns from the Mailchimp API, filters by `LIST_ID` and title pattern (`#NNN •`), and writes files to `archives/html/` and `archives/txt/`. Skips files that already exist. Run directly or via GitHub Actions.

2. **GitHub Actions** (`.github/workflows/sync_mailchimp.yml`) — runs `fetch_archives.py` on `workflow_dispatch` or `repository_dispatch` (event type `mailchimp_campaign_sent`), then commits and pushes any new files.

3. **Cloudflare Worker** (`cloudflare/index.js`) — bridges Mailchimp webhooks (which can't send custom headers) to the GitHub API. Receives a POST from Mailchimp, validates a `?key=` query param against `SECRET_KEY`, and forwards a `repository_dispatch` event to GitHub using `GITHUB_TOKEN`.

### File naming convention

```
{number}_{YYYY-MM-DD}.html   →   170_2026-03-05.html
{number}_{YYYY-MM-DD}.txt    →   170_2026-03-05.txt
```

The number is extracted from the campaign title via `re.match(r"#(\d+)\s*[•·]", title)`.

## Environment Variables

| Variable            | Where used                        |
|---------------------|-----------------------------------|
| `MAILCHIMP_API_KEY` | Python script + GitHub secret     |
| `MAILCHIMP_LIST_ID` | Python script + GitHub secret     |
| `OUTPUT_DIR`        | Python script (default: `archives`) |
| `GITHUB_TOKEN`      | Cloudflare Worker secret          |
| `GITHUB_REPO`       | Cloudflare Worker (`wrangler.toml`) |
| `SECRET_KEY`        | Cloudflare Worker secret          |
