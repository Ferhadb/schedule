#!/usr/bin/env python3
"""
fetch_schedule.py
Logs into ufaz.edupage.org and exports the current week's timetable
as schedule.json, ready to be served by GitHub Pages.
"""

import json
import os
import sys
from datetime import date, timedelta

# ---------------------------------------------------------------------------
# Credentials — read from environment variables (set as GitHub Secrets)
# ---------------------------------------------------------------------------
EDUPAGE_USERNAME = os.environ.get("EDUPAGE_USERNAME", "")
EDUPAGE_PASSWORD = os.environ.get("EDUPAGE_PASSWORD", "")
EDUPAGE_SUBDOMAIN = "ufaz"

if not EDUPAGE_USERNAME or not EDUPAGE_PASSWORD:
    print("ERROR: EDUPAGE_USERNAME and EDUPAGE_PASSWORD environment variables must be set.")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Import edupage-api  (package: edupage-api, module: edupage_api)
# ---------------------------------------------------------------------------
try:
    from edupage_api import Edupage
    from edupage_api.exceptions import BadCredentialsException
except ImportError as e:
    print(f"ERROR: edupage-api is not installed or has wrong structure: {e}")
    print("Run: pip install edupage-api")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------
edupage = Edupage()

try:
    print(f"Logging in as {EDUPAGE_USERNAME} to {EDUPAGE_SUBDOMAIN}.edupage.org …")
    edupage.login(EDUPAGE_USERNAME, EDUPAGE_PASSWORD, EDUPAGE_SUBDOMAIN)
    print("Login successful.")
except BadCredentialsException:
    print("ERROR: Bad credentials. Check EDUPAGE_USERNAME / EDUPAGE_PASSWORD.")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: Login failed: {e}")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Figure out current week (Monday → Sunday)
# ---------------------------------------------------------------------------
today = date.today()
monday = today - timedelta(days=today.weekday())       # Monday of current week
week_dates = [monday + timedelta(days=i) for i in range(7)]

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# ---------------------------------------------------------------------------
# Fetch timetable for each day
# ---------------------------------------------------------------------------
def fmt_time(t) -> str:
    """Return HH:MM string from a datetime.time object, or empty string."""
    if t is None:
        return ""
    try:
        return t.strftime("%H:%M")
    except AttributeError:
        return str(t)

days_data = []

for i, day_date in enumerate(week_dates):
    day_name = DAY_NAMES[i]

    timetable = None
    try:
        timetable = edupage.get_my_timetable(day_date)
    except Exception as e:
        print(f"  {day_name} ({day_date}): could not fetch timetable — {e}")

    lessons = []
    if timetable:
        try:
            for idx, lesson in enumerate(timetable.lessons, start=1):
                # Skip cancelled lessons
                if getattr(lesson, "is_cancelled", False):
                    continue

                # Subject
                subject = ""
                try:
                    subject = lesson.subject.name if lesson.subject else ""
                except Exception:
                    pass

                # Teachers (it's a list in v0.13)
                teacher = ""
                try:
                    teachers = lesson.teachers or []
                    teacher = ", ".join(t.name for t in teachers if t and t.name)
                except Exception:
                    pass

                # Classrooms (also a list)
                classroom = ""
                try:
                    classrooms = lesson.classrooms or []
                    classroom = ", ".join(c.name for c in classrooms if c and c.name)
                except Exception:
                    pass

                lessons.append({
                    "number": idx,
                    "subject": subject,
                    "teacher": teacher,
                    "classroom": classroom,
                    "start": fmt_time(lesson.start_time),
                    "end": fmt_time(lesson.end_time),
                    "online_link": getattr(lesson, "online_lesson_link", None) or "",
                })
        except Exception as e:
            print(f"  {day_name}: error iterating lessons — {e}")

    days_data.append({
        "day": day_name,
        "date": str(day_date),
        "lessons": lessons,
        "lesson_count": len(lessons),
    })
    print(f"  {day_name} ({day_date}): {len(lessons)} lesson(s)")

# ---------------------------------------------------------------------------
# Write schedule.json
# ---------------------------------------------------------------------------
output = {
    "week_start": str(monday),
    "fetched_at": today.isoformat(),
    "days": days_data,
}

output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schedule.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\nDone! schedule.json written to {output_path}")
