"""
Lightweight Flask handler for Slack slash commands.
"""
import os
import re
import hmac
import hashlib
import time
from datetime import date, timedelta
from flask import Flask, request, jsonify
from slack_sdk import WebClient

from bot.rotation import oncall_for, week_start
from bot.state import (
    get_team, get_overrides, get_rotation_start,
    set_override, clear_override,
    add_member, remove_member,
)
from bot.alerts import count_alerts_this_week

flask_app = Flask(__name__)

SIGNING_SECRET = os.environ["SLACK_SIGNING_SECRET"].encode()
client         = WebClient(token=os.environ["SLACK_BOT_TOKEN"])
DEFAULT_CHANNEL = os.environ["SLACK_CHANNEL_ID"]


def verify_slack(req) -> bool:
    ts = req.headers.get("X-Slack-Request-Timestamp", "")
    if abs(time.time() - float(ts)) > 300:
        return False
    sig_base = f"v0:{ts}:{req.get_data(as_text=True)}"
    expected = "v0=" + hmac.new(SIGNING_SECRET, sig_base.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, req.headers.get("X-Slack-Signature", ""))


def ephemeral(text: str):
    return jsonify({"response_type": "ephemeral", "text": text})


def get_channel_context(form):
    """Визначає channel_id і завантажує команду/ротацію для цього каналу."""
    channel_id = form.get("channel_id", DEFAULT_CHANNEL)
    team       = get_team(channel_id) or get_team(DEFAULT_CHANNEL)
    overrides  = get_overrides(channel_id)
    rs_str     = get_rotation_start(channel_id)
    from datetime import datetime
    rotation_start = datetime.strptime(rs_str, "%Y-%m-%d").date()
    return channel_id, team, overrides, rotation_start


@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    if not verify_slack(request):
        return "Unauthorized", 401

    command = request.form.get("command", "")
    text    = (request.form.get("text") or "").strip()
    channel_id, team, overrides, rotation_start = get_channel_context(request.form)

    # ── /oncall ───────────────────────────────────────────────────────────────
    if command == "/oncall":
        today   = date.today()
        current = oncall_for(today, overrides, team, rotation_start)
        ws      = week_start(today)
        ws_end  = ws + timedelta(days=6)
        try:
            alerts = count_alerts_this_week(client, channel_id)
            alerts_text = f"\n📊 Алертів цього тижня: *{alerts}*"
        except Exception:
            alerts_text = ""
        return ephemeral(
            f"🔔 *Зараз черговий:* <@{current['slack_id']}> ({current['name']})"
            f"{alerts_text}\n"
            f"📅 Тиждень: {ws.strftime('%d.%m')} – {ws_end.strftime('%d.%m.%Y')}"
        )

    # ── /oncall-list ──────────────────────────────────────────────────────────
    if command == "/oncall-list":
        if not team:
            return ephemeral("📋 Команда порожня. Додай учасників через `/oncall-add @user`")
        lines = "\n".join(f"{i+1}. <@{m['slack_id']}> ({m['name']})" for i, m in enumerate(team))
        return ephemeral(f"📋 *Команда в ротації ({len(team)} осіб):*\n{lines}")

    # ── /oncall-add @user1 @user2 ... ────────────────────────────────────────
    if command == "/oncall-add":
        # Slack передає mentions як @username (plain text) або <@USERID>
        # Підтримуємо обидва формати
        slack_ids = re.findall(r"<@(\w+)(?:\|[^>]*)?>", text)

        if not slack_ids:
            usernames = re.findall(r"@([\w.\-]+)", text)
            if not usernames:
                return ephemeral("❌ Usage: `/oncall-add @user` або `/oncall-add @user1 @user2 @user3`")
            # Завантажуємо список юзерів і шукаємо по username
            try:
                all_users = []
                cursor = None
                while True:
                    kwargs = {"limit": 200}
                    if cursor:
                        kwargs["cursor"] = cursor
                    resp = client.users_list(**kwargs)
                    all_users += resp["members"]
                    cursor = resp.get("response_metadata", {}).get("next_cursor")
                    if not cursor:
                        break
            except Exception as e:
                return ephemeral(f"❌ Не вдалось завантажити список юзерів: {e}")

            for uname in usernames:
                found = next((u for u in all_users
                              if u.get("name") == uname
                              or u.get("profile", {}).get("display_name", "").lower() == uname.lower()
                              or u.get("profile", {}).get("real_name", "").lower() == uname.lower()), None)
                if found:
                    slack_ids.append(found["id"])

        if not slack_ids:
            return ephemeral("❌ Не знайшов жодного юзера. Спробуй ввести ім'я точніше.")

        added, skipped = [], []
        for slack_id in slack_ids:
            try:
                profile = client.users_info(user=slack_id)
                name = profile["user"]["profile"].get("real_name") or profile["user"]["name"]
            except Exception:
                name = slack_id
            ok = add_member(channel_id, slack_id, name)
            if ok:
                added.append(f"<@{slack_id}> ({name})")
            else:
                skipped.append(f"<@{slack_id}>")

        lines = []
        if added:
            lines.append("✅ Додано: " + ", ".join(added))
        if skipped:
            lines.append("⚠️ Вже в команді: " + ", ".join(skipped))
        return ephemeral("\n".join(lines))

    # ── /oncall-remove @user ──────────────────────────────────────────────────
    if command == "/oncall-remove":
        user_match = re.search(r"<@(\w+)(?:\|[^>]*)?>", text)
        if not user_match:
            return ephemeral("❌ Usage: `/oncall-remove @user`")
        slack_id = user_match.group(1)
        ok = remove_member(channel_id, slack_id)
        if ok:
            return ephemeral(f"✅ <@{slack_id}> видалено з ротації")
        else:
            return ephemeral(f"⚠️ <@{slack_id}> не знайдений в команді")

    # ── /oncall-sub @user [YYYY-MM-DD] ────────────────────────────────────────
    if command == "/oncall-sub":
        user_match = re.search(r"<@(\w+)(?:\|[^>]*)?>", text)
        if not user_match:
            return ephemeral("❌ Usage: `/oncall-sub @user` or `/oncall-sub @user 2025-05-05`")
        slack_id   = user_match.group(1)
        known      = {m["slack_id"]: m["name"] for m in team}
        if slack_id not in known:
            return ephemeral(f"⚠️ <@{slack_id}> не знайдений в команді. Спочатку додай через `/oncall-add`")
        date_match = re.search(r"(\d{4}-\d{2}-\d{2})", text)
        ws         = date_match.group(1) if date_match else str(week_start(date.today()))
        set_override(ws, slack_id, channel_id)
        return ephemeral(f"✅ On-call для тижня `{ws}` → <@{slack_id}> ({known[slack_id]})")

    # ── /oncall-unsub [YYYY-MM-DD] ────────────────────────────────────────────
    if command == "/oncall-unsub":
        date_match = re.search(r"(\d{4}-\d{2}-\d{2})", text)
        ws         = date_match.group(1) if date_match else str(week_start(date.today()))
        clear_override(ws, channel_id)
        return ephemeral(f"✅ Заміна для тижня `{ws}` скасована, повертається стандартна ротація.")

    return "", 200


@flask_app.route("/health")
def health():
    return "OK", 200


if __name__ == "__main__":
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 3000)), debug=False)
