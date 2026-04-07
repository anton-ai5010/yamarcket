#!/usr/bin/env python3
"""
Генерация фоновых изображений брендов через OpenRouter (Gemini Flash Image).
Отправляет два референса и промпт, сохраняет результат 1792x2400 PNG.

Запуск:
    python3 generate_backgrounds.py                     # следующие 10 отсутствующих → bg_new/
    python3 generate_backgrounds.py --limit 5           # следующие 5 → bg_new/
    python3 generate_backgrounds.py discord hbo ea      # конкретные бренды → bg_new/
"""

import os, sys, re, base64, time, json
import requests
from pathlib import Path
from PIL import Image
import io

# ── Настройки ──────────────────────────────────────────────────────────────
REFS_DIR    = Path("/media/anton/Новый том/yamarcket/pipeline/images/references")
REF1        = REFS_DIR / "bg_appstore.png"
REF2        = REFS_DIR / "bg_xbox.png"
REVIEW_DIR  = REFS_DIR / "bg_new"       # сюда складываем для просмотра
FINAL_DIR   = REFS_DIR                  # сюда переносим после одобрения
TARGET_SIZE = (1792, 2400)
BATCH_SIZE  = 10                        # по умолчанию

MODEL   = "google/gemini-3.1-flash-image-preview"
API_URL = "https://openrouter.ai/api/v1/chat/completions"
DELAY   = 3  # секунды между запросами

