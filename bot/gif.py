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


def get_random_gif():
    """Шукає топ-25 GIF по рандомному тегу і повертає рандомний з них."""
    if not GIPHY_KEY:
        return None
    try:
        tag = random.choice(TAGS)
        r = requests.get(
            "https://api.giphy.com/v1/gifs/search",
            params={"api_key": GIPHY_KEY, "q": tag, "limit": 25, "rating": "g"},
            timeout=5,
        )
        r.raise_for_status()
        results = r.json().get("data", [])
        if not results:
            return None
        gif = random.choice(results)
        return gif.get("images", {}).get("original", {}).get("url")
    except Exception:
        return None
