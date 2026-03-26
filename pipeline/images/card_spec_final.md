# Финальная спецификация карточки товара

## Процесс рендеринга
1. Рендерим в **2160x2880** (×1.25 от Canva 1728x2304)
2. Уменьшаем до **1080x1440** (LANCZOS антиалиасинг)
3. Сохраняем в **PNG**
4. Коэффициент масштаба: S = 2160/1728 = **1.25**
5. Размеры шрифтов: Canva pt × 1.333 (pt→px) × S

## Холст Canva: 1728 × 2304 px

---

## Слои (все позиции в координатах Canva 1728x2304, в скрипте умножаются на S=1.25)

### 1. ФОН
- Файл: `fon_xbox_2k.png`
- Позиция: 0, 0, 1728, 2304
- На весь холст, ресайз до 2160x2880

### 2. ЗАГОЛОВОК
- Текст: `ПОДАРОЧНАЯ\nКАРТА {BRAND}`
- Позиция: left=173, top=126
- Шрифт: **FiraSans-Bold**, размер **130pt** (→ 173×S px)
- Межстрочный: 195 (в координатах Canva)
- Выравнивание: left
- Цвет "ПОДАРОЧНАЯ КАРТА": **#1E3A5F**
- Цвет бренда (напр. "XBOX"): **#4682B4**
- Тень: нет (убрали для чёткости)

### 3. НОМИНАЛ
- Текст: `10` (меняется)
- Позиция: left=251, top=684, W=168
- Шрифт: **FiraSans-Bold**, размер **120pt** (→ 160×S px)
- Выравнивание: **center** (внутри контейнера W=168)
- Цвет: **#4682B4** (стальной синий)

### 4. ВАЛЮТА
- Текст: `USD` (меняется)
- Позиция: left=210, top=876, W=249
- Шрифт: **FiraSans-Bold**, размер **100pt** (→ 133×S px)
- Выравнивание: **center** (внутри контейнера W=249)
- Цвет: **#1E3A5F** (тёмно-синий)

### 5. ФЛАГ СТРАНЫ
- Тип: изображение, круглое
- Позиция: left=1315, top=1209, W=225, H=225
- Круглая маска (ellipse)

### 6. НАЗВАНИЕ СТРАНЫ
- Текст: `США` (меняется)
- Позиция: left=1234, top=1478, W=387
- Шрифт: **FiraSans-Bold**, размер **47pt** (→ 63×S px)
- Выравнивание: **center** (внутри контейнера W=387)
- Цвет: **#1E3A5F**

### 7. НИЖНИЙ ТЕКСТ
- Строка 1: `ПОДХОДИТ ДЛЯ АККАУНТОВ {СТРАНА}` (меняется)
- Строка 2: `МГНОВЕННАЯ ЦИФРОВАЯ ДОСТАВКА` (фиксированная)
- Позиция: left=173, top=1813
- Межстрочный: 80 (в координатах Canva)
- Шрифт: **FiraSans-Bold**, размер **47pt** (→ 63×S px)
- Выравнивание: **left**
- Цвет: **#1E3A5F**

### 8. ЛОГОТИП
- Файл: `unnamed5_nobg_navy_hires.png`
- Позиция: left=572, top=2015, W=583, H=232

---

## Цвета

| HEX | Где |
|-----|-----|
| **#1E3A5F** | Заголовок ("ПОДАРОЧНАЯ КАРТА"), валюта, страна, нижний текст |
| **#4682B4** | Бренд в заголовке ("XBOX"), номинал |

## Шрифты

| Файл | Размер (Canva pt) | Pillow px (×1.333×S) | Где |
|------|-------------------|---------------------|-----|
| FiraSans-Bold.ttf | 130 | 216 | Заголовок |
| FiraSans-Bold.ttf | 120 | 200 | Номинал |
| FiraSans-Bold.ttf | 100 | 166 | Валюта |
| FiraSans-Bold.ttf | 47 | 79 | Страна, нижний текст |

## Динамические поля

| Поле | Пример | Источник |
|------|--------|---------|
| Бренд в заголовке | XBOX | service [41] |
| Номинал | 10 | номинал [46] |
| Валюта | USD | из названия товара |
| Название страны | США | территория [48] |
| Нижний текст строка 1 | ПОДХОДИТ ДЛЯ АККАУНТОВ США | территория [48] |
| Флаг | usa_flag.png | по стране |
| Фон | fon_xbox_2k.png | по бренду |

## Статические поля