# ── Список брендов (ключ, название, описание цветов/стиля) ─────────────────
BRANDS = [
    # Подписки и стриминг
    ("disney",           "Disney+",             "dark navy blue background, Disney+ logo, magic stars"),
    ("hbo",              "HBO Max",              "dark background with HBO Max logo in white, premium luxury look"),
    ("hulu",             "Hulu",                 "green and black, Hulu green logo, streaming service"),
    ("crunchyroll",      "Crunchyroll",          "orange and black, Crunchyroll orange logo, anime streaming"),
    ("deezer",           "Deezer",               "purple gradient, Deezer logo, music streaming"),
    ("blutv",            "BluTV",                "blue gradient, BluTV logo, Turkish streaming platform"),
    ("exxen",            "Exxen",                "dark blue and orange, Exxen logo, Turkish streaming"),
    ("weyyak",           "Weyyak",               "green and white, Weyyak logo, Arabic MENA streaming"),
    ("blacknut",         "Blacknut",             "dark purple and black, Blacknut logo, cloud gaming subscription"),
    ("worldofwarcraft",  "World of Warcraft",    "dark blue and gold, WoW logo, dragon, fantasy MMO subscription"),

    # Игровые платформы
    ("ea",               "EA",                   "black and red, EA logo, Electronic Arts gaming platform"),
    ("overwatch",        "Overwatch 2",          "orange and blue, Overwatch 2 logo, Blizzard hero shooter"),
    ("elderscrollsonline","The Elder Scrolls Online", "dark brown and gold, ESO dragon logo, RPG subscription"),
    ("runescape",        "RuneScape",            "dark blue and gold, RuneScape logo, medieval fantasy MMO"),
    ("garena",           "Garena",               "red and orange gradient, Garena logo, Southeast Asia gaming"),
    ("tencent",          "Tencent Games",        "blue and white, Tencent logo, gaming company"),
    ("netease",          "NetEase Games",        "red and white, NetEase logo, Chinese gaming"),
    ("seagm",            "SEAGM",                "blue and orange, SEAGM logo, digital game marketplace"),
    ("cherrycredits",    "Cherry Credits",       "cherry red and pink, Cherry Credits logo, gaming voucher"),

    # Мобильные игры — топ-апы
    ("pubgmobile",       "PUBG Mobile",          "orange and black, PUBG Mobile logo, battle royale"),
    ("freefire",         "Free Fire",            "orange flames and dark, Free Fire logo, Garena battle royale"),
    ("genshin",          "Genshin Impact",       "blue and gold, Genshin Impact logo, anime open world RPG"),
    ("zenlesszonezero",  "Zenless Zone Zero",    "yellow and black, ZZZ logo, HoYoverse urban RPG"),
    ("bloodstrike",      "Blood Strike",         "red and dark, Blood Strike logo, mobile FPS"),
    ("magicchess",       "Magic Chess: Go Go",   "colorful and playful, Magic Chess logo, auto battler game"),
    ("castleclash",      "Castle Clash",         "medieval castle, Castle Clash logo, strategy mobile game"),
    ("blackcloverm",     "Black Clover M",       "black and bright green, Black Clover M logo, anime mobile RPG"),
    ("doomsday",         "Doomsday: Last Survivors", "dark post-apocalyptic, zombie, Doomsday logo"),
    ("identityv",        "Identity V",           "black gothic and white, Identity V logo, horror asymmetric game"),
    ("newstatemobile",   "New State Mobile",     "futuristic blue and black, New State Mobile logo, PUBG sequel"),
    ("undawn",           "Undawn",               "post-apocalyptic green and dark, Undawn logo, survival RPG"),
    ("lordsmobile",      "Lords Mobile",         "medieval blue and gold, Lords Mobile logo, strategy game"),
    ("afkjourney",       "AFK Journey",          "fantasy purple and gold, AFK Journey logo, idle RPG"),

    # Платёжные системы
    ("cashlib",          "CASHlib",              "green and white, CASHlib logo, prepaid voucher Europe"),
    ("flexepin",         "Flexepin",             "blue and yellow, Flexepin logo, prepaid voucher card"),
    ("openbucks",        "Openbucks",            "green and white, Openbucks logo, gift card platform"),
    ("icash",            "iCash.One",            "gold and white, iCash logo, digital prepaid voucher"),
    ("silkpay",          "S1lkPay",              "silk blue gradient, SilkPay logo, digital payment"),
    ("truemoney",        "True Money",           "orange and white, True Money logo, Thai digital wallet"),
    ("r2games",          "R2Games",              "dark blue and orange, R2Games logo, browser games portal"),
    ("discounty",        "Discounty",            "orange and white, Discounty logo, discounted gift cards"),
    ("jawaker",          "Jawaker",              "green and white, Jawaker logo, Arabic card games platform"),
    ("salik",            "Salik",                "blue and white, Salik logo, UAE road toll system e-voucher"),
    ("phonepe",          "PhonePE",              "purple and white, PhonePE logo, Indian digital payment"),

    # Приложения и сервисы
    ("discord",          "Discord",              "indigo purple, Discord Wumpus logo, gaming chat platform"),
    ("tiktok",           "TikTok",               "black with neon pink and cyan, TikTok musical note logo"),
    ("meta",             "Meta",                 "blue gradient, Meta infinity logo, Facebook company"),
    ("skype",            "Skype",                "sky blue and white, Skype logo, video communication"),
    ("adobe",            "Adobe",                "red and white, Adobe logo, Creative Cloud software"),
    ("bitdefender",      "Bitdefender",          "dark blue and white, Bitdefender shield logo, antivirus"),
    ("voicemod",         "Voicemod",             "neon purple and pink, Voicemod logo, voice changer app"),
    ("exitlag",          "ExitLag",              "orange and dark, ExitLag logo, gaming network optimizer"),
    ("noping",           "NoPing",               "blue and orange, NoPing logo, gaming VPN tunnel"),
    ("capcut",           "CapCut",               "black and white, CapCut scissors logo, video editor app"),

    # E-commerce и ритейл
    ("uber",             "Uber",                 "black and white, Uber logo, ride sharing and delivery"),
    ("airbnb",           "Airbnb",               "coral pink and white, Airbnb logo, travel accommodation"),
    ("ebay",             "eBay",                 "multicolor red green blue yellow letters, eBay logo, online marketplace"),
    ("shein",            "SHEIN",                "black and white, SHEIN fashion logo, fast fashion"),
    ("hm",               "H&M",                  "red and white, H&M logo, fashion retail"),
    ("nike",             "Nike",                 "black and white, Nike swoosh logo, sportswear"),
    ("victoriassecret",  "Victoria's Secret",    "black and pink, Victoria's Secret logo, lingerie fashion"),
    ("walmart",          "Walmart",              "blue and yellow spark, Walmart logo, US retail"),
    ("abercrombie",      "Abercrombie & Fitch",  "dark brown and white, A&F moose logo, premium fashion"),
    ("talabat",          "Talabat",              "orange and white, Talabat logo, food delivery MENA"),
    ("deliveroo",        "Deliveroo",            "teal turquoise and white, Deliveroo kangaroo logo, food delivery"),

    # Мессенджеры и соцсети
    ("tinder",           "Tinder",               "orange flame gradient, Tinder logo, dating app"),
    ("tango",            "Tango Live",           "pink and purple gradient, Tango Live logo, live streaming"),

    # Крупные мобильные операторы
    ("att",              "AT&T",                 "blue and white, AT&T globe logo, US telecom carrier"),
    ("tmobile",          "T-Mobile",             "magenta hot pink and white, T-Mobile logo, telecom"),
    ("ee",               "EE",                   "bright green and grey, EE logo, UK mobile carrier"),
    ("kpn",              "KPN",                  "green and white, KPN logo, Netherlands telecom"),
    ("proximus",         "Proximus",             "purple and white, Proximus logo, Belgium telecom"),
    ("bouygues",         "Bouygues Telecom",     "blue and white, Bouygues Telecom logo, France"),
    ("movistar",         "Movistar",             "blue and green gradient, Movistar logo, Telefonica"),
    ("vivo",             "Vivo Brazil",          "blue and white, Vivo logo, Brazilian telecom"),
    ("chinamobile",      "China Mobile",         "blue and red, China Mobile logo, Chinese telecom"),
    ("huawei",           "HUAWEI",               "red and white, Huawei logo, tech brand gift card"),

    # Небольшие операторы
    ("a1",               "A1 Telekom Austria",   "red and white, A1 logo, Austria mobile carrier"),
    ("ayayildiz",        "AY YILDIZ",            "red and white, crescent and star, Turkish German carrier"),
    ("base",             "BASE",                 "orange and white, BASE logo, Belgian mobile operator"),
    ("batelco",          "Batelco",              "blue and white, Batelco logo, Bahrain telecom"),
    ("bhutantelecom",    "Bhutan Telecom",       "orange and blue, Bhutan Telecom logo"),
    ("blau",             "Blau Mobilfunk",       "blue and white, Blau logo, German budget carrier"),
    ("btc",              "BTC Botswana",         "orange and blue, BTC logo, Botswana telecom"),
    ("chinatelecom",     "China Telecom",        "blue and white, China Telecom logo"),
    ("chinaunicom",      "China Unicom",         "red and blue, China Unicom logo"),
    ("congstar",         "Congstar",             "green and white, Congstar logo, Germany budget carrier"),
    ("djezzy",           "Djezzy",               "red and white, Djezzy logo, Algeria mobile carrier"),
    ("econet",           "Econet Wireless",      "orange and white, Econet logo, African telecom"),
    ("eir",              "eir Mobile Ireland",   "purple and white, eir logo, Ireland mobile carrier"),
    ("epic",             "Epic Cyprus",          "blue and white, Epic logo, Cyprus telecom"),
    ("ethiotelecom",     "Ethio Telecom",        "blue and green, Ethio Telecom logo, Ethiopia"),
    ("euskaltel",        "Euskaltel",            "orange and white, Euskaltel logo, Spain Basque carrier"),
    ("fyve",             "FYVE Germany",         "dark blue and orange, FYVE logo, Germany"),
    ("fivevoip",         "Five VoIP",            "blue and white, Five logo, UAE VoIP service"),
    ("hellovoip",        "Hello! VoIP",          "green and white, Hello logo, UAE VoIP"),
    ("homobile",         "ho. Mobile Italy",     "white and pink, ho. logo, Italian budget carrier"),
    ("iliad",            "iliad Italy",          "red and white, iliad logo, Italian carrier"),
    ("jimmobile",        "JIM Mobile Belgium",   "red and white, JIM Mobile logo, Belgium"),
    ("kenamobile",       "Kena Mobile",          "pink and white, Kena Mobile logo, Italy TIM sub-brand"),
    ("luckymobile",      "Lucky Mobile Bahrain", "green and yellow, Lucky Mobile logo, Bahrain"),
    ("magenta",          "Magenta Telekom",      "magenta pink and white, Magenta logo, Austria T-Mobile"),
    ("mascom",           "Mascom Wireless",      "blue and orange, Mascom logo, Botswana carrier"),
    ("masmovil",         "MásMóvil",             "yellow and black, MásMóvil logo, Spain carrier"),
    ("mobilis",          "Mobilis Algeria",      "red and blue, Mobilis logo, Algeria telecom"),
    ("nowmobile",        "Now Mobile UK",        "white and blue, Now logo, Sky UK mobile"),
    ("omantel",          "Omantel",              "blue and green, Omantel logo, Oman telecom"),
    ("ortel",            "Ortel Mobile",         "blue and white, Ortel logo, Germany MVNO"),
    ("otelo",            "Otelo",                "orange and white, Otelo logo, Vodafone Germany sub-brand"),
    ("personal",         "Personal Argentina",   "red and white, Personal logo, Telecom Argentina"),
    ("rennamobile",      "Renna Mobile Oman",    "teal and white, Renna logo, Oman MVNO"),
    ("robi",             "Robi Axiata",          "red and white, Robi logo, Bangladesh mobile carrier"),
    ("safaricom",        "Safaricom",            "green and white, Safaricom logo, East Africa telecom"),
    ("simyo",            "Simyo Spain",          "orange and white, Simyo logo, Spain budget carrier"),
    ("tele2",            "Tele2 Lithuania",      "blue and white, Tele2 logo, Baltic telecom"),
    ("telekom",          "Telekom Romania",      "magenta and white, Telekom logo, Deutsche Telekom Romania"),
    ("teletalk",         "Teletalk Bangladesh",  "green and white, Teletalk logo, Bangladesh state carrier"),
    ("tim",              "TIM",                  "blue and white, TIM logo, Telecom Italia Brazil"),
    ("tiscali",          "Tiscali",              "blue and orange, Tiscali logo, Italy ISP"),
    ("tuenti",           "Tuenti Argentina",     "dark blue and green, Tuenti logo, Argentina carrier"),
    ("umniah",           "Umniah Jordan",        "pink and white, Umniah logo, Jordan mobile carrier"),
    ("verymobile",       "Very Mobile Italy",    "dark blue and yellow, Very Mobile logo, Italian carrier"),
    ("windtre",          "WINDTRE Italy",        "orange and blue, WINDTRE logo, Italian merged carrier"),
    ("yoigo",            "Yoigo Spain",          "purple and white, Yoigo logo, Spain carrier MasMovil"),
    ("youmobile",        "YouMobile Spain",      "orange and white, YouMobile logo, Spain MVNO"),
    ("algar",            "Algar Telecom Brazil", "green and yellow, Algar logo, Brazilian regional carrier"),
    ("drei",             "Drei Austria",         "red and black, Drei 3 logo, Austria Hutchison carrier"),

    # Мобильные операторы для категории "Тарифные планы"
    ("esim",             "eSIM",                 "teal and white, eSIM chip icon, virtual SIM card, digital connectivity, modern minimalist"),
    ("lebara",           "Lebara",               "green and white, Lebara logo, international mobile carrier, budget telecom"),
    ("zain",             "Zain",                 "purple and white, Zain logo, Middle East and Africa telecom carrier"),
    ("mobily",           "Mobily",               "blue and green, Mobily logo, Saudi Arabia Etihad Etisalat mobile operator"),
    ("stc",              "stc",                  "purple gradient and white, stc logo, Saudi Telecom Company carrier"),
    ("ooredoo",          "Ooredoo",              "red and white, Ooredoo logo, Qatar MENA telecom, circular logo design"),
    ("etisalat",         "Etisalat",             "green and white, Etisalat e& logo, UAE Emirates telecom carrier"),
    ("du",               "du",                   "green and white, du logo, UAE Emirates telecom mobile carrier"),
    ("virginmobile",     "Virgin Mobile",        "red and white, Virgin Mobile logo, Richard Branson telecom brand"),
    ("friendi",          "FRiENDi Mobile",       "orange and white, FRiENDi Mobile logo, Oman Saudi Arabia budget carrier"),
    ("africell",         "Africell",             "yellow and blue, Africell logo, African mobile operator"),
    ("airtel",           "Airtel",               "red and white, Airtel logo, Indian telecom operator Bangladesh"),
    ("banglalink",       "Banglalink",           "orange and white, Banglalink logo, Bangladesh mobile operator"),
    ("grameenphone",     "Grameenphone",         "green and blue, Grameenphone GP logo, Bangladesh Telenor carrier"),
    ("afghanwireless",   "Afghan Wireless",      "blue and red, Afghan Wireless AWCC logo, Afghanistan telecom"),
    ("atoma",            "ATOMA",                "blue and white, ATOMA logo, Afghanistan mobile operator"),
    ("movicel",          "Movicel",              "blue and orange, Movicel logo, Angola mobile operator"),
    ("ais",              "AIS Thailand",         "green and white, AIS logo, Advanced Info Service Thai telecom"),
    ("airalo",           "Airalo",               "blue and white, Airalo logo, global eSIM marketplace platform"),
    ("syma",             "Syma Mobile",          "blue and orange, Syma Mobile logo, France MVNO budget carrier"),
    ("salam",            "Salam Mobile",         "purple and white, Salam Mobile logo, Saudi Arabia telecom"),
    ("orange",           "Orange Telecom",       "orange and white, Orange logo, international telecom carrier"),
]

