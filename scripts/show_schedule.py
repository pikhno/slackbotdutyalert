"""Друкує графік ротації на рік вперед. Запуск: python scripts/show_schedule.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.rotation import full_schedule, ROTATION_START

if __name__ == "__main__":
    weeks = int(sys.argv[1]) if len(sys.argv) > 1 else 52
    print(f"Графік ротації від {ROTATION_START} на {weeks} тижнів:\n")
    print(f"{'#':<4} {'Тиждень (пн–нд)':<25} {'Черговий'}")
    print("─" * 55)
    for i, entry in enumerate(full_schedule(weeks), 1):
        print(f"{i:<4} {entry['week_start']} – {entry['week_end']}  {entry['oncall']['name']}")
