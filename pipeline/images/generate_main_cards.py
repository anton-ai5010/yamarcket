#!/usr/bin/env python3
"""
Генерация главных карточек товаров (1080x1440 PNG) через Pillow.
Новые карточки → output/main_cards_new/{бренд}/
Готовые (проверенные) → output/main_cards/{бренд}/

Запуск:
    python3 generate_main_cards.py                  # все отсутствующие
    python3 generate_main_cards.py --limit 5        # первые N
    python3 generate_main_cards.py --brand xbox     # только бренд
    python3 generate_main_cards.py --sku GFT1234    # один товар
"""
import json, re, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ── Пути ──────────────────────────────────────────────────────────────────
BASE       = Path("/media/anton/Новый том/yamarcket/pipeline/images")
REFS       = BASE / "references"
FLAGS_DIR  = REFS / "flags"
FONTS_DIR  = BASE / "fonts"
OUTPUT     = BASE / "output" / "main_cards"       # уже готовые
OUTPUT_NEW = BASE / "output" / "main_cards_new"   # новые (для проверки)
JSON_PATH  = Path("/media/anton/Новый том/yamarcket/new table/Онлайн-подписки и карты оплаты_истина_с_характеристиками.json")
LOGO_PATH  = REFS / "unnamed5_nobg_navy_hires.png"
FONT_PATH  = FONTS_DIR / "FiraSans-Bold.ttf"

# ── Размеры ───────────────────────────────────────────────────────────────
CW, CH   = 2160, 2880
S        = CW / 1728   # 1.25
FINAL_W  = 1080
FINAL_H  = 1440

# ── Цвета ─────────────────────────────────────────────────────────────────
DARK  = "#1E3A5F"
STEEL = "#4682B4"

# ── Позиции (Canva coords × S) ────────────────────────────────────────────
# Заголовок: два отдельных блока (из Canva DAHE-cb2fXI)
TITLE1_X     = int(109.21 * S)   # тип товара (ПОДАРОЧНАЯ КАРТА / ПОДПИСКА / ...)
TITLE1_Y     = int(49.86  * S)
TITLE2_X     = int(109.21 * S)   # название бренда (до 2 строк)
TITLE2_Y     = int(241.86 * S)
TITLE_MAX_W  = int(1511.70 * S)  # максимальная ширина обоих блоков
TITLE_LINE_H = int(192    * S)   # межстрочный интервал

# Номинал и валюта — общий центр X из Canva (335.03 * S)
NOM_CX = int(335 * S)   # общий центр для номинала и единицы (валюта/месяцы)
NOM_Y  = int(684 * S)
CUR_Y  = int(876 * S)
FLAG_X, FLAG_Y       = int(1315*S), int(1209*S)
FLAG_SIZE            = int(225*S)
CTR_X, CTR_Y, CTR_W = int(1234*S), int(1478*S), int(387*S)
BOTTOM_X, BOTTOM_Y  = int(109.21*S), int(1813*S)  # выровнено по TITLE1_X
BOTTOM_LINE_H        = int(80*S)
LOGO_X, LOGO_Y      = int(572*S), int(2015*S)
LOGO_W, LOGO_H      = int(583*S), int(232*S)

# ── Размеры шрифтов ───────────────────────────────────────────────────────
SZ_TITLE   = int(120 * (4/3) * S)  # 120pt Canva × 96dpi(4/3) × S=1.25 → 200px
SZ_NOM     = int(160 * S)
SZ_CUR     = int(133 * S)
SZ_CUR_SM  = int(133 * S * 0.8)  # для МЕСЯЦ/МЕСЯЦА/МЕСЯЦЕВ (-20%)
SZ_CUR_XSM = int(133 * S * 0.64) # для очень длинных слов типа DIAMONDS (-40%)
SZ_SMALL   = int(63  * S)
SZ_SMALL_SM = int(63 * S * 0.7)  # для длинных названий стран типа ВЕЛИКОБРИТАНИЯ (-30%)

