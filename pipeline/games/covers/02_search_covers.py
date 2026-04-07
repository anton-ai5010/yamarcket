"""
02_search_covers.py
Ищет AppID в Steam и обложки на RAWG для каждой уникальной игры.
Читает games_list.json, пишет covers_found.json.

Структура covers_found.json:
{
  "slug": {
    "cover_name": "...",
    "source": "steam" | "rawg" | "not_found",
    "app_id": 12345,          # только для Steam
    "cover_url": "https://...",
    "confidence": 0.95,
    "found_name": "...",       # как называется на сайте
  }
}

Настройка:
  - Steam API: ключ не нужен
  - RAWG API: нужен бесплатный ключ → https://rawg.io/apidocs → сохранить в ~/.zshrc как RAWG_API_KEY
    (если ключа нет — Xbox/Nintendo игры будут помечены "not_found")
"""
import json
import os
import re
import time
from difflib import SequenceMatcher
from pathlib import Path
from typing import Optional

import requests

ROOT = Path(__file__).parent.parent.parent.parent
GAMES_LIST = ROOT / "pipeline" / "images" / "output" / "games_covers" / "games_list.json"
OUT_PATH = ROOT / "pipeline" / "images" / "output" / "games_covers" / "covers_found.json"

RAWG_KEY = os.environ.get("RAWG_API_KEY", "")

# ─── Утилиты ──────────────────────────────────────────────────────────────────

def similarity(a: str, b: str) -> float:
    """Нечёткое сравнение строк (0..1)."""
    a = a.lower().strip()
    b = b.lower().strip()
    return SequenceMatcher(None, a, b).ratio()


def clean_name(name: str) -> str:
    """Убирает Edition/Pack/суффиксы для лучшего поиска."""
    name = re.sub(r"\s+(Standard|Deluxe|Premium|Gold|Ultimate|Complete|GOTY|Definitive|Remastered|Remake|Anniversary|Digital|Edition|Bundle|Pack|Upgrade|Collection)\b.*$",
                  "", name, flags=re.IGNORECASE)
    return name.strip()


# ─── Steam ────────────────────────────────────────────────────────────────────

STEAM_SEARCH = "https://store.steampowered.com/api/storesearch/"
STEAM_COVER_LIBRARY = "https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/library_600x900.jpg"
STEAM_COVER_HEADER = "https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/header.jpg"


def steam_search(game_name: str) -> Optional[dict]:
    """
    Поиск в Steam Store Search API.
    Возвращает {app_id, found_name, cover_url, confidence} или None.
    """
    params = {"term": game_name, "l": "english", "cc": "US"}
    try:
        r = requests.get(STEAM_SEARCH, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"  [Steam] Ошибка запроса: {e}")
        return None

    items = data.get("items", [])
    if not items:
        return None

    # Ищем лучшее совпадение по названию
    best = None
    best_score = 0.0
    for item in items[:5]:
        found_name = item.get("name", "")
        score = similarity(game_name, found_name)
        if score > best_score:
            best_score = score
            best = item

    if best is None or best_score < 0.35:
        return None

    app_id = best.get("id")
    found_name = best.get("name", "")

    # Проверяем наличие library cover (вертикальная 600x900)
    cover_url = STEAM_COVER_LIBRARY.format(appid=app_id)
    try:
        head = requests.head(cover_url, timeout=5, allow_redirects=True)
        if head.status_code != 200:
            cover_url = STEAM_COVER_HEADER.format(appid=app_id)
    except Exception:
        cover_url = STEAM_COVER_HEADER.format(appid=app_id)

    return {
        "source": "steam",
        "app_id": app_id,
        "found_name": found_name,
        "cover_url": cover_url,
        "confidence": round(best_score, 3),
    }


# ─── RAWG ─────────────────────────────────────────────────────────────────────

RAWG_SEARCH = "https://api.rawg.io/api/games"


