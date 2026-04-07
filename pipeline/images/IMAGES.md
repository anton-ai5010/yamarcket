# Изображения проекта YaMarket

Все изображения хранятся в Yandex Cloud Object Storage (S3-совместимый).

## Bucket

- **Bucket:** `yamarcket-images`
- **Endpoint:** `https://storage.yandexcloud.net`
- **Публичный доступ:** да (чтение)
- **Base URL:** `https://storage.yandexcloud.net/yamarcket-images/`

## Структура bucket

```
yamarcket-images/
├── main_cards/          # Главные карточки товаров (~2700 шт)
│   ├── appstore/        # Apple Gift Card
│   ├── steam/           # Steam
│   ├── playstation/     # PlayStation
│   ├── xbox/            # Xbox
│   ├── googleplay/      # Google Play
│   ├── nintendo/        # Nintendo
│   └── ...              # и другие бренды
├── instructions_v2/     # Инструкции по активации (~1650 шт)
├── universal/           # Универсальные карточки (доставка, отзыв, поддержка)
├── references/          # AI-фоны для генерации карточек (~210 шт)
│   └── flags/           # Флаги стран
├── fonts/               # Шрифты для генерации
└── games/               # Обложки игр
```

## Требования к изображениям

### Главные карточки (main_cards/)

- **Размер:** 1080x1440 px (соотношение 3:4)
- **Формат:** PNG, RGB
- **Вес:** ~1-2 MB
- **Рендер:** 2160x2880 → масштаб до 1080x1440
- **Содержание:** логотип бренда, номинал, регион, фирменный фон

### Инструкции (instructions_v2/)

- **Размер:** 1080x1440 px
- **Формат:** PNG, RGB
- **Содержание:** пошаговая инструкция активации с нумерованными шагами

### Универсальные (universal/)

- **Размер:** 1080x1440 px
- **Формат:** PNG, RGB
- **Типы:** email_example_card, delivery_card, feedback_card, support_card
- **Суффикс:** `_v{номер варианта}.png` — для каждого товара свой вариант

### Фоны-референсы (references/)

- **Размер:** 1792x2400 px (2K)
- **Формат:** PNG, RGB
- **Вес:** ~3-4 MB
- **Генерация:** AI через OpenRouter (модель на выбор)
- **Именование:** `bg_{brand_slug}.png`

### Шрифты (fonts/)

- **FiraSans** — основной шрифт (Regular, Medium, Bold, ExtraBold)
- **Moderustic** — альтернативный (Variable, Bold, Medium)
- **Nunito** — для номиналов (400, 700, 800, 900)
- **SourceSans** — дополнительный

## Скачивание изображений

### Всё целиком (aws-cli)
```bash
# Установка: pip install awscli
# Ключи из .env

export AWS_ACCESS_KEY_ID=<из .env>
export AWS_SECRET_ACCESS_KEY=<из .env>

# Скачать всё
aws s3 sync s3://yamarcket-images ./pipeline/images/yc/ \
  --endpoint-url https://storage.yandexcloud.net

# Скачать только фоны
aws s3 sync s3://yamarcket-images/references/ ./pipeline/images/references/ \
  --endpoint-url https://storage.yandexcloud.net

# Скачать только шрифты
aws s3 sync s3://yamarcket-images/fonts/ ./pipeline/images/fonts/ \
  --endpoint-url https://storage.yandexcloud.net
```

### Одну картинку (браузер/curl)
```bash
# Публичный доступ — просто открыть в браузере:
https://storage.yandexcloud.net/yamarcket-images/main_cards/appstore/GFT1_oae.jpg
https://storage.yandexcloud.net/yamarcket-images/references/bg_apple.png
https://storage.yandexcloud.net/yamarcket-images/fonts/FiraSans-Bold.ttf
```

## Загрузка изображений

```bash
# Загрузить файл
aws s3 cp my_card.png s3://yamarcket-images/main_cards/brand/filename.png \
  --endpoint-url https://storage.yandexcloud.net

# Загрузить папку
aws s3 sync ./my_cards/ s3://yamarcket-images/main_cards/brand/ \
  --endpoint-url https://storage.yandexcloud.net
```

Или через скрипт: `python pipeline/scripts/upload_images_to_yc.py`

## Генерация новых карточек

1. Убедиться что `.env` содержит все ключи (YC + OpenRouter)
2. Фоны: `python pipeline/scripts/generate_backgrounds.py`
3. Карточки: `python pipeline/scripts/generate_main_cards.py`
4. Загрузка: `python pipeline/scripts/upload_images_to_yc.py`
