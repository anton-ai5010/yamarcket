"""
make_card_video.py

Создаёт 30-секундное видео 1080x1440 для одной карточки.
Анимации: вылет карточки, 3D-вращение, блик, текст, CTA.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path
import os, sys

ROOT = Path(__file__).parent.parent.parent
FONTS = ROOT / "pipeline" / "images" / "fonts"
OUT_DIR = ROOT / "pipeline" / "images" / "output" / "videos"
OUT_DIR.mkdir(exist_ok=True)

W, H = 1080, 1440
FPS = 30
DURATION = 30
N = FPS * DURATION  # 900 frames

CARD_PATH = ROOT / "pipeline/images/output/main_cards/playstation/GFT164_ssha.png"

# ── Шрифты ───────────────────────────────────────────────────────────────────
font_bold   = ImageFont.truetype(str(FONTS / "FiraSans-Bold.ttf"), 52)
font_medium = ImageFont.truetype(str(FONTS / "FiraSans-Medium.ttf"), 38)
font_small  = ImageFont.truetype(str(FONTS / "FiraSans-Regular.ttf"), 32)
font_big    = ImageFont.truetype(str(FONTS / "FiraSans-Bold.ttf"), 68)

# ── Цвета ────────────────────────────────────────────────────────────────────
BG_TOP    = (8,  15,  40)
BG_BOT    = (20, 10,  55)
ACCENT    = (0, 160, 255)
GOLD      = (255, 210, 60)
WHITE     = (255, 255, 255)
WHITE80   = (255, 255, 255, 200)

STEPS = [
    "1. Войдите в PlayStation Store",
    "2. Откройте «Погасить код»",
    "3. Введите 12-значный код",
    "4. Средства зачислятся сразу",
]

# ── Easing-функции ────────────────────────────────────────────────────────────
def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))

def ease_out_back(t, s=1.70158):
    t = clamp(t)
    c3 = s + 1
    return 1 + c3 * (t - 1)**3 + s * (t - 1)**2

def ease_in_out_cubic(t):
    t = clamp(t)
    return 4*t**3 if t < 0.5 else 1 - (-2*t+2)**3/2

def ease_out_cubic(t):
    t = clamp(t)
    return 1 - (1 - t)**3

def ease_in_out_sine(t):
    t = clamp(t)
    return -(np.cos(np.pi * t) - 1) / 2

def lerp(a, b, t):
    return a + (b - a) * clamp(t)

def scene_t(frame, start_s, end_s):
    """Возвращает t=[0..1] для кадра внутри сцены."""
    s = start_s * FPS
    e = end_s   * FPS
    if e == s:
        return 1.0
    return clamp((frame - s) / (e - s))

# ── Фон ──────────────────────────────────────────────────────────────────────
def make_bg():
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        r = int(BG_TOP[0] + (BG_BOT[0]-BG_TOP[0])*t)
        g = int(BG_TOP[1] + (BG_BOT[1]-BG_TOP[1])*t)
        b = int(BG_TOP[2] + (BG_BOT[2]-BG_TOP[2])*t)
        draw.line([(0,y),(W,y)], fill=(r,g,b))
    return img

BG = make_bg()

# Тихие круги на фоне (decorative)
def draw_circles(base):
    out = base.copy()
    draw = ImageDraw.Draw(out, "RGBA")
    circles = [
        (200,  300, 380, (0,160,255, 18)),
        (900,  800, 500, (120,0,200, 14)),
        (100, 1100, 280, (0,200,150, 12)),
        (980,  200, 200, (255,180,0,  10)),
    ]
    for cx, cy, r, col in circles:
        draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=col)
    return out.convert("RGB")

BG_WITH_CIRCLES = draw_circles(BG)

# ── Перспективный наклон ──────────────────────────────────────────────────────
def find_coeffs(src, dst):
    A, b_vec = [], []
    for (x,y),(X,Y) in zip(src,dst):
        A += [[x,y,1,0,0,0,-X*x,-X*y],
              [0,0,0,x,y,1,-Y*x,-Y*y]]
        b_vec += [X, Y]
    A = np.array(A, dtype=float)
    b_vec = np.array(b_vec, dtype=float)
    return np.linalg.solve(A, b_vec)

def perspective_tilt(img, tilt):
    """tilt: -1 (влево) .. +1 (вправо), симулирует 3D поворот вокруг вертикальной оси."""
    w, h = img.size
    squeeze = abs(tilt) * 0.35
    if tilt >= 0:
        src = [(0,0),(w,0),(w,h),(0,h)]
        dst = [(w*squeeze, h*squeeze*0.25),
               (w,         0),
               (w,         h),
               (w*squeeze, h*(1 - squeeze*0.25))]
    else:
        sq = -tilt * 0.35
        src = [(0,0),(w,0),(w,h),(0,h)]
        dst = [(0,          0),
               (w*(1-sq),   h*sq*0.25),
               (w*(1-sq),   h*(1-sq*0.25)),
               (0,          h)]
    coeffs = find_coeffs(src, dst)
    return img.transform((w,h), Image.Transform.PERSPECTIVE, coeffs, Image.Resampling.BICUBIC)

def xscale_card(img, scale):
    """Сжимает по горизонтали (coin-flip эффект). scale=1 – норма, 0 – плоский."""
    scale = max(0.0, scale)
    w, h = img.size
    nw = max(1, int(w * scale))
    shrunk = img.resize((nw, h), Image.Resampling.LANCZOS)
    out = Image.new("RGBA", (w, h), (0,0,0,0))
    out.paste(shrunk, ((w - nw)//2, 0))
    return out

# ── Тень под карточкой ───────────────────────────────────────────────────────
def card_shadow(card_w, card_h, alpha=120):
    sh = Image.new("RGBA", (card_w+80, card_h+60), (0,0,0,0))
    draw = ImageDraw.Draw(sh)
    draw.ellipse([20, card_h-20, card_w+60, card_h+55], fill=(0,0,0,alpha))
    return sh.filter(ImageFilter.GaussianBlur(30))

# ── Блик (shine sweep) ───────────────────────────────────────────────────────
def shine_overlay(card_img, progress):
    """progress: 0..1 — блик едет слева направо."""
    w, h = card_img.size
    overlay = Image.new("RGBA", (w, h), (0,0,0,0))
    draw = ImageDraw.Draw(overlay)
    cx = int(progress * (w + 200)) - 100
    hw = 120
    for dx in range(-hw, hw):
        x = cx + dx
        if 0 <= x < w:
            a = int(90 * (1 - abs(dx)/hw) * np.sin(np.pi * progress))
            draw.line([(x, 0),(x, h)], fill=(255,255,255,a))
    return Image.alpha_composite(card_img.convert("RGBA"), overlay).convert("RGBA")

# ── Текст с тенью ────────────────────────────────────────────────────────────
def draw_text_shadow(draw, pos, text, font, fill, shadow_offset=3, shadow_alpha=100):
    sx, sy = pos[0]+shadow_offset, pos[1]+shadow_offset
    draw.text((sx, sy), text, font=font, fill=(0,0,0,shadow_alpha), anchor=pos[2] if len(pos)>2 else None)
    draw.text(pos[:2], text, font=font, fill=fill)

# ── Загрузка карточки ─────────────────────────────────────────────────────────
print("Загружаю карточку...")
card_orig = Image.open(CARD_PATH).convert("RGBA")
CARD_W, CARD_H = 820, int(820 * 1440/1080)  # scaled to fit nicely
card_orig = card_orig.resize((CARD_W, CARD_H), Image.Resampling.LANCZOS)

shadow_img = card_shadow(CARD_W, CARD_H)

CARD_X = (W - CARD_W) // 2   # центр по горизонтали
CARD_Y_FINAL = 100            # финальная Y-позиция карточки (вверху)
CARD_Y_CENTER = (H - CARD_H) // 2  # по центру экрана

# ── Генерация кадра ───────────────────────────────────────────────────────────
def make_frame(f):
    """f = номер кадра 0..N-1. Возвращает PIL Image RGB."""
    base = BG_WITH_CIRCLES.copy().convert("RGBA")
    draw = ImageDraw.Draw(base, "RGBA")
    t_total = f / N  # 0..1 весь ролик

    # ── СЦЕНА 1: 0–3с — карточка вылетает снизу ──────────────────────────
    if f < 3*FPS:
        t = ease_out_back(scene_t(f, 0, 3), s=1.5)
        card_y = int(lerp(H + 100, CARD_Y_CENTER, t))
        opacity = int(lerp(0, 255, ease_out_cubic(scene_t(f, 0, 0.5))))

        card_draw = card_orig.copy()
        card_draw.putalpha(opacity)
        # тень
        sh_copy = shadow_img.copy()
        sh_copy.putalpha(int(opacity * 0.5))
        base.paste(sh_copy, (CARD_X - 40, card_y + CARD_H - 30), sh_copy)
        base.paste(card_draw, (CARD_X, card_y), card_draw)

    # ── СЦЕНА 2: 3–9с — 3D качание + coin-flip ───────────────────────────
    elif f < 9*FPS:
        t_scene = scene_t(f, 3, 9)

        # Первые 2с: качание влево-вправо
        if f < 5*FPS:
            swing = np.sin(scene_t(f, 3, 5) * np.pi * 2.5) * 0.55 \
                    * (1 - scene_t(f, 3, 5)*0.4)
            card_img = perspective_tilt(card_orig, swing)
            scale_x = 1.0
        # 5–7с: coin flip (полный оборот)
        elif f < 7*FPS:
            t_flip = scene_t(f, 5, 7)
            # 0→0.5: сжимаем до 0, 0.5→1: растягиваем обратно
            if t_flip < 0.5:
                scale_x = 1 - ease_in_out_sine(t_flip*2)
            else:
                scale_x = ease_in_out_sine((t_flip-0.5)*2)
            card_img = card_orig
            if t_flip > 0.5:
                card_img = card_img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                card_img = card_img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)  # обратно
        # 7–9с: блик
        else:
            t_shine = scene_t(f, 7, 9)
            card_img = shine_overlay(card_orig, t_shine)
            scale_x = 1.0

        # Y: карточка медленно движется вверх
        card_y = int(lerp(CARD_Y_CENTER, CARD_Y_FINAL + 80, ease_in_out_cubic(scene_t(f, 3, 9))))

        if scale_x < 1.0:
            card_drawn = xscale_card(card_img.convert("RGBA"), scale_x)
        else:
            card_drawn = card_img.convert("RGBA")

        base.paste(shadow_img, (CARD_X - 40, card_y + CARD_H - 30), shadow_img)
        base.paste(card_drawn, (CARD_X, card_y), card_drawn)

    # ── СЦЕНА 3: 9–22с — карточка вверху, шаги инструкции ───────────────
    elif f < 22*FPS:
        card_y = CARD_Y_FINAL + 80

        # Лёгкое покачивание (breathing)
        breathe = np.sin(scene_t(f, 9, 22) * np.pi * 6) * 0.06
        card_drawn = perspective_tilt(card_orig, breathe)

        base.paste(shadow_img, (CARD_X - 40, card_y + CARD_H - 30), shadow_img)
        base.paste(card_drawn.convert("RGBA"), (CARD_X, card_y), card_drawn.convert("RGBA"))

        # Заголовок
        t_title = ease_out_cubic(clamp(scene_t(f, 9, 10.5)))
        title_y = int(lerp(card_y + CARD_H + 60, card_y + CARD_H + 40, t_title))
        title_alpha = int(255 * t_title)
        draw2 = ImageDraw.Draw(base, "RGBA")
        draw2.text((W//2, title_y), "Как активировать",
                   font=font_bold, fill=(255,255,255,title_alpha), anchor="mt")

        # Шаги — каждый появляется через 2.5с
        step_start = 10.5
        step_dur   = 2.5
        step_base_y = card_y + CARD_H + 110

        for i, step in enumerate(STEPS):
            t_step = ease_out_cubic(clamp(scene_t(f, step_start + i*step_dur,
                                                     step_start + i*step_dur + 1.2)))
            if t_step <= 0:
                break
            sy = step_base_y + i * 76
            sx_offset = int(lerp(60, 0, t_step))  # slide in from right
            alpha = int(255 * t_step)

            # Bullet circle
            bx, by = 60 + sx_offset, sy + 2
            draw2.ellipse([bx-18, by-18, bx+18, by+18], fill=(*ACCENT, alpha))
            draw2.text((bx, by), str(i+1), font=font_small,
                       fill=(255,255,255,alpha), anchor="mm")
            # Text
            draw2.text((100 + sx_offset, sy), step[3:], font=font_medium,
                       fill=(220,235,255,alpha), anchor="lm")

        # Разделитель
        if scene_t(f, 9, 11) >= 1:
            lw = int(W*0.8 * ease_out_cubic(clamp(scene_t(f, 10, 11))))
            lx = (W - lw)//2
            draw2.rectangle([lx, card_y+CARD_H+30, lx+lw, card_y+CARD_H+33],
                            fill=(255,255,255,40))

    # ── СЦЕНА 4: 22–27с — карточка возвращается по центру, пульс ────────
    elif f < 27*FPS:
        t_in = ease_out_back(scene_t(f, 22, 24.5), s=1.2)
        card_y = int(lerp(CARD_Y_FINAL + 80, CARD_Y_CENTER - 80, t_in))

        # Пульс / масштаб
        pulse = 1 + 0.025 * np.sin(scene_t(f, 22, 27) * np.pi * 4)
        pw = int(CARD_W * pulse)
        ph = int(CARD_H * pulse)
        px = (W - pw)//2
        card_pulsed = card_orig.resize((pw, ph), Image.Resampling.LANCZOS)

        # Блик финальный
        t_shine2 = ease_in_out_sine(scene_t(f, 24.5, 26.5))
        card_pulsed = shine_overlay(card_pulsed.convert("RGBA"), t_shine2)

        sh2 = card_shadow(pw, ph, alpha=int(80*t_in))
        base.paste(sh2, (px-40, card_y+ph-30), sh2)
        base.paste(card_pulsed, (px, card_y), card_pulsed)

        # "PlayStation Store США" подпись
        t_label = ease_out_cubic(clamp(scene_t(f, 23, 25)))
        alpha_l = int(255 * t_label)
        draw2 = ImageDraw.Draw(base, "RGBA")
        draw2.text((W//2, card_y + ph + 28),
                   "PlayStation Store · США · $10",
                   font=font_medium, fill=(180,210,255,alpha_l), anchor="mt")

    # ── СЦЕНА 5: 27–30с — CTA + fade out ─────────────────────────────────
    else:
        t_fade = scene_t(f, 27, 30)
        fade_out = 1 - ease_in_out_cubic(t_fade)  # 1→0

        # Карточка уходит вниз
        card_y = int(lerp(CARD_Y_CENTER - 80, H + 100, ease_in_out_cubic(scene_t(f, 27.5, 30))))
        card_small = card_orig.resize((int(CARD_W*0.7), int(CARD_H*0.7)), Image.Resampling.LANCZOS)
        cx2 = (W - int(CARD_W*0.7))//2
        alpha_card = int(255 * fade_out)
        card_small_a = card_small.copy()
        card_small_a.putalpha(alpha_card)
        base.paste(card_small_a, (cx2, card_y), card_small_a)

        # CTA блок
        draw2 = ImageDraw.Draw(base, "RGBA")
        cta_y = 900
        t_cta = ease_out_back(clamp(scene_t(f, 27, 28.2)), s=1.0)
        alpha_cta = int(255 * t_cta * fade_out)

        # Кнопка
        btn_w, btn_h = 680, 100
        bx = (W - btn_w)//2
        by = cta_y
        draw2.rounded_rectangle([bx, by, bx+btn_w, by+btn_h],
                                 radius=50, fill=(*ACCENT, alpha_cta))
        draw2.text((W//2, by + btn_h//2), "Купить на Яндекс Маркете",
                   font=font_bold, fill=(255,255,255,alpha_cta), anchor="mm")

        # Подпись
        draw2.text((W//2, by + btn_h + 40),
                   "Мгновенная доставка кода на почту",
                   font=font_small, fill=(180,200,255,alpha_cta), anchor="mt")

        # Финальный fade to black
        fade_black = int(255 * ease_in_out_cubic(clamp(scene_t(f, 28.5, 30))))
        if fade_black > 0:
            draw2.rectangle([0,0,W,H], fill=(0,0,0,fade_black))

    return base.convert("RGB")


# ── Рендер через moviepy ──────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"Рендер {N} кадров @ {FPS}fps = {DURATION}s...")
    import moviepy

    frames = []
    for f in range(N):
        if f % 90 == 0:
            print(f"  Кадр {f}/{N} ({f//FPS}с)...")
        frame = make_frame(f)
        frames.append(np.array(frame))

    print("Сборка видео...")
    from moviepy import ImageSequenceClip
    clip = ImageSequenceClip(frames, fps=FPS)

    out_path = str(OUT_DIR / "GFT164_ssha_promo.mp4")
    clip.write_videofile(out_path, fps=FPS, codec="libx264",
                         bitrate="6000k", audio=False, logger=None)
    print(f"\nГотово: {out_path}")
