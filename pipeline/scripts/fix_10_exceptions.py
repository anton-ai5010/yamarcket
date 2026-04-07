#!/usr/bin/env python3
"""
Генерация инструкционных картинок и обновление описаний/URL
для 10 SKU с generic-инструкциями:
  Disney (6 шт), Weyyak (1), Division 2 DLC/Ubisoft (1),
  Fallout 76 Gone Fission (1), ESO Xbox (1)
"""
import json
import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ── Пути ─────────────────────────────────────────────────────────────────────
BASE       = Path("/media/anton/Новый том/yamarcket/pipeline/images")
REFS       = BASE / "references"
FONTS_DIR  = BASE / "fonts"
OUT_LOCAL  = BASE / "output" / "instructions_v2"          # локальный вывод
OUT_GITHUB = Path("/media/anton/Новый том/yamarcket-images/instructions_v2")  # GitHub
JSON_PATH  = Path("/media/anton/Новый том/yamarcket/new table/Онлайн-подписки и карты оплаты_истина_с_характеристиками.json")
BASE_URL   = "https://raw.githubusercontent.com/anton-ai5010/yamarcket-images/main/instructions_v2/"

# ── Рендер ───────────────────────────────────────────────────────────────────
CW, CH  = 2160, 2880
S       = CW / 1728   # 1.25
DARK    = "#1E3A5F"
STEEL   = "#4682B4"

bg_src   = Image.open(REFS / "bg_clean.png").convert("RGBA")
bg_full  = bg_src.resize((CW, CH), Image.LANCZOS)
logo_src = Image.open(REFS / "unnamed5_nobg_navy_hires.png").convert("RGBA")
logo_res = logo_src.resize((int(583*S), int(232*S)), Image.LANCZOS)

LOGO_X    = int(572*S);   LOGO_Y    = int(2015*S)
BOTTOM_X  = int(173*S);   BOTTOM_Y  = int(1813*S);  BOTTOM_LH = int(80*S)
TITLE_X   = int(173*S)
MAX_TEXT_W = int(1382*S) - int(50*S)

font_title  = ImageFont.truetype(str(FONTS_DIR / "FiraSans-Bold.ttf"),   int(105*S))
font_steps  = ImageFont.truetype(str(FONTS_DIR / "FiraSans-Medium.ttf"), int(72*S))
font_bottom = ImageFont.truetype(str(FONTS_DIR / "FiraSans-Bold.ttf"),   int(63*S))


def wrap_text(text: str, font, max_w: int) -> list[str]:
    words = text.split()
    lines, cur = [], ""
    tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    for word in words:
        test = f"{cur} {word}".strip()
        if tmp.textlength(test, font=font) <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def generate_instruction(subtitle: str, steps: list[str], country: str, filename: str):
    card = bg_full.copy()
    draw = ImageDraw.Draw(card)

    # Заголовок
    draw.text((TITLE_X, int(126*S)), "Инструкция по активации", font=font_title, fill=DARK)

    # Подзаголовок (1–2 строки)
    sub_lines = subtitle.split("\n")
    sub_y     = int(280*S)
    sub_lh    = int(120*S)
    for i, line in enumerate(sub_lines):
        draw.text((TITLE_X, sub_y + i*sub_lh), line, font=font_title, fill=STEEL)

    # Шаги
    steps_y     = int((520 + (len(sub_lines)-1)*120) * S)
    available_h = BOTTOM_Y - steps_y - int(50*S)
    step_h      = available_h // len(steps)
    line_h      = int(78*S)
    bullet_r    = int(10*S)
    text_x      = BOTTOM_X + int(50*S)

    for idx, step in enumerate(steps):
        y  = steps_y + idx * step_h
        bx = BOTTOM_X + int(15*S)
        by = y + int(35*S)
        draw.ellipse((bx-bullet_r, by-bullet_r, bx+bullet_r, by+bullet_r), fill=DARK)
        for li, line in enumerate(wrap_text(step, font_steps, MAX_TEXT_W)):
            draw.text((text_x, y + li*line_h), line, font=font_steps, fill=DARK)

    # Нижний блок + лого
    draw.text((BOTTOM_X, BOTTOM_Y),           f"ПОДХОДИТ ДЛЯ АККАУНТОВ {country}", font=font_bottom, fill=DARK)
    draw.text((BOTTOM_X, BOTTOM_Y+BOTTOM_LH), "МГНОВЕННАЯ ЦИФРОВАЯ ДОСТАВКА",      font=font_bottom, fill=DARK)
    card.paste(logo_res, (LOGO_X, LOGO_Y), logo_res)

    # Сохраняем в оба места
    final = card.resize((1080, 1440), Image.LANCZOS)
    for dest_dir in (OUT_LOCAL, OUT_GITHUB):
        dest_dir.mkdir(parents=True, exist_ok=True)
        out_path = dest_dir / filename
        final.convert("RGB").save(out_path, "JPEG", quality=92, optimize=True)

    print(f"  ✓ {filename}")


