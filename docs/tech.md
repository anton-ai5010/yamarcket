# Technical Context

## Stack

- **Python 3.12** — все скрипты обработки данных
- **openpyxl** — чтение/запись Excel (xlsx) файлов Яндекс Маркета
- **Pillow (PIL)** — генерация изображений карточек: рендер 2160×2880, сохранение 1080×1440
- **boto3** — загрузка изображений в Yandex Cloud Object Storage (S3-совместимый API)
- **python-dotenv** — конфигурация через `.env` (ключи YC не хранятся в коде)
- **moviepy 2.x** — сборка MP4 видео из кадров (ImageSequenceClip)
- **numpy** — работа с пиксельными массивами при генерации видео и эффектов
- **JSON (не JSONL)** — источник истины хранится как один большой JSON-объект

## Шрифты

- `FiraSans-Bold.ttf` — заголовки карточек, размеры 58-105pt в зависимости от масштаба
- `FiraSans-Medium.ttf` — подзаголовки, метки
- `FiraSans-Regular.ttf` — текст шагов, мелкий текст
- Все шрифты в `pipeline/images/fonts/`

## Конфигурация (.env в корне проекта)

```
YC_ACCESS_KEY_ID=...
YC_SECRET_ACCESS_KEY=...
YC_BUCKET=yamarcket
YC_ENDPOINT=https://storage.yandexcloud.net
```

## Pipeline Flow (актуальный, 2026-03)

```
JSON источник истины
  new table/Онлайн-подписки и карты оплаты_истина_с_характеристиками.json
    ↓
  sync_json_to_xlsx.py
    ↓
  new table/2_updated.xlsx → загрузка в ЛК Яндекс Маркета
```

Отдельные файлы для загрузки:
- `2_subscriptions.xlsx` — 56 подписок (признак-вариант: только AV = Продолжительность)
- `3.xlsx` — карты оплаты (признак-вариант: AU + AR + AP)

## Image Pipeline Flow

```
pipeline/images/generate_cards.py (Pillow)
  → pipeline/images/output/main_cards/{brand}/{SKU}_{country}.png  (PNG 1080×1440)
    ↓
  push_main_cards.py
  — конвертирует PNG → JPG в yamarcket-images/main_cards/{brand}/
  — обновляет JSON: первая ссылка = raw GitHub URL
    ↓
  convert_to_png_and_upload.py
  — конвертирует JPG → PNG обратно (YC принимает PNG)
  — загружает в YC Storage: main_cards/{brand}/{SKU}_{country}.png
  — удаляет JPG локально и из S3
  — обновляет JSON: .jpg → .png в URL
    ↓
  generate_card_variants.py
  — 50 вариантов × 4 универсальные карточки → YC Storage universal/
  — обновляет JSON: добавляет URL вариантов каждому товару
    ↓
  sync_json_to_xlsx.py
  — выгружает JSON в xlsx для Маркета
```

## Storage Structure (Yandex Cloud)

```
bucket: yamarcket
  main_cards/
    playstation/   GFT{N}_{country}.png  (329 файлов)
    steam/         GFT{N}_{country}.png  (146+ файлов)
    xbox/          GFT{N}_{country}.png  (146+ файлов)
  universal/
    email_example_card_v01..v50.png
    delivery_card_v01..v50.png
    feedback_card_v01..v50.png
    support_card_v01..v50.png
  instructions_v2/
    instr_steam_browser.png
    instr_steam_client.png
    instr_steam_wallet.png
    instr_ps_console.png
    instr_ps_app.png
    instr_xbox_console.png
    instr_xbox_app.png
    instr_xbox_site.png
    instr_apple_iphone.png
    instr_apple_itunes.png
    instr_apple_mac.png
    instr_google_android.png
    instr_google_browser.png
    instr_nintendo_site.png
    instr_nintendo_switch.png
    instr_amazon_app.png
    instr_amazon_site.png
    instr_spotify.png
    instr_roblox.png
    instr_epic.png
    instr_battlenet.png
    instr_ea.png
    instr_razer.png
    instr_riot.png
    instr_mobile_voucher.png
    instr_mobile_legends.png
    instr_midasbuy.png
    instr_paysafe_pin.png
    instr_paysafe_wallet.png
    instr_netflix.png
    instr_shop2game.png
    instr_valorant.png
    instr_universal.png
    email_example_card.png  (+ другие универсальные)
  games/
    обложки игр (JPG)
```

## JSON Source of Truth — Структура

Файл: `new table/Онлайн-подписки и карты оплаты_истина_с_характеристиками.json`

```json
{
  "Данные о товарах": [
    [...строка 1 — служебная...],
    [...строка 2 — служебная...],
    [...строка 3 — служебная...],
    ["Ваш SKU", "Название товара", ..., "Ссылка на изображение", ...]  // строка 4 (индекс 3) — ЗАГОЛОВКИ
    [...строка 5 — описание полей...],
    [...строка 6 — типы...],
    [...строка 7 — допустимые значения...],
    // С индекса 7 (строка 8) начинаются GFT-товары:
    ["GFT1", "Название товара", ..., "URL,URL,URL", ...]
    // ...3334 товара
  ]
}
```

Колонки данных (нумерация с 0 в строке-заголовке):
- `[0]` — Ваш SKU (GFT1, GFT2 ...)
- `[1]` — Название товара
- `[4]` — Бренд
- `[7]` — Ссылка на изображение (несколько через запятую)
- `[8]` — Описание товара (HTML)
- `[9]` — Категория на Маркете
- `[10]` — Теги
- `[38]` — Характеристики товара (JSON-строка с парами ключ:значение)
- Колонки AU, AV — признаки вариантов (Номинал карты, Продолжительность подписки)

## Video Generation (make_card_video_pro.py)

- 30 секунд, 30 fps = 900 кадров, 1080×1440
- 5 сцен: появление → floating+rock → фичи → 360° поворот → CTA
- Эффекты: 3D перспективный поворот, glow, отражение, частицы, gradient bg
- Рендер через numpy + Pillow поkадрово, сборка moviepy ImageSequenceClip
- Кодек: libx264, битрейт 8000k
- Выход: `pipeline/images/output/videos/{SKU}_pro.mp4`

## Key Decisions

- **JSON over JSONL**: весь каталог хранится как один JSON-объект, не построчный JSONL — проще выгружать xlsx одним скриптом
- **PNG over JPG**: изображения в S3 хранятся как PNG (лучше качество, нет артефактов сжатия); в yamarcket-images репозитории можно и JPG для экономии места
- **50 variant cards**: Яндекс Маркет детектирует дубликаты изображений между карточками; 50 вариантов с пиксельным сдвигом обходят это ограничение
- **Separate xlsx for subscriptions**: подписки (AV) и карты (AU) нельзя смешивать в одном файле — разные признаки-варианты; решение — два отдельных xlsx
- **Raw GitHub URLs for images**: главные карточки ссылаются на GitHub raw URLs; universal + instructions — на YC Storage public URLs
- **Render at 2x then scale**: генерация при 2160×2880 для качества, сохранение как 1080×1440 (anti-aliasing при downscale)
