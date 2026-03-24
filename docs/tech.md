# Technical Context

## Stack
- Python 3.12 — скрипты обработки данных
- openpyxl — чтение/запись Excel файлов
- Pillow (PIL) — генерация изображений карточек
- JSONL — промежуточный формат данных пайплайна

## Why This Stack
Python + openpyxl — простейший способ работать с Excel-выгрузками Яндекс Маркета. JSONL вместо прямой работы с xlsx — проще парсить, валидировать и редактировать построчно. Pillow — генерация карточных изображений 1080x1440.

## Pipeline Flow
```
xlsx (Яндекс Маркет) → prepare.py → source.jsonl + work.jsonl
  → loop0 (группировка) → loop1 (характеристики) → loop2 (названия/теги)
  → loop3 (описания) → loop4 (инструкции)
  → validate.py → finalize.py → xlsx (загрузка обратно)
```

## Key Decisions
- **JSONL over direct xlsx editing**: пайплайн работает с JSON Lines, конвертация на входе/выходе через prepare.py и finalize.py
- **Group-based processing**: карты/подписки обрабатываются группами по бренду/региону (~2600 шт.), игры — по одной (~730 шт.)
- **write_result.py as safe interface**: Claude пишет в work.jsonl только через этот скрипт для валидации данных
