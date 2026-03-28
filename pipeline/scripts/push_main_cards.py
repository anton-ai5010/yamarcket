#!/usr/bin/env python3
"""
1. Конвертирует PNG из output/main_cards/{brand}/ → JPEG в yamarcket-images/main_cards/{brand}/
2. Удаляет старые плоские JPEG из yamarcket-images/main_cards/
3. Обновляет JSON — заменяет первую ссылку на главную карточку новым URL
"""

import json
import re
from pathlib import Path
from PIL import Image

# Пути
PIPELINE_ROOT  = Path("/media/anton/Новый том/yamarcket/pipeline")
IMAGES_REPO    = Path("/media/anton/Новый том/yamarcket-images")
JSON_PATH      = Path("/media/anton/Новый том/yamarcket/new table/Онлайн-подписки и карты оплаты_истина_с_характеристиками.json")
SRC_ROOT       = PIPELINE_ROOT / "images/output/main_cards"
DST_ROOT       = IMAGES_REPO / "main_cards"
RAW_BASE       = "https://raw.githubusercontent.com/anton-ai5010/yamarcket-images/main/main_cards"
JPEG_QUALITY   = 87

# ─── 1. Конвертация PNG → JPEG ────────────────────────────────────────────────
png_files = sorted(SRC_ROOT.glob("*/*.png"))
print(f"PNG файлов к конвертации: {len(png_files)}")

converted = 0
sku_to_url = {}  # GFT123 → raw URL

for png in png_files:
    brand = png.parent.name
    dst_dir = DST_ROOT / brand
    dst_dir.mkdir(parents=True, exist_ok=True)

    jpg_name = png.stem + ".jpg"
    jpg_path = dst_dir / jpg_name

    if not jpg_path.exists():
        img = Image.open(png).convert("RGB")
        img.save(jpg_path, "JPEG", quality=JPEG_QUALITY, optimize=True)
        converted += 1

    # SKU из имени файла (напр. GFT15_oae.jpg → GFT15)
    sku = re.match(r"(GFT\d+)", png.stem)
    if sku:
        sku_to_url[sku.group(1)] = f"{RAW_BASE}/{brand}/{jpg_name}"

print(f"Сконвертировано: {converted}, пропущено: {len(png_files) - converted}")

# ─── 2. Удаление старых плоских JPEG ─────────────────────────────────────────
old_flat = list(DST_ROOT.glob("GFT*.jpg"))
print(f"\nСтарых плоских JPEG: {len(old_flat)}")
for f in old_flat:
    f.unlink()
print("Удалены.")

# ─── 3. Обновление JSON ───────────────────────────────────────────────────────
print("\nЧитаю JSON...")
with open(JSON_PATH, encoding="utf-8") as f:
    data = json.load(f)

updated = 0
no_card = []

for row in data["Данные о товарах"]:
    if not isinstance(row, list) or len(row) < 8:
        continue
    sku_raw = str(row[0] or "").strip()
    if not re.match(r"^GFT\d+$", sku_raw):
        # Попробуем привести
        if isinstance(row[0], float):
            sku_raw = f"GFT{int(row[0])}"
        else:
            continue
    if not re.match(r"^GFT\d+$", sku_raw):
        continue

    new_url = sku_to_url.get(sku_raw)
    if not new_url:
        no_card.append(sku_raw)
        continue

    imgs_str = str(row[7] or "").strip()
    if imgs_str and imgs_str != "None":
        imgs = [u.strip() for u in imgs_str.split(",") if u.strip()]
    else:
        imgs = []

    # Убираем старый URL главной карточки (содержит SKU)
    imgs = [u for u in imgs if sku_raw not in u]

    # Вставляем новый URL первым
    imgs = [new_url] + imgs

    row[7] = ", ".join(imgs)
    updated += 1

print(f"Обновлено товаров: {updated}")
print(f"Без главной карточки: {len(no_card)} (игры/DLC или не сгенерированы)")
if no_card[:5]:
    print("  Примеры:", no_card[:5])

print("\nСохраняю JSON...")
with open(JSON_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
print("Готово.")