# ── Маппинг бренд (JSON) → ключ bg-файла ──────────────────────────────────
BRAND_TO_BG = {
    "Sony": "playstation",
    "Microsoft": "xbox",
    "Valve": "steam",
    "Google": "googleplay",
    "Apple": "apple",
    "Amazon": "amazon",
    "Nintendo": "nintendo",
    "Roblox Corporation": "roblox",
    "Riot Games": "leagueoflegends",
    "Razer": "razer",
    "Spotify": "spotify",
    "Netflix": "netflix",
    "Disney": "disney",
    "HBO": "hbo",
    "Meta": "meta",
    "Tencent Games": "tencent",
    # Apple регионы
    **{f"Apple Gift Card | {c}": "apple"
       for c in ["AE","AT","AU","BE","DE","ES","FI","FR","IE","IT","JP","LU","NL","PL","PT","SA","UK","US"]},
    # Battle.net
    **{f"Battle.net Gift Card | {c}": "battlenet" for c in ["BR","CA","EU","MX","PL","UK","US"]},
    **{f"Battle.net gift card | {c}": "battlenet" for c in ["MY","SG","TH"]},
    # Fortnite
    "Fortnite": "fortnite",
    **{f"Fortnite Gift Card | {c}": "fortnite" for c in ["AE","EU","SA","UK","US"]},
    # Valorant
    **{f"Valorant Gift Card | {c}": "valorant" for c in ["AU","BR","EU","RU","TR","UK","US"]},
    # Riot Cash
    **{f"Riot Cash Card | {c}": "riot" for c in ["AE","BH","BR","EU","KW","LATAM","SA","TR","UK","US"]},
    "2XKO Gift Card | TR": "riot",
    # PaysafeCard
    **{f"PaysafeCard | {c}": "paysafecard" for c in ["AE","DE","ES","FR","NL","PT","UK"]},
    # Neosurf
    **{f"Neosurf | {c}": "neosurf" for c in ["AU","CA","EU","UK"]},
    # MiFinity
    "MiFinity Voucher | NO": "mifinity",
    "MiFinity eVoucher EUR": "mifinity",
    "MiFinity eVoucher USD": "mifinity",
    # Rewarble
    "Rewarble": "rewarble",
    "Rewarble Gift Card EUR": "rewarble",
    "Rewarble Gift Card USD": "rewarble",
    # Eneba / Kinguin
    "Eneba Gift Card | EUR": "eneba",
    "Eneba Gift Card | USD": "eneba",
    "Kinguin Gift Card | EU": "kinguin",
    # Twitch
    **{f"Twitch Gift Card | {c}": "twitch" for c in ["EU","UK","US"]},
    # Vodafone
    **{f"Vodafone {c}": "vodafone" for c in ["Albania","Egypt","Germany","Italy","Portugal","Romania","Spain"]},
    "Vodafone Voucher | NL": "vodafone", "Vodafone Voucher | QA": "vodafone",
    "Vodafone | DE": "vodafone", "Vodafone | UK": "vodafone",
    # Orange
    **{f"Orange {c}": "orange" for c in ["Botswana","Egypt","Romania","Spain"]},
    "Orange Voucher | BE": "orange", "Orange Voucher | FR": "orange",
    "Orange Voucher | JO": "orange", "Orange | LU": "orange",
    # O2
    "O2 Czech Republic": "o2", "O2 Germany": "o2", "O2 | DE": "o2", "O2 | UK": "o2",
    # Three
    "Three | IE": "three", "Three | UK": "three",
    # Lyca
    **{f"Lyca Mobile {c}": "lyca" for c in ["France","Italy","Portugal","Spain"]},
    **{f"Lyca Mobile Voucher | {c}": "lyca" for c in ["AT","BE","DE","FR","IE","IT","NL","UK"]},
    # Red Bull Mobile
    "Red Bull Mobile Voucher | OM": "redbullmobile",
    "Red Bull Mobile Voucher | SA": "redbullmobile",
    # DIGI
    "DIGI Italy": "digi", "DIGI Spain": "digi",
    # Claro / Unitel / Alou / Roshan
    "Claro Argentina": "claro", "Claro Brazil": "claro",
    "Unitel Angola": "unitelt", "Unitel T+ Cape Verde": "unitelt",
    "Alou Cape Verde": "alou",
    "Roshan Afghanistan": "roshan",
    # Delta Force
    "Delta Force Mobile Top Up":               "deltaforcemobile",
    "Delta Force Mobile Top Up MENA (Garena)": "deltaforcemobile",
    "Delta Force Mobile Top Up SEA (Garena)":  "deltaforcemobile",
    "Delta Force Voucher (Garena)":            "deltaforcemobile",
    "Delta Force Voucher (Midasbuy)":          "deltaforce",
    # Мобильные игры
    "Mobile Legends: Bang Bang Top Up ID": "mobilelegends",
    "Mobile Legends: Bang Bang Top Up PH": "mobilelegends",
    "Mobile Legends: Bang Bang Voucher": "mobilelegends",
    "Honor of Kings Gift Card": "honorofkings",
    "Honor of Kings Top Up": "honorofkings",
    "Bigo Live Gift Card": "bigolive",
    "Bigo Live Topup": "bigolive",
    "imo Gift Code": "imo",
    "Destiny: Rising Top Up": "destinyrising",
    "Dragonheir: Silent Gods": "dragonheir",
    "Call of Duty® Points": "callofduty",
    "PUBG Mobile Gift Card": "pubgmobile",
    "Free Fire Gift Card": "freefire",
    "Genshin Impact Top Up": "genshin",
    "Zenless Zone Zero Top Up": "zenlesszonezero",
    "Blood Strike Top Up": "bloodstrike",
    "Blood Strike Top Up (MENA)": "bloodstrike",
    "Magic Chess: Go Go": "magicchess",
    "Castle Clash: World Ruler": "castleclash",
    "Black Clover M Gift Card": "blackcloverm",
    "Doomsday: Last Survivors Gift Card": "doomsday",
    "Doomsday: Last Survivors Top Up": "doomsday",
    "Identity V Top Up": "identityv",
    "New State Mobile Gift Card": "newstatemobile",
    "Undawn gift card": "undawn",
    "Lords Mobile Gift Card": "lordsmobile",
    "AFK Journey": "afkjourney",
    # Прочие платёжные
    "CASHlib Voucher | EU": "cashlib", "CASHlib Voucher | NO": "cashlib",
    "Flexepin | EU": "flexepin",
    "Openbucks Gift Card": "openbucks",
    "iCash.One Voucher USD": "icash",
    "S1lkPay Voucher": "silkpay",
    "True Money Cash Card": "truemoney",
    "R2Games": "r2games",
    "Discounty | GL": "discounty",
    "Jawaker Token": "jawaker",
    "Salik eVoucher | AE": "salik",
    "PhonePE Voucher": "phonepe",
    # Стриминг / подписки
    "Crunchyroll Premium": "crunchyroll",
    "Deezer Premium": "deezer",
    "Blu TV | TR": "blutv",
    "Exxen | TR": "exxen",
    "Weyyak": "weyyak",
    "Blacknut Gift Card": "blacknut",
    "World of Warcraft | US": "worldofwarcraft",
    "The Elder Scrolls Online": "elderscrollsonline",
    "The Elder Scrolls Online | GL": "elderscrollsonline",
    "Old School RuneScape | GL": "runescape",
    "RuneScape Membership": "runescape",
    "RuneScape | GL": "runescape",
    "EA Gift Card | EU": "ea", "EA Gift Card | USA": "ea",
    "Overwatch® 2": "overwatch",
    "Garena Voucher": "garena",
    "NetEase Games Pay Card": "netease",
    "SEAGM Gift Card": "seagm",
    "Cherry Credits Gift Card": "cherrycredits",
    "Travian Legends": "travian",
    "JetonCash": "jetoncash",
    # Сервисы
    "Discord Gift Card": "discord",
    "TikTok": "tiktok",
    "Skype Gift Card | AU": "skype",
    "Adobe Digital Code": "adobe",
    "Bitdefender Subscription": "bitdefender",
    "Voicemod": "voicemod",
    **{f"ExitLag Gift Card | Tier {n}": "exitlag" for n in [1, 2, 3]},
    "NoPing": "noping",
    "CapCut Basic Membership | EU": "capcut",
    "CapCut Basic Membership | US": "capcut",
    "Hulu Gift Card | US": "hulu",
    # Ритейл
    "Uber": "uber",
    "airbnb Gift Card | US": "airbnb",
    "eBay Gift Card": "ebay",
    "SHEIN Gift Card | GCC": "shein",
    "H&M | US": "hm",
    "Nike gift card | US": "nike",
    "Victoria's Secret Gift Card": "victoriassecret",
    "Walmart gift card": "walmart",
    "Abercrombie & Fitch Gift Card": "abercrombie",
    "Talabat Gift Card": "talabat",
    "Deliveroo Gift Card | AE": "deliveroo",
    "Tinder gift card | BR": "tinder",
    "Tango Live Voucher": "tango",
    "noon gift card | AE": "noon", "noon gift card | SA": "noon",
    "HUAWEI Gift Card | AE": "huawei",
    # Операторы
    "AT&T Prepaid Voucher | US": "att",
    "T-Mobile Germany": "tmobile",
    "EE Mobile | UK": "ee",
    "KPN Mobile Voucher | NL": "kpn",
    "Proximus Voucher | BE": "proximus",
    "Bouygues | FR": "bouygues",
    "Movistar Argentina": "movistar",
    "Vivo Brazil": "vivo",
    "China Mobile China": "chinamobile",
    "A1 Voucher | AT": "a1",
    "AY YILDIZ Germany": "ayayildiz",
    "Base Voucher | BE": "base",
    "BASE Mobile Germany": "base",
    "Batelco Voucher | BH": "batelco",
    "Bhutan Telecom Bhutan": "bhutantelecom",
    "Blau Germany": "blau", "Blau Voucher | DE": "blau",
    "btc Botswana": "btc",
    "China Telecom China": "chinatelecom",
    "China Unicom China": "chinaunicom",
    "Congstar Germany": "congstar",
    "Djezzy Algeria": "djezzy",
    "Econet Burundi": "econet",
    "eir Mobile | IE": "eir",
    "Epic Cyprus": "epic",
    "Ethio Telecom Ethiopia": "ethiotelecom",
    "Euskaltel Spain": "euskaltel",
    "FYVE Germany": "fyve",
    "Five VoIP eVoucher | AE": "fivevoip",
    "Hello! VoIP Voucher | AE": "hellovoip",
    "ho. Mobile Italy": "homobile",
    "iliad Italy": "iliad",
    "JIM Mobile Voucher | BE": "jimmobile",
    "Kena Mobile Italy": "kenamobile",
    "Lucky Mobile Voucher | BH": "luckymobile",
    "Magenta Voucher | AT": "magenta",
    "Mascom Botswana": "mascom",
    "MASMOVIL Spain": "masmovil",
    "Mobilis Algeria": "mobilis",
    "Now Mobile Voucher | UK": "nowmobile",
    "Omantel Voucher | OM": "omantel",
    "Ortel Mobile Germany": "ortel",
    "Otelo Germany": "otelo",
    "Personal Argentina": "personal",
    "Renna Mobile Voucher | OM": "rennamobile",
    "Robi Bangladesh": "robi",
    "Safaricom Ethiopia": "safaricom",
    "Simyo Spain": "simyo",
    "Tele2 Lithuania": "tele2",
    "Telekom Romania": "telekom",
    "Teletalk Bangladesh": "teletalk",
    "TIM Brazil": "tim", "TIM Italy": "tim",
    "Tiscali Italy": "tiscali",
    "Tuenti Argentina": "tuenti",
    "Umniah Voucher | JO": "umniah",
    "Very Mobile Italy": "verymobile",
    "WINDTRE Italy": "windtre",
    "Windtre Italy": "windtre",
    "Yoigo Spain": "yoigo",
    "YouMobile Spain": "youmobile",
    "Algar Telecom Brazil": "algar",
    "Drei Voucher | AT": "drei",
}

