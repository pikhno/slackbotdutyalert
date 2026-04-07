"""
Рахує алерти в каналі за поточний тиждень (пн–сьогодні).
Алерт = повідомлення, що містить хоча б один з ALERT_PATTERNS.
"""
import os
from datetime import datetime, timedelta, timezone
from slack_sdk import WebClient

# Патерни через кому у env-змінній, наприклад: "FIRING,CRITICAL,[ALERT]"
_raw = os.environ.get("ALERT_PATTERNS", "FIRING,CRITICAL,ALERT,alert:")
ALERT_PATTERNS = [p.strip() for p in _raw.split(",") if p.strip()]


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
            text = msg.get("text", "")
            if any(p.lower() in text.lower() for p in ALERT_PATTERNS):
                count += 1

        if not resp.get("has_more"):
            break
        cursor = resp["response_metadata"]["next_cursor"]

    return count
