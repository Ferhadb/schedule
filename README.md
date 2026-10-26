# Schedule App

A lightweight static web app that shows my weekly university timetable fetched from [ufaz.edupage.org](https://ufaz.edupage.org).

Built so my team lead can check when I have free time to come to work.

## Features

- Weekly schedule showing all lessons per day
- Lesson count badge per day
- Today's column is highlighted
- Auto-updated twice a week via GitHub Actions

## How it works

```
GitHub Actions (Mon + Thu, 06:00 UTC)
    ↓
fetch_schedule.py (logs into Edupage, dumps schedule.json)
    ↓
git commit schedule.json → main branch
    ↓
GitHub Pages serves index.html + schedule.json
```

## Setup

### 1. Create a GitHub repository and enable GitHub Pages

- Push this folder to a new repo (e.g. `your-username/schedule`)
- Go to **Settings → Pages → Source → Deploy from branch → `main` / `/ (root)`**

### 2. Add Edupage credentials as repository secrets

Go to **Settings → Secrets and variables → Actions → New repository secret**:

| Secret name | Value |
|---|---|
| `EDUPAGE_USERNAME` | Your Edupage username / email |
| `EDUPAGE_PASSWORD` | Your Edupage password |

### 3. Trigger the first run

Go to **Actions → Fetch Edupage Schedule → Run workflow**.

After it completes, `schedule.json` will be updated and the page will show your real data.

### 4. Share the link

Your GitHub Pages URL will be:
```
https://<your-username>.github.io/<repo-name>/
```

## Local development

```bash
pip install -r requirements.txt
export EDUPAGE_USERNAME="your_username"
export EDUPAGE_PASSWORD="your_password"
python fetch_schedule.py
# open index.html in a browser (via a local server, not file://)
python -m http.server 8080
```
