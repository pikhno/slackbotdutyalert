"""
Lightweight Flask handler for Slack slash commands.
No Slack Bolt — responds immediately to beat the 3-second timeout.
"""
import os
import re
import hmac
import hashlib
import time
from datetime import date, timedelta
from flask import Flask, request, jsonify

from bot.rotation import oncall_for, week_start, TEAM
from bot.state import get_overrides, set_override, clear_override
from bot.alerts import count_alerts_this_week
from slack_sdk import WebClient

flask_app = Flask(__name__)

SIGNING_SECRET = os.environ["SLACK_SIGNING_SECRET"].encode()
client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])
CHANNEL_ID = os.environ["SLACK_CHANNEL_ID"]


def verify_slack(req) -> bool:
    ts = req.headers.get("X-Slack-Request-Timestamp", "")
    if abs(time.time() - float(ts)) > 300:
        return False
    sig_base = f"v0:{ts}:{req.get_data(as_text=True)}"
    expected = "v0=" + hmac.new(SIGNING_SECRET, sig_base.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, req.headers.get("X-Slack-Signature", ""))


def ephemeral(text: str):
    return jsonify({"response_type": "ephemeral", "text": text})


@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    if not verify_slack(request):
        return "Unauthorized", 401

    command = request.form.get("command", "")
    text    = (request.form.get("text") or "").strip()

    # /oncall
    if command == "/oncall":
        overrides = get_overrides()
        today     = date.today()
        current   = oncall_for(today, overrides)
        ws        = week_start(today)
        ws_end    = ws + timedelta(days=6)
        try:
            alerts = count_alerts_this_week(client, CHANNEL_ID)
            alerts_text = f"\n📊 Алертів цього тижня: *{alerts}*"
        except Exception:
            alerts_text = ""
        return ephemeral(
            f"🔔 *Зараз черговий:* <@{current['slack_id']}> ({current['name']})"
            f"{alerts_text}\n"
            f"📅 Тиждень: {ws.strftime('%d.%m')} – {ws_end.strftime('%d.%m.%Y')}"
        )

    # /oncall-sub @user [YYYY-MM-DD]
    if command == "/oncall-sub":
        user_match = re.search(r"<@(\w+)(?:\|[^>]*)?>", text)
        if not user_match:
            return ephemeral("❌ Usage: `/oncall-sub @user` or `/oncall-sub @user 2025-05-05`")
        target_id  = user_match.group(1)
        known      = {m["slack_id"]: m["name"] for m in TEAM}
        if target_id not in known:
            return ephemeral(f"⚠️ <@{target_id}> not found in the team list.")
        date_match = re.search(r"(\d{4}-\d{2}-\d{2})", text)
        ws         = date_match.group(1) if date_match else str(week_start(date.today()))
        set_override(ws, target_id)
        return ephemeral(f"✅ On-call for week `{ws}` → <@{target_id}> ({known[target_id]})")

    # /oncall-unsub [YYYY-MM-DD]
    if command == "/oncall-unsub":
        date_match = re.search(r"(\d{4}-\d{2}-\d{2})", text)
        ws         = date_match.group(1) if date_match else str(week_start(date.today()))
        clear_override(ws)
        return ephemeral(f"✅ Override for week `{ws}` removed, back to regular rotation.")

    return "", 200


@flask_app.route("/health")
def health():
    return "OK", 200


if __name__ == "__main__":
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 3000)), debug=False)
