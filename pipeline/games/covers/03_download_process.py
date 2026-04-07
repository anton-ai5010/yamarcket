"""
03_download_process.py
Скачивает обложки, конвертирует в 1080x1440 PNG (3:4).

Обработка изображения:
  - Оригинал (любой размер) центрируется на размытом фоне 1080x1440
  - Фон = само изображение, растянутое и размытое (как в Steam Library)
  - Итог: 1080x1440 PNG

Структура файлов:
  raw/{slug}.jpg или .png   — скачанный оригинал
  final/{slug}.png           — обработанный 1080x1440
  sku_mapping.json           — SKU → URL для загрузки в 1.xlsx
"""
import json
import time
import re
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image, ImageFilter, ImageEnhance

ROOT = Path(__file__).parent.parent.parent.parent
COVERS_DIR = ROOT / "pipeline" / "images" / "output" / "games_covers"
GAMES_LIST = COVERS_DIR / "games_list.json"
COVERS_FOUND = COVERS_DIR / "covers_found.json"
RAW_DIR = COVERS_DIR / "raw"
FINAL_DIR = COVERS_DIR / "final"
MAPPING_OUT = COVERS_DIR / "sku_mapping.json"

TARGET_W, TARGET_H = 1080, 1440  # 3:4

RAW_DIR.mkdir(parents=True, exist_ok=True)
FINAL_DIR.mkdir(parents=True, exist_ok=True)


# ─── Обработка изображения ────────────────────────────────────────────────────

def make_blurred_bg(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """
    Создаёт фон 1080x1440: само изображение растянуто + сильный blur + затемнение.
    """
    bg = img.resize((target_w, target_h), Image.LANCZOS)
    bg = bg.filter(ImageFilter.GaussianBlur(40))
    bg = ImageEnhance.Brightness(bg).enhance(0.45)
    return bg


def fit_image(img: Image.Image, target_w: int, target_h: int) -> tuple[Image.Image, int, int]:
    """
    Масштабирует img с сохранением пропорций чтобы вписаться в target.
    Возвращает (resized_img, offset_x, offset_y).
    """
    img_ratio = img.width / img.height
    target_ratio = target_w / target_h

    if img_ratio > target_ratio:
        # Шире — подгоняем по ширине
        new_w = target_w
        new_h = round(target_w / img_ratio)
    else:
        # Уже или равно — подгоняем по высоте
        new_h = target_h
        new_w = round(target_h * img_ratio)

    resized = img.resize((new_w, new_h), Image.LANCZOS)
    off_x = (target_w - new_w) // 2
    off_y = (target_h - new_h) // 2
    return resized, off_x, off_y


def process_cover(raw_path: Path) -> Image.Image:
    """Преобразует обложку в 1080x1440 PNG с blur-фоном."""
    with Image.open(raw_path) as img:
        img = img.convert("RGB")
        bg = make_blurred_bg(img, TARGET_W, TARGET_H)
        front, ox, oy = fit_image(img, TARGET_W, TARGET_H)
        bg.paste(front, (ox, oy))
        return bg.copy()


# ─── Скачивание ───────────────────────────────────────────────────────────────

def download_cover(url: str, dest_path: Path) -> bool:
    """Скачивает обложку. Возвращает True при успехе."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; YaMarketBot/1.0)"}
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()

        # Проверяем что это изображение
        content_type = r.headers.get("content-type", "")
        if "image" not in content_type and len(r.content) < 5000:
            return False

        dest_path.write_bytes(r.content)
        return True
    except Exception as e:
        print(f"    [DL] Ошибка: {e}")
        return False


# ─── Основная логика ──────────────────────────────────────────────────────────

def main():
    print("Читаю данные...")
    with open(GAMES_LIST, "r", encoding="utf-8") as f:
        games_data = json.load(f)
    with open(COVERS_FOUND, "r", encoding="utf-8") as f:
        covers_found = json.load(f)

    sku_to_cover = games_data["sku_to_cover"]
    games_list = games_data["games"]

    # Статистика
    stats = {"ok": 0, "skip": 0, "fail": 0, "not_found": 0}

    for i, game in enumerate(games_list):
        slug = game["slug"]
        cover_name = game["cover_name"]
        found = covers_found.get(slug, {})

        cover_url = found.get("cover_url")
        final_path = FINAL_DIR / f"{slug}.png"

        print(f"[{i+1}/{len(games_list)}] {cover_name[:55]}", end="  ")

        if final_path.exists():
            print("уже есть, пропускаю")
            stats["skip"] += 1
            continue

        if not cover_url:
            print("✗ обложка не найдена")
            stats["not_found"] += 1
            continue

        # Определяем расширение
        ext = ".jpg" if "jpg" in cover_url.lower() else ".png"
        raw_path = RAW_DIR / f"{slug}{ext}"

        # Скачиваем если нет
        if not raw_path.exists():
            ok = download_cover(cover_url, raw_path)
            if not ok:
                print("✗ ошибка скачивания")
                stats["fail"] += 1
                continue
            time.sleep(0.3)

        # Обрабатываем
        try:
            result_img = process_cover(raw_path)
            result_img.save(final_path, "PNG", optimize=True)
            print(f"✓ сохранено {result_img.size}")
            stats["ok"] += 1
        except Exception as e:
            print(f"✗ ошибка обработки: {e}")
            stats["fail"] += 1

    print()
    print(f"Результаты:")
    print(f"  Обработано:   {stats['ok']}")
    print(f"  Пропущено:    {stats['skip']}")
    print(f"  Не найдено:   {stats['not_found']}")
    print(f"  Ошибки:       {stats['fail']}")

    # Создаём маппинг SKU → путь к файлу
    print()
    print("Создаю sku_mapping.json...")
    sku_mapping = {}
    for sku, slug in sku_to_cover.items():
        final_path = FINAL_DIR / f"{slug}.png"
        sku_mapping[sku] = {
            "slug": slug,
            "local_path": str(final_path),
            "exists": final_path.exists(),
        }

    with open(MAPPING_OUT, "w", encoding="utf-8") as f:
        json.dump(sku_mapping, f, ensure_ascii=False, indent=2)

    total = len(sku_mapping)
    exists = sum(1 for v in sku_mapping.values() if v["exists"])
    print(f"  SKU с готовыми обложками: {exists}/{total}")
    print(f"  Файл: {MAPPING_OUT}")


if __name__ == "__main__":
    main()