# ── Игры/DLC — пропускаем ──────────────────────────────────────────────────
GAME_KEYWORDS = [
    'Age of ', 'American Truck', 'Apex Legends', 'Arizona Sunshine', 'Arma ',
    "Assassin's Creed", "Assassins Creed", 'Assetto', 'Atomic Heart', 'Avatar:',
    'Battlefield', 'Beyond:', 'Borderlands', 'Bully:', 'Clair Obscur',
    'Crusader Kings', 'DARK SOULS', 'DEATHLOOP', 'DOOM', 'DayZ', 'Dead Cells',
    'Dead Island', 'Dead Rising', 'Desperados', 'Destiny 2 |', 'Diablo® IV',
    'Digimon', 'Disco Elysium', 'Dishonored', 'Dying Light', 'EA SPORTS',
    'ELDEN RING', 'Euro Truck', 'FATAL FRAME', 'FINAL FANTASY', 'Fallout 3',
    'Fallout 4', 'Fallout 76', 'Fallout: New Vegas', 'Fallout® Classic',
    'Farming Simulator', 'For The King', 'GTA Online', 'Grand Theft Auto V',
    'Garden Simulator', 'Ghost of Tsushima', 'Ghostwire:', 'HELLDIVERS',
    'Halo Infinite', 'Hell is Us', 'Hellblade:', 'Heretic + Hexen',
    'Hollow Knight:', 'Immortals Fenyx', 'Indiana Jones', 'Just Cause',
    'Jump Space', 'Kao the Kangaroo', 'Killing Floor', 'King of Meat',
    'Kingdom Come:', 'LEGO®', 'Laika:', 'Life is Strange', 'Lost in Random',
    'OCTOPATH', 'Mafia:', 'Marathon |', "Marvel's Midnight", 'Max Payne',
    'Metro Awakening', 'Metro Exodus', 'Microsoft Flight Simulator',
    'Midnight Murder', 'Minecraft', 'Monster Hunter', 'MySims', 'NBA 2K',
    'NHL®', 'Ninja Gaiden', 'PUBG: BATTLEGROUNDS', 'PAC-MAN', 'Planet Zoo',
    'Planet of Lana', 'Plants vs. Zombies™: Replanted', 'Pokémon™', 'Prey |',
    'REANIMAL', 'REMATCH', 'REMNANT', 'RIDE ', 'Ready or Not',
    'Red Dead Redemption', 'Resident Evil', 'RimWorld', 'SCUM |',
    'SILENT HILL f', 'Say No!', 'Sea of Thieves', 'Skull and Bones',
    'Smalland:', 'Split Fiction', 'Squad |', 'Star Fire:', 'Starfield',
    'Still Wakes', 'Street Fighter', 'Stronghold Crusader', 'Super Street:',
    'TEKKEN', 'TT Isle of Man', 'Terraforming Mars', 'Terraria', 'The Crew™',
    'The Elder Scrolls III:', 'The Elder Scrolls IV:', 'The Elder Scrolls V:',
    'The First Berserker', 'The Forever Winter', 'The Last of Us',
    'The Lord of the Rings:', 'The Outer Worlds 2', 'The Settlers',
    'The Sims™ 4', "Tom Clancy's", 'Tormented Souls', 'Train Sim World',
    'V Rising', 'VOID/BREAKER', 'Vampire: The Masquerade', 'WUCHANG:',
    'WWE 2K', 'Warhammer 40,000:', 'Wavetale', 'White Shadows', 'Wolfenstein',
    'skate.™', 'ARC Raiders', 'ASKA |', '7 Days to Die', 'Onimusha',
    'Outlast 2', 'Call of Duty®: Black Ops 7',
]

