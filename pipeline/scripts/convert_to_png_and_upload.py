"""
convert_to_png_and_upload.py

1. main_cards: копирует оригинальные PNG из pipeline/images/output/main_cards/
   (для тех у кого нет оригинала — конвертирует из JPG)
2. instructions_v2, games: конвертирует JPG → PNG
3. Удаляет JPG из yamarcket-images/
4. Загружает новые PNG в Yandex Object Storage
5. Обновляет .jpg → .png в JSON-источнике истины
"""
import os
import json
import shutil
import boto3
from PIL import Image
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).parent.parent.parent
IMAGES_ROOT = ROOT.parent / "yamarcket-images"
PIPELINE_PNG = ROOT / "pipeline" / "images" / "output" / "main_cards"
JSON_PATH = ROOT / "new table" / "Онлайн-подписки и карты оплаты_истина_с_характеристиками.json"

load_dotenv(ROOT / ".env")
ACCESS_KEY = os.environ["YC_ACCESS_KEY_ID"]
SECRET_KEY = os.environ["YC_SECRET_ACCESS_KEY"]
BUCKET = os.environ["YC_BUCKET"]
ENDPOINT = os.environ["YC_ENDPOINT"]

session = boto3.session.Session()
s3 = session.client(
    service_name="s3",
    endpoint_url=ENDPOINT,
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    region_name="ru-central1",
)


def upload_png(local_path: Path, key: str):
    s3.upload_file(
        str(local_path), BUCKET, key,
        ExtraArgs={"ContentType": "image/png", "ACL": "public-read"},
    )


def delete_old_jpg(key: str):
    try:
        s3.delete_object(Bucket=BUCKET, Key=key)
    except Exception:
        pass


def process_main_cards():
    """Используем оригинальные PNG из pipeline, остальное конвертируем из JPG."""
    print("\n=== main_cards/ ===")
    # Индекс оригиналов: stem → path
    originals = {}
    for subdir in PIPELINE_PNG.iterdir():
        if subdir.is_dir():
            for f in subdir.glob("*.png"):
                originals[f.stem] = f

    print(f"  Оригинальных PNG в pipeline: {len(originals)}")

    jpg_files = list((IMAGES_ROOT / "main_cards").rglob("*.jpg"))
    print(f"  JPG в yamarcket-images: {len(jpg_files)}")

    copied = converted = uploaded = failed = 0
    for jpg in jpg_files:
        png = jpg.with_suffix(".png")
        stem = jpg.stem

        # Сначала создаём PNG локально
        if stem in originals:
            # Копируем оригинал из pipeline
            shutil.copy2(originals[stem], png)
            copied += 1
        else:
            # Конвертируем из JPG
            try:
                with Image.open(jpg) as img:
                    img.save(png, "PNG")
                converted += 1
            except Exception as e:
                print(f"  FAIL конвертация {jpg.name}: {e}")
                failed += 1
                continue

        # Загружаем PNG в S3
        subdir = jpg.parent.name  # steam, playstation, xbox
        key_png = f"main_cards/{subdir}/{png.name}"
        key_jpg = f"main_cards/{subdir}/{jpg.name}"
        try:
            upload_png(png, key_png)
            delete_old_jpg(key_jpg)
            jpg.unlink()
            uploaded += 1
        except Exception as e:
            print(f"  FAIL загрузка {png.name}: {e}")
            failed += 1

        if (copied + converted) % 300 == 0 and (copied + converted) > 0:
            print(f"  [{copied+converted}/{len(jpg_files)}] из pipeline: {copied}, конвертировано: {converted}...")

    print(f"  Из pipeline: {copied}, конвертировано: {converted}, загружено: {uploaded}, ошибок: {failed}")


def process_dir(dir_name: str):
    """Конвертирует JPG → PNG и перезагружает в S3."""
    print(f"\n=== {dir_name}/ ===")
    jpg_files = list((IMAGES_ROOT / dir_name).rglob("*.jpg"))
    print(f"  JPG файлов: {len(jpg_files)}")

    ok = failed = 0
    for i, jpg in enumerate(jpg_files):
        png = jpg.with_suffix(".png")
        try:
            with Image.open(jpg) as img:
                img.save(png, "PNG")

            key_png = f"{dir_name}/{png.name}"
            key_jpg = f"{dir_name}/{jpg.name}"
            upload_png(png, key_png)
            delete_old_jpg(key_jpg)
            jpg.unlink()
            ok += 1
        except Exception as e:
            print(f"  FAIL {jpg.name}: {e}")
            failed += 1

        if (i + 1) % 200 == 0:
            print(f"  [{i+1}/{len(jpg_files)}] ok: {ok}, ошибок: {failed}...")

    print(f"  Готово: {ok} загружено, {failed} ошибок")


def update_json_urls():
    """Меняет .jpg → .png в URL изображений JSON."""
    print("\n=== Обновление JSON ===")
    with open(JSON_PATH, encoding="utf-8") as f:
        data = json.load(f)

    rows = data["Данные о товарах"]
    headers = rows[3]
    img_col = next(i for i, h in enumerate(headers) if h and "изображени" in str(h).lower())

    updated = 0
    for row in rows[7:]:
        if not row or not str(row[0] or "").startswith("GFT"):
            continue
        val = str(row[img_col] or "")
        if ".jpg" in val:
            row[img_col] = val.replace(".jpg", ".png")
            updated += 1

    print(f"  Обновлено строк: {updated}")
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    print("  JSON сохранён.")


def main():
    process_main_cards()
    process_dir("instructions_v2")
    process_dir("games")
    update_json_urls()
    print("\nВсё готово! Запустите sync_json_to_xlsx.py для обновления xlsx.")


if __name__ == "__main__":
    main()
