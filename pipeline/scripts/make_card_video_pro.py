"""
make_card_video_pro.py  —  Professional 30s promo video, 1080x1440
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
from pathlib import Path
import random, math

ROOT   = Path(__file__).parent.parent.parent
FONTS  = ROOT / "pipeline" / "images" / "fonts"
OUT    = ROOT / "pipeline" / "images" / "output" / "videos" / "GFT164_pro.mp4"
CARD_PATH = ROOT / "pipeline/images/output/main_cards/playstation/GFT164_ssha.png"

W, H   = 1080, 1440
FPS    = 30
DUR    = 30
N      = FPS * DUR   # 900 frames

# ── Шрифты ───────────────────────────────────────────────────────────────────
fb  = ImageFont.truetype(str(FONTS / "FiraSans-Bold.ttf"),    64)
fm  = ImageFont.truetype(str(FONTS / "FiraSans-Medium.ttf"),  42)
fr  = ImageFont.truetype(str(FONTS / "FiraSans-Regular.ttf"), 34)
fb2 = ImageFont.truetype(str(FONTS / "FiraSans-Bold.ttf"),    80)

# ── Easing ───────────────────────────────────────────────────────────────────
def clamp(v, a=0., b=1.): return max(a, min(b, v))
def lerp(a, b, t):        return a + (b-a)*clamp(t)
def iec(t):               # ease-in-out cubic
    t=clamp(t); return 4*t**3 if t<.5 else 1-(-2*t+2)**3/2
def oback(t, s=1.7):      # ease-out-back
    t=clamp(t); return 1+(s+1)*(t-1)**3+s*(t-1)**2
def ocubic(t):            # ease-out cubic
    t=clamp(t); return 1-(1-t)**3
def iosine(t):            # ease-in-out sine
    t=clamp(t); return -(math.cos(math.pi*t)-1)/2

def st(f, s, e):          # scene-local t
    return clamp((f - s*FPS) / max(1,(e-s)*FPS))

# ── Perspective helpers ───────────────────────────────────────────────────────
def find_coeffs(out_pts, in_pts):
    """PIL PERSPECTIVE coefficients: output → input mapping."""
    A, b = [], []
    for (xd,yd),(xs,ys) in zip(out_pts, in_pts):
        A += [[xd,yd,1,0,0,0,-xs*xd,-xs*yd],
              [0,0,0,xd,yd,1,-ys*xd,-ys*yd]]
        b += [xs, ys]
    A = np.array(A, dtype=float)
    b = np.array(b, dtype=float)
    return np.linalg.solve(A, b)

def rotate_y(img, angle_deg, fov=1400):
    """True 3D perspective rotation around Y axis."""
    ang = math.radians(angle_deg)
    ca, sa = math.cos(ang), math.sin(ang)
    w, h = img.size
    hw, hh = w/2, h/2

    src = [(0,0),(w,0),(w,h),(0,h)]
    proj = []
    for x,y in [(-hw,-hh),(hw,-hh),(hw,hh),(-hw,hh)]:
        x3 = x*ca; z3 = x*sa
        zc = z3 + fov
        if zc < 1: zc = 1
        proj.append((x3*fov/zc + hw,  y*fov/zc + hh))

    # check if degenerate (edge-on)
    xs = [p[0] for p in proj]
    if max(xs)-min(xs) < 2:
        return Image.new("RGBA",(w,h),(0,0,0,0))

    draw_img = img.copy()
    if ca < 0:   # back face → flip horizontal
        draw_img = draw_img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)

    coeffs = find_coeffs(proj, src)
    result = draw_img.transform((w,h), Image.Transform.PERSPECTIVE,
                                 coeffs, Image.Resampling.BICUBIC)
    return result

# ── Glow behind card ─────────────────────────────────────────────────────────
def make_glow(card_rgba, radius=80, tint=(80,140,255), strength=0.7):
    """Radial glow aura from card silhouette."""
    alpha = card_rgba.split()[3]
    glow  = Image.new("RGBA", card_rgba.size, (*tint,0))
    glow.putalpha(alpha)
    glow  = glow.filter(ImageFilter.GaussianBlur(radius))
    glow  = glow.filter(ImageFilter.GaussianBlur(radius//2))
    arr   = np.array(glow).astype(float)
    arr[...,3] = np.clip(arr[...,3]*strength, 0, 255)
    return Image.fromarray(arr.astype(np.uint8))

# ── Reflection ───────────────────────────────────────────────────────────────
def make_reflection(card_rgba, refl_h=260):
    w, h  = card_rgba.size
    refl  = card_rgba.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    refl  = refl.crop((0,0,w,refl_h))
    arr   = np.array(refl).astype(float)
    for row in range(refl_h):
        t = row/refl_h        # 0=top(near card) 1=bottom(far)
        arr[row,:,3] *= (1-t)*0.45
    return Image.fromarray(arr.astype(np.uint8))

# ── Particles ────────────────────────────────────────────────────────────────
rng = random.Random(42)
PARTICLES = [
    {'x': rng.uniform(0,W), 'y': rng.uniform(0,H),
     'vy': rng.uniform(0.3,1.2), 'vx': rng.uniform(-0.3,0.3),
     'r':  rng.uniform(1.5,4.5),
     'a':  rng.uniform(60,160),
     'phase': rng.uniform(0, 2*math.pi)}
    for _ in range(70)
]

def draw_particles(draw, frame):
    for p in PARTICLES:
        t = (frame*0.6 + p['phase']) % (H+50)
        x = p['x'] + p['vx']*frame + 12*math.sin(frame*0.02+p['phase'])
        y = (H + 50 - t*p['vy']*0.8) % H
        # twinkle
        alpha = int(p['a'] * (0.5 + 0.5*math.sin(frame*0.07+p['phase'])))
        r = p['r']
        draw.ellipse([x-r, y-r, x+r, y+r], fill=(255,255,255,alpha))

# ── Gradient background ───────────────────────────────────────────────────────
def make_bg(accent=(30,20,80)):
    img = Image.new("RGB",(W,H))
    draw = ImageDraw.Draw(img)
    top = (5, 3, 18); bot = (12, 6, 40)
    for y in range(H):
        t = y/H
        c = tuple(int(top[i]+(bot[i]-top[i])*t) for i in range(3))
        draw.line([(0,y),(W,y)], fill=c)
    return img

BG = make_bg()

# Центральный радиальный глоу (статичный)
def make_center_glow(cx=540, cy=600, rx=480, ry=520, col=(40,30,120)):
    layer = Image.new("RGBA",(W,H),(0,0,0,0))
    draw  = ImageDraw.Draw(layer)
    steps = 18
    for i in range(steps,0,-1):
        t  = i/steps
        r  = int(rx*(1-t*0.05)); rr = int(ry*(1-t*0.05))
        al = int(60*(1-t)**1.4)
        draw.ellipse([cx-r, cy-rr, cx+r, cy+rr], fill=(*col, al))
    return layer.filter(ImageFilter.GaussianBlur(40))

CENTER_GLOW = make_center_glow()

# ── Load card ────────────────────────────────────────────────────────────────
print("Загружаю карточку...")
_card_raw = Image.open(CARD_PATH).convert("RGBA")
CW, CH   = 760, int(760*1440//1080)   # 760×1013
card_base = _card_raw.resize((CW,CH), Image.Resampling.LANCZOS)

# Pre-compute glow for static card
card_glow_static = make_glow(card_base, radius=90, tint=(60,120,255), strength=0.85)
card_refl        = make_reflection(card_base, refl_h=280)

CX = (W - CW)//2   # center X

# Card vertical position: centre of screen minus a bit
CARD_Y = (H - CH)//2 - 60   # ≈ 193

# ── Text blocks ──────────────────────────────────────────────────────────────
INFO_Y = CARD_Y + CH + 36   # just below card

def draw_centered(draw, y, text, font, fill):
    draw.text((W//2, y), text, font=font, fill=fill, anchor="mt")

def fade_text(draw, y, text, font, fill, alpha):
    col = (*fill[:3], int(alpha)) if len(fill)==3 else (*fill[:3], int(alpha))
    draw.text((W//2, y), text, font=font, fill=col, anchor="mt")

FEATURES = [
    ("⚡", "Мгновенный код на почту"),
    ("🔒", "Официальный ключ"),
    ("🌍", "Регион: США · Только USD"),
]

# ── Main render ───────────────────────────────────────────────────────────────
def make_frame(f):
    base = BG.copy().convert("RGBA")

    # center glow always present (fade in)
    glow_a = clamp(f/(1.5*FPS))
    cg = CENTER_GLOW.copy()
    arr = np.array(cg).astype(float)
    arr[...,3] *= glow_a
    base = Image.alpha_composite(base, Image.fromarray(arr.astype(np.uint8)))

    # particles (start at 1s)
    if f > FPS:
        pdraw = ImageDraw.Draw(base, "RGBA")
        draw_particles(pdraw, f)

    draw = ImageDraw.Draw(base, "RGBA")

    # ── SCENE 1: 0–3s — карточка появляется из центра ─────────────────
    if f < 3*FPS:
        t = oback(st(f,0,2.8), s=1.4)
        scale = lerp(0.55, 1.0, t)
        alpha = int(255 * ocubic(st(f,0,1.0)))

        sw, sh = int(CW*scale), int(CH*scale)
        sx = (W-sw)//2
        sy = CARD_Y + (CH-sh)//2

        card_s = card_base.resize((sw,sh), Image.Resampling.LANCZOS)
        glow_s = card_glow_static.resize(
            (int(sw*1.35), int(sh*1.35)), Image.Resampling.LANCZOS)
        gx = sx - (glow_s.width - sw)//2
        gy = sy - (glow_s.height - sh)//2

        # glow
        ga = np.array(glow_s).astype(float); ga[...,3] *= alpha/255
        base.alpha_composite(Image.fromarray(ga.astype(np.uint8)), (max(0,gx), max(0,gy)))
        # card
        ca = card_s.copy(); ca.putalpha(
            Image.fromarray((np.array(ca.split()[3]).astype(float)*alpha/255).astype(np.uint8)))
        base.alpha_composite(ca, (sx, sy))

    # ── SCENE 2: 3–12s — floating + slow Y-rock (±18°) ────────────────
    elif f < 12*FPS:
        t_sc = st(f, 3, 12)

        # Gentle float
        float_y = int(14 * math.sin(t_sc * math.pi * 2.8))
        # Slow Y-rock back-and-forth ±18°
        rock_angle = 18 * math.sin(t_sc * math.pi * 1.6)

        card_r = rotate_y(card_base, rock_angle)
        glow_r = make_glow(card_r, radius=85, tint=(60,120,255), strength=0.9)

        # glow
        gw,gh = int(CW*1.38), int(CH*1.38)
        glow_big = glow_r.resize((gw,gh), Image.Resampling.LANCZOS)
        gx = CX - (gw-CW)//2; gy = CARD_Y + float_y - (gh-CH)//2
        base.alpha_composite(glow_big, (max(0,gx), max(0,gy)))
        # card
        base.alpha_composite(card_r, (CX, CARD_Y + float_y))
        # reflection
        refl_y = CARD_Y + float_y + CH
        refl_copy = card_refl.copy()
        base.alpha_composite(refl_copy, (CX, refl_y))

        # Название и номинал появляются в 4.5s
        if f >= int(4.5*FPS):
            ta  = ocubic(st(f, 4.5, 6.0))
            fade_text(draw, INFO_Y + 10,
                      "PlayStation Store", fm, (160,200,255), 255*ta)
            fade_text(draw, INFO_Y + 64,
                      "$10 · США", fb, (255,255,255), 255*ta)

    # ── SCENE 3: 12–22s — карточка чуть меньше, фичи ─────────────────
    elif f < 22*FPS:
        # Card remains at CARD_Y, but floats
        t_sc = st(f, 12, 22)
        float_y = int(10 * math.sin(t_sc * math.pi * 3))

        # Card stays normal
        glow_big = card_glow_static.resize(
            (int(CW*1.38), int(CH*1.38)), Image.Resampling.LANCZOS)
        gx = CX - (glow_big.width-CW)//2
        gy = CARD_Y + float_y - (glow_big.height-CH)//2
        base.alpha_composite(glow_big, (max(0,gx), max(0,gy)))
        base.alpha_composite(card_base, (CX, CARD_Y+float_y))
        base.alpha_composite(card_refl, (CX, CARD_Y+float_y+CH))

        # Постоянный заголовок
        draw.text((W//2, INFO_Y+10), "PlayStation Store",
                  font=fm, fill=(160,200,255,220), anchor="mt")
        draw.text((W//2, INFO_Y+64), "$10 · США",
                  font=fb, fill=(255,255,255,255), anchor="mt")

        # Разделитель
        lw = int(600 * ocubic(st(f, 12, 13)))
        draw.rectangle([(W//2-lw//2, INFO_Y+136), (W//2+lw//2, INFO_Y+139)],
                       fill=(255,255,255,50))

        # 3 фичи, каждая появляется через 2.5s
        for i,(icon,txt) in enumerate(FEATURES):
            t_feat = ocubic(st(f, 13.5+i*2.4, 14.7+i*2.4))
            if t_feat <= 0: break
            fy = INFO_Y + 158 + i*90
            alpha_f = int(255*t_feat)

            # иконка-кружок
            bx, by = W//2-240, fy+21
            draw.ellipse([bx-22,by-22,bx+22,by+22],
                         fill=(30,100,200,alpha_f))
            draw.text((bx, by), icon, font=fr,
                      fill=(255,255,255,alpha_f), anchor="mm")
            # текст
            draw.text((bx+44, by), txt, font=fm,
                      fill=(220,235,255,alpha_f), anchor="lm")

    # ── SCENE 4: 22–27s — 360° rotation, потом глоу-взрыв ────────────
    elif f < 27*FPS:
        t_rot  = st(f, 22, 26)
        angle  = 360 * iec(t_rot)   # 0→360°

        card_r = rotate_y(card_base, angle)
        glow_r = make_glow(card_r, radius=90,
                           tint=(80,160,255), strength=1.0 + 0.4*abs(math.cos(math.radians(angle))))

        gw,gh  = int(CW*1.45), int(CH*1.45)
        glow_big = glow_r.resize((gw,gh), Image.Resampling.LANCZOS)
        gx = CX-(gw-CW)//2; gy = CARD_Y-(gh-CH)//2
        base.alpha_composite(glow_big, (max(0,gx),max(0,gy)))
        base.alpha_composite(card_r, (CX, CARD_Y))
        base.alpha_composite(card_refl, (CX, CARD_Y+CH))

        # После окончания вращения (26s) — заголовок возвращается
        if f >= 26*FPS:
            ta = ocubic(st(f, 26, 27))
            draw.text((W//2, INFO_Y+10), "PlayStation Store",
                      font=fm, fill=(160,200,255,int(220*ta)), anchor="mt")
            draw.text((W//2, INFO_Y+64), "$10 · США",
                      font=fb, fill=(255,255,255,int(255*ta)), anchor="mt")

    # ── SCENE 5: 27–30s — CTA + fade to black ─────────────────────────
    else:
        # Card stays, slight float
        float_y = int(8*math.sin(st(f,27,30)*math.pi*2))
        glow_big = card_glow_static.resize(
            (int(CW*1.38),int(CH*1.38)), Image.Resampling.LANCZOS)
        gx = CX-(glow_big.width-CW)//2; gy = CARD_Y+float_y-(glow_big.height-CH)//2
        base.alpha_composite(glow_big, (max(0,gx),max(0,gy)))
        base.alpha_composite(card_base, (CX, CARD_Y+float_y))

        # CTA кнопка
        t_cta  = oback(st(f, 27, 28.3), s=0.9)
        alpha_cta = int(255*t_cta)

        btn_w, btn_h = 740, 108
        bx, by = (W-btn_w)//2, INFO_Y+30
        # Тень кнопки
        draw.rounded_rectangle([bx+4,by+6,bx+btn_w+4,by+btn_h+6],
                                radius=54, fill=(0,0,0,int(80*t_cta)))
        # Кнопка градиент (два слоя)
        draw.rounded_rectangle([bx,by,bx+btn_w,by+btn_h],
                                radius=54, fill=(0,120,255,alpha_cta))
        draw.rounded_rectangle([bx,by,bx+btn_w,by+btn_h//2],
                                radius=54, fill=(40,160,255,int(alpha_cta*0.35)))
        draw.text((W//2, by+btn_h//2), "Купить на Яндекс Маркете",
                  font=fb, fill=(255,255,255,alpha_cta), anchor="mm")

        # Подпись
        draw.text((W//2, by+btn_h+28),
                  "Мгновенная доставка · Оригинальный код",
                  font=fr, fill=(140,170,220,alpha_cta), anchor="mt")

        # Fade to black
        fade = int(255*iec(st(f, 28.3, 30.0)))
        if fade > 0:
            draw.rectangle([0,0,W,H], fill=(0,0,0,fade))

    return np.array(base.convert("RGB"))


# ── Render ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"Рендер {N} кадров ({DUR}s @ {FPS}fps)...")
    frames = []
    for f in range(N):
        if f % 90 == 0:
            print(f"  {f//FPS}s / {DUR}s ...")
        frames.append(make_frame(f))

    print("Сборка MP4...")
    from moviepy import ImageSequenceClip
    clip = ImageSequenceClip(frames, fps=FPS)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    clip.write_videofile(str(OUT), fps=FPS, codec="libx264",
                         bitrate="8000k", audio=False, logger=None)
    print(f"\n✓  {OUT}")