NAME_GAME_MARKERS = [
    'игра в электронном формате', 'ключ steam', 'steam key',
    'ключ активации', 'игровой ключ', 'pc game',
]

def is_game(brand: str, name: str = "") -> bool:
    if any(brand.startswith(kw) for kw in GAME_KEYWORDS):
        return True
    name_lower = name.lower()
    return any(m in name_lower for m in NAME_GAME_MARKERS)


# ── Вспомогательные функции ────────────────────────────────────────────────

def get_bg_key(brand: str, name: str = "") -> str:
    # Apple: разбиваем по имени товара
    clean_brand = re.sub(r'\s*\|.*$', '', brand).strip()
    if clean_brand in ("Apple", "Apple Gift Card"):
        if 'iTunes,App Store' in name or ('App Store' in name and 'iTunes' not in name):
            return "appstore"
        return "itunes"
    if brand in BRAND_TO_BG:
        return BRAND_TO_BG[brand]
    key = re.sub(r'\s*\|.*$', '', brand.lower())
    key = re.sub(r'\s+(gift card|top up|voucher|mobile|telecom|wireless)$', '', key)
    key = re.sub(r'[^a-z0-9]', '', key)
    return key


def get_sku(row: list) -> str:
    raw = row[0]
    if isinstance(raw, float):
        return f"GFT{int(raw)}"
    return f"GFT{str(raw).replace('GFT', '')}"


def territory_slug(territory: str) -> str:
    TR = {'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'yo','ж':'zh',
          'з':'z','и':'i','й':'y','к':'k','л':'l','м':'m','н':'n','о':'o',
          'п':'p','р':'r','с':'s','т':'t','у':'u','ф':'f','х':'kh','ц':'ts',
          'ч':'ch','ш':'sh','щ':'shch','ъ':'','ы':'y','ь':'','э':'e','ю':'yu','я':'ya'}
    result = ""
    for ch in territory.lower():
        if ch in TR:
            result += TR[ch]
        elif ch.isascii() and ch.isalnum():
            result += ch
        elif ch in (' ', '_', '-'):
            result += '_'
    return result[:25] or "world"


def center_x(draw, text, font, box_x, box_w):
    tw = int(draw.textlength(text, font=font))
    return box_x + max(0, (box_w - tw) // 2)


def make_flag(territory: str, country_map: dict) -> Image.Image:
    flag_key = country_map.get(territory, "global")
    flag_path = FLAGS_DIR / f"{flag_key}.png"
    if not flag_path.exists():
        flag_path = FLAGS_DIR / "global.png"
    flag = Image.open(flag_path).convert("RGBA").resize((FLAG_SIZE, FLAG_SIZE), Image.LANCZOS)
    mask = Image.new("L", (FLAG_SIZE, FLAG_SIZE), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, FLAG_SIZE-1, FLAG_SIZE-1), fill=255)
    circle = Image.new("RGBA", (FLAG_SIZE, FLAG_SIZE), (0, 0, 0, 0))
    circle.paste(flag, (0, 0), mask)
    return circle


