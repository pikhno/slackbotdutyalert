"""
Щоп'ятничне оголошення — постить у всі канали що є в Gist.
Запускається GitHub Actions або вручну: python scripts/announce.py
"""
import os
import sys
from datetime import date, timedelta, datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from slack_sdk import WebClient

from bot.rotation import oncall_for, week_start
from bot.state import load, DEFAULT_CHANNEL, DEFAULT_TEAM
from bot.alerts import count_alerts_this_week
from bot.gif import get_random_gif
from bot.spin import WISHES
import random

SLACK_TOKEN = os.environ["SLACK_BOT_TOKEN"]


def announce_channel(client: WebClient, channel_id: str, team: list, overrides: dict, rotation_start: date) -> None:
    today = date.today()

    days_to_monday    = (7 - today.weekday()) % 7 or 7
    next_monday       = today + timedelta(days=days_to_monday)
    next_ws           = week_start(next_monday)
    week_after_ws     = next_ws + timedelta(weeks=1)

    next_oncall       = oncall_for(next_monday, overrides, team, rotation_start)
    week_after_oncall = oncall_for(week_after_ws + timedelta(days=1), overrides, team, rotation_start)
    current_oncall    = oncall_for(today, overrides, team, rotation_start)

    try:
        alert_count = count_alerts_this_week(client, channel_id)
    except Exception:
        alert_count = "—"

    current_ws     = week_start(today)
    current_ws_end = current_ws + timedelta(days=6)
    next_ws_end    = next_ws + timedelta(days=6)
    wish           = random.choice(WISHES)

    plain_text = f"Черговий на {next_ws.strftime('%d.%m')}–{next_ws_end.strftime('%d.%m')}: {next_oncall['name']}"

    blocks = [
        # Заголовок
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "🔔 On-Call цього тижня", "emoji": True}
        },
        # Черговий + побажання
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Черговий на наступний тиждень:*\n<@{next_oncall['slack_id']}> ({next_oncall['name']})\n\n_{wish}_"
            }
        },
        {"type": "divider"},
        # Підсумок поточного тижня
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*📋 Підсумок тижня {current_ws.strftime('%d.%m')}–{current_ws_end.strftime('%d.%m')}*"
            }
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Черговий:*\n{current_oncall['name']}"},
                {"type": "mrkdwn", "text": f"*Алертів:*\n{alert_count}"},
            ]
        },
        {"type": "divider"},
        # Наступні два тижні
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*📅 {next_ws.strftime('%d.%m')}–{next_ws_end.strftime('%d.%m')}:*\n<@{next_oncall['slack_id']}>"},
                {"type": "mrkdwn", "text": f"*📅 {week_after_ws.strftime('%d.%m')}–{(week_after_ws + timedelta(days=6)).strftime('%d.%m')}:*\n<@{week_after_oncall['slack_id']}>"},
            ]
        },
        # Команди
        {
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": "💡 `/oncall` · `/oncall-sub @user` · `/oncall-unsub` · `/oncall-add @user` · `/oncall-remove @user` · `/oncall-list`"}]
        },
    ]

    gif_url = get_random_gif()
    if gif_url:
        blocks.append({"type": "image", "image_url": gif_url, "alt_text": "on-call vibes"})

    client.chat_postMessage(channel=channel_id, blocks=blocks, text=plain_text)
    print(f"  ✓ {channel_id} — next: {next_oncall['name']}, alerts: {alert_count}")


def main() -> None:
    client = WebClient(token=SLACK_TOKEN)

    try:
        state    = load()
        channels = state.get("channels", {})
    except Exception:
        channels = {}

    if not channels:
        channels = {
            DEFAULT_CHANNEL: {
                "team": DEFAULT_TEAM,
                "rotation_start": "2025-04-14",
                "overrides": {},
            }
        }

    print(f"Announcing to {len(channels)} channel(s)...")
    for channel_id, data in channels.items():
        try:
            team      = data.get("team") or DEFAULT_TEAM
            overrides = data.get("overrides", {})
            rs        = datetime.strptime(data.get("rotation_start", "2025-04-14"), "%Y-%m-%d").date()
            announce_channel(client, channel_id, team, overrides, rs)
        except Exception as e:
            print(f"  ✗ {channel_id}: {e}")


if __name__ == "__main__":
    main()
