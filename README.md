# Slack On-Call Bot

Ротація чергових у Slack-каналі алертів.

- Щоп'ятниці о **10:00 Kyiv** — спін-анімація + оголошення чергового на тиждень
- `/черговий` — хто зараз on-call + скільки алертів за тиждень
- `/замінити @user` — замінити чергового (лікарняний / відпустка)
- `/скасувати-заміну` — скасувати заміну

---

## 1. Створити Slack App

1. Зайти на https://api.slack.com/apps → **Create New App** → **From scratch**
2. Назва: `On-Call Bot`, вибрати workspace

### OAuth Scopes (Features → OAuth & Permissions → Bot Token Scopes)
```
chat:write
chat:write.public
channels:history
groups:history
commands
```

3. **Install App** → скопіювати **Bot User OAuth Token** (`xoxb-...`)
4. **Basic Information** → скопіювати **Signing Secret**

### Slash Commands (Features → Slash Commands)
| Command | Request URL | Опис |
|---|---|---|
| `/черговий` | `https://YOUR_APP.onrender.com/slack/events` | Хто зараз on-call |
| `/замінити` | `https://YOUR_APP.onrender.com/slack/events` | Замінити чергового |
| `/скасувати-заміну` | `https://YOUR_APP.onrender.com/slack/events` | Скасувати заміну |

5. **Event Subscriptions** → увімкнути → Request URL: `https://YOUR_APP.onrender.com/slack/events`
6. Запросити бота в канал: `/invite @On-Call Bot`

---

## 2. Знайти Slack ID учасників

В Slack: натиснути на аватар → **View full profile** → **⋮ More** → **Copy member ID**

Відкрити `bot/rotation.py` і замінити `SLACK_ID_*` на реальні ID:
```python
TEAM = [
    {"name": "Mykhailo Zelenskyi", "slack_id": "U0123MYKHAILO"},
    {"name": "Maks Kovalenko",     "slack_id": "U0123MAKS"},
    {"name": "Nadiia Pielie",      "slack_id": "U0123NADIIA"},
    {"name": "Vlad Kemeniash",     "slack_id": "U0123VLAD"},
]
```

---

## 3. Створити GitHub Gist (для зберігання замін)

1. Зайти на https://gist.github.com
2. Назва файлу: `oncall_state.json`
3. Вміст:
```json
{
  "overrides": {}
}
```
4. **Create secret gist** → скопіювати ID з URL (`gist.github.com/user/<ID>`)
5. Створити GitHub PAT: https://github.com/settings/tokens → **Generate new token (classic)** → scope: `gist`

---

## 4. Деплой Flask-app на Render.com (для slash commands)

1. Зайти на https://render.com → **New Web Service** → вибрати цей репозиторій
2. Render сам підхопить `render.yaml`
3. У **Environment Variables** додати:
   - `SLACK_BOT_TOKEN`
   - `SLACK_SIGNING_SECRET`
   - `SLACK_CHANNEL_ID`
   - `GIST_ID`
   - `GIST_TOKEN`
4. Зберегти URL (`https://slack-oncall-bot.onrender.com`) → вставити в Slack slash commands

---

## 5. GitHub Secrets для Actions

У репозиторії: **Settings → Secrets and variables → Actions → New repository secret**

| Secret | Що вставити |
|---|---|
| `SLACK_BOT_TOKEN` | `xoxb-...` |
| `SLACK_CHANNEL_ID` | `C...` |
| `GIST_ID` | ID gist |
| `GIST_TOKEN` | GitHub PAT зі scope gist |
| `ALERT_PATTERNS` | `FIRING,CRITICAL,ALERT` (або свої) |

---

## 6. Ручне тестування

### Переглянути графік (не постить у Slack):
```bash
python scripts/show_schedule.py        # 52 тижні
python scripts/show_schedule.py 10     # перші 10 тижнів
```

### Запустити оголошення локально:
```bash
cp .env.example .env
# Заповнити .env реальними значеннями
source .env  # або використати python-dotenv
python scripts/announce.py
```

### Через GitHub Actions вручну:
- **Actions → Manual Test → Run workflow** → вибрати `announce` або `show_schedule`
- **Actions → Friday On-Call Announcement → Run workflow** → `dry_run: true` (без постингу)

---

## Структура проекту

```
slack-oncall-bot/
├── .github/workflows/
│   ├── friday_announcement.yml   # Крон: щоп'ятниці 10:00 Kyiv
│   └── manual_test.yml           # Ручний запуск
├── bot/
│   ├── rotation.py               # Логіка ротації
│   ├── state.py                  # Стан у GitHub Gist
│   ├── alerts.py                 # Лічильник алертів
│   └── spin.py                   # Анімація «барабан»
├── scripts/
│   ├── announce.py               # П'ятничний скрипт
│   └── show_schedule.py          # Перегляд графіку
├── app.py                        # Flask + Slack Bolt (slash commands)
├── requirements.txt
├── render.yaml                   # Конфіг для Render.com
└── .env.example
```

---

## Зміна чергового (лікарняний / відпустка)

У Slack:
```
/замінити @Nadiia              → замінює поточний тиждень
/замінити @Nadiia 2025-05-05   → замінює конкретний тиждень (вказати понеділок)
/скасувати-заміну              → повертає стандартну ротацію
/скасувати-заміну 2025-05-05   → скасовує заміну на конкретний тиждень
```
