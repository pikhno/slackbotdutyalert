"""
Рахує алерти в каналі за поточний тиждень (пн–сьогодні) і групує їх за назвою.
Алерт = повідомлення від Alertmanager app (bot_id B03E15RC1QT).

Alertmanager шле алерти класичними Slack attachments, і різні правила
заповнюють їх по-різному:
  - деякі мають структуровані fields (title/value) — container, ingress тощо;
  - деякі просто дамплять лейбли як текст "namespace: production\n..." в att.text
    без жодних fields, зате шлють кожне правило під власним username
    (напр. #ruaup: username="vm_available_memory_bytes_low" — це і є alertname);
  - деякі мають att.text як людське речення-заголовок (напр. "targeted mailing
    processing too slowly").
Тому назву витягуємо за пріоритетом: title/pretext → text як заголовок (тільки
якщо це не дамп лейблів) → відоме поле з fields → username повідомлення →
те саме поле, витягнуте з дампу лейблів у text → fallback → сам текст
повідомлення.
"""
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from slack_sdk import WebClient

ALERTMANAGER_BOT_ID = "B03E15RC1QT"

# Поля attachment'а, з яких можна витягнути щось осмислене як назву алерту,
# якщо немає title/text-заголовка. Порядок — пріоритет.
NAME_FIELD_KEYS = ("alertname", "ingress", "label_app", "container", "topic", "pod", "summary")

# Рядок виду "namespace: production" — лейбл, а не людське речення.
_LABEL_LINE_RE = re.compile(r"^([\w][\w.\-]*):\s*(.+)$")

MAX_NAME_LEN = 80
TOP_N_ALERTS = 5


def _clean(text: str) -> str:
    text = (text or "").strip()
    text = re.sub(r"^\*+|\*+$", "", text).strip()
    return text.replace("`", "'")


def _parse_label_lines(text: str) -> dict:
    """Парсить текст виду "key: value\\nkey2: value2" у словник, якщо він на це схожий."""
    result = {}
    for line in (text or "").split("\n"):
        m = _LABEL_LINE_RE.match(line.strip())
        if m:
            result[m.group(1).strip().lower()] = m.group(2).strip()
    return result


def _alert_name(msg: dict) -> str:
    for att in msg.get("attachments", []) or []:
        title = _clean(att.get("title") or att.get("pretext") or "")
        if title:
            return title[:MAX_NAME_LEN]

        raw_text = att.get("text") or ""
        text_as_labels = _parse_label_lines(raw_text)

        if raw_text and not text_as_labels:
            first_line = _clean(raw_text.split("\n")[0])
            if first_line:
                return first_line[:MAX_NAME_LEN]

        fields = {
            (f.get("title") or "").strip().lower(): (f.get("value") or "").strip()
            for f in att.get("fields", [])
        }
        for key in NAME_FIELD_KEYS:
            if fields.get(key):
                return fields[key][:MAX_NAME_LEN]

    # Деякі канали (напр. #ruaup) не заповнюють жодне зі структурованих полів
    # вище, зате шлють кожне правило під власним username — це і є назва алерту.
    username = _clean(msg.get("username") or "")
    if username:
        return username[:MAX_NAME_LEN]

    for att in msg.get("attachments", []) or []:
        text_as_labels = _parse_label_lines(att.get("text") or "")
        for key in NAME_FIELD_KEYS:
            if text_as_labels.get(key):
                return text_as_labels[key][:MAX_NAME_LEN]

        fallback = _clean((att.get("fallback") or "").split("\n")[0])
        if fallback:
            return fallback[:MAX_NAME_LEN]

    text = _clean((msg.get("text") or "").split("\n")[0])
    return text[:MAX_NAME_LEN] or "Інше"


def week_alert_stats(client: WebClient, channel_id: str) -> dict:
    """Повертає {"total": int, "by_name": Counter} за поточний тиждень."""
    now = datetime.now(timezone.utc)
    monday = now - timedelta(days=now.weekday())
    oldest = monday.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()

    by_name: Counter = Counter()
    cursor = None

    while True:
        kwargs: dict = {"channel": channel_id, "oldest": str(oldest), "limit": 200}
        if cursor:
            kwargs["cursor"] = cursor

        resp = client.conversations_history(**kwargs)

        for msg in resp.get("messages", []):
            if msg.get("bot_id") == ALERTMANAGER_BOT_ID:
                by_name[_alert_name(msg)] += 1

        if not resp.get("has_more"):
            break
        cursor = resp["response_metadata"]["next_cursor"]

    return {"total": sum(by_name.values()), "by_name": by_name}


def count_alerts_this_week(client: WebClient, channel_id: str) -> int:
    return week_alert_stats(client, channel_id)["total"]


def format_alert_breakdown(by_name: Counter) -> str:
    """Топ-N алертів за кількістю (менше, якщо різних типів менше N)."""
    most_common = sorted(by_name.items(), key=lambda kv: kv[1], reverse=True)[:TOP_N_ALERTS]
    return "\n".join(f"• `{name}` — *{count}*" for name, count in most_common)
