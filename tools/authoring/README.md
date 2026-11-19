# Генераторы уроков пилотного пакета

Уроки py-02…py-10 написаны как Python-скрипты: `cd tools/authoring && python3 py05.py` перезаписывает файлы урока
(scenario.json, notes.md, lesson.json, assignments). Действия анимации привязываются к фразам озвучки по подстроке (`at=`).
После правки: `python3 tools/validate_content.py content/packs`.
