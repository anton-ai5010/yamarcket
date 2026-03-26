# Спецификация карточки-инструкции по активации

## Процесс рендеринга
1. Рендерим в **2160x2880** (холст 1728x2304, масштаб S = 2160/1728 = 1.25)
2. Уменьшаем до **1080x1440** (LANCZOS)
3. Сохраняем в **PNG**

## Фон
- Файл: `pipeline/images/references/fon_bes_kartochry_4k.png`
- Чистый голубой фон с рамкой, без карты бренда

## Элементы

### 1. ЗАГОЛОВОК — "Инструкция по активации"
- Позиция: left=173, top=126 (координаты Canva 1728)
- Шрифт: **FiraSans-Bold**, 70pt Canva 1536 → Pillow: int(105 * S)
- Цвет: **#1E3A5F**
- Выравнивание: left
- Текст фиксированный

### 2. ПОДЗАГОЛОВОК — где активировать
- Позиция: left=173, top=280
- Шрифт: **FiraSans-Bold**, тот же размер что заголовок
- Цвет: **#4682B4** (стальной синий)
- Может быть 1 или 2 строки (межстрочный: 120)
- Примеры:
  - "Через клиент STEAM на пк" (1 строка)
  - "На консоли\nPlayStation 4 / PS5" (2 строки)
  - "На сайте\nmicrosoft.com/redeem" (2 строки)

### 3. ПУНКТЫ ИНСТРУКЦИИ
- Позиция X: left=173 (как нижний текст)
- Позиция Y: динамическая — 520 + (кол-во строк подзаголовка - 1) × 120
- Ширина блока: 1382 (как нижний текст на главной карточке)
- Шрифт: **FiraSans-Medium**, 48pt Canva → Pillow: int(72 * S)
- Цвет: **#1E3A5F**
- Буллеты: круг r=10, цвет #1E3A5F, слева от текста
- Текст автоматически переносится по ширине блока
- Расстояние между пунктами: динамическое (доступное пространство / кол-во пунктов)
- Межстрочный внутри пункта: 78
- Минимум 2 шага, максимум 5 шагов

### 4. НИЖНИЙ ТЕКСТ — ТОЧНО как на главной карточке
- Позиция: left=173, top=1813
- Шрифт: **FiraSans-Bold**, 47pt → Pillow: int(63 * S)
- Цвет: **#1E3A5F**
- Межстрочный: 80
- Строка 1 (динамическая): "ПОДХОДИТ ДЛЯ АККАУНТОВ {СТРАНА}"
- Строка 2 (фиксированная): "МГНОВЕННАЯ ЦИФРОВАЯ ДОСТАВКА"

### 5. ЛОГОТИП — ТОЧНО как на главной карточке
- Файл: `pipeline/images/references/unnamed5_nobg_navy_hires.png`
- Позиция: left=572, top=2015, W=583, H=232

---

## Типы инструкций (32 картинки)

### С несколькими способами (по картинке на каждый):

| Сервис | Подзаголовок | Шагов |
|--------|-------------|-------|
| Steam клиент | Через клиент STEAM на пк | 5 |
| Steam браузер | Через браузер на сайте Steam | 3 |
| Steam кошелёк | Пополнение кошелька Steam | 5 |
| Xbox консоль | На консоли Xbox | 4 |
| Xbox сайт | На сайте\nmicrosoft.com/redeem | 3 |
| Xbox приложение | В приложении Xbox\nна телефоне | 3 |
| PlayStation консоль | На консоли\nPlayStation 4 / PS5 | 4 |
| PlayStation PS App | Через приложение\nPS App на телефоне | 3 |
| Apple iPhone/iPad | На iPhone или iPad | 4 |
| Apple Mac | На Mac | 3 |
| Apple iTunes ПК | На ПК через iTunes | 3 |
| Google Play Android | На Android устройстве | 4 |
| Google Play браузер | Через браузер\nplay.google.com | 3 |
| Nintendo Switch | На консоли\nNintendo Switch | 4 |
| Nintendo сайт | На сайте Nintendo | 2 |
| Amazon сайт | На сайте Amazon | 4 |
| Amazon приложение | В приложении Amazon | 4 |
| Paysafecard PIN | Оплата PIN-кодом | 4 |
| Paysafecard кошелёк | Через кошелёк myPaysafe | 3 |

### С одним способом (1 картинка):

| Сервис | Подзаголовок | Шагов |
|--------|-------------|-------|
| Roblox | На сайте roblox.com/redeem | 4 |
| Netflix | На сайте netflix.com/redeem | 4 |
| Spotify | На сайте spotify.com/redeem | 4 |
| Riot Games | На сайте Riot Games | 4 |
| Valorant | В клиенте Valorant на ПК | 4 |
| Razer Gold | На сайте gold.razer.com | 4 |
| Battle.net | На сайте или в клиенте\nBattle.net | 4 |
| EA App | В клиенте EA App | 4 |
| Epic Games | На сайте Epic Games | 4 |
| Мобильный ваучер | Активация через email | 4 |
| Midasbuy | На сайте Midasbuy | 4 |
| Shop2game | На сайте Shop2game | 4 |
| Mobile Legends | В игре Mobile Legends | 4 |

