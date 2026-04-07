"""
update_image_urls_to_yc.py

Заменяет URL изображений в JSON-источнике истины:
  raw.githubusercontent.com/anton-ai5010/yamarcket-images/main/
  → storage.yandexcloud.net/yamarcket-images/
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
JSON_PATH = ROOT / "new table" / "Онлайн-подписки и карты оплаты_истина_с_характеристиками.json"

OLD_BASE = "https://raw.githubusercontent.com/anton-ai5010/yamarcket-images/main/"
NEW_BASE = "https://storage.yandexcloud.net/yamarcket-images/"


def main():
    print(f"Читаю {JSON_PATH.name}...")
    with open(JSON_PATH, encoding="utf-8") as f:
        data = json.load(f)

    rows = data["Данные о товарах"]
    # Заголовки в строке 3 (индекс 3), данные с индекса 7
    headers = rows[3]
    # Находим индекс колонки с изображениями
    img_col = None
    for i, h in enumerate(headers):
        if h and "изображени" in str(h).lower():
            img_col = i
            break

    if img_col is None:
        print("ОШИБКА: колонка изображений не найдена!")
        return

    print(f"Колонка изображений: {img_col} ({headers[img_col]})")

    updated = 0
    for row in rows[7:]:
        if not row or not str(row[0] or "").startswith("GFT"):
            continue
        val = str(row[img_col] or "")
        if OLD_BASE in val:
            row[img_col] = val.replace(OLD_BASE, NEW_BASE)
            updated += 1

    print(f"Обновлено строк: {updated}")

    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=None, separators=(",", ":"))

    print("Сохранено.")


if __name__ == "__main__":
    main()
