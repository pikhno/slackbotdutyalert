"""
Slack Bolt app для слеш-команд.
Деплой: Render.com (free tier) або будь-який хостинг з публічним URL.
"""
import os
import re
from datetime import date, timedelta

from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from flask import Flask, request

from bot.rotation import oncall_for, week_start, TEAM
from bot.state import get_overrides, set_override, clear_override
from bot.alerts import count_alerts_this_week

slack_app = App(
    token=os.environ["SLACK_BOT_TOKEN"],
    signing_secret=os.environ["SLACK_SIGNING_SECRET"],
)

flask_app = Flask(__name__)
handler   = SlackRequestHandler(slack_app)


# ──────────────────────────────────────────────────────────────────────────────
# /черговий  — хто зараз on-call
# ──────────────────────────────────────────────────────────────────────────────
@slack_app.command("/черговий")
def cmd_oncall(ack, respond, command):
    ack()
    overrides = get_overrides()
    today     = date.today()
    current   = oncall_for(today, overrides)
    ws        = week_start(today)
    ws_end    = ws + timedelta(days=6)

    try:
        alert_count = count_alerts_this_week(slack_app.client, os.environ["SLACK_CHANNEL_ID"])
        alerts_text = f"📊 Алертів цього тижня: *{alert_count}*\n"
    except Exception:
        alerts_text = ""

    respond(
        f"🔔 *Зараз черговий:* <@{current['slack_id']}> ({current['name']})\n"
        f"{alerts_text}"
        f"📅 Тиждень: {ws.strftime('%d.%m')} – {ws_end.strftime('%d.%m.%Y')}"
    )


# ──────────────────────────────────────────────────────────────────────────────
# /замінити @user [YYYY-MM-DD]  — замінити чергового на тиждень
# ──────────────────────────────────────────────────────────────────────────────
@slack_app.command("/замінити")
def cmd_substitute(ack, respond, command):
    ack()
    text = (command.get("text") or "").strip()

    user_match = re.search(r"<@(\w+)(?:\|[^>]*)?>", text)
    if not user_match:
        respond("❌ Використання: `/замінити @user` або `/замінити @user 2025-05-05`")
        return

    target_id  = user_match.group(1)
    date_match = re.search(r"(\d{4}-\d{2}-\d{2})", text)
    ws         = date_match.group(1) if date_match else str(week_start(date.today()))

    # Перевіримо, що user є в команді
    known = {m["slack_id"]: m["name"] for m in TEAM}
    if target_id not in known:
        respond(f"⚠️ <@{target_id}> не знайдений у списку команди. Перевір SLACK_ID у `bot/rotation.py`.")
        return

    set_override(ws, target_id)
    respond(f"✅ Черговий на тиждень `{ws}` → <@{target_id}> ({known[target_id]})")


# ──────────────────────────────────────────────────────────────────────────────
# /скасувати-заміну [YYYY-MM-DD]
# ──────────────────────────────────────────────────────────────────────────────
@slack_app.command("/скасувати-заміну")
def cmd_clear_sub(ack, respond, command):
    ack()
    text       = (command.get("text") or "").strip()
    date_match = re.search(r"(\d{4}-\d{2}-\d{2})", text)
    ws         = date_match.group(1) if date_match else str(week_start(date.today()))

    clear_override(ws)
    respond(f"✅ Заміна на тиждень `{ws}` скасована, повертається стандартна ротація.")


# ──────────────────────────────────────────────────────────────────────────────
# Flask routes
# ──────────────────────────────────────────────────────────────────────────────
@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)


@flask_app.route("/health")
def health():
    return "OK", 200


if __name__ == "__main__":
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 3000)), debug=False)
