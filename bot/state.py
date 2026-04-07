"""
Зберігає стан бота у GitHub Gist (безкоштовно, доступно з будь-де).

Структура oncall_state.json:
{
  "overrides": {
    "2025-05-05": "SLACK_ID_NADIIA"   // замінюємо чергового на конкретний тиждень
  }
}
"""
import os
import json
import requests

GIST_ID = os.environ["GIST_ID"]
GITHUB_TOKEN = os.environ["GIST_TOKEN"]
FILENAME = "oncall_state.json"
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}
API = f"https://api.github.com/gists/{GIST_ID}"

DEFAULT_STATE = {"overrides": {}}


def load() -> dict:
    r = requests.get(API, headers=HEADERS, timeout=10)
    r.raise_for_status()
    content = r.json()["files"][FILENAME]["content"]
    return json.loads(content)


def save(state: dict) -> None:
    payload = {"files": {FILENAME: {"content": json.dumps(state, indent=2, ensure_ascii=False)}}}
    r = requests.patch(API, headers=HEADERS, json=payload, timeout=10)
    r.raise_for_status()


def get_overrides() -> dict:
    try:
        return load().get("overrides", {})
    except Exception:
        return {}


def set_override(week_start: str, slack_id: str) -> None:
    state = load()
    state.setdefault("overrides", {})[week_start] = slack_id
    save(state)


def clear_override(week_start: str) -> None:
    state = load()
    state.get("overrides", {}).pop(week_start, None)
    save(state)