# ── Утилиты ────────────────────────────────────────────────────────────────

def get_api_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if key:
        return key
    zshrc = Path.home() / ".zshrc"
    if zshrc.exists():
        text = zshrc.read_text()
        m = re.search(r'export OPENROUTER_API_KEY=["\']?([^"\'\n]+)["\']?', text)
        if m:
            return m.group(1)
    raise RuntimeError("OPENROUTER_API_KEY не найден ни в env, ни в ~/.zshrc")


def encode_image(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode()


def generate_bg(api_key: str, brand_name: str, description: str,
                ref1_b64: str, ref2_b64: str) -> bytes:
    prompt = (
        f"Create the same style image as these two references. "
        f"Make a gift card for {brand_name}. "
        f"{description}. "
        f"Same light blue gradient background, same angle, same 3D render. "
        f"IMPORTANT: No numbers, prices, barcodes. Only brand logo."
    )

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{ref1_b64}"}},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{ref2_b64}"}},
                    {"type": "text", "text": prompt},
                ],
            }
        ],
        "modalities": ["image", "text"],
        "image_config": {"aspect_ratio": "3:4", "image_size": "2K"},
    }

    r = requests.post(
        API_URL,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=payload,
        timeout=120,
    )
    if not r.ok:
        raise RuntimeError(f"HTTP {r.status_code}: {r.text[:300]}")

    data = r.json()
    msg = data["choices"][0]["message"]
    images = msg.get("images", [])
    if not images:
        raise RuntimeError(f"No images in response: {json.dumps(data)[:500]}")

    url = images[0]["image_url"]["url"]
    b64_data = url.split(",", 1)[1]
    return base64.b64decode(b64_data)


