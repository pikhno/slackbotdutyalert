from slack_sdk import WebClient
import time
import random

WISHES = [
    "Нехай алерти обходять тебе стороною 🍀",
    "Нехай всі алерти мовчать як риба 🐟",
    "Удачі! Пам'ятай: це просто числа на екрані 📊",
    "Нехай логи будуть чисті, а деплої — зелені 🟢",
    "Сподіваємось, твій тиждень буде нуднішим за шпалери 🧱",
    "Нехай чергування буде тихим як бібліотека о 3 ночі 🌙",
    "Бажаємо 0 інцидентів і 100% кави ☕",
    "Хай баги самі себе фіксять! (не хай, але хотілось би) 🐛",
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


def spin_reveal(client: WebClient, channel: str, ts: str, names: list[str], winner: str) -> None:
    wish = random.choice(WISHES)

    for _ in range(10):
        name = random.choice(names)
        client.chat_update(
            channel=channel,
            ts=ts,
            text=f"🎰 *Крутимо барабан...* _{name}_",
        )
        time.sleep(0.20)

    for _ in range(5):
        name = random.choice(names)
        client.chat_update(
            channel=channel,
            ts=ts,
            text=f"🎯 *Майже...* _{name}_",
        )
        time.sleep(0.45)

    client.chat_update(
        channel=channel,
        ts=ts,
        text=f"🎯 *Черговий наступного тижня* — @{winner}\n_\"{wish}\"_",
    )
