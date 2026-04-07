from __future__ import annotations
from datetime import date, timedelta

# ─── Склад команди ────────────────────────────────────────────────────────────
# slack_id: Settings → Copy member ID (через правий клік на аватарі)
TEAM = [
    {"name": "Mykhailo Zelenskyi", "slack_id": "U06DM9D1SQH"},
    {"name": "Maks Kovalenko",     "slack_id": "U03Q2KMSLNP"},
    {"name": "Nadiia Pielie",      "slack_id": "U0A6DCFSKD4"},
    {"name": "Vlad Kemeniash",     "slack_id": "U0AFFG97A80"},
]

# Перший понеділок ротації (тиждень 13–19 квітня 2025, черговий — Mykhailo)
ROTATION_START = date(2025, 4, 14)


def week_start(d: date) -> date:
    """Повертає понеділок тижня, в якому знаходиться дата d."""
    return d - timedelta(days=d.weekday())


def oncall_for(d: date, overrides: dict | None = None) -> dict:
    """Повертає чергового на тиждень, що містить дату d."""
    ws = week_start(d)
    key = str(ws)
    if overrides and key in overrides:
        override_id = overrides[key]
        for m in TEAM:
            if m["slack_id"] == override_id:
                return m
    weeks = (ws - ROTATION_START).days // 7
    return TEAM[weeks % len(TEAM)]


def full_schedule(weeks: int = 52, overrides: dict | None = None) -> list[dict]:
    """Повертає графік на N тижнів вперед від ROTATION_START."""
    overrides = overrides or {}
    result = []
    for i in range(weeks):
        ws = ROTATION_START + timedelta(weeks=i)
        member = oncall_for(ws, overrides)
        result.append({
            "week_start": str(ws),
            "week_end":   str(ws + timedelta(days=6)),
            "oncall":     member,
        })
    return result
