"""
generate_card_variants.py

Создаёт 50 вариантов каждой из 4 универсальных карточек.
Отличия: сдвиг нижней части (логотип + текст) на 1-7 пикселей по x/y.
Загружает в YC Object Storage, обновляет JSON, пересобирает xlsx.
"""
import os
import json
import boto3
from PIL import Image, ImageChops
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).parent.parent.parent
IMAGES_ROOT = ROOT.parent / "yamarcket-images"
JSON_PATH = ROOT / "new table" / "Онлайн-подписки и карты оплаты_истина_с_характеристиками.json"

load_dotenv(ROOT / ".env")
BUCKET = os.environ["YC_BUCKET"]
BASE_URL = f"https://storage.yandexcloud.net/{BUCKET}/"

s3 = boto3.session.Session().client(
    service_name="s3",
    endpoint_url=os.environ["YC_ENDPOINT"],
    aws_access_key_id=os.environ["YC_ACCESS_KEY_ID"],
    aws_secret_access_key=os.environ["YC_SECRET_ACCESS_KEY"],
    region_name="ru-central1",
)

CARDS = [
    "email_example_card.png",
    "delivery_card.png",
    "feedback_card.png",
    "support_card.png",
]

N_VARIANTS = 50
W, H = 1080, 1440

# Сетка сдвигов: 10 по x × 5 по y = 50 вариантов
# x: -4..+5, y: -2..+2
SHIFTS = [(x - 4, y - 2) for y in range(5) for x in range(10)]  # 50 штук


def make_variant(img: Image.Image, dx: int, dy: int) -> Image.Image:
    """Сдвигает нижнюю часть (логотип) на dx, dy пикселей."""
    result = img.copy()
    # Нижняя часть — последние 220 пикселей (логотип КодХаб + подпись)
    split_y = H - 220
    bottom = img.crop((0, split_y, W, H))
    # Сдвигаем через offset
    shifted = ImageChops.offset(bottom, dx, dy)
    result.paste(shifted, (0, split_y))
    return result


def upload(local_path: Path, key: str):
    s3.upload_file(
        str(local_path), BUCKET, key,
        ExtraArgs={"ContentType": "image/png", "ACL": "public-read"},
    )


def generate_and_upload():
    """Генерирует варианты и загружает в S3."""
    tmp_dir = Path("/tmp/card_variants")
    tmp_dir.mkdir(exist_ok=True)

    # {card_stem: [url_v00, url_v01, ..., url_v49]}
    variant_urls = {}

    for card_name in CARDS:
        src = IMAGES_ROOT / card_name
        stem = card_name.replace(".png", "")
        print(f"\n{card_name}: генерирую {N_VARIANTS} вариантов...")

        with Image.open(src) as orig:
            img = orig.convert("RGB")

        urls = []
        for i, (dx, dy) in enumerate(SHIFTS):
            variant = make_variant(img, dx, dy)
            fname = f"{stem}_v{i+1:02d}.png"
            local = tmp_dir / fname
            variant.save(local, "PNG")

            key = f"universal/{fname}"
            upload(local, key)
            urls.append(BASE_URL + key)

            if (i + 1) % 10 == 0:
                print(f"  {i+1}/{N_VARIANTS} загружено")

        variant_urls[stem] = urls
        print(f"  Готово: {len(urls)} вариантов")

    return variant_urls


def update_json(variant_urls: dict):
    """Распределяет варианты по товарам в JSON."""
    print("\nОбновляю JSON...")
    with open(JSON_PATH, encoding="utf-8") as f:
        data = json.load(f)

    rows = data["Данные о товарах"]
    headers = rows[3]
    img_col = next(i for i, h in enumerate(headers) if h and "изображени" in str(h).lower())

    # Собираем GFT-строки
    gft_rows = [row for row in rows[7:] if row and str(row[0] or "").startswith("GFT")]
    print(f"  Товаров: {len(gft_rows)}")

    stems = list(variant_urls.keys())  # порядок: email, delivery, feedback, support

    for idx, row in enumerate(gft_rows):
        variant_idx = idx % N_VARIANTS  # 0..49

        # Текущие URL
        val = str(row[img_col] or "")
        urls = [u.strip() for u in val.split(",") if u.strip()]

        # Убираем старые универсальные карточки (любые варианты)
        old_stems = set(stems) | {s + f"_v{j+1:02d}" for s in stems for j in range(N_VARIANTS)}
        keep = []
        for u in urls:
            fname = u.split("/")[-1].replace(".png", "").replace(".jpg", "")
            base = fname.rsplit("_v", 1)[0] if "_v" in fname else fname
            if base not in set(stems):
                keep.append(u)

        # Добавляем новые варианты
        new_cards = [variant_urls[stem][variant_idx] for stem in stems]
        row[img_col] = ",".join(keep + new_cards)

    print(f"  Обновлено: {len(gft_rows)} строк")
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    print("  JSON сохранён.")


def main():
    print(f"Генерирую {N_VARIANTS} вариантов × {len(CARDS)} карточек = {N_VARIANTS * len(CARDS)} файлов")
    variant_urls = generate_and_upload()
    update_json(variant_urls)

    print("\nЗапускаю sync_json_to_xlsx.py...")
    import subprocess
    result = subprocess.run(
        ["python3", "pipeline/scripts/sync_json_to_xlsx.py"],
        cwd=str(ROOT), capture_output=True, text=True
    )
    # Выводим только итог
    for line in result.stdout.splitlines():
        if any(x in line for x in ["Обновлено", "Сохраняю", "Готово", "Результат"]):
            print(" ", line)

    print("\nГотово! Загружай new table/2_updated.xlsx в Маркет.")


if __name__ == "__main__":
    main()
