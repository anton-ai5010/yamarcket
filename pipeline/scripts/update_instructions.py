#!/usr/bin/env python3
"""
Массовое обновление инструкций по активации в описаниях товаров.
Заменяет generic инструкции и обновляет существующие на новые с несколькими способами.
"""

import json
import re
import copy

JSON_PATH = "/media/anton/Новый том/yamarcket/new table/Онлайн-подписки и карты оплаты_истина_с_характеристиками.json"

# ============================================================
# ИНСТРУКЦИИ ПО СЕРВИСАМ (HTML)
# ============================================================

INSTRUCTIONS = {}

# --- STEAM: КЛЮЧ ИГРЫ (567 товаров) ---
INSTRUCTIONS['steam_game'] = """<h2>Инструкция по активации ключа игры в Steam</h2>
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

# --- STEAM: ПОПОЛНЕНИЕ КОШЕЛЬКА (143 товара) ---
INSTRUCTIONS['steam_wallet'] = """<h2>Инструкция по активации кода Steam</h2>
<p><b>Способ 1 — Через клиент Steam на ПК:</b></p>
<ol>
<li>Откройте клиент Steam и войдите в свой аккаунт</li>
<li>Нажмите на имя профиля → «Об аккаунте»</li>
<li>Перейдите в «Пополнить баланс» → «Код кошелька или подарочной карты Steam»</li>
<li>Введите код и нажмите «Продолжить» — средства мгновенно зачислятся на баланс</li>
</ol>
<p><b>Способ 2 — Через браузер на сайте Steam:</b></p>
<ol>
<li>Перейдите на store.steampowered.com/account и войдите в аккаунт</li>
<li>Выберите «Пополнить баланс» и введите код</li>
<li>Подтвердите — средства зачислятся на баланс</li>
</ol>"""

# --- XBOX STORE / MICROSOFT STORE ---
INSTRUCTIONS['xbox'] = """<h2>Инструкция по активации кода Xbox</h2>
<p><b>Способ 1 — На консоли Xbox:</b></p>
<ol>
<li>Нажмите кнопку Xbox на геймпаде для вызова меню</li>
<li>Перейдите в «Магазин» → «Использовать код» (Redeem Code)</li>
<li>Введите 25-значный код и подтвердите</li>
<li>Средства, игра или подписка активируются на вашем аккаунте</li>
</ol>
<p><b>Способ 2 — На сайте microsoft.com/redeem:</b></p>
<ol>
<li>Перейдите на microsoft.com/redeem и войдите в аккаунт Microsoft</li>
<li>Введите 25-значный код и нажмите «Далее»</li>
<li>Средства, игра или подписка активируются на аккаунте</li>
</ol>
<p><b>Способ 3 — В приложении Xbox на телефоне:</b></p>
<ol>
<li>Откройте приложение Xbox на смартфоне и войдите в аккаунт</li>
<li>Нажмите на иконку профиля → «Оплата» → «Погасить код»</li>
<li>Введите 25-значный код и подтвердите активацию</li>
</ol>"""

# --- PLAYSTATION STORE ---
INSTRUCTIONS['playstation'] = """<h2>Инструкция по активации кода PlayStation Store</h2>
<p><b>Способ 1 — На консоли PlayStation (PS4/PS5):</b></p>
<ol>
<li>Включите консоль и войдите в свой аккаунт PlayStation Network</li>
<li>Откройте PlayStation Store с главного экрана</li>
<li>Перейдите в раздел «Погасить код» (Redeem Code)</li>
<li>Введите 12-значный код и подтвердите — средства мгновенно поступят на баланс</li>
</ol>
<p><b>Способ 2 — Через приложение PS App на телефоне:</b></p>
<ol>
<li>Откройте приложение PlayStation App на смартфоне и войдите в аккаунт</li>
<li>Перейдите в «Настройки» → «Погасить код»</li>
<li>Введите 12-значный код и подтвердите активацию</li>
</ol>"""

# --- GOOGLE PLAY ---
INSTRUCTIONS['google_play'] = """<h2>Инструкция по активации кода Google Play</h2>
<p><b>Способ 1 — На Android-устройстве:</b></p>
<ol>
<li>Откройте приложение Google Play на смартфоне или планшете</li>
<li>Нажмите на иконку профиля → «Платежи и подписки» → «Погасить код»</li>
<li>Введите код без пробелов и нажмите «Подтвердить»</li>
<li>Средства мгновенно зачислятся на баланс Google Play</li>
</ol>
<p><b>Способ 2 — Через браузер на play.google.com:</b></p>
<ol>
<li>Перейдите на play.google.com/redeem в браузере</li>
<li>Войдите в аккаунт Google</li>
<li>Введите код без пробелов и нажмите «Погасить»</li>
</ol>"""

# --- APP STORE / ITUNES / APPLE ---
INSTRUCTIONS['apple'] = """<h2>Инструкция по активации кода Apple Gift Card</h2>
<p><b>Способ 1 — На iPhone или iPad:</b></p>
<ol>
<li>Откройте App Store на вашем устройстве</li>
<li>Нажмите на иконку профиля в правом верхнем углу</li>
<li>Выберите «Погасить подарочную карту или код»</li>
<li>Введите код вручную или отсканируйте камерой — средства мгновенно зачислятся на баланс Apple ID</li>
</ol>
<p><b>Способ 2 — На Mac:</b></p>
<ol>
<li>Откройте App Store на Mac</li>
<li>Нажмите на своё имя в левом нижнем углу → «Погасить подарочную карту»</li>
<li>Введите код и нажмите «Готово»</li>
</ol>
<p><b>Способ 3 — На ПК через iTunes:</b></p>
<ol>
<li>Откройте iTunes на компьютере</li>
<li>Перейдите в «Учетная запись» → «Погасить»</li>
<li>Введите код и подтвердите активацию</li>
</ol>"""

# --- AMAZON ---
INSTRUCTIONS['amazon'] = """<h2>Инструкция по активации подарочной карты Amazon</h2>
<p><b>Способ 1 — На сайте Amazon:</b></p>
<ol>
<li>Перейдите на региональный сайт Amazon и войдите в аккаунт</li>
<li>Откройте «Account» → «Gift Cards» → «Redeem a Gift Card»</li>
<li>Введите код и нажмите «Apply to Your Account»</li>
<li>Сумма мгновенно зачислится на баланс</li>
</ol>
<p><b>Способ 2 — В приложении Amazon:</b></p>
<ol>
<li>Откройте приложение Amazon на смартфоне и войдите в аккаунт</li>
<li>Перейдите в «Account» → «Gift Cards» → «Redeem a Gift Card»</li>
<li>Введите код и нажмите «Apply to Your Account»</li>
<li>Сумма мгновенно зачислится на баланс</li>
</ol>"""

# --- NINTENDO ESHOP ---
INSTRUCTIONS['nintendo'] = """<h2>Инструкция по активации кода Nintendo eShop</h2>
<p><b>Способ 1 — На консоли Nintendo Switch:</b></p>
<ol>
<li>Откройте Nintendo eShop из главного меню</li>
<li>Нажмите на иконку пользователя и выберите «Ввести код» (Enter Code)</li>
<li>Введите 16-значный код и нажмите «Подтвердить»</li>
<li>Средства зачислятся на баланс eShop</li>
</ol>
<p><b>Способ 2 — На сайте Nintendo:</b></p>
<ol>
<li>Перейдите на ec.nintendo.com/redeem и войдите в аккаунт Nintendo</li>
<li>Введите 16-значный код и нажмите «Подтвердить»</li>
</ol>"""

# --- NINTENDO SWITCH ONLINE ---
INSTRUCTIONS['nintendo_online'] = """<h2>Инструкция по активации подписки Nintendo Switch Online</h2>
<p><b>Способ 1 — На консоли Nintendo Switch:</b></p>
<ol>
<li>Откройте Nintendo eShop из главного меню</li>
<li>Нажмите на иконку пользователя и выберите «Ввести код» (Enter Code)</li>
<li>Введите код подписки и нажмите «Подтвердить»</li>
<li>Подписка Nintendo Switch Online активируется на аккаунте</li>
</ol>
<p><b>Способ 2 — На сайте Nintendo:</b></p>
<ol>
<li>Перейдите на ec.nintendo.com/redeem и войдите в аккаунт Nintendo</li>
<li>Введите код подписки и подтвердите</li>
</ol>"""

# --- ROBLOX ---
INSTRUCTIONS['roblox'] = """<h2>Инструкция по активации кода Roblox</h2>
<ol>
<li>Перейдите на сайт roblox.com/redeem и войдите в аккаунт</li>
<li>Введите код с обратной стороны карты</li>
<li>Нажмите «Redeem»</li>
<li>Робуксы или кредит зачислятся на ваш аккаунт</li>
</ol>"""

# --- RIOT GAMES / LEAGUE OF LEGENDS / 2XKO ---
INSTRUCTIONS['riot'] = """<h2>Инструкция по активации кода Riot Games</h2>
<ol>
<li>Запустите клиент Riot и войдите в аккаунт</li>
<li>Перейдите в магазин → «Purchase RP» → «Prepaid Cards»</li>
<li>Введите код без пробелов и нажмите «Submit»</li>
<li>Средства мгновенно зачислятся на баланс</li>
</ol>"""

# --- VALORANT ---
INSTRUCTIONS['valorant'] = """<h2>Инструкция по активации кода Valorant</h2>
<ol>
<li>Запустите Valorant на ПК и войдите в аккаунт</li>
<li>Нажмите иконку VP (монетка) в правом верхнем углу</li>
<li>Выберите вкладку «Prepaid Cards and Codes»</li>
<li>Введите PIN-код и нажмите «Submit»</li>
</ol>"""

# --- RAZER GOLD ---
INSTRUCTIONS['razer'] = """<h2>Инструкция по активации кода Razer Gold</h2>
<p><b>Способ 1 — На сайте gold.razer.com:</b></p>
<ol>
<li>Перейдите на gold.razer.com и войдите в аккаунт</li>
<li>Нажмите «Wallet» → «Reload» (Пополнить баланс)</li>
<li>Выберите «Razer Gold PIN» и введите код</li>
<li>Подтвердите — средства зачислятся в кошелёк Razer Gold</li>
</ol>
<p><b>Способ 2 — В приложении Razer Gold:</b></p>
<ol>
<li>Откройте приложение Razer Gold на смартфоне</li>
<li>Перейдите в «Wallet» → «Redeem»</li>
<li>Отсканируйте QR-код или введите PIN вручную</li>
<li>Подтвердите — средства зачислятся</li>
</ol>"""

# --- NETFLIX ---
INSTRUCTIONS['netflix'] = """<h2>Инструкция по активации кода Netflix</h2>
<ol>
<li>Перейдите на netflix.com/redeem</li>
<li>Войдите в аккаунт Netflix или создайте новый</li>
<li>Введите код подарочной карты и нажмите «Погасить»</li>
<li>Баланс аккаунта будет пополнен</li>
</ol>"""

# --- SPOTIFY ---
INSTRUCTIONS['spotify'] = """<h2>Инструкция по активации кода Spotify</h2>
<ol>
<li>Перейдите на spotify.com/redeem в браузере</li>
<li>Войдите в аккаунт Spotify</li>
<li>Введите PIN-код и нажмите «Активировать»</li>
<li>Подписка Premium активируется на аккаунте</li>
</ol>"""

# --- BATTLE.NET / BLIZZARD ---
INSTRUCTIONS['battlenet'] = """<h2>Инструкция по активации кода Battle.net</h2>
<ol>
<li>Откройте Battle.net на сайте или в клиенте и войдите в аккаунт</li>
<li>Перейдите в «Account» → «Redeem a Code»</li>
<li>Введите код и подтвердите</li>
<li>Средства зачислятся на баланс Battle.net</li>
</ol>"""

# --- EA APP ---
INSTRUCTIONS['ea'] = """<h2>Инструкция по активации кода EA</h2>
<p><b>Способ 1 — В клиенте EA App на ПК:</b></p>
<ol>
<li>Откройте EA App на компьютере и войдите в аккаунт</li>
<li>Перейдите в «Settings» → «Redeem Code» (Активировать код)</li>
<li>Введите код и подтвердите</li>
<li>Средства или игра добавятся в аккаунт</li>
</ol>
<p><b>Способ 2 — На сайте EA:</b></p>
<ol>
<li>Перейдите на account.ea.com и войдите в аккаунт</li>
<li>Откройте «Payments» → «Redeem Code»</li>
<li>Введите код и подтвердите</li>
</ol>"""

# --- EPIC GAMES STORE / FORTNITE ---
INSTRUCTIONS['epic'] = """<h2>Инструкция по активации кода Epic Games</h2>
<ol>
<li>Перейдите на epicgames.com и войдите в аккаунт Epic Games</li>
<li>Откройте меню аккаунта → «Redeem Code»</li>
<li>Введите PIN-код без дефисов</li>
<li>Выберите платформу (если требуется) и подтвердите</li>
</ol>"""

# --- PAYSAFECARD ---
INSTRUCTIONS['paysafecard'] = """<h2>Инструкция по использованию ваучера Paysafecard</h2>
<p><b>Способ 1 — Оплата PIN-кодом:</b></p>
<ol>
<li>На сайте, где хотите оплатить, выберите способ оплаты «Paysafecard»</li>
<li>Введите 16-значный PIN-код ваучера</li>
<li>Подтвердите сумму оплаты</li>
<li>Средства спишутся с ваучера</li>
</ol>
<p><b>Способ 2 — Через кошелёк myPaysafe:</b></p>
<ol>
<li>Войдите в кошелёк на paysafecard.com (или создайте аккаунт)</li>
<li>Перейдите в раздел «Prepaid codes» → «Добавить PIN»</li>
<li>Введите 16-значный PIN-код и подтвердите</li>
</ol>"""

# --- NEOSURF ---
INSTRUCTIONS['neosurf'] = """<h2>Инструкция по использованию ваучера Neosurf</h2>
<ol>
<li>На сайте, где хотите оплатить, выберите способ оплаты «Neosurf»</li>
<li>Введите 10–16-значный код Neosurf</li>
<li>Подтвердите оплату</li>
</ol>"""

# --- CASHLIB ---
INSTRUCTIONS['cashlib'] = """<h2>Инструкция по использованию ваучера CASHlib</h2>
<ol>
<li>На странице оплаты выберите «Prepaid Voucher» или «CASHlib»</li>
<li>Введите 16-значный PIN-код</li>
<li>Подтвердите сумму и валюту</li>
</ol>"""

# --- REWARBLE ---
INSTRUCTIONS['rewarble'] = """<h2>Инструкция по активации карты Rewarble</h2>
<ol>
<li>Войдите в личный кабинет Rewarble</li>
<li>Перейдите в раздел «Redeem» и введите код</li>
<li>Выберите тип карты (Visa или Mastercard)</li>
<li>Получите реквизиты: номер карты, срок действия, CVC</li>
</ol>"""

# --- META QUEST ---
INSTRUCTIONS['meta_quest'] = """<h2>Инструкция по активации кода Meta Quest</h2>
<p><b>Способ 1 — На VR-гарнитуре Meta Quest:</b></p>
<ol>
<li>Откройте магазин → «Settings» → «Payments» → «Redeem Code»</li>
<li>Введите код без пробелов</li>
<li>Подтвердите — баланс пополнится</li>
</ol>
<p><b>Способ 2 — Через приложение Meta Quest на телефоне:</b></p>
<ol>
<li>Откройте приложение Meta Quest на смартфоне</li>
<li>Перейдите в «Menu» → «Wallet» → «Redeem»</li>
<li>Введите код и подтвердите</li>
</ol>"""

# --- TWITCH ---
INSTRUCTIONS['twitch'] = """<h2>Инструкция по активации кода Twitch</h2>
<ol>
<li>Войдите в аккаунт Twitch</li>
<li>Перейдите в «Wallet» → «Redeem a Code»</li>
<li>Введите код и подтвердите регион</li>
<li>Баланс зачислится в кошелёк</li>
</ol>"""

# --- DISCORD ---
INSTRUCTIONS['discord'] = """<h2>Инструкция по активации кода Discord</h2>
<ol>
<li>Откройте Discord → Настройки (шестерёнка) → «Billing» → «Redeem»</li>
<li>Введите код и нажмите «Активировать»</li>
<li>Подписка Nitro будет активирована</li>
</ol>"""

# --- KINGUIN ---
INSTRUCTIONS['kinguin'] = """<h2>Инструкция по активации карты Kinguin</h2>
<ol>
<li>Войдите на kinguin.net</li>
<li>Перейдите в «Wallet» → «Redeem Gift Card»</li>
<li>Введите код и подтвердите</li>
</ol>"""

# --- ENEBA ---
INSTRUCTIONS['eneba'] = """<h2>Инструкция по активации карты Eneba</h2>
<ol>
<li>Войдите в личный кабинет Eneba</li>
<li>Перейдите в «Wallet» → «Redeem»</li>
<li>Введите код и подтвердите валюту</li>
</ol>"""

# --- NOON ---
INSTRUCTIONS['noon'] = """<h2>Инструкция по активации карты Noon</h2>
<ol>
<li>Войдите в аккаунт Noon</li>
<li>Перейдите в «Account» → «Wallet» → «Gift Cards» → «Redeem»</li>
<li>Введите код и подтвердите</li>
</ol>"""

# --- BIGO LIVE ---
INSTRUCTIONS['bigo'] = """<h2>Инструкция по активации кода Bigo Live</h2>
<ol>
<li>Откройте приложение Bigo Live</li>
<li>Перейдите в профиль → «Recharge» → «Redeem»</li>
<li>Введите код и подтвердите</li>
</ol>"""

# --- TANGO LIVE ---
INSTRUCTIONS['tango'] = """<h2>Инструкция по активации кода Tango Live</h2>
<ol>
<li>Откройте приложение Tango Live</li>
<li>Перейдите в профиль → «Wallet» → «Redeem Code»</li>
<li>Введите код и подтвердите</li>
</ol>"""

# --- EXITLAG ---
INSTRUCTIONS['exitlag'] = """<h2>Инструкция по активации ваучера ExitLag</h2>
<ol>
<li>Войдите на сайт ExitLag → «Subscriptions»</li>
<li>Нажмите «Redeem» и введите ваучер</li>
<li>Подтвердите — подписка будет активирована</li>
</ol>"""

# --- MIFINITY ---
INSTRUCTIONS['mifinity'] = """<h2>Инструкция по активации ваучера MiFinity</h2>
<ol>
<li>Войдите в личный кабинет MiFinity</li>
<li>Перейдите в «Пополнение» → «eVoucher»</li>
<li>Введите код и подтвердите</li>
</ol>"""

# --- ICASH ONE ---
INSTRUCTIONS['icash'] = """<h2>Инструкция по активации ваучера iCash One</h2>
<ol>
<li>Войдите на icash.one</li>
<li>Перейдите в «Redeem» и введите код</li>
<li>Подтвердите — баланс обновится в кошельке</li>
</ol>"""

# --- JETONCASH ---
INSTRUCTIONS['jetoncash'] = """<h2>Инструкция по использованию ваучера JetonCash</h2>
<ol>
<li>На сайте, где хотите оплатить, выберите «JetonCash»</li>
<li>Введите код ваучера</li>
<li>Подтвердите оплату</li>
</ol>"""

# --- FLEXEPIN ---
INSTRUCTIONS['flexepin'] = """<h2>Инструкция по использованию ваучера Flexepin</h2>
<ol>
<li>На сайте, где хотите оплатить, выберите «Flexepin»</li>
<li>Введите 16–20-значный PIN-код</li>
<li>Подтвердите оплату</li>
</ol>"""

# --- CHERRY CREDITS ---
INSTRUCTIONS['cherry'] = """<h2>Инструкция по активации Cherry Credits</h2>
<ol>
<li>Войдите на cherrycredits.com</li>
<li>Перейдите в «Profile» → «Redeem» и введите код</li>
<li>Через Cherry Exchange выберите игру и подтвердите</li>
</ol>"""

# --- S1LKPAY ---
INSTRUCTIONS['s1lkpay'] = """<h2>Инструкция по активации ваучера S1lkPay</h2>
<ol>
<li>Войдите в аккаунт сервиса, где хотите оплатить</li>
<li>В разделе пополнения введите код</li>
<li>Подтвердите — баланс зачислится</li>
</ol>"""

# --- OPENBUCKS ---
INSTRUCTIONS['openbucks'] = """<h2>Инструкция по использованию ваучера Openbucks</h2>
<ol>
<li>На сайте, где хотите оплатить, выберите «oBucks»</li>
<li>Введите код и нажмите «Redeem»</li>
<li>Подтвердите оплату</li>
</ol>"""

# --- SEAGM ---
INSTRUCTIONS['seagm'] = """<h2>Инструкция по активации кода SEAGM</h2>
<ol>
<li>Войдите на seagm.com</li>
<li>Перейдите в кошелёк и введите код</li>
<li>Подтвердите — баланс зачислится</li>
</ol>"""

# --- GARENA ---
INSTRUCTIONS['garena'] = """<h2>Инструкция по активации кода Garena</h2>
<ol>
<li>Перейдите в Garena Redeem Center</li>
<li>Войдите в аккаунт и введите PIN</li>
<li>Нажмите «Redeem» и дождитесь подтверждения</li>
</ol>"""

# --- SHOP2GAME / DELTA FORCE ---
INSTRUCTIONS['shop2game'] = """<h2>Инструкция по активации кода Shop2game</h2>
<ol>
<li>Перейдите на shop2game.com</li>
<li>Выберите игру и войдите в аккаунт</li>
<li>Выберите способ оплаты «Garena Voucher» и введите код</li>
<li>Валюта зачислится в игру</li>
</ol>"""

# --- MIDASBUY / PUBG MOBILE ---
INSTRUCTIONS['midasbuy'] = """<h2>Инструкция по активации кода Midasbuy</h2>
<ol>
<li>Перейдите на midasbuy.com/redeem</li>
<li>Введите Player ID (UID игрока)</li>
<li>Введите код без пробелов</li>
<li>UC мгновенно зачислятся на аккаунт</li>
</ol>"""

# --- MOBILE LEGENDS ---
INSTRUCTIONS['mobile_legends'] = """<h2>Инструкция по активации кода Mobile Legends</h2>
<ol>
<li>Откройте Mobile Legends: Bang Bang</li>
<li>Перейдите в «Настройки» → «Redemption Code»</li>
<li>Введите код и нажмите «Okay»</li>
<li>Награды появятся в игровой почте</li>
</ol>"""

# --- HONOR OF KINGS ---
INSTRUCTIONS['honor_of_kings'] = """<h2>Инструкция по активации кода Honor of Kings</h2>
<ol>
<li>Перейдите на сайт пополнения (codashop.com/honor-of-kings)</li>
<li>Войдите и введите UID игрока</li>
<li>Введите код ваучера и нажмите «Submit»</li>
<li>Токены зачислятся в игру</li>
</ol>"""

# --- HUAWEI APPGALLERY ---
INSTRUCTIONS['huawei'] = """<h2>Инструкция по активации кода Huawei AppGallery</h2>
<ol>
<li>Откройте AppGallery на устройстве Huawei</li>
<li>Перейдите в «Me» → «Balance» → «Redeem»</li>
<li>Введите код и подтвердите регион</li>
<li>Баланс обновится в кошельке</li>
</ol>"""

# --- PHONEPE ---
INSTRUCTIONS['phonepe'] = """<h2>Инструкция по активации кода PhonePe</h2>
<ol>
<li>Напишите в чат на Яндекс Маркете — вам отправят номер карты и PIN-код</li>
<li>Откройте приложение PhonePe на смартфоне</li>
<li>Перейдите в «Мой профиль» → «Все способы оплаты» → «PhonePe Gift Card»</li>
<li>Нажмите «Claim now», введите номер карты и PIN-код</li>
<li>Баланс зачислится на аккаунт</li>
</ol>"""

# --- ADOBE ---
INSTRUCTIONS['adobe'] = """<h2>Инструкция по активации кода Adobe</h2>
<ol>
<li>Перейдите на redeem.adobe.com и войдите с Adobe ID</li>
<li>Введите 24-значный код</li>
<li>Подписка автоматически активируется</li>
</ol>"""

# --- SHEIN ---
INSTRUCTIONS['shein'] = """<h2>Инструкция по активации карты SHEIN</h2>
<ol>
<li>Войдите в SHEIN → профиль → «My Wallet» → «Gift Card»</li>
<li>Нажмите «Add Gift Card» и введите 16-значный код + PIN</li>
<li>Баланс зачислится на аккаунт</li>
</ol>"""

# --- SKYPE ---
INSTRUCTIONS['skype'] = """<h2>Инструкция по активации кода Skype</h2>
<ol>
<li>Войдите в Skype</li>
<li>Перейдите на secure.skype.com/wallet/account/voucher</li>
<li>Введите код и нажмите «Redeem»</li>
</ol>"""

# --- RUNESCAPE ---
INSTRUCTIONS['runescape'] = """<h2>Инструкция по активации кода RuneScape</h2>
<ol>
<li>Войдите на runescape.com</li>
<li>Перейдите в «Shop» → «Pre-paid Cards» → «Activate Card»</li>
<li>Введите код и нажмите «Redeem»</li>
</ol>"""

# --- GENSHIN IMPACT ---
INSTRUCTIONS['genshin'] = """<h2>Инструкция по активации кода Genshin Impact</h2>
<ol>
<li>В игре откройте «Settings» → «Account» → «Redeem Code»</li>
<li>Введите код и подтвердите</li>
<li>Награды появятся в игровом почтовом ящике</li>
</ol>"""

# --- DEEZER ---
INSTRUCTIONS['deezer'] = """<h2>Инструкция по активации кода Deezer</h2>
<ol>
<li>Войдите на сайт Deezer → «Settings» → «Subscriptions» → «Redeem code»</li>
<li>Введите код и подтвердите</li>
<li>Подписка активируется</li>
</ol>"""

# --- CRUNCHYROLL ---
INSTRUCTIONS['crunchyroll'] = """<h2>Инструкция по активации кода Crunchyroll</h2>
<ol>
<li>Откройте веб-версию Crunchyroll (не мобильное приложение)</li>
<li>Перейдите в раздел подписки и введите код</li>
<li>Проверьте обновление в «Subscriptions»</li>
</ol>"""

# --- HULU ---
INSTRUCTIONS['hulu'] = """<h2>Инструкция по активации кода Hulu</h2>
<ol>
<li>Перейдите на hulu.com/gift и войдите в аккаунт</li>
<li>Введите PIN-код и нажмите «Redeem»</li>
</ol>"""

# --- TINDER ---
INSTRUCTIONS['tinder'] = """<h2>Инструкция по активации кода Tinder</h2>
<ol>
<li>Войдите в Tinder → «Настройки» → «Платежи» → «Погасить код»</li>
<li>Введите код и подтвердите</li>
</ol>"""

# --- CAPCUT ---
INSTRUCTIONS['capcut'] = """<h2>Инструкция по активации кода CapCut</h2>
<ol>
<li>Откройте веб-версию CapCut (не мобильное приложение)</li>
<li>Выберите план подписки</li>
<li>Введите промо-код в поле при оформлении и подтвердите</li>
</ol>"""

# --- BLU TV ---
INSTRUCTIONS['blutv'] = """<h2>Инструкция по активации кода Blu TV</h2>
<ol>
<li>Войдите в Blu TV → «Billing» → «Redeem»</li>
<li>Введите код и подтвердите</li>
</ol>"""

# --- EXXEN ---
INSTRUCTIONS['exxen'] = """<h2>Инструкция по активации кода Exxen</h2>
<ol>
<li>Войдите в Exxen → профиль → «Billing» → «Gift Code»</li>
<li>Введите код и подтвердите</li>
</ol>"""

# --- WEYYAK ---
INSTRUCTIONS['weyyak'] = """<h2>Инструкция по активации кода Weyyak</h2>
<ol>
<li>Войдите в Weyyak → «Redeem»</li>
<li>Введите код и подтвердите подписку</li>
</ol>"""

# --- BLACKNUT ---
INSTRUCTIONS['blacknut'] = """<h2>Инструкция по активации кода Blacknut</h2>
<ol>
<li>Войдите на Blacknut → «Redeem/Billing»</li>
<li>Введите код и подтвердите</li>
<li>Подписка активируется</li>
</ol>"""

# --- BITDEFENDER ---
INSTRUCTIONS['bitdefender'] = """<h2>Инструкция по активации кода Bitdefender</h2>
<ol>
<li>Войдите на сайт Bitdefender</li>
<li>Перейдите в раздел активации и введите код</li>
<li>Подписка на антивирус активируется</li>
</ol>"""

# --- NOPING ---
INSTRUCTIONS['noping'] = """<h2>Инструкция по активации ваучера NoPing</h2>
<ol>
<li>Войдите на сайт NoPing → «Subscriptions» → «Redeem»</li>
<li>Введите ваучер и подтвердите</li>
</ol>"""

# --- SALIK ---
INSTRUCTIONS['salik'] = """<h2>Инструкция по пополнению Salik</h2>
<ol>
<li>Откройте приложение Salik → «Top Up» → «Recharge»</li>
<li>Введите PIN-код и выберите тег</li>
<li>Подтвердите через SMS</li>
</ol>"""

# --- WALMART ---
INSTRUCTIONS['walmart'] = """<h2>Инструкция по активации карты Walmart</h2>
<ol>
<li>Войдите на walmart.com → «Wallet» → «Gift Cards» → «Add»</li>
<li>Введите 16-значный номер и PIN</li>
<li>Баланс зачислится</li>
</ol>"""

# --- NIKE ---
INSTRUCTIONS['nike'] = """<h2>Инструкция по использованию карты Nike</h2>
<ol>
<li>При оформлении заказа на nike.com введите номер карты и PIN в поле «Gift Card»</li>
<li>Скидка применится к заказу</li>
</ol>"""

# --- H&M ---
INSTRUCTIONS['hm'] = """<h2>Инструкция по использованию карты H&amp;M</h2>
<ol>
<li>При оформлении заказа на hm.com введите код и PIN в поле «Gift Card»</li>
<li>Сумма спишется с карты</li>
</ol>"""

# --- VICTORIA'S SECRET ---
INSTRUCTIONS['victorias_secret'] = """<h2>Инструкция по использованию карты Victoria's Secret</h2>
<ol>
<li>При оформлении заказа на victoriassecret.com введите 16-значный код и PIN</li>
<li>Сумма спишется с карты</li>
</ol>"""

# --- EBAY ---
INSTRUCTIONS['ebay'] = """<h2>Инструкция по активации карты eBay</h2>
<ol>
<li>Войдите на eBay → профиль → «Gift cards/Balance» → «Redeem»</li>
<li>Введите код и подтвердите через email/SMS</li>
</ol>"""

# --- AIRBNB ---
INSTRUCTIONS['airbnb'] = """<h2>Инструкция по активации карты Airbnb</h2>
<ol>
<li>Войдите в Airbnb → «Платежи и выплаты» → «Подарочный баланс» → «Погасить код»</li>
<li>Введите код и PIN</li>
</ol>"""

# --- UBER ---
INSTRUCTIONS['uber'] = """<h2>Инструкция по активации карты Uber</h2>
<ol>
<li>Откройте Uber → «Wallet» → «Add code»</li>
<li>Введите PIN и подтвердите</li>
</ol>"""

# --- ABERCROMBIE ---
INSTRUCTIONS['abercrombie'] = """<h2>Инструкция по использованию карты Abercrombie & Fitch</h2>
<ol>
<li>При оформлении заказа на abercrombie.com введите код и PIN в поле «Gift Cards»</li>
<li>Сумма спишется с карты</li>
</ol>"""

# --- DELIVEROO ---
INSTRUCTIONS['deliveroo'] = """<h2>Инструкция по активации кода Deliveroo</h2>
<ol>
<li>Откройте Deliveroo → «Account» → «Vouchers and credit» → «Redeem»</li>
<li>Введите код и подтвердите</li>
</ol>"""

# --- TALABAT ---
INSTRUCTIONS['talabat'] = """<h2>Инструкция по активации кода Talabat</h2>
<ol>
<li>Откройте Talabat → «Wallet» → «Redeem»</li>
<li>Введите код и подтвердите</li>
</ol>"""

# --- ROCKSTAR GAMES ---
INSTRUCTIONS['rockstar'] = """<h2>Инструкция по активации кода Rockstar Games</h2>
<ol>
<li>Войдите на socialclub.rockstargames.com</li>
<li>Перейдите в раздел активации и введите код</li>
<li>Игра добавится в библиотеку</li>
</ol>"""

# --- R2GAMES ---
INSTRUCTIONS['r2games'] = """<h2>Инструкция по активации кода R2Games</h2>
<ol>
<li>Войдите на r2games.com</li>
<li>Перейдите в «Wallet» → «Redeem» и введите код</li>
<li>Баланс зачислится</li>
</ol>"""

# --- NETEASE GAMES ---
INSTRUCTIONS['netease'] = """<h2>Инструкция по активации кода NetEase Games</h2>
<ol>
<li>Войдите в аккаунт NetEase</li>
<li>Перейдите в раздел пополнения и введите код</li>
<li>Средства зачислятся</li>
</ol>"""

# --- IMO ---
INSTRUCTIONS['imo'] = """<h2>Инструкция по активации кода imo</h2>
<ol>
<li>Откройте приложение imo</li>
<li>Перейдите в настройки аккаунта → «Redeem» или «Пополнение»</li>
<li>Введите код и подтвердите</li>
</ol>"""

# --- EA PLAY ---
INSTRUCTIONS['ea_play'] = """<h2>Инструкция по активации подписки EA Play</h2>
<p><b>Способ 1 — В клиенте EA App на ПК:</b></p>
<ol>
<li>Откройте EA App и войдите в аккаунт</li>
<li>Перейдите в «Settings» → «Redeem Code»</li>
<li>Введите код и подтвердите — подписка EA Play активируется</li>
</ol>
<p><b>Способ 2 — На сайте EA:</b></p>
<ol>
<li>Перейдите на account.ea.com и войдите в аккаунт</li>
<li>Откройте «Payments» → «Redeem Code»</li>
<li>Введите код и подтвердите</li>
</ol>"""

# --- TIKTOK ---
INSTRUCTIONS['tiktok'] = """<h2>Инструкция по активации кода TikTok</h2>
<ol>
<li>Войдите в аккаунт TikTok на сайте или в приложении</li>
<li>Найдите раздел «Redeem» или «Пополнение»</li>
<li>Введите код без пробелов и подтвердите</li>
</ol>"""

# --- VOICEMOD ---
INSTRUCTIONS['voicemod'] = """<h2>Инструкция по активации кода Voicemod</h2>
<ol>
<li>Войдите в аккаунт Voicemod</li>
<li>Перейдите в раздел активации и введите код</li>
<li>Подтвердите — подписка активируется</li>
</ol>"""

# --- TRUE MONEY ---
INSTRUCTIONS['truemoney'] = """<h2>Инструкция по активации ваучера True Money</h2>
<ol>
<li>Откройте приложение True Money или TrueMoney Wallet</li>
<li>Перейдите в раздел пополнения и введите код</li>
<li>Подтвердите — баланс зачислится</li>
</ol>"""

# --- EA SPORTS FC MOBILE ---
INSTRUCTIONS['ea_fc_mobile'] = """<h2>Инструкция по активации кода EA SPORTS FC Mobile</h2>
<ol>
<li>Откройте EA SPORTS FC Mobile на смартфоне</li>
<li>Перейдите в магазин → «Redeem Code»</li>
<li>Введите код без пробелов и подтвердите</li>
<li>FC Points зачислятся на аккаунт</li>
</ol>"""

# --- ZENLESS ZONE ZERO ---
INSTRUCTIONS['zzz'] = """<h2>Инструкция по активации кода Zenless Zone Zero</h2>
<ol>
<li>В игре откройте «Settings» → «Account» → «Redeem Code»</li>
<li>Введите код и подтвердите</li>
<li>Награды появятся в игровом почтовом ящике</li>
</ol>"""

# --- MAGIC CHESS ---
INSTRUCTIONS['magic_chess'] = """<h2>Инструкция по активации кода Magic Chess: Go Go</h2>
<ol>
<li>Откройте Magic Chess: Go Go</li>
<li>Перейдите в «Настройки» → «Redemption Code»</li>
<li>Введите код и подтвердите</li>
</ol>"""

# --- IDENTITY V ---
INSTRUCTIONS['identity_v'] = """<h2>Инструкция по активации кода Identity V</h2>
<ol>
<li>Откройте Identity V и войдите в аккаунт</li>
<li>Перейдите в «Settings» → «Redeem Code»</li>
<li>Введите код и подтвердите</li>
</ol>"""

# --- МОБИЛЬНЫЙ ОПЕРАТОР (универсальная) ---
INSTRUCTIONS['mobile_operator'] = """<h2>Инструкция по пополнению баланса</h2>
<ol>
<li>Откройте приложение оператора на смартфоне и войдите в аккаунт</li>
<li>Перейдите в раздел пополнения (Top-up / Recharge)</li>
<li>Введите код ваучера без пробелов и подтвердите</li>
<li>Баланс зачислится, придёт SMS-подтверждение</li>
</ol>"""

# --- ИГРОВАЯ ВАЛЮТА (универсальная) ---
INSTRUCTIONS['game_currency'] = """<h2>Инструкция по активации кода</h2>
<ol>
<li>Откройте игру и войдите в аккаунт</li>
<li>Перейдите в настройки или магазин</li>
<li>Найдите раздел «Redeem Code» или «Активировать код»</li>
<li>Введите код без пробелов и подтвердите</li>
<li>Валюта или награды появятся в аккаунте</li>
</ol>"""

# --- УНИВЕРСАЛЬНАЯ ---
INSTRUCTIONS['universal'] = """<h2>Инструкция по активации кода</h2>
<ol>
<li>Войдите в аккаунт на сайте или в приложении сервиса</li>
<li>Найдите раздел «Redeem» / «Активировать код» / «Пополнение»</li>
<li>Введите код без пробелов и подтвердите</li>
<li>Баланс или подписка активируются на аккаунте</li>
</ol>"""


# ============================================================
# МАППИНГ СЕРВИСОВ → КЛЮЧ ИНСТРУКЦИИ
# ============================================================

SERVICE_MAP = {
    # Multi-method
    'Xbox Store': 'xbox',
    'Microsoft Store': 'xbox',
    'PlayStation Store': 'playstation',
    'Google Play': 'google_play',
    'App Store': 'apple',
    'App Store,iTunes': 'apple',
    'App Store,Tunes': 'apple',
    'App Srore,iTunes': 'apple',
    'Amazon': 'amazon',
    'Nintendo eShop': 'nintendo',
    'Nintendo Switch Online': 'nintendo_online',
    'Paysafecard': 'paysafecard',
    'Meta Quest': 'meta_quest',
    'EA App': 'ea',
    'EA Play': 'ea_play',
    'Razer Gold': 'razer',

    # Single-method services
    'Roblox': 'roblox',
    'Riot': 'riot',
    'League of Legends': 'riot',
    '2XKO': 'riot',
    'Valorant': 'valorant',
    'Netflix': 'netflix',
    'Spotify': 'spotify',
    'Battle net': 'battlenet',
    'Blizzard': 'battlenet',
    'Epic': 'epic',
    'Epic Games Store': 'epic',
    'Neosurf': 'neosurf',
    'CASHlib': 'cashlib',
    'Rewarble': 'rewarble',
    'Twitch': 'twitch',
    'Discord': 'discord',
    'Kinguin': 'kinguin',
    'Eneba': 'eneba',
    'Noon': 'noon',
    'Bigo Live': 'bigo',
    'Tango Live': 'tango',
    'ExitLag': 'exitlag',
    'MiFinity': 'mifinity',
    'iCash One': 'icash',
    'JetonCash': 'jetoncash',
    'Flexepin': 'flexepin',
    'Cherry Credits': 'cherry',
    'S1lkPay': 's1lkpay',
    'Openbucks': 'openbucks',
    'SEAGM': 'seagm',
    'Garena': 'garena',
    'shop2game': 'shop2game',
    'Midasbuy': 'midasbuy',
    'Mobile Legends': 'mobile_legends',
    'Honor of Kings': 'honor_of_kings',
    'Huawei': 'huawei',
    'PhonePE': 'phonepe',
    'Adobe': 'adobe',
    'SHEIN': 'shein',
    'Skype': 'skype',
    'RuneScape': 'runescape',
    'Genshin Impact': 'genshin',
    'Deezer': 'deezer',
    'Crunchyroll': 'crunchyroll',
    'Hulu': 'hulu',
    'Tinder': 'tinder',
    'CapCut': 'capcut',
    'Blu TV': 'blutv',
    'Exxen': 'exxen',
    'Weyyak': 'weyyak',
    'Blacknut': 'blacknut',
    'Bitdefender': 'bitdefender',
    'NoPing': 'noping',
    'Salik': 'salik',
    'Walmart': 'walmart',
    'Nike': 'nike',
    'H&M': 'hm',
    "Victoria's Secret": 'victorias_secret',
    'eBay': 'ebay',
    'Airbnb': 'airbnb',
    'Uber': 'uber',
    'Abercrombie & Fitch': 'abercrombie',
    'Deliveroo': 'deliveroo',
    'Talabat': 'talabat',
    'Rockstar': 'rockstar',
    'Rockstar Games': 'rockstar',
    'R2Games': 'r2games',
    'NetEase Games': 'netease',
    'imo': 'imo',
    'TikTok': 'tiktok',
    'Voicemod': 'voicemod',
    'True Money': 'truemoney',
    'EA SPORTS FC Mobile': 'ea_fc_mobile',
    'Zenless Zone Zero': 'zzz',
    'Magic Chess: Go Go': 'magic_chess',
    'Identity V': 'identity_v',

    # Game currencies (universal game instruction)
    'Castle Clash: World Ruler': 'game_currency',
    'Doomsday: Last Survivors': 'game_currency',
    'Arena Breakout': 'game_currency',
    'Undawn': 'game_currency',
    'Jawaker': 'game_currency',
    'AFK Journey': 'game_currency',
    'Destiny: Rising': 'game_currency',
    'Dragonheir: Silent Gods': 'game_currency',
    'Travian Legends': 'game_currency',
    'Blood Strike': 'game_currency',
    'Black Clover Mobile': 'game_currency',
    'PUBG New State Mobile': 'game_currency',
    'PUBG: BATTLEGROUNDS': 'game_currency',
    'Lords Mobile': 'game_currency',
    'Robi': 'game_currency',
}

# Mobile operators
MOBILE_OPERATORS = {
    'Orange', 'Vodafone', 'vodafone', 'O2', 'Three', 'EE Mobile', 'Drei', 'Blau',
    'Lyca Mobile', 'eir Mobile', 'KPN Mobile', 'Proximus', 'AT&T', 'Lebara',
    'Etisalat', 'du', 'Syma Mobile', 'Zain', 'Airalo', 'A1', 'Bouygues',
    'Claro', 'Movistar', 'Personal', 'Tuenti', 'DIGI', 'TIM', 'iliad', 'Windtre',
    'Euskaltel', 'MASMOVIL', 'Simyo', 'Yoigo', 'YouMobile', 'Red Bull Mobile',
    'Bhutan Telecom', 'Tele2', 'BASE Mobile', 'Base', 'Jim Mobile', 'Now Mobile',
    'Batelco', 'Omantel', 'Umniah', 'Renna', 'Magenta',
    'Telekom', 'Congstar', 'FYVE', 'Ortel Mobile', 'T-Mobile', 'Otelo',
    'AY YILDIZ', 'Kena Mobile', 'ho.', 'Ho.', 'Very Mobile', 'Tiscali',
    'Djezzy', 'Mobilis', 'China Mobile', 'China Telecom', 'China Unicom',
    'Algar Telecom', 'Vivo', 'Econet', 'Ethio Telecom', 'Safaricom',
    'Mascom', 'btc', 'Teletalk', 'Lucky Mobile', 'Hello VoIP', 'Five VoIP',
    'Alou', 'Unitel', 'Unitel T+', 'Roshan',
}


def get_instruction_key(service, description):
    """Определить ключ инструкции для данного сервиса."""
    if not service:
        return 'universal'

    # Steam: различаем ключ игры vs пополнение кошелька
    if service == 'Steam':
        desc_lower = description.lower() if description else ''
        # Wallet cards: "пополнение кошелька", "wallet", "баланс steam"
        if any(kw in desc_lower for kw in ['кошелёк', 'кошелек', 'wallet', 'пополнение баланса steam', 'карта steam', 'gift card steam', 'подарочная карта steam']):
            return 'steam_wallet'
        # Default: game key
        return 'steam_game'

    # Lookup in service map
    if service in SERVICE_MAP:
        return SERVICE_MAP[service]

    # Mobile operators
    if service in MOBILE_OPERATORS:
        return 'mobile_operator'

    # Fallback
    return 'universal'


def replace_instruction(description, new_instruction):
    """Заменить секцию инструкции в описании."""
    if not description:
        return description

    # Find instruction section: look for <h2> containing "Инструкция" or "активации" or "использованию" or "пополнению"
    patterns = [
        r'<h2>[^<]*[Ии]нструкция[^<]*</h2>',
        r'<h2>[^<]*активации[^<]*</h2>',
        r'<h2>[^<]*использовани[^<]*</h2>',
        r'<h2>[^<]*пополнени[^<]*</h2>',
        r'<h2>[^<]*Как активировать[^<]*</h2>',
        r'<h2>[^<]*Активация[^<]*</h2>',
    ]

    instr_start = -1
    for pat in patterns:
        m = re.search(pat, description)
        if m:
            instr_start = m.start()
            break

    if instr_start == -1:
        # No instruction section found, append at end
        return description.rstrip() + '\n\n' + new_instruction.strip()

    # Replace from instruction h2 to end
    return description[:instr_start].rstrip() + '\n\n' + new_instruction.strip()


def main():
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    rows = data['Данные о товарах']

    updated = 0
    skipped = 0
    no_service = 0
    stats = {}

    for i in range(7, len(rows)):
        service = rows[i][45] if len(rows[i]) > 45 and rows[i][45] else None
        description = rows[i][9] if rows[i][9] else None

        if not service or not description:
            no_service += 1
            continue

        instr_key = get_instruction_key(service, description)

        if instr_key not in INSTRUCTIONS:
            skipped += 1
            continue

        new_instr = INSTRUCTIONS[instr_key]
        new_desc = replace_instruction(description, new_instr)

        if new_desc != description:
            rows[i][9] = new_desc
            updated += 1
            stats[instr_key] = stats.get(instr_key, 0) + 1
        else:
            skipped += 1

    # Save
    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n=== РЕЗУЛЬТАТ ===")
    print(f"Обновлено: {updated}")
    print(f"Без изменений: {skipped}")
    print(f"Без сервиса: {no_service}")
    print(f"\nПо типам инструкций:")
    for key, cnt in sorted(stats.items(), key=lambda x: -x[1]):
        print(f"  {key}: {cnt}")


if __name__ == '__main__':
    main()
