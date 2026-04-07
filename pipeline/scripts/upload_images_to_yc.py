"""
upload_images_to_yc.py

Загружает все изображения из yamarcket-images/ в Yandex Object Storage.
Структура бакета повторяет локальную: main_cards/, instructions_v2/, games/

Использует boto3 (AWS S3-совместимый API).
Устанавливка: pip install boto3 python-dotenv
"""
import os
import boto3
from pathlib import Path
from dotenv import load_dotenv

# Загружаем .env из корня проекта
ROOT = Path(__file__).parent.parent.parent
load_dotenv(ROOT / ".env")

ACCESS_KEY = os.environ["YC_ACCESS_KEY_ID"]
SECRET_KEY = os.environ["YC_SECRET_ACCESS_KEY"]
BUCKET = os.environ["YC_BUCKET"]
ENDPOINT = os.environ["YC_ENDPOINT"]

# Папка с изображениями (отдельный репозиторий рядом)
IMAGES_ROOT = ROOT.parent / "yamarcket-images"
UPLOAD_DIRS = ["main_cards", "instructions_v2", "games"]

session = boto3.session.Session()
s3 = session.client(
    service_name="s3",
    endpoint_url=ENDPOINT,
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    region_name="ru-central1",
)


def upload_dir(local_dir: Path, prefix: str):
    files = list(local_dir.rglob("*.jpg")) + list(local_dir.rglob("*.png"))
    print(f"\n{prefix}/: {len(files)} файлов")
    ok = skip = fail = 0

    for i, f in enumerate(files):
        # Ключ в бакете: main_cards/steam/GFT123.jpg
        key = prefix + "/" + f.relative_to(local_dir).as_posix()

        # Проверяем — уже загружен?
        try:
            s3.head_object(Bucket=BUCKET, Key=key)
            skip += 1
            continue
        except Exception:
            pass

        try:
            content_type = "image/jpeg" if f.suffix.lower() == ".jpg" else "image/png"
            s3.upload_file(
                str(f),
                BUCKET,
                key,
                ExtraArgs={"ContentType": content_type, "ACL": "public-read"},
            )
            ok += 1
            if (ok + fail) % 200 == 0:
                print(f"  [{ok+fail}/{len(files)}] загружено {ok}, ошибок {fail}...")
        except Exception as e:
            print(f"  FAIL {f.name}: {e}")
            fail += 1

    print(f"  Готово: {ok} загружено, {skip} уже было, {fail} ошибок")
    return ok, skip, fail


def main():
    print(f"Бакет: {BUCKET}")
    print(f"Папка: {IMAGES_ROOT}")

    if not IMAGES_ROOT.exists():
        print(f"ОШИБКА: папка {IMAGES_ROOT} не найдена!")
        return

    total_ok = total_skip = total_fail = 0
    for d in UPLOAD_DIRS:
        local = IMAGES_ROOT / d
        if not local.exists():
            print(f"Пропускаю {d}/ — папка не найдена")
            continue
        ok, skip, fail = upload_dir(local, d)
        total_ok += ok
        total_skip += skip
        total_fail += fail

    print(f"\nИтого: {total_ok} загружено, {total_skip} уже было, {total_fail} ошибок")
    print(f"\nURL изображений: {ENDPOINT}/{BUCKET}/main_cards/steam/GFT123.jpg")


if __name__ == "__main__":
    main()