BRAND_DISPLAY_OVERRIDE = {
    "Google":                                "GOOGLE PLAY",
    "Riot Games":                            "LEAGUE OF LEGENDS",
    "Valve":                                 "STEAM WALLET",
    "Sony":                                  "PLAYSTATION",
    "Adobe Digital Code":                    "ADOBE",
    "China Mobile China":                    "CHINA MOBILE",
    "China Telecom China":                   "CHINA TELECOM",
    "China Unicom China":                    "CHINA UNICOM",
    "Delta Force Mobile Top Up":             "DELTA FORCE MOBILE",
    "Delta Force Mobile Top Up MENA (Garena)": "DELTA FORCE MOBILE",
    "Delta Force Mobile Top Up SEA (Garena)":  "DELTA FORCE MOBILE",
    "Delta Force Voucher (Garena)":          "DELTA FORCE MOBILE",
    "Delta Force Voucher (Midasbuy)":        "DELTA FORCE",
}

def brand_display_from_name(brand: str, name: str) -> str:
    """Для Microsoft/Apple определяем отображение по названию товара."""
    clean = re.sub(r'\s*\|.*$', '', brand).strip()
    if clean in ("Apple", "Apple Gift Card"):
        if 'iTunes,App Store' in name or ('App Store' in name and 'iTunes' not in name):
            return "APP STORE"
        return "ITUNES"
    if clean == "Microsoft":
        n = name.lower()
        if 'ea play' in n:
            return "EA PLAY"
        if 'game pass ultimate' in n:
            return "XBOX GAME PASS ULTIMATE"
        if 'game pass core' in n:
            return "XBOX GAME PASS CORE"
        if 'pc game pass' in n:
            return "PC GAME PASS"
        if 'game pass' in n:
            return "XBOX GAME PASS"
        return "XBOX"
    return brand_display(brand)


def brand_display(brand: str) -> str:
    clean = re.sub(r'\s*\|.*$', '', brand).strip()
    if clean in BRAND_DISPLAY_OVERRIDE:
        return BRAND_DISPLAY_OVERRIDE[clean]
    for s in [' Gift Card', ' Top Up', ' Topup', ' Voucher', ' Mobile',
              ' Telecom', ' Wireless', ' Prepaid', ' Membership', ' Premium',
              ' Subscription', ' Corporation', ' Games', ' Botswana',
              ' Albania', ' Egypt', ' Germany', ' Italy', ' Portugal',
              ' Romania', ' Spain', ' Brazil', ' Argentina', ' Algeria',
              ' Ethiopia', ' Bangladesh', ' Lithuania',
              ' Digital Code']:
        clean = clean.replace(s, '')
    return clean.strip().upper()


# Бренд → название игровой валюты
BRAND_TO_GAME_CURRENCY = {
    "Call of Duty® Points":                  "POINTS",
    "Roblox Corporation":                    "ROBUX",
    "Fortnite":                              "V-BUCKS",
    "Mobile Legends: Bang Bang Top Up ID":   "DIAMONDS",
    "Mobile Legends: Bang Bang Top Up PH":   "DIAMONDS",
    "Mobile Legends: Bang Bang Voucher":     "DIAMONDS",
    "Honor of Kings Gift Card":              "TOKENS",
    "Honor of Kings Top Up":                 "TOKENS",
    "Bigo Live Gift Card":                   "DIAMONDS",
    "Bigo Live Topup":                       "DIAMONDS",
    "imo Gift Code":                         "COINS",
    "Delta Force Mobile Top Up":             "DELTA COINS",
    "Delta Force Mobile Top Up MENA (Garena)": "DELTA COINS",
    "Delta Force Mobile Top Up SEA (Garena)":  "DELTA COINS",
    "Delta Force Voucher (Garena)":          "DELTA COINS",
    "Delta Force Voucher (Midasbuy)":        "DELTA COINS",
    "Destiny: Rising Top Up":               "COINS",
    "Dragonheir: Silent Gods":              "GEMS",
    "PUBG Mobile Gift Card":                "UC",
    "Free Fire Gift Card":                  "DIAMONDS",
    "Genshin Impact Top Up":                "CRYSTALS",
    "Zenless Zone Zero Top Up":             "POLYCHROME",
    "Blood Strike Top Up":                  "GOLD",
    "Blood Strike Top Up (MENA)":           "GOLD",
    "Magic Chess: Go Go":                   "DIAMONDS",
    "Castle Clash: World Ruler":            "GEMS",
    "Black Clover M Gift Card":             "GEMS",
    "Doomsday: Last Survivors Gift Card":   "GEMS",
    "Doomsday: Last Survivors Top Up":      "GEMS",
    "Identity V Top Up":                    "CLUES PACKAGE",
    "New State Mobile Gift Card":           "NC",
    "Undawn gift card":                     "GOLD",
    "Lords Mobile Gift Card":               "GEMS",
    "AFK Journey":                          "DIAMONDS",
    "Arena Breakout":                       "COINS",
    "Garena Voucher":                       "SHELLS",
    "NetEase Games Pay Card":               "COINS",
    "SEAGM Gift Card":                      "CREDITS",
    "Cherry Credits Gift Card":             "CC",
    "R2Games":                              "COINS",
    "Jawaker Token":                        "TOKENS",
    "Tango Live Voucher":                   "COINS",
}

# Бренды которые являются игровой валютой (для determine_type)
GAME_CURRENCY_BRANDS = set(BRAND_TO_GAME_CURRENCY.keys())


def determine_type(row: list) -> str:
    nominal  = row[46] if len(row) > 46 else None
    duration = row[47] if len(row) > 47 else None
    brand    = str(row[10] or "").strip() if len(row) > 10 else ""
    name     = str(row[6]  or "").lower()
    game_cur_kw = ['robux', 'v-buck', 'vbuck', ' vp', 'fc point', 'coins',
                   'gems', 'diamonds', ' tokens', 'credits', 'points', 'top up']
    if brand in GAME_CURRENCY_BRANDS:
        return "game_currency"
    if any(c in name for c in game_cur_kw):
        return "game_currency"
    nom_str = str(nominal).strip() if nominal else ""
    dur_str = str(duration).strip() if duration else ""
    if nom_str and nom_str not in ('None', '99 лет', ''):
        return "gift_card"
    if dur_str and dur_str not in ('None', '99 лет', ''):
        return "subscription"
    return "gift_card"