# ═══════════════════════════════════════════════════════════════════════════
# 1. DISNEY GIFT CARD — 2 картинки
# ═══════════════════════════════════════════════════════════════════════════
print("Генерирую Disney...")
generate_instruction(
    subtitle="На сайте disneyplus.com/redeem",
    steps=[
        "Перейдите на disneyplus.com/redeem и войдите в аккаунт Disney",
        "Введите код подарочной карты в соответствующее поле",
        "Нажмите «Активировать» — баланс мгновенно зачислится на аккаунт",
        "Средства спишутся автоматически при следующем списании за подписку",
    ],
    country="США",
    filename="instr_disney_disneyplus_ssha.jpg",
)
generate_instruction(
    subtitle="В магазине shopDisney\nna shopdisney.com",
    steps=[
        "Перейдите на shopdisney.com и добавьте товары в корзину",
        "На странице оплаты выберите «Gift Card» в способах оплаты",
        "Введите номер подарочной карты и PIN-код",
        "Нажмите «Применить» и подтвердите — сумма будет списана с карты",
    ],
    country="США",
    filename="instr_disney_shopdisney_ssha.jpg",
)

# ═══════════════════════════════════════════════════════════════════════════
# 2. UBISOFT CONNECT — 2 картинки (для Division 2 DLC)
# ═══════════════════════════════════════════════════════════════════════════
print("Генерирую Ubisoft Connect...")
generate_instruction(
    subtitle="В клиенте Ubisoft Connect\nна ПК",
    steps=[
        "Откройте Ubisoft Connect на ПК и войдите в аккаунт",
        "Нажмите на иконку меню (три полоски) → «Активировать ключ»",
        "Введите 12-значный код активации и нажмите «Активировать»",
        "DLC добавится в вашу библиотеку Ubisoft Connect",
    ],
    country="ВСЕХ СТРАН",
    filename="instr_ubisoft_ubisoft_client_vse_strany.jpg",
)
generate_instruction(
    subtitle="На сайте Ubisoft\nubisoft.com/redeem",
    steps=[
        "Перейдите на ubisoft.com/redeem и войдите в аккаунт Ubisoft",
        "Введите 12-значный код активации в поле",
        "Нажмите «Активировать» и подтвердите",
        "DLC добавится в библиотеку — можно скачать через клиент",
    ],
    country="ВСЕХ СТРАН",
    filename="instr_ubisoft_ubisoft_site_vse_strany.jpg",
)

# ═══════════════════════════════════════════════════════════════════════════
# 3. ESO (The Elder Scrolls Online) — Xbox подписка — 3 картинки
# ═══════════════════════════════════════════════════════════════════════════
print("Генерирую ESO Xbox...")
generate_instruction(
    subtitle="На консоли Xbox",
    steps=[
        "Нажмите кнопку Xbox на геймпаде для вызова меню",
        "Перейдите в «Магазин» → «Использовать код» (Redeem Code)",
        "Введите 25-значный код и подтвердите",
        "Подписка ESO Plus активируется на вашем аккаунте",
    ],
    country="ВСЕХ СТРАН",
    filename="instr_theelderscrollsonlin_xbox_console_vse_strany.jpg",
)
generate_instruction(
    subtitle="На сайте\nmicrosoft.com/redeem",
    steps=[
        "Перейдите на microsoft.com/redeem и войдите в аккаунт Microsoft",
        "Введите 25-значный код и нажмите «Далее»",
        "Подтвердите применение кода — подписка ESO Plus активируется",
    ],
    country="ВСЕХ СТРАН",
    filename="instr_theelderscrollsonlin_xbox_site_vse_strany.jpg",
)
generate_instruction(
    subtitle="В приложении Xbox\nна телефоне",
    steps=[
        "Откройте приложение Xbox на смартфоне и войдите в аккаунт",
        "Нажмите на иконку профиля → «Оплата» → «Погасить код»",
        "Введите 25-значный код и подтвердите активацию",
        "Подписка ESO Plus активируется на аккаунте",
    ],
    country="ВСЕХ СТРАН",
    filename="instr_theelderscrollsonlin_xbox_app_vse_strany.jpg",
)