---

## Рабочий скрипт

```python
from PIL import Image, ImageDraw, ImageFont
import os

BASE = "/media/anton/Новый том/yamarcket/pipeline/images"
REFS = f"{BASE}/references"
FONTS = f"{BASE}/fonts"
OUTPUT = f"{BASE}/output"

bg = Image.open(f"{REFS}/fon_bes_kartochry_4k.png").convert("RGBA")
logo = Image.open(f"{REFS}/unnamed5_nobg_navy_hires.png").convert("RGBA")

CW, CH = 2160, 2880
S = CW / 1728

bg_resized = bg.resize((CW, CH), Image.LANCZOS)

LOGO_W, LOGO_H = int(583 * S), int(232 * S)
logo_resized = logo.resize((LOGO_W, LOGO_H), Image.LANCZOS)
LOGO_X = int(572 * S)
LOGO_Y = int(2015 * S)
BOTTOM_X = int(173 * S)
BOTTOM_Y = int(1813 * S)
BOTTOM_LH = int(80 * S)
DARK = "#1E3A5F"
STEEL = "#4682B4"
TITLE_X = int(173 * S)
MAX_TEXT_W = int(1382 * S) - int(50 * S)

font_title = ImageFont.truetype(f"{FONTS}/FiraSans-Bold.ttf", int(105 * S))
font_steps = ImageFont.truetype(f"{FONTS}/FiraSans-Medium.ttf", int(72 * S))
font_bottom = ImageFont.truetype(f"{FONTS}/FiraSans-Bold.ttf", int(63 * S))

def draw_bottom(card, country="США"):
    draw = ImageDraw.Draw(card)
    draw.text((BOTTOM_X, BOTTOM_Y), f"ПОДХОДИТ ДЛЯ АККАУНТОВ {country}", font=font_bottom, fill=DARK)
    draw.text((BOTTOM_X, BOTTOM_Y + BOTTOM_LH), "МГНОВЕННАЯ ЦИФРОВАЯ ДОСТАВКА", font=font_bottom, fill=DARK)
    card.paste(logo_resized, (LOGO_X, LOGO_Y), logo_resized)

def wrap_text(text, font, max_width):
    words = text.split(' ')
    lines, current = [], ''
    tmp = ImageDraw.Draw(Image.new("RGBA",(1,1)))
    for word in words:
        test = f'{current} {word}'.strip()
        if tmp.textlength(test, font=font) <= max_width:
            current = test
        else:
            if current: lines.append(current)
            current = word
    if current: lines.append(current)
    return lines

def generate_instruction(subtitle, steps, country, filename):
    card = bg_resized.copy()
    draw = ImageDraw.Draw(card)

    draw.text((TITLE_X, int(126 * S)), "Инструкция по активации", font=font_title, fill=DARK)

    sub_lines = subtitle.split('\n')
    sub_y = int(280 * S)
    sub_line_h = int(120 * S)
    for i, line in enumerate(sub_lines):
        draw.text((TITLE_X, sub_y + i * sub_line_h), line, font=font_title, fill=STEEL)

    steps_y = int((520 + (len(sub_lines) - 1) * 120) * S)
    available_h = BOTTOM_Y - steps_y - int(50 * S)
    step_h = available_h // len(steps)
    line_h = int(78 * S)
    bullet_r = int(10 * S)
    steps_x = BOTTOM_X
    text_x = steps_x + int(50 * S)

    for idx, step in enumerate(steps):
        y = steps_y + idx * step_h
        bx = steps_x + int(15 * S)
        by = y + int(35 * S)
        draw.ellipse((bx - bullet_r, by - bullet_r, bx + bullet_r, by + bullet_r), fill=DARK)
        wrapped = wrap_text(step, font_steps, MAX_TEXT_W)
        for li, line in enumerate(wrapped):
            draw.text((text_x, y + li * line_h), line, font=font_steps, fill=DARK)

    draw_bottom(card, country)

    final = card.resize((1080, 1440), Image.LANCZOS)
    final.convert("RGB").save(f"{OUTPUT}/{filename}", "PNG")
```

## Динамические поля

| Поле | Пример | Когда меняется |
|------|--------|---------------|
| Подзаголовок | "Через клиент STEAM на пк" | Для каждого метода активации |
| Пункты инструкции | 2-5 шагов | Для каждого метода активации |
| Страна в нижнем тексте | "США" | Для каждого товара |

## Статические поля

| Поле | Значение |
|------|----------|
| Заголовок | "Инструкция по активации" |
| Строка 2 внизу | "МГНОВЕННАЯ ЦИФРОВАЯ ДОСТАВКА" |
| Логотип | Кодхаб |
| Фон | fon_bes_kartochry_4k.png |
