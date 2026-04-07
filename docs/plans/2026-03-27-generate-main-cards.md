# Generate Main Cards — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use forge:executing-plans or forge:subagent-driven-development to implement this plan task-by-task.

**Goal:** Сгенерировать главные карточки (1080x1440 PNG) для всех ~2529 оставшихся товаров (ваучеры, пополнения, подписки) — исключая игры и DLC.

**Architecture:** Один Python-скрипт `pipeline/images/generate_main_cards.py` читает JSON с товарами, фильтрует игры, определяет тип карточки (gift card / подписка / игровая валюта), рендерит через Pillow (2160×2880 → 1080×1440) и сохраняет PNG. Пропускает уже существующие SKU.

**Tech Stack:** Python 3, Pillow, pathlib, json, re

---

## Контекст и ресурсы

### Файлы проекта
| Файл | Назначение |
|------|-----------|
| `new table/Онлайн-подписки и карты оплаты_истина_с_характеристиками.json` | Данные товаров (3341 строк) |
| `pipeline/images/references/bg_*.png` | Фоны брендов (1792×2400, ~170 шт.) |
| `pipeline/images/references/flags/*.png` | Флаги стран |
| `pipeline/images/references/flags/country_to_flag.json` | Маппинг страна → файл флага |
| `pipeline/images/references/unnamed5_nobg_navy_hires.png` | Логотип магазина |
| `pipeline/images/fonts/FiraSans-Bold.ttf` | Шрифт для всех текстов |
| `pipeline/images/output/main_cards/` | Готовые карточки (уже 1868 шт.) |
| `pipeline/images/card_spec_final.md` | Полная спецификация дизайна |

### Спецификация дизайна (из card_spec_final.md)
- Рендер: **2160×2880** → resize до **1080×1440** (LANCZOS)
- Масштаб S = 2160/1728 = **1.25**
- Шрифт: **FiraSans-Bold.ttf** везде
- Цвета: `#1E3A5F` (тёмно-синий), `#4682B4` (стальной синий)

| Элемент | Canva pt | px в скрипте (pt×1.333×S) | Позиция (Canva × S) |
|---------|----------|--------------------------|---------------------|
| Заголовок (строка 1-2) | 130pt | 216px | x=216, y=158 |
| Номинал / срок | 120pt | 200px | x=314, y=855 (center W=210) |
| Валюта / единица | 100pt | 166px | x=263, y=1095 (center W=311) |
| Страна / флаг подпись | 47pt | 79px | x=1543, y=1848 (center W=484) |
| Нижний текст | 47pt | 79px | x=216, y=2266 |
| Флаг (круглый) | — | 281×281px | x=1644, y=1511 |
| Логотип | — | 729×290px | x=715, y=2519 |
| Межстрока заголовка | — | 244px | — |
| Межстрока нижнего текста | — | 100px | — |

### Три типа карточек

