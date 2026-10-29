# Schedule App

A lightweight static web app that shows my weekly university timetable fetched from [ufaz.edupage.org](https://ufaz.edupage.org).

Built so my team lead can check when I have free time to come to work.

## Features

- Weekly schedule showing all lessons per day
- Lesson count badge per day
- Group badges on split lessons (e.g. `PW Group 1` / `PW Group 2`)
- Green office-hour highlights on selected lessons
- Today's column is highlighted
- Auto-updated twice a week from your Mac

## How it works

```
Mac scheduler (Mon + Thu, 10:00 Baku time)
    ↓
fetch_schedule.py (logs into Edupage, dumps schedule.json)
    ↓
git commit and push schedule.json → main branch
    ↓
GitHub Pages serves index.html + schedule.json
```

## Setup

### 1. Create a GitHub repository and enable GitHub Pages

- Push this folder to a new repo (e.g. `your-username/schedule`)
- Go to **Settings → Pages → Source → Deploy from branch → `main` / `/ (root)`**

### 2. Set up automatic updates on your Mac

GitHub's hosted runner cannot reach `ufaz.edupage.org`, although the site opens from your Mac. In Terminal, from this repository, run:

```bash
python3 scripts/local_schedule.py setup
```

Enter your EduPage username and password at the prompts. Setup stores them in a local file that Git ignores and restricts to your macOS user, installs the Python dependency, fetches the timetable once, and pushes `schedule.json` to GitHub. It then schedules updates for Monday and Thursday at 10:00 Baku time. Your Mac must be on and logged in when the job runs; if it is asleep, macOS will run the missed job after it wakes.

The initial push uses your existing Git credentials. If it fails, sign in to GitHub for command-line Git, then run the setup command again. GitHub Pages may take a few minutes to show the new file.

To run an update manually:

```bash
python3 scripts/local_schedule.py run
```

If an automatic update fails, inspect `.schedule-update-error.log` in this repository.

### 3. Share the link

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
