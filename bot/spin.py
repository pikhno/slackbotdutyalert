"""Текстова анімація «барабан» через послідовні chat.update."""
import time
import random
from slack_sdk import WebClient

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
    client.chat_update(
        channel=channel,
        ts=ts,
        text=f"🎯 *Черговий на наступний тиждень* — <@{winner['slack_id']}> ({winner['name']})",
    )


def _update(client: WebClient, channel: str, ts: str, text: str) -> None:
    client.chat_update(channel=channel, ts=ts, text=text)