TERRITORY_TO_CURRENCY = {
    "США": "USD", "US": "USD", "USA": "USD",
    "ОАЭ": "AED", "AE": "AED",
    "Саудовская Аравия": "SAR", "SA": "SAR",
    "Турция": "TRY", "TR": "TRY",
    "Великобритания": "GBP", "UK": "GBP",
    "Япония": "JPY", "JP": "JPY",
    "Австралия": "AUD", "AU": "AUD",
    "Канада": "CAD", "CA": "CAD",
    "Бразилия": "BRL", "BR": "BRL",
    "Мексика": "MXN", "MX": "MXN",
    "Польша": "PLN", "PL": "PLN",
    "Швейцария": "CHF", "CH": "CHF",
    "Швеция": "SEK", "SE": "SEK",
    "Норвегия": "NOK", "NO": "NOK",
    "Дания": "DKK", "DK": "DKK",
    "Румыния": "RON", "RO": "RON",
    "Венгрия": "HUF", "HU": "HUF",
    "Чехия": "CZK", "CZ": "CZK",
    "Индия": "INR", "IN": "INR",
    "Сингапур": "SGD", "SG": "SGD",
    "Гонконг": "HKD", "HK": "HKD",
    "Тайвань": "TWD", "TW": "TWD",
    "Таиланд": "THB", "TH": "THB",
    "Малайзия": "MYR", "MY": "MYR",
    "Индонезия": "IDR", "ID": "IDR",
    "Филиппины": "PHP", "PH": "PHP",
    "Вьетнам": "VND", "VN": "VND",
    "ЮАР": "ZAR", "ZA": "ZAR",
    "Кувейт": "KWD", "KW": "KWD",
    "Катар": "QAR", "QA": "QAR",
    "Оман": "OMR", "OM": "OMR",
    "Бахрейн": "BHD", "BH": "BHD",
    "Иордания": "JOD", "JO": "JOD",
    "Ливан": "LBP", "LB": "LBP",
    "Аргентина": "ARS", "AR": "ARS",
    "Колумбия": "COP", "CO": "COP",
    "Чили": "CLP", "CL": "CLP",
    "Нигерия": "NGN", "NG": "NGN",
    "Грузия": "GEL", "GE": "GEL",
    "Украина": "UAH", "UA": "UAH",
    "Алжир": "DZD", "DZ": "DZD",
    "Египет": "EGP", "EG": "EGP",
    "Ирак": "IQD", "IQ": "IQD",
    "Китай": "CNY", "CN": "CNY",
    "Южная Корея": "KRW", "KR": "KRW",
    "Новая Зеландия": "NZD", "NZ": "NZD",
    "Европа": "EUR", "EU": "EUR",
    "все страны": "USD", "GL": "USD",
}


def extract_game_currency_label(row: list) -> str:
    brand = str(row[10] or "").strip() if len(row) > 10 else ""
    return BRAND_TO_GAME_CURRENCY.get(brand, "COINS")


def extract_nominal_currency(row: list) -> tuple:
    nominal = row[46] if len(row) > 46 else None
    name = str(row[6] or "")
    territory = str(row[48] or "").strip().replace('\n', ' ') if len(row) > 48 else ""
    currencies = ['USD','EUR','GBP','AED','TRY','SAR','JPY','INR','BRL','MXN',
                  'AUD','CAD','PLN','CHF','SEK','NOK','DKK','HUF','CZK','RON',
                  'ALL','DZD','BDT','BTN','BWP','EGP','ETB','IQD','JOD','KWD',
                  'LBP','OMR','PHP','QAR','SGD','THB','TWD','VND','ZAR','GEL',
                  'UAH','ARS','CLP','COP','MYR','IDR','NGN','HKD','TWD','KRW',
                  'CNY','NZD','BHD','KWD','BDT','NGN']
    currency = next((c for c in currencies if c in name), "")
    # Фолбек по территории
    if not currency and territory:
        currency = TERRITORY_TO_CURRENCY.get(territory, "")
    # Финальный фолбек — USD
    if not currency:
        currency = "USD"
    nom_str = ""
    if nominal and str(nominal).strip() not in ('', 'None'):
        try:
            n = float(str(nominal))
            nom_str = str(int(n)) if n == int(n) else f"{n:.0f}"
        except Exception:
            nom_str = str(nominal)
    return nom_str, currency


def extract_duration(row: list) -> tuple:
    dur = str(row[47] or "") if len(row) > 47 else ""
    m = re.match(r'(\d+)\s*(месяц|год|лет|day|month|year)', dur.lower())
    if not m:
        return "", ""
    n, unit = int(m.group(1)), m.group(2)
    if 'год' in unit or 'year' in unit:
        label = "ГОД" if n == 1 else ("ГОДА" if 2 <= n <= 4 else "ЛЕТ")
    else:
        label = "МЕСЯЦ" if n == 1 else ("МЕСЯЦА" if 2 <= n <= 4 else "МЕСЯЦЕВ")
    return str(n), label


# ── Рендер одной карточки ─────────────────────────────────────────────────

