"""
Перегенерирует email_example_card.png без логотипа Яндекс Маркета.
Показывает стилизованный конверт и текст — без чужих брендов.
"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
FONTS = ROOT / "pipeline" / "images" / "fonts"
OUT = ROOT.parent / "yamarcket-images" / "email_example_card.png"

W, H = 1080, 1440

# Цвета (тот же стиль что у остальных карточек)
BG_TOP = (178, 225, 245)
BG_BOT = (210, 240, 255)
TEXT_DARK = (20, 50, 80)
CARD_BG = (255, 255, 255)
ACCENT = (30, 130, 200)

font_bold = ImageFont.truetype(str(FONTS / "FiraSans-Bold.ttf"), 58)
font_medium = ImageFont.truetype(str(FONTS / "FiraSans-Medium.ttf"), 38)
font_regular = ImageFont.truetype(str(FONTS / "FiraSans-Regular.ttf"), 32)
font_small = ImageFont.truetype(str(FONTS / "FiraSans-Regular.ttf"), 27)
font_mono = ImageFont.truetype(str(FONTS / "FiraSans-Medium.ttf"), 34)

img = Image.new("RGB", (W, H))
draw = ImageDraw.Draw(img)

# Градиентный фон
for y in range(H):
    t = y / H
    r = int(BG_TOP[0] + (BG_BOT[0] - BG_TOP[0]) * t)
    g = int(BG_TOP[1] + (BG_BOT[1] - BG_TOP[1]) * t)
    b = int(BG_TOP[2] + (BG_BOT[2] - BG_TOP[2]) * t)
    draw.line([(0, y), (W, y)], fill=(r, g, b))

# Заголовок
draw.text((540, 80), "Пример письма с кодом", font=font_bold, fill=TEXT_DARK, anchor="mt")

# Белая карточка-письмо
card_x, card_y = 60, 190
card_w, card_h = 960, 790
draw.rounded_rectangle([card_x, card_y, card_x+card_w, card_y+card_h],
                        radius=24, fill=CARD_BG,
                        outline=(200, 220, 235), width=2)

# Шапка письма (цветная полоса)
draw.rounded_rectangle([card_x, card_y, card_x+card_w, card_y+80],
                        radius=24, fill=ACCENT)
draw.rectangle([card_x, card_y+56, card_x+card_w, card_y+80], fill=ACCENT)
draw.text((card_x+48, card_y+40), "✉  Активация цифрового товара",
          font=font_medium, fill=(255,255,255), anchor="lm")

# Поля письма
y = card_y + 110
draw.text((card_x+48, y), "Кому:", font=font_small, fill=(120,150,170))
draw.text((card_x+180, y), "ваш@email.com", font=font_small, fill=TEXT_DARK)

y += 52
draw.line([(card_x+40, y), (card_x+card_w-40, y)], fill=(230,240,248), width=1)

y += 24
draw.text((card_x+48, y), "Тема:", font=font_small, fill=(120,150,170))
draw.text((card_x+180, y), "Ваш код активации готов", font=font_small, fill=TEXT_DARK)

y += 52
draw.line([(card_x+40, y), (card_x+card_w-40, y)], fill=(230,240,248), width=1)

# Тело письма
y += 36
draw.text((card_x+48, y), "Здравствуйте!", font=font_medium, fill=TEXT_DARK)
y += 60
draw.text((card_x+48, y), "Вот ваш код активации:", font=font_regular, fill=(60,80,100))

# Блок с кодом
y += 56
code_box = [card_x+80, y, card_x+card_w-80, y+90]
draw.rounded_rectangle(code_box, radius=12,
                        fill=(240, 248, 255), outline=ACCENT, width=2)
draw.text((card_x+card_w//2, y+45), "XXXX-XXXX-XXXX-XXXX",
          font=font_mono, fill=ACCENT, anchor="mm")

y += 120
draw.text((card_x+48, y), "Скопируйте код и активируйте его", font=font_regular, fill=(60,80,100))
y += 48
draw.text((card_x+48, y), "по инструкции из карточки товара.", font=font_regular, fill=(60,80,100))

y += 72
draw.text((card_x+48, y), "Срок активации:", font=font_small, fill=(120,150,170))
y += 40
draw.text((card_x+48, y), "указан на странице товара", font=font_small, fill=TEXT_DARK)

y += 60
draw.line([(card_x+40, y), (card_x+card_w-40, y)], fill=(230,240,248), width=1)
y += 24
draw.text((card_x+48, y), "Если возникли вопросы — напишите в чат поддержки",
          font=font_small, fill=(120,150,170))

# Нижняя подпись
draw.text((540, 1020), "ПОСЛЕ ПОКУПКИ ВЫ ПОЛУЧИТЕ", font=font_bold, fill=TEXT_DARK, anchor="mt")
draw.text((540, 1085), "ПИСЬМО С КОДОМ АКТИВАЦИИ", font=font_bold, fill=TEXT_DARK, anchor="mt")
draw.text((540, 1150), "НА ВАШУ ПОЧТУ", font=font_bold, fill=TEXT_DARK, anchor="mt")

# Логотип КодХаб
draw.text((540, 1310), "КОДХАБ", font=font_bold, fill=TEXT_DARK, anchor="mm")

img.save(OUT, "PNG")
print(f"Сохранено: {OUT}")
