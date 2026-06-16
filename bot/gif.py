"""
Тягне рандомний тематичний GIF з Giphy API.
"""
import os
import random
import requests

GIPHY_KEY = os.environ.get("GIPHY_API_KEY", "")

TAGS = [
    "this is fine fire",
    "stressed programmer",
    "server down",
    "panic button",
    "help me",
    "everything is fine",
    "good luck",
    "you got this",
    "sending help",
    "office chaos",
    "stay calm",
    "superhero ready",
    "let's go work",
    "disaster incoming",
    "rip meme",
    "good luck you'll need it",
    "this is fine meme",
    "crying at work",
    "send help",
    "game over",
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
        images = gif.get("images", {})
        return (
            images.get("fixed_height", {}).get("url")
            or images.get("original", {}).get("url")
        )
    except Exception:
        return None
