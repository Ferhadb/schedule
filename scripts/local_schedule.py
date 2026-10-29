#!/usr/bin/env python3
"""Fetch the timetable on this Mac and publish schedule.json to GitHub Pages."""

import getpass
import json
import os
import plistlib
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CREDENTIALS = ROOT / ".schedule_credentials.json"
VENV = ROOT / ".venv"
LABEL = "org.ferhadb.schedule.refresh"
PLIST = Path.home() / "Library" / "LaunchAgents" / f"{LABEL}.plist"


def run_command(*args, env=None):
    subprocess.run(args, cwd=ROOT, env=env, check=True)


def git(*args):
    run_command("/usr/bin/git", *args)


def git_output(*args):
    return subprocess.check_output(("/usr/bin/git", *args), cwd=ROOT, text=True).strip()


def update():
    if not CREDENTIALS.exists():
        raise RuntimeError("Run setup first to save your EduPage credentials.")
    if not (VENV / "bin" / "python").exists():
        raise RuntimeError("Run setup first to install the Python dependencies.")
    if git_output("branch", "--show-current") != "main":
        raise RuntimeError("The schedule updater must run from the main branch.")
    if git_output("status", "--porcelain"):
        raise RuntimeError("The repository has local changes. Commit or move them before updating the schedule.")

    credentials = json.loads(CREDENTIALS.read_text(encoding="utf-8"))
    environment = os.environ.copy()
    environment.update(
        EDUPAGE_USERNAME=credentials["username"],
        EDUPAGE_PASSWORD=credentials["password"],
        GIT_TERMINAL_PROMPT="0",
    )

    git("pull", "--rebase", "origin", "main")
    run_command(str(VENV / "bin" / "python"), "fetch_schedule.py", env=environment)
    if not git_output("status", "--porcelain", "--", "schedule.json"):
        print("schedule.json is already current.")
        return

    git("add", "--", "schedule.json")
    git("-c", "user.name=schedule-updater", "-c", "user.email=schedule-updater@users.noreply.github.com",
        "commit", "-m", "chore: update schedule.json [skip ci]")
    for attempt in range(3):
        try:
            git("push", "origin", "main")
            print("Published schedule.json to GitHub Pages.")
            return
        except subprocess.CalledProcessError:
            if attempt == 2:
                raise
            git("pull", "--rebase", "origin", "main")


def setup():
    if sys.platform != "darwin":
        raise RuntimeError("This setup is for macOS.")
    if not shutil.which("git"):
        raise RuntimeError("Git is required.")

    username = input("EduPage username: ").strip()
    password = getpass.getpass("EduPage password: ")
    if not username or not password:
        raise RuntimeError("Both EduPage fields are required.")

    descriptor = os.open(CREDENTIALS, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as file:
        json.dump({"username": username, "password": password}, file)
    CREDENTIALS.chmod(0o600)

    run_command(sys.executable, "-m", "venv", str(VENV))
    run_command(str(VENV / "bin" / "python"), "-m", "pip", "install", "-r", "requirements.txt")

    # Publish once now, so setup confirms that login and GitHub access both work.
    update()

    PLIST.parent.mkdir(parents=True, exist_ok=True)
    job = {
        "Label": LABEL,
        "ProgramArguments": [str(VENV / "bin" / "python"), str(Path(__file__).resolve()), "run"],
        "WorkingDirectory": str(ROOT),
        "RunAtLoad": True,
        "StartCalendarInterval": [
            {"Weekday": 1, "Hour": 10, "Minute": 0},
            {"Weekday": 4, "Hour": 10, "Minute": 0},
        ],
        "StandardOutPath": str(ROOT / ".schedule-update.log"),
        "StandardErrorPath": str(ROOT / ".schedule-update-error.log"),
    }
    with PLIST.open("wb") as file:
        plistlib.dump(job, file)

    domain = f"gui/{os.getuid()}"
    subprocess.run(("/bin/launchctl", "bootout", domain, str(PLIST)), check=False,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    run_command("/bin/launchctl", "bootstrap", domain, str(PLIST))
    print(f"Scheduled for Monday and Thursday at 10:00 local time. Job: {PLIST}")


if __name__ == "__main__":
    try:
        if len(sys.argv) != 2 or sys.argv[1] not in {"setup", "run"}:
            raise RuntimeError("Usage: python3 scripts/local_schedule.py setup|run")
        (setup if sys.argv[1] == "setup" else update)()
    except (RuntimeError, subprocess.CalledProcessError, KeyError, json.JSONDecodeError) as error:
        print(f"Schedule update failed: {error}", file=sys.stderr)
        sys.exit(1)