print()

# ═══════════════════════════════════════════════════════════════════════════
# 4. ОБНОВЛЕНИЕ JSON
# ═══════════════════════════════════════════════════════════════════════════
print("Обновляю JSON...")

with open(JSON_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

items = data["Данные о товарах"]

# Новые HTML-инструкции
INSTR_DISNEY = """<h2>Инструкция по активации подарочной карты Disney</h2>
<p><b>Способ 1 — Disney+ (активация подписки):</b></p>
<ol>
<li>Перейдите на disneyplus.com/redeem и войдите в аккаунт Disney</li>
<li>Введите код подарочной карты в соответствующее поле</li>
<li>Нажмите «Активировать» — баланс мгновенно зачислится на аккаунт</li>
<li>Средства спишутся автоматически при следующем платеже за подписку</li>
</ol>
<p><b>Способ 2 — Покупки в shopDisney:</b></p>
<ol>
<li>Перейдите на shopdisney.com и добавьте товары в корзину</li>
<li>На странице оплаты выберите «Gift Card» в способах оплаты</li>
<li>Введите номер подарочной карты и PIN-код, нажмите «Применить»</li>
</ol>"""

INSTR_WEYYAK = """<h2>Инструкция по активации подписки Weyyak</h2>
<ol>
<li>Перейдите на weyyak.com или откройте приложение Weyyak и войдите в аккаунт</li>
<li>Перейдите в «Тарифные планы» и выберите «Активировать карту Weyyak» (Redeem Card)</li>
<li>Введите полученный код в соответствующее поле и нажмите «Подтвердить»</li>
<li>Подписка активируется мгновенно — можно начинать просмотр</li>
</ol>"""

INSTR_UBISOFT = """<h2>Инструкция по активации ключа Ubisoft Connect</h2>
<p><b>Способ 1 — В клиенте Ubisoft Connect на ПК:</b></p>
<ol>
<li>Откройте Ubisoft Connect на ПК и войдите в аккаунт</li>
<li>Нажмите на иконку меню (три полоски) → «Активировать ключ»</li>
<li>Введите 12-значный код активации и нажмите «Активировать»</li>
<li>DLC добавится в вашу библиотеку Ubisoft Connect</li>
</ol>
<p><b>Способ 2 — На сайте Ubisoft:</b></p>
<ol>
<li>Перейдите на ubisoft.com/redeem и войдите в аккаунт Ubisoft</li>
<li>Введите 12-значный код активации и нажмите «Активировать»</li>
<li>DLC добавится в библиотеку — можно скачать через клиент</li>
</ol>"""

INSTR_STEAM_GAME = """<h2>Инструкция по активации ключа в Steam</h2>
<p><b>Способ 1 — Через клиент Steam на ПК:</b></p>
<ol>
<li>Откройте клиент Steam и войдите в свой аккаунт</li>
<li>В верхнем меню нажмите «Игры» → «Активировать продукт в Steam»</li>
<li>Примите пользовательское соглашение Steam</li>
<li>Введите ключ активации и нажмите «Далее» — игра добавится в библиотеку</li>
</ol>
<p><b>Способ 2 — Через браузер на сайте Steam:</b></p>
<ol>
<li>Перейдите на store.steampowered.com/account/registerkey</li>
<li>Войдите в свой аккаунт Steam</li>
<li>Введите ключ активации и нажмите «Продолжить»</li>
</ol>"""

INSTR_ESO_XBOX = """<h2>Инструкция по активации подписки ESO на Xbox</h2>
<p><b>Способ 1 — На консоли Xbox:</b></p>
<ol>
<li>Нажмите кнопку Xbox на геймпаде для вызова меню</li>
<li>Перейдите в «Магазин» → «Использовать код» (Redeem Code)</li>
<li>Введите 25-значный код и подтвердите</li>
<li>Подписка ESO Plus активируется на вашем аккаунте</li>
</ol>
<p><b>Способ 2 — На сайте microsoft.com/redeem:</b></p>
<ol>
<li>Перейдите на microsoft.com/redeem и войдите в аккаунт Microsoft</li>
<li>Введите 25-значный код и нажмите «Далее»</li>
<li>Подтвердите применение кода — подписка ESO Plus активируется</li>
</ol>
<p><b>Способ 3 — В приложении Xbox на телефоне:</b></p>
<ol>
<li>Откройте приложение Xbox на смартфоне и войдите в аккаунт</li>
<li>Нажмите на иконку профиля → «Оплата» → «Погасить код»</li>
<li>Введите 25-значный код и подтвердите активацию</li>
</ol>"""

# Маппинг SKU → (новые URL инструкций, HTML инструкция)
FIXES = {
    # Disney — 6 SKU
    "GFT2792": {
        "instr_urls": ["instr_disney_disneyplus_ssha.jpg", "instr_disney_shopdisney_ssha.jpg"],
        "instr_html": INSTR_DISNEY,
    },
    "GFT2793": {
        "instr_urls": ["instr_disney_disneyplus_ssha.jpg", "instr_disney_shopdisney_ssha.jpg"],
        "instr_html": INSTR_DISNEY,
    },
    "GFT2794": {
        "instr_urls": ["instr_disney_disneyplus_ssha.jpg", "instr_disney_shopdisney_ssha.jpg"],
        "instr_html": INSTR_DISNEY,
    },
    "GFT2795": {
        "instr_urls": ["instr_disney_disneyplus_ssha.jpg", "instr_disney_shopdisney_ssha.jpg"],
        "instr_html": INSTR_DISNEY,
    },
    "GFT2796": {
        "instr_urls": ["instr_disney_disneyplus_ssha.jpg", "instr_disney_shopdisney_ssha.jpg"],
        "instr_html": INSTR_DISNEY,
    },
    "GFT2797": {
        "instr_urls": ["instr_disney_disneyplus_ssha.jpg", "instr_disney_shopdisney_ssha.jpg"],
        "instr_html": INSTR_DISNEY,
    },
    # Weyyak — 1 SKU (изображение уже есть, только обновляем URL и текст)
    "GFT5916": {
        "instr_urls": ["instr_weyyak_vse_strany.jpg"],
        "instr_html": INSTR_WEYYAK,
    },
    # Division 2 DLC — Ubisoft Connect
    "GFT5919": {
        "instr_urls": ["instr_ubisoft_ubisoft_client_vse_strany.jpg", "instr_ubisoft_ubisoft_site_vse_strany.jpg"],
        "instr_html": INSTR_UBISOFT,
    },
    # Fallout 76: Gone Fission — Steam (используем уже существующие картинки fallout76)
    "GFT5929": {
        "instr_urls": ["instr_fallout76burningspri_steam_client_vse_strany.jpg",
                       "instr_fallout76burningspri_steam_browser_vse_strany.jpg"],
        "instr_html": INSTR_STEAM_GAME,
    },
    # ESO Subscription — Xbox
    "GFT5932": {
        "instr_urls": ["instr_theelderscrollsonlin_xbox_console_vse_strany.jpg",
                       "instr_theelderscrollsonlin_xbox_site_vse_strany.jpg",
                       "instr_theelderscrollsonlin_xbox_app_vse_strany.jpg"],
        "instr_html": INSTR_ESO_XBOX,
    },
}

INSTR_PATTERN = re.compile(
    r"(<h2>Инструкция по активации.*?)(?=\Z)",
    re.DOTALL,
)

updated_rows = 0
for row in items:
    if not row or not row[0] or not str(row[0]).startswith("GFT"):
        continue
    sku = str(row[0])
    if sku not in FIXES:
        continue

    fix = FIXES[sku]

    # — Обновляем изображения (col 7) ——————————————————
    current_imgs = str(row[7]) if len(row) > 7 and row[7] else ""
    urls = [u.strip() for u in current_imgs.split(",") if u.strip()]

    # Убираем старые instr_ URL
    non_instr = [u for u in urls if "instr_" not in u]
    new_instr  = [BASE_URL + fname for fname in fix["instr_urls"]]

    # Первый элемент — главная карточка, потом инструкции, потом остальные
    main = [u for u in non_instr if "main_cards" in u or "games/" in u]
    rest = [u for u in non_instr if u not in main]
    new_urls = (main + new_instr + rest)[:30]
    row[7] = ",".join(new_urls)

    # — Обновляем описание (col 9) ——————————————————————
    desc = str(row[9]) if len(row) > 9 and row[9] else ""
    # Ищем блок инструкции и заменяем
    if "Инструкция по активации" in desc:
        idx = desc.find("<h2>Инструкция по активации")
        desc = desc[:idx] + fix["instr_html"]
    else:
        # Нет инструкции — добавляем в конец
        desc = desc.rstrip() + "\n" + fix["instr_html"]
    row[9] = desc

    print(f"  {sku}: {len(new_instr)} instr imgs → {len(new_urls)} total")
    updated_rows += 1

print(f"\nОбновлено строк: {updated_rows}")

with open(JSON_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=None, separators=(",", ":"))

print("JSON сохранён.")
