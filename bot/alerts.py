"""
Рахує алерти в каналі за поточний тиждень (пн–сьогодні).
Алерт = повідомлення від Alertmanager app (bot_id B03E15RC1QT).
"""
from datetime import datetime, timedelta, timezone
from slack_sdk import WebClient

ALERTMANAGER_BOT_ID = "B03E15RC1QT"


def count_alerts_this_week(client: WebClient, channel_id: str) -> int:
    now = datetime.now(timezone.utc)
    monday = now - timedelta(days=now.weekday())
    oldest = monday.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()

    count = 0
    cursor = None

    while True:
        kwargs: dict = {"channel": channel_id, "oldest": str(oldest), "limit": 200}
        if cursor:
            kwargs["cursor"] = cursor

        resp = client.conversations_history(**kwargs)

        for msg in resp.get("messages", []):
            if msg.get("bot_id") == ALERTMANAGER_BOT_ID:
                count += 1

        if not resp.get("has_more"):
            break
        cursor = resp["response_metadata"]["next_cursor"]

    return count