def save_image(img_bytes: bytes, out_path: Path):
    img = Image.open(io.BytesIO(img_bytes))
    if img.size != TARGET_SIZE:
        img = img.resize(TARGET_SIZE, Image.LANCZOS)
    img.save(out_path, "PNG", optimize=True)


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    REVIEW_DIR.mkdir(exist_ok=True)

    api_key = get_api_key()
    print(f"API key: {api_key[:8]}...")

    ref1_b64 = encode_image(REF1)
    ref2_b64 = encode_image(REF2)
    print(f"Референсы: {REF1.name}, {REF2.name}")
    print(f"Вывод → {REVIEW_DIR}\n")

    # Парсим аргументы: --limit N или список ключей
    args = sys.argv[1:]
    limit = BATCH_SIZE
    filter_keys = []

    i = 0
    while i < len(args):
        if args[i] == "--limit" and i + 1 < len(args):
            limit = int(args[i + 1])
            i += 2
        else:
            filter_keys.append(args[i])
            i += 1

    if filter_keys:
        todo = [(k, n, d) for k, n, d in BRANDS if k in filter_keys]
        print(f"Режим: конкретные бренды ({len(todo)} шт.) → {REVIEW_DIR.name}/")
    else:
        # Пропускаем уже готовые (есть в FINAL_DIR или REVIEW_DIR)
        already_done = {
            f.stem.replace("bg_", "")
            for f in list(FINAL_DIR.glob("bg_*.png")) + list(REVIEW_DIR.glob("bg_*.png"))
        }
        remaining = [(k, n, d) for k, n, d in BRANDS if k not in already_done]
        todo = remaining[:limit]
        total_left = len(remaining)
        print(f"Режим: батч {limit} шт. (осталось всего {total_left} / {len(BRANDS)})")
        if total_left > limit:
            print(f"Следующий батч: {remaining[limit][0]} ... {remaining[min(limit*2-1, total_left-1)][0]}")

    if not todo:
        print("Нечего генерировать — все файлы уже есть.")
        return

    print()
    ok_count = 0
    err_count = 0

    for idx, (key, name, desc) in enumerate(todo, 1):
        out_path = REVIEW_DIR / f"bg_{key}.png"
        print(f"[{idx}/{len(todo)}] {key} ({name})... ", end="", flush=True)
        try:
            img_bytes = generate_bg(api_key, name, desc, ref1_b64, ref2_b64)
            save_image(img_bytes, out_path)
            size_kb = out_path.stat().st_size // 1024
            print(f"✓ {size_kb}KB")
            ok_count += 1
        except Exception as e:
            print(f"✗ ERROR: {e}")
            err_count += 1

        if idx < len(todo):
            time.sleep(DELAY)

    print(f"\nГотово: {ok_count} OK, {err_count} ошибок")
    print(f"Смотри в: {REVIEW_DIR}")


if __name__ == "__main__":
    main()
