"""
Щоп'ятничне оголошення.
Запускається GitHub Actions або вручну: python scripts/announce.py
"""
import os
import sys
import time
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from slack_sdk import WebClient

from bot.rotation import oncall_for, week_start, TEAM
from bot.state import get_overrides
from bot.spin import spin_reveal
from bot.alerts import count_alerts_this_week

SLACK_TOKEN = os.environ["SLACK_BOT_TOKEN"]
CHANNEL_ID  = os.environ["SLACK_CHANNEL_ID"]


def main() -> None:
    client    = WebClient(token=SLACK_TOKEN)
    overrides = get_overrides()
    today     = date.today()

    # Визначаємо наступний понеділок
    days_to_monday  = (7 - today.weekday()) % 7 or 7
    next_monday     = today + timedelta(days=days_to_monday)
    next_ws         = week_start(next_monday)
    week_after_ws   = next_ws + timedelta(weeks=1)

    next_oncall      = oncall_for(next_monday, overrides)
    week_after_oncall = oncall_for(week_after_ws + timedelta(days=1), overrides)

    # Алерти поточного тижня
    current_oncall = oncall_for(today, overrides)
    alert_count    = count_alerts_this_week(client, CHANNEL_ID)

    # 1. Постимо «затравку» (вона стане фреймом спін-анімації)
    resp = client.chat_postMessage(
        channel=CHANNEL_ID,
        text="🎰  Хто черговий на наступний тиждень?  🎰",
    )
    ts = resp["ts"]
    time.sleep(0.8)

    # 2. Спін-анімація → фінальне ім'я
    spin_reveal(client, CHANNEL_ID, ts, next_oncall, TEAM)
    time.sleep(1.0)

    # 3. Підсумкове повідомлення
    current_ws     = week_start(today)
    current_ws_end = current_ws + timedelta(days=6)
    next_ws_end    = next_ws + timedelta(days=6)

    summary = (
        f"📋 *Підсумок тижня {current_ws.strftime('%d.%m')}–{current_ws_end.strftime('%d.%m')}*"
        f" (черговий: {current_oncall['name']}):\n"
        f"• Алертів: *{alert_count}*\n\n"
        f"📅 *{next_ws.strftime('%d.%m')}–{next_ws_end.strftime('%d.%m')}:* "
        f"<@{next_oncall['slack_id']}>\n"
        f"📅 *{week_after_ws.strftime('%d.%m')}–{(week_after_ws + timedelta(days=6)).strftime('%d.%m')}:* "
        f"<@{week_after_oncall['slack_id']}>\n\n"
        f"_Змінити чергового: `/oncall-sub @user` або `/oncall-sub @user 2025-05-05`_"
    )
    client.chat_postMessage(channel=CHANNEL_ID, text=summary)
    print(f"Done. Next on-call: {next_oncall['name']}, alerts this week: {alert_count}")


if __name__ == "__main__":
    main()