| Поле | Значение |
|------|----------|
| Нижний текст строка 2 | МГНОВЕННАЯ ЦИФРОВАЯ ДОСТАВКА |
| Логотип | Кодхаб (unnamed5_nobg_navy_hires.png) |

## Необходимые ресурсы для массовой генерации

### Фоны (по бренду) — минимум 1728x2304
- Xbox — `fon_xbox_2k.png` ✅ есть
- Apple — нужен
- Google Play — нужен
- Steam — нужен
- PlayStation — нужен
- Nintendo — нужен
- Roblox — нужен
- Amazon — нужен
- Netflix — нужен
- Spotify — нужен
- и другие бренды

### Флаги стран (круглые) — PNG с прозрачным фоном
- США — `usa_flag.png` ✅ есть (конвертирован из SVG)
- Нужны флаги для всех стран из каталога

### Шрифты ✅ все есть
- FiraSans-Bold.ttf
- FiraSans-Medium.ttf (запас)
- FiraSans-Regular.ttf (запас)

---

## Типы карточек

### Тип 1 — Подарочная карта / пополнение счета
- Заголовок: `ПОДАРОЧНАЯ КАРТА` (#1E3A5F) + `{БРЕНД}` (#4682B4)
- Большое число: номинал (10, 25, 50, 100, 1000...)
- Под числом: код валюты (USD, EUR, TRY, AED...)
- Примеры: Xbox Gift Card, Apple Gift Card, Steam Wallet, Google Play, PlayStation Store

### Тип 2 — Подписка
- Заголовок: `{ПОЛНОЕ НАЗВАНИЕ ПОДПИСКИ}` (весь #1E3A5F, без голубого!)
- Большое число: срок (1, 3, 6, 12)
- Под числом: `МЕСЯЦ` / `МЕСЯЦА` / `МЕСЯЦЕВ` / `ГОД`
- Примеры: Xbox Game Pass Ultimate, Spotify Premium, Netflix, Nintendo Switch Online

### Тип 3 — Игровая валюта
- Заголовок: `ИГРОВАЯ ВАЛЮТА` (#1E3A5F) + `{БРЕНД}` (#4682B4) — или аналогично Тип 1
- Большое число: количество валюты (4500, 1000...)
- Под числом: название валюты (ROBUX, V-BUCKS, VP, FC POINTS...)
- Примеры: Roblox Robux, Fortnite V-Bucks, Valorant VP

### Тип 4 — Игра / DLC (Steam/Xbox ключ)
- Заголовок: `{НАЗВАНИЕ ИГРЫ}` (весь #1E3A5F)
- Большое число: нет (или цена)
- Под числом: `STEAM KEY` / `XBOX KEY`
- Примеры: Fallout 4 GOTY, DOOM Eternal

---

## Рабочий скрипт генерации (проверенный)

Файл: `pipeline/images/output/` — результаты генерации

```python
from PIL import Image, ImageDraw, ImageFont
import os

BASE = "/media/anton/Новый том/yamarcket/pipeline/images"
REFS = f"{BASE}/references"
FONTS = f"{BASE}/fonts"
OUTPUT = f"{BASE}/output"

# Загрузка ресурсов
bg = Image.open(f"{REFS}/fon_xbox_2k.png").convert("RGBA")
logo = Image.open(f"{REFS}/unnamed5_nobg_navy_hires.png").convert("RGBA")
flag = Image.open(f"{REFS}/usa_flag.png").convert("RGBA")

# Рендер в 2160x2880, потом resize до 1080x1440
CW, CH = 2160, 2880
S = CW / 1728  # 1.25

bg_resized = bg.resize((CW, CH), Image.LANCZOS)
logo_resized = logo.resize((int(583*S), int(232*S)), Image.LANCZOS)

# Флаг — круглая маска
FLAG_SIZE = int(225*S)
flag_resized = flag.resize((FLAG_SIZE, FLAG_SIZE), Image.LANCZOS)
mask = Image.new("L", (FLAG_SIZE, FLAG_SIZE), 0)
ImageDraw.Draw(mask).ellipse((0, 0, FLAG_SIZE-1, FLAG_SIZE-1), fill=255)
flag_circle = Image.new("RGBA", (FLAG_SIZE, FLAG_SIZE), (0,0,0,0))
flag_circle.paste(flag_resized, (0,0), mask)

# Шрифты: Canva pt × 1.333 × S
font_title = ImageFont.truetype(f"{FONTS}/FiraSans-Bold.ttf", int(173*S))   # 130pt
font_nominal = ImageFont.truetype(f"{FONTS}/FiraSans-Bold.ttf", int(160*S)) # 120pt
font_currency = ImageFont.truetype(f"{FONTS}/FiraSans-Bold.ttf", int(133*S))# 100pt
font_country = ImageFont.truetype(f"{FONTS}/FiraSans-Bold.ttf", int(63*S))  # 47pt
font_bottom = ImageFont.truetype(f"{FONTS}/FiraSans-Bold.ttf", int(63*S))   # 47pt

DARK = "#1E3A5F"
STEEL = "#4682B4"

# Позиции (Canva координаты × S)
TITLE_X, TITLE_Y = int(173*S), int(126*S)
NOM_X, NOM_Y, NOM_W = int(251*S), int(684*S), int(168*S)
CUR_X, CUR_Y, CUR_W = int(210*S), int(876*S), int(249*S)
FLAG_X, FLAG_Y = int(1315*S), int(1209*S)
COUNTRY_X, COUNTRY_Y, COUNTRY_W = int(1234*S), int(1478*S), int(387*S)
BOTTOM_X, BOTTOM_Y = int(173*S), int(1813*S)
LOGO_X, LOGO_Y = int(572*S), int(2015*S)
LINE_H = int(195*S)
BOTTOM_LINE_H = int(80*S)

def center_x(text, font, box_x, box_w):
    tmp = ImageDraw.Draw(Image.new("RGBA",(1,1)))
    tw = tmp.textlength(text, font=font)
    return box_x + (box_w - int(tw)) // 2

# Сборка карточки
card = bg_resized.copy()
card.paste(flag_circle, (FLAG_X, FLAG_Y), flag_circle)
draw = ImageDraw.Draw(card)

# Заголовок
draw.text((TITLE_X, TITLE_Y), "ПОДАРОЧНАЯ", font=font_title, fill=DARK)
draw.text((TITLE_X, TITLE_Y + LINE_H), "КАРТА ", font=font_title, fill=DARK)
kw = draw.textlength("КАРТА ", font=font_title)
draw.text((TITLE_X + int(kw), TITLE_Y + LINE_H), "XBOX", font=font_title, fill=STEEL)

# Номинал (по центру)
nom_cx = center_x("10", font_nominal, NOM_X, NOM_W)
draw.text((nom_cx, NOM_Y), "10", font=font_nominal, fill=STEEL)

# Валюта (по центру)
cur_cx = center_x("USD", font_currency, CUR_X, CUR_W)
draw.text((cur_cx, CUR_Y), "USD", font=font_currency, fill=DARK)

# Страна (по центру)
country_cx = center_x("США", font_country, COUNTRY_X, COUNTRY_W)
draw.text((country_cx, COUNTRY_Y), "США", font=font_country, fill=DARK)

# Нижний текст (по левому краю)
for i, line in enumerate(["ПОДХОДИТ ДЛЯ АККАУНТОВ США", "МГНОВЕННАЯ ЦИФРОВАЯ ДОСТАВКА"]):
    draw.text((BOTTOM_X, BOTTOM_Y + i*BOTTOM_LINE_H), line, font=font_bottom, fill=DARK)

# Логотип
card.paste(logo_resized, (LOGO_X, LOGO_Y), logo_resized)

# Финал: уменьшаем и сохраняем PNG
final = card.resize((1080, 1440), Image.LANCZOS)
final.convert("RGB").save(f"{OUTPUT}/xbox_10_usd_usa.png", "PNG")
```

## Ключевые файлы проекта

| Файл | Назначение |
|------|-----------|
| `new table/Онлайн-подписки и карты оплаты_истина_с_характеристиками.json` | Основной JSON с данными товаров (названия, описания, характеристики) |
| `new table/1.xlsx` | Excel для загрузки на Яндекс Маркет (формат Маркета, 10 листов) |
| `new table/generated_names.json` | Сгенерированные названия с ротацией |
| `pipeline/images/card_spec_final.md` | ЭТА спецификация |
| `pipeline/images/output/` | Сгенерированные карточки (PNG) |
| `pipeline/images/references/fon_xbox_2k.png` | Фон Xbox (1728x2304) |
| `pipeline/images/references/unnamed5_nobg_navy_hires.png` | Логотип Кодхаб |
| `pipeline/images/references/usa_flag.png` | Флаг США (круглый) |
| `pipeline/images/fonts/FiraSans-Bold.ttf` | Шрифт для всех текстов |
| `rules/research/activation_instructions_all_services.md` | Инструкции активации 20 сервисов |
| `rules/research/competitor_descriptions_examples.md` | Примеры описаний конкурентов |
