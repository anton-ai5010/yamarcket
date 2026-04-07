"""
01_extract_games.py
Извлекает список всех игр/DLC из JSON таблицы.
Создаёт games_list.json со структурой:
  - games: список уникальных игр {cover_name, platform, skus, slug}
  - sku_to_cover: маппинг SKU → slug
"""
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent.parent
JSON_PATH = ROOT / "new table" / "Онлайн-подписки и карты оплаты_истина_с_характеристиками.json"
OUT_PATH = ROOT / "pipeline" / "images" / "output" / "games_covers" / "games_list.json"

PLATFORM_SERVICES = {'Steam', 'Xbox', 'Epic Games', 'EA App', 'Battle.net', 'Ubisoft Connect', 'GOG', ''}

# Суффиксы в названиях standalone-игр, которые мешают поиску
NAME_SUFFIXES = [
    ' игра в электронном формате', ' цифровой ключ', ' электронный ключ',
    ' лицензионный ключ', ' цифровая версия', ' оригинальный ключ',
    ' официальный ключ', ' ключ активации',
]


def slugify(name: str) -> str:
    """Преобразует название в slug для имени файла."""
    s = name.lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_-]+", "_", s)
    s = s.strip("_")
    return s[:80]  # ограничение длины


def extract_cover_name(name_str: str, servis_str: str) -> str:
    """Определяет название игры для поиска обложки."""
    if servis_str not in PLATFORM_SERVICES:
        # DLC/игра с конкретным названием сервиса
        return servis_str

    # Standalone: извлекаем название из поля "Название товара"
    cover = name_str.split("|")[0].strip()
    for suffix in NAME_SUFFIXES:
        cover = re.sub(re.escape(suffix), "", cover, flags=re.IGNORECASE)
    return cover.strip()


def determine_source(platform: str, cover_name: str) -> str:
    """Определяет основной источник для поиска обложки."""
    p = platform.lower()
    if "xbox" in p:
        return "rawg"
    if "nintendo" in p or "switch" in p:
        return "rawg"
    return "steam"  # ПК / Steam по умолчанию


def main():
    print(f"Читаю {JSON_PATH}...")
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    items = data["Данные о товарах"]

    game_info = {}      # cover_name → {platform, skus, slug, source}
    sku_to_cover = {}   # SKU → slug

    for row in items[7:]:
        sku = row[0] if len(row) > 0 else None
        name = row[6] if len(row) > 6 else None
        primenenie = row[39] if len(row) > 39 else None
        naznachenie = row[40] if len(row) > 40 else None
        servis = row[41] if len(row) > 41 else None
        platform = row[43] if len(row) > 43 else None

        if not sku or not name:
            continue
        if primenenie != "сервис активации" or naznachenie != "игры":
            continue

        sku_str = str(sku)
        name_str = str(name)
        servis_str = str(servis or "")
        plat_str = str(platform or "")

        cover_name = extract_cover_name(name_str, servis_str)
        slug = slugify(cover_name)
        source = determine_source(plat_str, cover_name)

        if cover_name not in game_info:
            game_info[cover_name] = {
                "cover_name": cover_name,
                "slug": slug,
                "platform": plat_str,
                "source": source,
                "skus": [],
            }

        game_info[cover_name]["skus"].append(sku_str)
        sku_to_cover[sku_str] = slug

    games_list = sorted(game_info.values(), key=lambda x: x["cover_name"])

    result = {
        "total_games": len(games_list),
        "total_skus": len(sku_to_cover),
        "games": games_list,
        "sku_to_cover": sku_to_cover,
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Уникальных игр: {len(games_list)}")
    print(f"Всего SKU:      {len(sku_to_cover)}")
    print(f"Сохранено:      {OUT_PATH}")


if __name__ == "__main__":
    main()