def render_card(row: list, bg_key: str, logo: Image.Image,
                fonts: dict, country_map: dict) -> Image.Image:
    brand     = str(row[10] or "").strip()
    name      = str(row[6]  or "")
    territory = str(row[48] or "все страны").replace('\n', ' ').strip() if len(row) > 48 else "все страны"
    ctype     = determine_type(row)
    bname     = brand_display_from_name(brand, name)

    bg_path = REFS / f"bg_{bg_key}.png"
    if not bg_path.exists():
        bg_path = REFS / "bg_clean.png"
    bg   = Image.open(bg_path).convert("RGBA").resize((CW, CH), Image.LANCZOS)
    flag = make_flag(territory, country_map)

    card = bg.copy()
    card.paste(flag, (FLAG_X, FLAG_Y), flag)
    draw = ImageDraw.Draw(card)

    # ── Блок 1: тип товара (одна строка, тёмный) ──────────────────────────
    TYPE_LABEL = {
        "gift_card":     "ПОДАРОЧНАЯ КАРТА",
        "subscription":  "ПОДПИСКА",
        "game_currency": "ИГРОВАЯ ВАЛЮТА",
    }
    type_text  = TYPE_LABEL.get(ctype, "ПОДАРОЧНАЯ КАРТА")
    title_font = fonts['title']
    draw.text((TITLE1_X, TITLE1_Y), type_text, font=title_font, fill=DARK)

    # ── Блок 2: название бренда (до 2 строк, стальной синий) ──────────────
    # Авто-подгонка шрифта под ширину
    brand_font = fonts['title']
    sz = SZ_TITLE
    while sz > int(SZ_TITLE * 0.5):
        if int(draw.textlength(bname, font=brand_font)) <= TITLE_MAX_W:
            break
        sz -= 4
        brand_font = ImageFont.truetype(str(FONT_PATH), sz)

    # Разбивка на 2 строки если не влезает в одну
    if int(draw.textlength(bname, font=brand_font)) <= TITLE_MAX_W:
        draw.text((TITLE2_X, TITLE2_Y), bname, font=brand_font, fill=STEEL)
    else:
        words = bname.split()
        mid   = max(1, len(words) // 2)
        line1 = " ".join(words[:mid])
        line2 = " ".join(words[mid:])
        draw.text((TITLE2_X, TITLE2_Y),               line1, font=brand_font, fill=STEEL)
        draw.text((TITLE2_X, TITLE2_Y + TITLE_LINE_H), line2, font=brand_font, fill=STEEL)

    # Номинал / срок
    if ctype == "subscription":
        num_str, unit_str = extract_duration(row)
    elif ctype == "game_currency":
        num_str, _ = extract_nominal_currency(row)
        unit_str   = extract_game_currency_label(row)
    else:
        num_str, unit_str = extract_nominal_currency(row)

    if num_str:
        tw = int(draw.textlength(num_str, font=fonts['nominal']))
        draw.text((NOM_CX - tw // 2, NOM_Y), num_str, font=fonts['nominal'], fill=STEEL)
    if unit_str:
        XSMALL_UNIT_WORDS = ('DIAMONDS',)
        SMALL_UNIT_WORDS  = ('МЕСЯЦ', 'МЕСЯЦА', 'МЕСЯЦЕВ') + tuple(BRAND_TO_GAME_CURRENCY.values())
        if unit_str in XSMALL_UNIT_WORDS:
            unit_font = fonts['currency_xsmall']
        elif unit_str in SMALL_UNIT_WORDS:
            unit_font = fonts['currency_small']
        else:
            unit_font = fonts['currency']
        unit_lh   = int(unit_font.size * 1.1)
        # Многословные метки (напр. "DELTA COINS") — каждое слово на своей строке
        words = unit_str.split()
        if len(words) > 1:
            for i, word in enumerate(words):
                tw = int(draw.textlength(word, font=unit_font))
                draw.text((NOM_CX - tw // 2, CUR_Y + i * unit_lh), word, font=unit_font, fill=DARK)
        else:
            tw = int(draw.textlength(unit_str, font=unit_font))
            draw.text((NOM_CX - tw // 2, CUR_Y), unit_str, font=unit_font, fill=DARK)

    # Страна под флагом (многословные — каждое слово на своей строке)
    ter_upper = territory.upper()
    ter_words = ter_upper.split()
    # Длинные слова (>10 символов) рендерим уменьшенным шрифтом -30%
    ter_font  = fonts['small_sm'] if any(len(w) > 10 for w in ter_words) else fonts['small']
    ter_lh    = int(ter_font.size * 1.15)
    for i, word in enumerate(ter_words):
        cx = center_x(draw, word, ter_font, CTR_X, CTR_W)
        draw.text((cx, CTR_Y + i * ter_lh), word, font=ter_font, fill=DARK)

    # Нижний текст
    for i, line in enumerate([f"ПОДХОДИТ ДЛЯ АККАУНТОВ {ter_upper}",
                               "МГНОВЕННАЯ ЦИФРОВАЯ ДОСТАВКА"]):
        draw.text((BOTTOM_X, BOTTOM_Y + i * BOTTOM_LINE_H), line, font=fonts['small'], fill=DARK)

    # Логотип
    card.paste(logo, (LOGO_X, LOGO_Y), logo)
    return card


# ── Main ──────────────────────────────────────────────────────────────────

def load_resources():
    logo = Image.open(LOGO_PATH).convert("RGBA").resize((LOGO_W, LOGO_H), Image.LANCZOS)
    fonts = {
        'title':    ImageFont.truetype(str(FONT_PATH), SZ_TITLE),
        'nominal':  ImageFont.truetype(str(FONT_PATH), SZ_NOM),
        'currency':       ImageFont.truetype(str(FONT_PATH), SZ_CUR),
        'currency_small':  ImageFont.truetype(str(FONT_PATH), SZ_CUR_SM),
        'currency_xsmall': ImageFont.truetype(str(FONT_PATH), SZ_CUR_XSM),
        'small':    ImageFont.truetype(str(FONT_PATH), SZ_SMALL),
        'small_sm': ImageFont.truetype(str(FONT_PATH), SZ_SMALL_SM),
    }
    with open(FLAGS_DIR / "country_to_flag.json", encoding="utf-8") as f:
        country_map = json.load(f)
    # Дополнительные страны
    country_map.update({
        "Кабо-Верде": "cape_verde", "Ботсвана": "botswana",
        "Эфиопия": "ethiopia", "Алжир": "algeria",
        "Королевство Бутан": "bhutan", "Бангладеш": "bangladesh",
        "Кипр": "cyprus", "Афганистан": "afghanistan",
        "Ангола": "angola", "Бурунди": "burundi",
        "Албания": "albania", "Литва": "lithuania",
        "СНГ": "russia", "Страны Персидского залива": "global",
        "Российская Федерация + страны СНГ": "russia",
    })
    return logo, fonts, country_map


def load_existing_skus() -> set:
    skus = set()
    for f in OUTPUT.rglob("*.png"):
        m = re.match(r'(GFT\d+)', f.stem)
        if m:
            skus.add(m.group(1))
    return skus


def save_card(card: Image.Image, bg_key: str, sku: str, territory: str,
              out_root: Path = None) -> Path:
    if out_root is None:
        out_root = OUTPUT_NEW
    brand_dir = out_root / bg_key
    brand_dir.mkdir(parents=True, exist_ok=True)
    slug     = territory_slug(territory)
    out_path = brand_dir / f"{sku}_{slug}.png"
    final    = card.resize((FINAL_W, FINAL_H), Image.LANCZOS)
    final.convert("RGB").save(str(out_path), "PNG")
    return out_path


def main():
    args          = sys.argv[1:]
    limit         = None
    filter_brand  = None
    filter_sku    = None
    regen_all        = False   # --all: перегенерировать всё в main_cards/
    filter_multiword    = False   # --multiword: только многословные территории
    filter_longterritory = False  # --longterritory: слова >10 символов в названии страны

    i = 0
    while i < len(args):
        if args[i] == "--limit" and i+1 < len(args):
            limit = int(args[i+1]); i += 2
        elif args[i] == "--brand" and i+1 < len(args):
            filter_brand = args[i+1].lower(); i += 2
        elif args[i] == "--sku" and i+1 < len(args):
            filter_sku = args[i+1]; i += 2
        elif args[i] == "--all":
            regen_all = True; i += 1
        elif args[i] == "--multiword":
            regen_all = True; filter_multiword = True; i += 1
        elif args[i] == "--longterritory":
            regen_all = True; filter_longterritory = True; i += 1
        else:
            i += 1

    out_dir = OUTPUT if regen_all else OUTPUT_NEW
    out_dir.mkdir(parents=True, exist_ok=True)

    print("Загрузка данных и ресурсов...")
    with open(JSON_PATH, encoding="utf-8") as f:
        data = json.load(f)
    products = data['Данные о товарах']

    logo, fonts, country_map = load_resources()
    existing_skus             = set() if regen_all else load_existing_skus()
    if regen_all:
        print("Режим --all: перегенерация всех карточек → main_cards/")
    else:
        print(f"Уже готово: {len(existing_skus)} карточек")

    todo = []
    skipped_games = 0
    skipped_no_bg = []
    for row in products[4:]:
        if not isinstance(row, list) or len(row) <= 10:
            continue
        brand = row[10]
        if not brand or not isinstance(brand, str) or brand.strip() in (
            'Название производителя или бренда.',
            'Заполните, чтобы товар попал в фильтр.'
        ):
            continue
        brand = brand.strip()
        name = str(row[6] or "") if len(row) > 6 else ""
        if is_game(brand, name):
            skipped_games += 1
            continue

        sku = get_sku(row)
        if not re.match(r'^GFT\d+$', sku):
            continue
        if sku in existing_skus:
            continue

        bg_key   = get_bg_key(brand, name)
        bg_path  = REFS / f"bg_{bg_key}.png"
        if not bg_path.exists():
            skipped_no_bg.append((sku, brand, bg_key))
            bg_key = "clean"

        if filter_sku    and sku != filter_sku:
            continue
        if filter_brand  and bg_key != filter_brand:
            continue

        todo.append((row, bg_key, sku))

    if filter_multiword:
        todo = [(row, bg, sku) for row, bg, sku in todo
                if len(str(row[48] or '').replace('\n',' ').strip().split()) > 1]
    if filter_longterritory:
        todo = [(row, bg, sku) for row, bg, sku in todo
                if any(len(w) > 10 for w in str(row[48] or '').replace('\n',' ').strip().split())]
    if limit:
        todo = todo[:limit]

    print(f"Игр/DLC пропущено: {skipped_games}")
    if skipped_no_bg:
        print(f"Без bg-файла ({len(skipped_no_bg)}, используют clean):")
        for sku, brand, key in skipped_no_bg[:5]:
            print(f"  {sku} {brand} → bg_{key}.png")
    print(f"К генерации: {len(todo)}")
    print(f"Карточки → {out_dir}\n")

    ok = err = 0
    for idx, (row, bg_key, sku) in enumerate(todo, 1):
        brand     = str(row[10]).strip()
        territory = str(row[48] or "все страны").replace('\n', ' ').strip() if len(row) > 48 else "все страны"
        print(f"[{idx}/{len(todo)}] {sku}  {brand[:35]:<35} bg={bg_key}... ", end="", flush=True)
        try:
            card = render_card(row, bg_key, logo, fonts, country_map)
            out  = save_card(card, bg_key, sku, territory, out_dir)
            print(f"✓")
            ok += 1
        except Exception as e:
            print(f"✗ {e}")
            err += 1

    print(f"\nГотово: {ok} OK, {err} ошибок")
    print(f"Смотри в: {out_dir}")


if __name__ == "__main__":
    main()
