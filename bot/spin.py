"""Текстова анімація «барабан» через послідовні chat.update."""
import time
import random
from slack_sdk import WebClient

WISHES = [
    "Нехай алерти обходять тебе стороною 🍀",
    "Нехай всі алерти мовчать як риба 🐟",
    "Удачі! Пам'ятай: це просто числа на екрані 📊",
    "Нехай логи будуть чисті, а деплої — зелені 🟢",
    "Сподіваємось, твій тиждень буде нуднішим за шпалери 🧱",
    "Нехай чергування буде тихим як бібліотека о 3 ночі 🌙",
    "Бажаємо 0 інцидентів і 100% кави ☕",
    "Хай баги самі себе фіксують! (не хай, але хотілось би) 🐛",
    "Тримай телефон поряд. І валеріанку теж 💊",
    "Нехай моніторинг дивиться на тебе з повагою 👀",
    "Удачі, герою! Місто не знає, але воно вдячне 🦸",
    "P99 latency — нижче за твій пульс 💓",
    "Хай error rate буде як твій настрій в понеділок вранці — близько до нуля 📉",
    "Нехай всі мікросервіси поводяться як слухняні діти 👼",
    "Дихай рівно. Більшість алертів — false positive 😌",
    "Нехай Grafana показує тільки зелені дашборди 📈",
    "Команда вірить у тебе. Ми поруч (в Slack, звісно) 🤝",
]

# Кількість кадрів «крутіння» і затримка між ними
FAST_FRAMES = 10
SLOW_FRAMES = 5
FAST_DELAY  = 0.20
SLOW_DELAY  = 0.45
FINAL_PAUSE = 0.80


def spin_reveal(client: WebClient, channel: str, ts: str, winner: dict, all_names: list) -> None:
    """
    Анімує повідомлення з ts: 'барабан' крутиться і зупиняється на winner.
    """
    names = [m if isinstance(m, str) else m["name"] for m in all_names]

    # Швидка фаза
    for _ in range(FAST_FRAMES):
        picks = random.choices(names, k=3)
        _update(client, channel, ts, f"🎰  {' → '.join(picks)}")
        time.sleep(FAST_DELAY)

    # Сповільнення
    for _ in range(SLOW_FRAMES):
        picks = random.choices(names, k=2)
        _update(client, channel, ts, f"🎰  {' ・ '.join(picks)} ・ ?")
        time.sleep(SLOW_DELAY)

    # Передфінал
    _update(client, channel, ts, f"🎰  ... {winner['name']} ...")
    time.sleep(FINAL_PAUSE)

    # Фінальне відкриття
    wish = random.choice(WISHES)
    client.chat_update(
        channel=channel,
        ts=ts,
        text=f"🎯 *Черговий на наступний тиждень* — <@{winner['slack_id']}> ({winner['name']})\n_{wish}_",
    )


def _update(client: WebClient, channel: str, ts: str, text: str) -> None:
    client.chat_update(channel=channel, ts=ts, text=text)
