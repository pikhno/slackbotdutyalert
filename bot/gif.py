"""
Тягне рандомний тематичний GIF з Giphy API.
"""
import os
import random
import requests

GIPHY_KEY = os.environ.get("GIPHY_API_KEY", "")

# Теги по настрою — чергуються рандомно
TAGS = [
    "this is fine fire",
    "monday morning coffee",
    "stressed programmer",
    "server down",
    "panic button",
    "help me",
    "everything is fine",
    "good luck",
    "you got this",
    "sending help",
    "office chaos",
    "coffee please",
    "stay calm",
    "superhero ready",
    "let's go work",
]


def get_random_gif() -> str | None:
    """Повертає URL gif або None якщо щось пішло не так."""
    if not GIPHY_KEY:
        return None
    try:
        tag = random.choice(TAGS)
        r = requests.get(
            "https://api.giphy.com/v1/gifs/random",
            params={"api_key": GIPHY_KEY, "tag": tag, "rating": "g"},
            timeout=5,
        )
        r.raise_for_status()
        data = r.json().get("data", {})
        return data.get("images", {}).get("original", {}).get("url")
    except Exception:
        return None
