# Генераторы уроков пилотного пакета

Уроки py-02…py-10 написаны как Python-скрипты: `cd tools/authoring && python3 py05.py` перезаписывает файлы урока
(scenario.json, notes.md, lesson.json, assignments). Действия анимации привязываются к фразам озвучки по подстроке (`at=`).
После правки: `python3 tools/validate_content.py content/packs`.

## Состав
- Python-уроки: `lib.py` (`from lib import *`; `begin`, `stdout_task`, `fn_task`, `predict_task`, `finish`), пример — `pd06.py`, `sec07.py`.
- Веб: `mk.py`/`webib.py` (`scene`, `page`, `style`, `web_verify`), пример — `web05.py`, `web06.py`. Проверки в Chromium на ширине 360 px.
- JavaScript: `jsib.py` (`js_run`, `fn_task`, `merge_js_lesson`), пример — `js06.py`, `js07.py`.
- Проекты: `projects.py` (`milestone`, `write_project`, `verify`), пример — `portfolio.py`. `write_project` сам проверяет эталон, заготовки и неверные решения и не записывает проект, если проверка не прошла.
- Kotlin-уроки используют заглушки `tools/kotlin-stubs/android` (см. TECHNICAL_DECISIONS).

## Проверка
1. Локально: `python3 tools/validate_content.py content/packs` (ошибки про отсутствующие fastapi/sql/kotlin-воркер — ограничение среды).
2. В CI по пакету: `gh workflow run validate-pack.yml --ref wip -f packs="<пакет>"`, затем `gh run view <id> --json status,conclusion`.
3. Перед слиянием в `main` — полный Android-CI и workflow «Narrate lessons» (озвучка).

