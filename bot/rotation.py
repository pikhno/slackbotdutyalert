from __future__ import annotations
from datetime import date, timedelta

# Дефолтна команда (використовується для announce.py і show_schedule.py)
TEAM = [
    {"name": "Mykhailo Zelenskyi", "slack_id": "U06DM9D1SQH"},
    {"name": "Maks Kovalenko",     "slack_id": "U03Q2KMSLNP"},
    {"name": "Nadiia Pielie",      "slack_id": "U0A6DCFSKD4"},
    {"name": "Vlad Kemeniash",     "slack_id": "U0AFFG97A80"},
]

ROTATION_START = date(2025, 4, 14)


def week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())


def oncall_for(d: date, overrides: dict | None = None, team: list | None = None, rotation_start: date | None = None) -> dict:
    """Повертає чергового на тиждень що містить дату d."""
    t = team or TEAM
    rs = rotation_start or ROTATION_START
    ws = week_start(d)
    key = str(ws)
    if overrides and key in overrides:
        override_id = overrides[key]
        for m in t:
            if m["slack_id"] == override_id:
                return m
    if not t:
        return {"name": "???", "slack_id": ""}
    weeks = (ws - rs).days // 7
    return t[weeks % len(t)]


def full_schedule(weeks: int = 52, overrides: dict | None = None, team: list | None = None, rotation_start: date | None = None) -> list[dict]:
    t = team or TEAM
    rs = rotation_start or ROTATION_START
    overrides = overrides or {}
    result = []
    for i in range(weeks):
        ws = rs + timedelta(weeks=i)
        member = oncall_for(ws, overrides, t, rs)
        result.append({
            "week_start": str(ws),
            "week_end":   str(ws + timedelta(days=6)),
            "oncall":     member,
        })
    return result