**Тип 1 — Подарочная карта / пополнение (nominal[46] есть)**
- Строка 1: `ПОДАРОЧНАЯ` (цвет #1E3A5F)
- Строка 2: `КАРТА ` + `{БРЕНД}` (КАРТА=#1E3A5F, бренд=#4682B4)
- Большое число: номинал (10, 25, 100…)
- Под числом: валюта из названия (USD, EUR, AED, TRY…)
- Нижний текст: `ПОДХОДИТ ДЛЯ АККАУНТОВ {СТРАНА}` / `МГНОВЕННАЯ ЦИФРОВАЯ ДОСТАВКА`

**Тип 2 — Подписка (duration[47] есть, nominal[46] нет)**
- Строка 1: полное название подписки (весь #1E3A5F, без голубого)
- Строка 2: — (пусто или вторая строка названия)
- Большое число: цифра срока (1, 3, 6, 12)
- Под числом: `МЕСЯЦ` / `МЕСЯЦА` / `МЕСЯЦЕВ` / `ГОД`
- Нижний текст: `ПОДХОДИТ ДЛЯ АККАУНТОВ {СТРАНА}` / `МГНОВЕННАЯ ЦИФРОВАЯ ДОСТАВКА`

**Тип 3 — Игровая валюта (nominal[46] = количество, не денежный)**
- Определяется: nominal содержит слова (ROBUX, V-BUCKS, VP, FC POINTS, COINS и т.п.) — берём из названия
- Строка 1: `ИГРОВАЯ` (#1E3A5F)
- Строка 2: `ВАЛЮТА ` + `{БРЕНД}` (#4682B4)
- Большое число: количество (4500, 13500…)
- Под числом: тип валюты

### Маппинг бренд → bg_key (основные)
```python
BRAND_TO_BG = {
    # Platform names as in JSON → bg file key
    "Sony": "playstation",
    "Microsoft": "xbox",
    "Valve": "steam",
    "Google": "googleplay",
    "Apple": "apple",
    "Amazon": "amazon",
    "Nintendo": "nintendo",
    "Roblox Corporation": "roblox",
    "Riot Games": "riot",
    "Razer": "razer",
    "Spotify": "spotify",
    "Netflix": "netflix",
    # Regional variants → same key
    "Apple Gift Card | AE": "apple",
    "Apple Gift Card | US": "apple",
    # ... (полный маппинг в скрипте)
    # Fallback: brand.lower() stripped → ищем bg_{key}.png
}
```

### Маппинг территория → флаг (дополнения к country_to_flag.json)
```json
"Кабо-Верде": "cape_verde",
"Ботсвана": "botswana",
"Эфиопия": "ethiopia",
"Алжир": "algeria",
"Королевство Бутан": "bhutan",
"Бангладеш": "bangladesh",
"Кипр": "cyprus",
"Афганистан": "afghanistan",
"Ангола": "angola",
"Бурунди": "burundi",
"Албания": "albania",
"Литва": "lithuania",
"СНГ": "russia"
```

---

## Task 1: Расширить country_to_flag.json

**Files:**
- Modify: `pipeline/images/references/flags/country_to_flag.json`

**Step 1: Добавить отсутствующие страны**

Открыть JSON и добавить в конец объекта:
```json
"Кабо-Верде": "cape_verde",
"Ботсвана": "botswana",
"Эфиопия": "ethiopia",
"Алжир": "algeria",
"Королевство Бутан": "bhutan",
"Бангладеш": "bangladesh",
"Кипр": "cyprus",
"Афганистан": "afghanistan",
"Ангола": "angola",
"Бурунди": "burundi",
"Албания": "albania",
"Литва": "lithuania",
"СНГ": "russia",
"Страны Персидского залива": "global",
"Российская Федерация + страны СНГ": "russia",
"Ирак": "global",
"Иракский курдистан": "global"
```

**Step 2: Проверить что флаги-файлы существуют**
```bash
python3 -c "
import json
from pathlib import Path
flags_dir = Path('pipeline/images/references/flags')
with open(flags_dir / 'country_to_flag.json') as f:
    mapping = json.load(f)
missing = [v for v in set(mapping.values()) if not (flags_dir / f'{v}.png').exists()]
print('Missing flag files:', missing)
"
```
Ожидаем: `Missing flag files: []` (все файлы есть)

**Step 3: Commit**
```bash
git add pipeline/images/references/flags/country_to_flag.json
git commit -m "data: add missing countries to country_to_flag mapping"
```

---

## Task 2: Написать скрипт generate_main_cards.py

**Files:**
- Create: `pipeline/images/generate_main_cards.py`

**Step 1: Создать файл со структурой и константами**

```python
#!/usr/bin/env python3
"""
Генерация главных карточек товаров (1080x1440 PNG) через Pillow.
Читает JSON с товарами, фильтрует игры/DLC, генерирует карточки.

Запуск:
    python3 generate_main_cards.py                    # все отсутствующие
    python3 generate_main_cards.py --limit 50         # первые 50
    python3 generate_main_cards.py --brand vodafone   # только бренд
    python3 generate_main_cards.py --sku GFT1234      # один товар
"""
import json, os, re, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from collections import defaultdict

# ── Пути ──────────────────────────────────────────────────────────────────
BASE       = Path("/media/anton/Новый том/yamarcket/pipeline/images")
REFS       = BASE / "references"
FLAGS_DIR  = REFS / "flags"
FONTS_DIR  = BASE / "fonts"
OUTPUT     = BASE / "output" / "main_cards"
JSON_PATH  = Path("/media/anton/Новый том/yamarcket/new table/Онлайн-подписки и карты оплаты_истина_с_характеристиками.json")

LOGO_PATH  = REFS / "unnamed5_nobg_navy_hires.png"
FONT_PATH  = FONTS_DIR / "FiraSans-Bold.ttf"

# ── Размеры ───────────────────────────────────────────────────────────────
CW, CH   = 2160, 2880   # рендер
S        = CW / 1728    # 1.25
FINAL_W  = 1080
FINAL_H  = 1440

# ── Цвета ─────────────────────────────────────────────────────────────────
DARK  = "#1E3A5F"
STEEL = "#4682B4"

# ── Позиции (Canva coords × S) ────────────────────────────────────────────
TITLE_X      = int(173 * S)
TITLE_Y      = int(126 * S)
TITLE_LINE_H = int(195 * S)
NOM_X, NOM_Y, NOM_W   = int(251*S), int(684*S), int(168*S)
CUR_X, CUR_Y, CUR_W   = int(210*S), int(876*S), int(249*S)
FLAG_X, FLAG_Y         = int(1315*S), int(1209*S)
FLAG_SIZE              = int(225*S)
CTR_X, CTR_Y, CTR_W   = int(1234*S), int(1478*S), int(387*S)
BOTTOM_X, BOTTOM_Y    = int(173*S), int(1813*S)
BOTTOM_LINE_H          = int(80*S)
LOGO_X, LOGO_Y        = int(572*S), int(2015*S)
LOGO_W, LOGO_H        = int(583*S), int(232*S)

# ── Размеры шрифтов (Canva pt × 1.333 × S) ───────────────────────────────
SZ_TITLE   = int(173 * S)   # 130pt
SZ_NOM     = int(160 * S)   # 120pt
SZ_CUR     = int(133 * S)   # 100pt
SZ_COUNTRY = int(63  * S)   # 47pt
SZ_BOTTOM  = int(63  * S)   # 47pt
```

**Step 2: Добавить маппинг брендов и список игр**

```python
# ── Маппинг бренд (JSON) → ключ bg-файла ──────────────────────────────────
BRAND_TO_BG = {
    # Платформы
    "Sony": "playstation",
    "Microsoft": "xbox",
    "Valve": "steam",
    "Google": "googleplay",
    "Apple": "apple",
    "Amazon": "amazon",
    "Nintendo": "nintendo",
    "Roblox Corporation": "roblox",
    "Riot Games": "riot",
    "Razer": "razer",
    "Spotify": "spotify",
    "Netflix": "netflix",
    "Disney": "disney",
    "HBO": "hbo",
    "Meta": "meta",
    "Tencent Games": "tencent",
    "Twitch Gift Card | EU": "twitch",
    "Twitch Gift Card | UK": "twitch",
    "Twitch Gift Card | US": "twitch",
    # Apple регионы
    **{f"Apple Gift Card | {c}": "apple" for c in
       ["AE","AT","AU","BE","DE","ES","FI","FR","IE","IT","JP","LU","NL","PL","PT","SA","UK","US"]},
    # Battle.net регионы
    **{f"Battle.net Gift Card | {c}": "battlenet" for c in ["BR","CA","EU","MX","PL","UK","US"]},
    **{f"Battle.net gift card | {c}": "battlenet" for c in ["MY","SG","TH"]},
    # Fortnite
    **{f"Fortnite Gift Card | {c}": "fortnite" for c in ["AE","EU","SA","UK","US"]},
    "Fortnite": "fortnite",
    # Valorant
    **{f"Valorant Gift Card | {c}": "valorant" for c in ["AU","BR","EU","RU","TR","UK","US"]},
    # Riot Cash
    **{f"Riot Cash Card | {c}": "riot" for c in ["AE","BH","BR","EU","KW","LATAM","SA","TR","UK","US"]},
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
    # Eneba
    "Eneba Gift Card | EUR": "eneba",
    "Eneba Gift Card | USD": "eneba",
    # Kinguin
    "Kinguin Gift Card | EU": "kinguin",
    # Операторы с несколькими брендами
    **{f"Vodafone {c}": "vodafone" for c in ["Albania","Egypt","Germany","Italy","Portugal","Romania","Spain"]},
    "Vodafone Voucher | NL": "vodafone",
    "Vodafone Voucher | QA": "vodafone",
    "Vodafone | DE": "vodafone",
    "Vodafone | UK": "vodafone",
    **{f"Orange {c}": "orange" for c in ["Botswana","Egypt","Romania","Spain"]},
    "Orange Voucher | BE": "orange",
    "Orange Voucher | FR": "orange",
    "Orange Voucher | JO": "orange",
    "Orange | LU": "orange",
    "O2 Czech Republic": "o2",
    "O2 Germany": "o2",
    "O2 | DE": "o2",
    "O2 | UK": "o2",
    "Three | IE": "three",
    "Three | UK": "three",
    **{f"Lyca Mobile {c}": "lyca" for c in ["France","Italy","Portugal","Spain"]},
    **{f"Lyca Mobile Voucher | {c}": "lyca" for c in ["AT","BE","DE","FR","IE","IT","NL","UK"]},
    "Red Bull Mobile Voucher | OM": "redbullmobile",
    "Red Bull Mobile Voucher | SA": "redbullmobile",
    "DIGI Italy": "digi",
    "DIGI Spain": "digi",
    "Claro Argentina": "claro",
    "Claro Brazil": "claro",
    "Unitel Angola": "unitelt",
    "Unitel T+ Cape Verde": "unitelt",
    "Alou Cape Verde": "alou",
    "Roshan Afghanistan": "roshan",
    # Delta Force
    "Delta Force Mobile Top Up": "deltaforce",
    "Delta Force Mobile Top Up MENA (Garena)": "deltaforce",
    "Delta Force Mobile Top Up SEA (Garena)": "deltaforce",
    "Delta Force Voucher (Garena)": "deltaforce",
    "Delta Force Voucher (Midasbuy)": "deltaforce",
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
    # Прочие
    "Travian Legends": "travian",
    "JetonCash": "jetoncash",
    "Discord Gift Card": "discord",
    "Hulu Gift Card | US": "hulu",
    "Crunchyroll Premium": "crunchyroll",
    "Deezer Premium": "deezer",
    "Blu TV | TR": "blutv",
    "Exxen | TR": "exxen",
    "Weyyak": "weyyak",
    "Blacknut Gift Card": "blacknut",
    "World of Warcraft | US": "worldofwarcraft",
    "EA Gift Card | EU": "ea",
    "EA Gift Card | USA": "ea",
    "Overwatch® 2": "overwatch",
    "The Elder Scrolls Online": "elderscrollsonline",
    "The Elder Scrolls Online | GL": "elderscrollsonline",
    "Old School RuneScape | GL": "runescape",
    "RuneScape Membership": "runescape",
    "RuneScape | GL": "runescape",
    "Garena Voucher": "garena",
    "NetEase Games Pay Card": "netease",
    "SEAGM Gift Card": "seagm",
    "Cherry Credits Gift Card": "cherrycredits",
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
    "CASHlib Voucher | EU": "cashlib",
    "CASHlib Voucher | NO": "cashlib",
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
    "TikTok": "tiktok",
    "Skype Gift Card | AU": "skype",
    "Adobe Digital Code": "adobe",
    "Bitdefender Subscription": "bitdefender",
    "Voicemod": "voicemod",
    **{f"ExitLag Gift Card | Tier {n}": "exitlag" for n in [1,2,3]},
    "NoPing": "noping",
    "CapCut Basic Membership | EU": "capcut",
    "CapCut Basic Membership | US": "capcut",
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
    "AT&T Prepaid Voucher | US": "att",
    "T-Mobile Germany": "tmobile",
    "EE Mobile | UK": "ee",
    "KPN Mobile Voucher | NL": "kpn",
    "Proximus Voucher | BE": "proximus",
    "Bouygues | FR": "bouygues",
    "Vivo Brazil": "vivo",
    "China Mobile China": "chinamobile",
    "HUAWEI Gift Card | AE": "huawei",
    "A1 Voucher | AT": "a1",
    "AY YILDIZ Germany": "ayayildiz",
    "Base Voucher | BE": "base",
    "BASE Mobile Germany": "base",
    "Batelco Voucher | BH": "batelco",
    "Bhutan Telecom Bhutan": "bhutantelecom",
    "Blau Germany": "blau",
    "Blau Voucher | DE": "blau",
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
    "Movistar Argentina": "movistar",
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
    "TIM Brazil": "tim",
    "TIM Italy": "tim",
    "Tiscali Italy": "tiscali",
    "Tuenti Argentina": "tuenti",
    "Umniah Voucher | JO": "umniah",
    "Very Mobile Italy": "verymobile",
    "WINDTRE Italy": "windtre",
    "Yoigo Spain": "yoigo",
    "YouMobile Spain": "youmobile",
    "Algar Telecom Brazil": "algar",
    "Drei Voucher | AT": "drei",
    "noon gift card | AE": "noon",
    "noon gift card | SA": "noon",
    "2XKO Gift Card | TR": "riot",
    "Tencent Games": "tencent",
    "Meta": "meta",
    "HUAWEI Gift Card | AE": "huawei",
    "Hulu Gift Card | US": "hulu",
    "Victoria's Secret Gift Card": "victoriassecret",
}

# ── Фильтр игр (бренды, которые НЕ нужно генерировать) ────────────────────
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

def is_game_brand(brand: str) -> bool:
    return any(brand.startswith(kw) for kw in GAME_KEYWORDS)
```

**Step 3: Добавить функции рендеринга**

```python
# ── Загрузка ресурсов ──────────────────────────────────────────────────────
def load_resources():
    logo = Image.open(LOGO_PATH).convert("RGBA")
    logo = logo.resize((LOGO_W, LOGO_H), Image.LANCZOS)
    fonts = {
        'title':   ImageFont.truetype(str(FONT_PATH), SZ_TITLE),
        'nominal': ImageFont.truetype(str(FONT_PATH), SZ_NOM),
        'currency':ImageFont.truetype(str(FONT_PATH), SZ_CUR),
        'country': ImageFont.truetype(str(FONT_PATH), SZ_COUNTRY),
        'bottom':  ImageFont.truetype(str(FONT_PATH), SZ_BOTTOM),
    }
    with open(FLAGS_DIR / "country_to_flag.json", encoding="utf-8") as f:
        country_map = json.load(f)
    return logo, fonts, country_map


def make_flag(territory: str, country_map: dict) -> Image.Image | None:
    flag_key = country_map.get(territory)
    if not flag_key:
        # попытка по первому слову
        first = territory.split()[0]
        flag_key = country_map.get(first, "global")
    flag_path = FLAGS_DIR / f"{flag_key}.png"
    if not flag_path.exists():
        flag_path = FLAGS_DIR / "global.png"
    flag = Image.open(flag_path).convert("RGBA").resize((FLAG_SIZE, FLAG_SIZE), Image.LANCZOS)
    mask = Image.new("L", (FLAG_SIZE, FLAG_SIZE), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, FLAG_SIZE-1, FLAG_SIZE-1), fill=255)
    circle = Image.new("RGBA", (FLAG_SIZE, FLAG_SIZE), (0,0,0,0))
    circle.paste(flag, (0,0), mask)
    return circle


def center_text_x(draw: ImageDraw.Draw, text: str, font, box_x: int, box_w: int) -> int:
    tw = int(draw.textlength(text, font=font))
    return box_x + (box_w - tw) // 2


def get_bg_key(brand: str) -> str:
    if brand in BRAND_TO_BG:
        return BRAND_TO_BG[brand]
    # Fallback: нормализуем
    key = re.sub(r'\s*\|.*$', '', brand.lower())
    key = re.sub(r'\s+(gift card|top up|voucher|mobile|telecom)$', '', key)
    key = re.sub(r'[^a-z0-9]', '', key)
    return key


def determine_card_type(row: list) -> str:
    """gift_card | subscription | game_currency"""
    nominal = row[46] if len(row) > 46 else None
    duration = row[47] if len(row) > 47 else None
    name = str(row[6] or "").lower()

    game_currencies = ['robux', 'v-bucks', 'vbucks', 'vp', 'fc point', 'coin',
                       'gems', 'diamonds', 'tokens', 'points', 'credits', 'gold']
    if any(c in name for c in game_currencies):
        return "game_currency"
    if nominal and str(nominal).strip() not in ['', 'None', '99 лет']:
        return "gift_card"
    if duration and str(duration).strip() not in ['', 'None', '99 лет']:
        return "subscription"
    return "gift_card"


def extract_nominal_currency(row: list) -> tuple[str, str]:
    """Возвращает (номинал_строка, валюта)"""
    nominal = row[46] if len(row) > 46 else None
    name = str(row[6] or "")
    # Попытка вытащить валюту из названия
    currencies = ['USD','EUR','GBP','AED','TRY','SAR','JPY','INR','BRL','MXN',
                  'AUD','CAD','PLN','CHF','SEK','NOK','DKK','HUF','CZK','RON',
                  'ALL','DZD','BDT','BTN','BWP','CLP','COP','EGP','ETB','HRK',
                  'IQD','JOD','KWD','LBP','LTL','MAD','NGN','OMR','PHP','QAR',
                  'RUB','SGD','THB','TWD','TZS','UAH','VND','ZAR']
    currency = ""
    for c in currencies:
        if c in name:
            currency = c
            break

    nom_str = ""
    if nominal and str(nominal).strip() not in ['', 'None']:
        try:
            n = float(str(nominal))
            nom_str = str(int(n)) if n == int(n) else str(n)
        except:
            nom_str = str(nominal)

    return nom_str, currency


def extract_duration(row: list) -> tuple[str, str]:
    """Возвращает (цифра, единица: МЕСЯЦ/МЕСЯЦА/МЕСЯЦЕВ/ГОД/ГОДА/ЛЕТ)"""
    duration = str(row[47] or "") if len(row) > 47 else ""
    m = re.match(r'(\d+)\s*(месяц|год|лет|day|month|year)', duration.lower())
    if not m:
        return "", ""
    n = int(m.group(1))
    unit_raw = m.group(2)
    if 'год' in unit_raw or 'year' in unit_raw:
        if n == 1:
            return str(n), "ГОД"
        elif 2 <= n <= 4:
            return str(n), "ГОДА"
        else:
            return str(n), "ЛЕТ"
    else:  # месяц
        if n == 1:
            return str(n), "МЕСЯЦ"
        elif 2 <= n <= 4:
            return str(n), "МЕСЯЦА"
        else:
            return str(n), "МЕСЯЦЕВ"


def get_brand_display(brand: str) -> str:
    """Короткое название бренда для заголовка (XBOX, STEAM, APPLE...)"""
    # Убираем региональный суффикс
    name = re.sub(r'\s*\|.*$', '', brand).strip()
    # Убираем длинные слова
    for suffix in [' Gift Card', ' Top Up', ' Voucher', ' Mobile', ' Telecom',
                   ' Wireless', ' Prepaid', ' Membership', ' Premium',
                   ' Subscription', ' Corporation', ' Games']:
        name = name.replace(suffix, '')
    return name.strip().upper()


def render_card(row: list, bg_key: str, logo: Image.Image,
                fonts: dict, country_map: dict) -> Image.Image:
    """Рендерит одну карточку, возвращает Image 2160x2880."""
    brand = str(row[10] or "").strip()
    territory = str(row[48] or "все страны").strip() if len(row) > 48 else "все страны"
    card_type = determine_card_type(row)

    # Загрузка фона
    bg_path = REFS / f"bg_{bg_key}.png"
    if not bg_path.exists():
        bg_path = REFS / "bg_clean.png"
    bg = Image.open(bg_path).convert("RGBA").resize((CW, CH), Image.LANCZOS)

    # Флаг
    flag_circle = make_flag(territory, country_map)

    card = bg.copy()
    card.paste(flag_circle, (FLAG_X, FLAG_Y), flag_circle)

    draw = ImageDraw.Draw(card)
    brand_display = get_brand_display(brand)

    # ── Заголовок ──────────────────────────────────────────────────────────
    if card_type == "subscription":
        # Весь заголовок тёмно-синий, разбиваем на 2 строки по смыслу
        words = brand_display.split()
        mid = len(words) // 2
        line1 = " ".join(words[:mid]) if mid else brand_display
        line2 = " ".join(words[mid:]) if mid else ""
        draw.text((TITLE_X, TITLE_Y), line1, font=fonts['title'], fill=DARK)
        if line2:
            draw.text((TITLE_X, TITLE_Y + TITLE_LINE_H), line2, font=fonts['title'], fill=DARK)
    elif card_type == "game_currency":
        draw.text((TITLE_X, TITLE_Y), "ИГРОВАЯ", font=fonts['title'], fill=DARK)
        draw.text((TITLE_X, TITLE_Y + TITLE_LINE_H), "ВАЛЮТА ", font=fonts['title'], fill=DARK)
        kw = int(draw.textlength("ВАЛЮТА ", font=fonts['title']))
        draw.text((TITLE_X + kw, TITLE_Y + TITLE_LINE_H), brand_display, font=fonts['title'], fill=STEEL)
    else:  # gift_card
        draw.text((TITLE_X, TITLE_Y), "ПОДАРОЧНАЯ", font=fonts['title'], fill=DARK)
        draw.text((TITLE_X, TITLE_Y + TITLE_LINE_H), "КАРТА ", font=fonts['title'], fill=DARK)
        kw = int(draw.textlength("КАРТА ", font=fonts['title']))
        draw.text((TITLE_X + kw, TITLE_Y + TITLE_LINE_H), brand_display, font=fonts['title'], fill=STEEL)

    # ── Номинал / срок ─────────────────────────────────────────────────────
    if card_type == "subscription":
        num_str, unit_str = extract_duration(row)
    else:
        num_str, unit_str = extract_nominal_currency(row)

    if num_str:
        cx = center_text_x(draw, num_str, fonts['nominal'], NOM_X, NOM_W)
        draw.text((cx, NOM_Y), num_str, font=fonts['nominal'], fill=STEEL)
    if unit_str:
        cx = center_text_x(draw, unit_str, fonts['currency'], CUR_X, CUR_W)
        draw.text((cx, CUR_Y), unit_str, font=fonts['currency'], fill=DARK)

    # ── Страна ─────────────────────────────────────────────────────────────
    cx = center_text_x(draw, territory.upper(), fonts['country'], CTR_X, CTR_W)
    draw.text((cx, CTR_Y), territory.upper(), font=fonts['country'], fill=DARK)

    # ── Нижний текст ───────────────────────────────────────────────────────
    bottom_lines = [
        f"ПОДХОДИТ ДЛЯ АККАУНТОВ {territory.upper()}",
        "МГНОВЕННАЯ ЦИФРОВАЯ ДОСТАВКА",
    ]
    for i, line in enumerate(bottom_lines):
        draw.text((BOTTOM_X, BOTTOM_Y + i * BOTTOM_LINE_H), line,
                  font=fonts['bottom'], fill=DARK)

    # ── Логотип ────────────────────────────────────────────────────────────
    card.paste(logo, (LOGO_X, LOGO_Y), logo)

    return card
```

**Step 4: Добавить main() с аргументами и батч-обработкой**

```python
def get_sku(row: list) -> str:
    raw = row[0]
    if isinstance(raw, float):
        return f"GFT{int(raw)}"
    return f"GFT{str(raw).replace('GFT','')}"


def get_territory_slug(territory: str) -> str:
    import unicodedata
    t = territory.lower().strip()
    transliterate = {
        'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'yo','ж':'zh',
        'з':'z','и':'i','й':'y','к':'k','л':'l','м':'m','н':'n','о':'o',
        'п':'p','р':'r','с':'s','т':'t','у':'u','ф':'f','х':'kh','ц':'ts',
        'ч':'ch','ш':'sh','щ':'shch','ъ':'','ы':'y','ь':'','э':'e','ю':'yu','я':'ya',
    }
    result = ""
    for ch in t:
        if ch in transliterate:
            result += transliterate[ch]
        elif ch.isascii() and (ch.isalnum() or ch in '-_'):
            result += ch
        elif ch == ' ':
            result += '_'
    return result[:30] or "world"


def load_existing_skus() -> set:
    skus = set()
    for f in OUTPUT.rglob("*.png"):
        m = re.match(r'(GFT\d+)', f.stem)
        if m:
            skus.add(m.group(1))
    return skus


def save_card(card: Image.Image, brand_key: str, sku: str, territory: str):
    out_dir = OUTPUT / brand_key
    out_dir.mkdir(parents=True, exist_ok=True)
    slug = get_territory_slug(territory)
    out_path = out_dir / f"{sku}_{slug}.png"
    final = card.resize((FINAL_W, FINAL_H), Image.LANCZOS)
    final.convert("RGB").save(str(out_path), "PNG")
    return out_path


def main():
    args = sys.argv[1:]
    limit = None
    filter_brand = None
    filter_sku = None

    i = 0
    while i < len(args):
        if args[i] == "--limit" and i+1 < len(args):
            limit = int(args[i+1]); i += 2
        elif args[i] == "--brand" and i+1 < len(args):
            filter_brand = args[i+1]; i += 2
        elif args[i] == "--sku" and i+1 < len(args):
            filter_sku = args[i+1]; i += 2
        else:
            i += 1

    print("Загрузка данных...")
    with open(JSON_PATH, encoding="utf-8") as f:
        data = json.load(f)
    products = data['Данные о товарах']

    logo, fonts, country_map = load_resources()
    existing_skus = load_existing_skus()
    print(f"Уже готово: {len(existing_skus)} карточек")

    # Собираем список товаров для генерации
    todo = []
    for row in products[4:]:
        if not isinstance(row, list) or len(row) <= 10:
            continue
        brand = row[10]
        if not brand or not isinstance(brand, str):
            continue
        brand = brand.strip()
        if brand in ['Название производителя или бренда.', 'Заполните, чтобы товар попал в фильтр.']:
            continue
        if is_game_brand(brand):
            continue

        sku = get_sku(row)
        if sku in existing_skus:
            continue

        bg_key = get_bg_key(brand)
        bg_path = REFS / f"bg_{bg_key}.png"
        if not bg_path.exists():
            # Fallback на clean background
            bg_key = "clean"

        if filter_sku and sku != filter_sku:
            continue
        if filter_brand and bg_key != filter_brand.lower():
            continue

        todo.append((row, bg_key, sku))

    if limit:
        todo = todo[:limit]

    print(f"К генерации: {len(todo)}\n")

    ok = err = 0
    for idx, (row, bg_key, sku) in enumerate(todo, 1):
        brand = str(row[10]).strip()
        territory = str(row[48] or "все страны").strip() if len(row) > 48 else "все страны"
        print(f"[{idx}/{len(todo)}] {sku} {brand[:30]:<30} → bg_{bg_key}... ", end="", flush=True)
        try:
            card = render_card(row, bg_key, logo, fonts, country_map)
            out = save_card(card, bg_key, sku, territory)
            print(f"✓ {out.name}")
            ok += 1
        except Exception as e:
            print(f"✗ {e}")
            err += 1

    print(f"\nГотово: {ok} OK, {err} ошибок")

if __name__ == "__main__":
    main()
```

**Step 5: Commit**
```bash
git add pipeline/images/generate_main_cards.py
git commit -m "feat: add main card generator script (Pillow, 1080x1440)"
```

---

## Task 3: Тест на 5 карточках

**Step 1: Запустить тест**
```bash
cd "/media/anton/Новый том/yamarcket"
python3 pipeline/images/generate_main_cards.py --limit 5
```
Ожидаем: `5 OK, 0 ошибок`, файлы в `output/main_cards/`

**Step 2: Проверить размер файлов**
```bash
python3 -c "
from PIL import Image
from pathlib import Path
for f in sorted(Path('pipeline/images/output/main_cards').rglob('*.png'))[-5:]:
    img = Image.open(f)
    print(f.name, img.size)
"
```
Ожидаем: все `(1080, 1440)`

**Step 3: Визуальная проверка**
- Открыть несколько PNG из `output/main_cards/`
- Проверить: фон соответствует бренду, заголовок читается, флаг отображается

---

## Task 4: Генерация всех оставшихся карточек

**Step 1: Запустить полную генерацию**
```bash
cd "/media/anton/Новый том/yamarcket"
python3 pipeline/images/generate_main_cards.py 2>&1 | tee /tmp/cards_gen.log
```

**Step 2: Проверить итог**
```bash
tail -5 /tmp/cards_gen.log
# Ожидаем: "Готово: XXXX OK, N ошибок"

# Подсчитать итого карточек
find pipeline/images/output/main_cards -name "*.png" | wc -l
```

**Step 3: Проверить ошибки (если есть)**
```bash
grep "✗" /tmp/cards_gen.log | head -20
```
Для каждой ошибки — добавить бренд в BRAND_TO_BG или проверить bg-файл.

**Step 4: Повторный запуск для неудавшихся**
```bash
python3 pipeline/images/generate_main_cards.py 2>&1 | tail -5
# Ожидаем: "К генерации: 0" (все готово) или небольшое число
```

**Step 5: Commit**
```bash
git add pipeline/images/generate_main_cards.py
git commit -m "feat: generate main cards for all non-game products"
```

---

## Ожидаемый результат

- ~2529 новых карточек PNG (1080×1440)
- Разложены по папкам: `output/main_cards/{brand_key}/`
- Имена файлов: `{SKU}_{territory_slug}.png`
- Итого карточек: 1868 (было) + ~2529 = ~4397

---

## Три варианта выполнения

**1. Subagent (эта сессия)** — я выполняю задачи по одной с проверкой между ними.
- REQUIRED: `forge:subagent-driven-development`

**2. Batch (новая сессия)** — новый терминал, задачи батчами по 3, пауза между.
- REQUIRED: `forge:executing-plans`

**3. Autonomous (новая сессия)** — максимально автономно, проверяешь результат в конце.
- REQUIRED: `forge:subagent-driven-development`
- Команда: `claude "Прочитай docs/plans/2026-03-27-generate-main-cards.md и выполни план. Используй forge:subagent-driven-development."`
