"""
Тимчасовий debug-скрипт: дампить сирий JSON останніх алертів у каналі,
щоб побачити реальну структуру повідомлення (title/text/fields/username/bot_profile).

Використання (env): DEBUG_CHANNEL_ID=<channel> python scripts/debug_alerts.py
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from slack_sdk import WebClient
from bot.alerts import ALERTMANAGER_BOT_ID

client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])
channel_id = os.environ["DEBUG_CHANNEL_ID"]
limit = int(os.environ.get("DEBUG_LIMIT", "5"))

resp = client.conversations_history(channel=channel_id, limit=100)
count = 0
for msg in resp.get("messages", []):
    if msg.get("bot_id") != ALERTMANAGER_BOT_ID:
        continue
    print("=" * 80)
    print(json.dumps(msg, indent=2, ensure_ascii=False))
    count += 1
    if count >= limit:
        break

if count == 0:
    print("No alertmanager messages found in this page.")