def rawg_search(game_name: str) -> Optional[dict]:
    """
    Поиск в RAWG API (нужен бесплатный ключ).
    Возвращает {found_name, cover_url, confidence} или None.
    """
    if not RAWG_KEY:
        return None

    params = {"search": game_name, "key": RAWG_KEY, "page_size": 5}
    try:
        r = requests.get(RAWG_SEARCH, params=params, timeout=10)
        r.raise_for_status()
        results = r.json().get("results", [])
    except Exception as e:
        print(f"  [RAWG] Ошибка запроса: {e}")
        return None

    if not results:
        return None

    best = None
    best_score = 0.0
    for item in results:
        found_name = item.get("name", "")
        score = similarity(game_name, found_name)
        if score > best_score:
            best_score = score
            best = item

    if best is None or best_score < 0.35:
        return None

    cover_url = best.get("background_image", "")
    if not cover_url:
        return None

    return {
        "source": "rawg",
        "app_id": None,
        "found_name": best.get("name", ""),
        "cover_url": cover_url,
        "confidence": round(best_score, 3),
    }


# ─── Основная логика ──────────────────────────────────────────────────────────

def find_cover(game: dict) -> dict:
    """Поиск обложки для одной игры (Steam → RAWG → fallback)."""
    cover_name = game["cover_name"]
    source_hint = game["source"]

    result = {
        "cover_name": cover_name,
        "slug": game["slug"],
        "source": "not_found",
        "app_id": None,
        "cover_url": None,
        "found_name": None,
        "confidence": 0.0,
    }

    # Стратегия: Steam первый для PC, RAWG первый для Xbox/Nintendo
    if source_hint == "steam":
        found = steam_search(cover_name)
        if not found or found["confidence"] < 0.55:
            # Пробуем очищенное название
            cleaned = clean_name(cover_name)
            if cleaned != cover_name:
                found2 = steam_search(cleaned)
                if found2 and found2["confidence"] > (found["confidence"] if found else 0):
                    found = found2
        if found and found["confidence"] >= 0.40:
            result.update(found)
            return result
        # Fallback на RAWG
        found = rawg_search(cover_name)
        if found and found["confidence"] >= 0.40:
            result.update(found)
    else:
        # Xbox / Nintendo → RAWG первым
        found = rawg_search(cover_name)
        if not found or found["confidence"] < 0.55:
            found2 = steam_search(cover_name)
            if found2 and found2["confidence"] > (found["confidence"] if found else 0):
                found = found2
        if found and found["confidence"] >= 0.40:
            result.update(found)

    return result


def main():
    print(f"Читаю {GAMES_LIST}...")
    with open(GAMES_LIST, "r", encoding="utf-8") as f:
        data = json.load(f)

    games = data["games"]
    print(f"Игр для поиска: {len(games)}")
    if not RAWG_KEY:
        print("  [WARN] RAWG_API_KEY не задан — Xbox/Nintendo игры могут быть не найдены")
    print()

    # Загружаем уже найденные (для продолжения после прерывания)
    found_results = {}
    if OUT_PATH.exists():
        with open(OUT_PATH, "r", encoding="utf-8") as f:
            found_results = json.load(f)
        print(f"  Уже найдено: {len(found_results)}, продолжаю с {len(found_results)}...")

    stats = {"steam": 0, "rawg": 0, "not_found": 0}

    for i, game in enumerate(games):
        slug = game["slug"]

        if slug in found_results:
            continue  # уже найдено

        print(f"[{i+1}/{len(games)}] {game['cover_name'][:60]}", end="  ")

        result = find_cover(game)
        found_results[slug] = result

        src = result["source"]
        conf = result["confidence"]
        stats[src] = stats.get(src, 0) + 1

        if src != "not_found":
            print(f"✓ {src} ({conf:.2f}) → {result['found_name'][:50]}")
        else:
            print("✗ не найдено")

        # Сохраняем после каждой игры (можно прерваться и продолжить)
        with open(OUT_PATH, "w", encoding="utf-8") as f:
            json.dump(found_results, f, ensure_ascii=False, indent=2)

        # Rate limiting
        time.sleep(0.5)

    print()
    print(f"Результаты:")
    print(f"  Steam:     {stats.get('steam', 0)}")
    print(f"  RAWG:      {stats.get('rawg', 0)}")
    print(f"  Не найдено: {stats.get('not_found', 0)}")
    print(f"Сохранено: {OUT_PATH}")


if __name__ == "__main__":
    main()
