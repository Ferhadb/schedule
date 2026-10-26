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
# Login
# ---------------------------------------------------------------------------
try:
    from edupage_api import Edupage
    from edupage_api.exceptions import BadCredentialsException, LoginDataParsingException
    from edupage_api.dbi import EduStudent
except ImportError:
    print("ERROR: edupage-api is not installed. Run: pip install edupage-api")
    sys.exit(1)

edupage = Edupage()

try:
    print(f"Logging in as {EDUPAGE_USERNAME} to {EDUPAGE_SUBDOMAIN}.edupage.org …")
    edupage.login(EDUPAGE_USERNAME, EDUPAGE_PASSWORD, EDUPAGE_SUBDOMAIN)
    print("Login successful.")
except BadCredentialsException:
    print("ERROR: Bad credentials. Check EDUPAGE_USERNAME / EDUPAGE_PASSWORD.")
    sys.exit(1)
except LoginDataParsingException as e:
    print(f"ERROR: Failed to parse login data: {e}")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Figure out current week (Monday → Sunday)
# ---------------------------------------------------------------------------
today = date.today()
monday = today - timedelta(days=today.weekday())          # Monday of current week
week_dates = [monday + timedelta(days=i) for i in range(7)]  # Mon–Sun

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# ---------------------------------------------------------------------------
# Fetch timetable for each day
# ---------------------------------------------------------------------------
def format_time(t) -> str:
    """Return HH:MM string from a time-like object, or empty string."""
    if t is None:
        return ""
    try:
        return t.strftime("%H:%M")
    except AttributeError:
        return str(t)

days_data = []

for i, day_date in enumerate(week_dates):
    day_name = DAY_NAMES[i]
    try:
        from edupage_api.lunches import EduDate  # some versions use this path
    except ImportError:
        try:
            from edupage_api import EduDate
        except ImportError:
            EduDate = None

    try:
        if EduDate is not None:
            edu_date = EduDate(day_date.year, day_date.month, day_date.day)
            timetable = edupage.get_timetable(edu_date)
        else:
            timetable = edupage.get_timetable(day_date)
    except Exception as e:
        print(f"  {day_name} ({day_date}): could not fetch timetable — {e}")
        timetable = None

    lessons = []
    if timetable:
        try:
            lesson_objects = timetable.lessons if hasattr(timetable, "lessons") else []
            for idx, lesson in enumerate(lesson_objects, start=1):
                subject = ""
                try:
                    subject = lesson.subject.name if lesson.subject else ""
                except Exception:
                    pass
                teacher = ""
                try:
                    teacher = lesson.teacher.name if lesson.teacher else ""
                except Exception:
                    pass
                classroom = ""
                try:
                    classroom = lesson.classroom.name if lesson.classroom else ""
                except Exception:
                    pass

                lessons.append({
                    "number": idx,
                    "subject": subject,
                    "teacher": teacher,
                    "classroom": classroom,
                    "start": format_time(getattr(lesson, "start_time", None) or getattr(lesson, "start", None)),
                    "end": format_time(getattr(lesson, "end_time", None) or getattr(lesson, "end", None)),
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
# Write output
# ---------------------------------------------------------------------------
output = {
    "week_start": str(monday),
    "fetched_at": today.isoformat(),
    "days": days_data,
}

output_path = os.path.join(os.path.dirname(__file__), "schedule.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\nDone! schedule.json written to {output_path}")
