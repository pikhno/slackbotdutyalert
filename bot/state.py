"""
Стан бота у GitHub Gist.

Структура oncall_state.json:
{
  "channels": {
    "C0AP2D2KLEP": {
      "team": [
        {"name": "Mykhailo Zelenskyi", "slack_id": "U06DM9D1SQH"},
        ...
      ],
      "rotation_start": "2025-04-14",
      "overrides": {
        "2025-05-05": "U0A6DCFSKD4"
      }
    }
  }
}
"""
import os
import json
import requests
from datetime import date

GIST_ID      = os.environ["GIST_ID"]
GITHUB_TOKEN = os.environ["GIST_TOKEN"]
FILENAME     = "oncall_state.json"
HEADERS      = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}
API = f"https://api.github.com/gists/{GIST_ID}"

# Дефолтна команда (для зворотної сумісності)
DEFAULT_CHANNEL = os.environ.get("SLACK_CHANNEL_ID", "")
DEFAULT_TEAM = [
    {"name": "Mykhailo Zelenskyi", "slack_id": "U06DM9D1SQH"},
    {"name": "Maks Kovalenko",     "slack_id": "U03Q2KMSLNP"},
    {"name": "Nadiia Pielie",      "slack_id": "U0A6DCFSKD4"},
    {"name": "Vlad Kemeniash",     "slack_id": "U0AFFG97A80"},
]


def load() -> dict:
    r = requests.get(API, headers=HEADERS, timeout=10)
    r.raise_for_status()
    content = r.json()["files"][FILENAME]["content"]
    return json.loads(content)


def save(state: dict) -> None:
    payload = {"files": {FILENAME: {"content": json.dumps(state, indent=2, ensure_ascii=False)}}}
    r = requests.patch(API, headers=HEADERS, json=payload, timeout=10)
    r.raise_for_status()


def _channel_data(state: dict, channel_id: str) -> dict:
    """Повертає дані каналу, створює якщо нема."""
    if "channels" not in state:
        # Міграція старого формату
        state["channels"] = {
            DEFAULT_CHANNEL: {
                "team": DEFAULT_TEAM,
                "rotation_start": "2025-04-14",
                "overrides": state.get("overrides", {}),
            }
        }
    if channel_id not in state["channels"]:
        state["channels"][channel_id] = {
            "team": [],
            "rotation_start": str(date.today()),
            "overrides": {},
        }
    return state["channels"][channel_id]


# ── Team management ────────────────────────────────────────────────────────────

def get_team(channel_id: str) -> list:
    try:
        state = load()
        return _channel_data(state, channel_id).get("team", [])
    except Exception:
        return DEFAULT_TEAM if channel_id == DEFAULT_CHANNEL else []


def add_member(channel_id: str, slack_id: str, name: str) -> bool:
    """Додає учасника. Повертає False якщо вже є."""
    state = load()
    ch = _channel_data(state, channel_id)
    if any(m["slack_id"] == slack_id for m in ch["team"]):
        return False
    ch["team"].append({"name": name, "slack_id": slack_id})
    save(state)
    return True


def remove_member(channel_id: str, slack_id: str) -> bool:
    """Видаляє учасника. Повертає False якщо не знайдений."""
    state = load()
    ch = _channel_data(state, channel_id)
    before = len(ch["team"])
    ch["team"] = [m for m in ch["team"] if m["slack_id"] != slack_id]
    if len(ch["team"]) == before:
        return False
    save(state)
    return True


def get_rotation_start(channel_id: str) -> str:
    try:
        state = load()
        return _channel_data(state, channel_id).get("rotation_start", str(date.today()))
    except Exception:
        return "2025-04-14"


# ── Overrides ─────────────────────────────────────────────────────────────────

def get_overrides(channel_id: str = "") -> dict:
    try:
        state = load()
        ch_id = channel_id or DEFAULT_CHANNEL
        return _channel_data(state, ch_id).get("overrides", {})
    except Exception:
        return {}


def set_override(week_start: str, slack_id: str, channel_id: str = "") -> None:
    state = load()
    ch = _channel_data(state, channel_id or DEFAULT_CHANNEL)
    ch.setdefault("overrides", {})[week_start] = slack_id
    save(state)


def clear_override(week_start: str, channel_id: str = "") -> None:
    state = load()
    ch = _channel_data(state, channel_id or DEFAULT_CHANNEL)
    ch.get("overrides", {}).pop(week_start, None)
    save(state)
