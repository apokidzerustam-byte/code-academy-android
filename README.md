# Code Academy Android

Бесплатная офлайн-академия программирования для Android: анимированные уроки с озвучкой, редактор кода, запуск программ,
автопроверка заданий, подсказки, адаптивное повторение, мини-проекты и необязательный ИИ-наставник, работающий на телефоне.
Без аккаунта, без рекламы и без интернета: в APK нет разрешения `INTERNET`.

**Статус: 0.10.0 (MVP-кандидат).** Работает полный цикл урока (видео-сценарий → конспект → редактор → запуск → задание → проверка →
подсказка → прогресс), 15 уроков (Python — 10, веб, SQL, FastAPI, Kotlin) и 4 мини-проекта. Полный курс из 15 этапов ещё не написан:
подробная честная картина — в [docs/ACCEPTANCE.md](docs/ACCEPTANCE.md) и [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md).

## Установка на телефон
Инструкция по шагам — [docs/USER_GUIDE.md](docs/USER_GUIDE.md). Коротко: APK с озвучкой курса весит около 180 МБ и не
помещается в git (лимит 100 МБ на файл), поэтому каждая успешная сборка `main` кладёт его в
[черновик релиза «Прототип (последняя сборка)»](https://github.com/apokidzerustam-byte/code-academy-android/releases) —
он виден владельцу репозитория после входа в GitHub. Скачать `code-academy-proto.apk`, открыть, разрешить установку из этого
источника. Новая версия ставится поверх старой.

## Что внутри
| Папка | Назначение |
| --- | --- |
| `app/` | Приложение (Kotlin, Compose): курс, редактор, раннеры Python/Web/SQL, адаптивное обучение, наставник, настройки |
| `app/src/main/cpp/` | JNI-обёртка над llama.cpp (нейросетевой наставник) |
| `app/src/main/python/ca_runner.py` | Учебная песочница Python (режим A) |
| `content/` | Контент-пакеты (JSON + конспекты), схемы, база знаний наставника |
| `editor-web/`, `web-runner/`, `pyodide-web/` | Исходники редактора CodeMirror, веб-раннера (HTML/CSS/JS, SQL, Kotlin) и раннера Pyodide (собираются в assets) |
| `harness-tests/` | Тесты песочницы и валидатора контента (pytest) |
| `tools/` | Валидатор контента, загрузка исходников llama.cpp |
| `ci/` | Скрипты CI: тесты на эмуляторе, аудит APK, замеры старта, проверка модели наставника |
| `content-pipeline/` | Производство контента (озвучка), в APK не входит |
| `docs/` | Статус, архитектура, решения, тест-отчёт, приёмка, релиз, руководство, лицензии |

## Документы
- [USER_GUIDE.md](docs/USER_GUIDE.md) — установка, обновление, настройки, наставник, резервная копия, что делать при сбое.
- [ACCEPTANCE.md](docs/ACCEPTANCE.md) — соответствие ТЗ: что выполнено и проверено, что нет.
- [RELEASE.md](docs/RELEASE.md) — как выпустить версию, релизный ключ подписи, чего нельзя делать с ключом.
- [ARCHITECTURE.md](docs/ARCHITECTURE.md), [TECHNICAL_DECISIONS.md](docs/TECHNICAL_DECISIONS.md), [DATA_MODEL.md](docs/DATA_MODEL.md).
- [TEST_REPORT.md](docs/TEST_REPORT.md), [TEST_PLAN.md](docs/TEST_PLAN.md), [CHANGELOG.md](docs/CHANGELOG.md), [TODO.md](docs/TODO.md).
- [LICENSES.md](docs/LICENSES.md) — реестр лицензий (версии зависимостей CI прикладывает к каждому релизу: `dependencies.txt`).

## Сборка
Сборка и тесты идут в GitHub Actions (`.github/workflows/android.yml`): JVM-тесты, эмуляторы Android 10 и 14, проверка наставника
с настоящими моделями, аудит APK. Релиз — тег `v*` (workflow «Выпуск»), результат — черновик релиза.

Локально (JDK 17, Android SDK + NDK 29, Python 3.13, Node 22, Gradle 8.14):
```
cd editor-web && npm install && npm run build && cd ..   # аналогично web-runner, pyodide-web (см. android.yml)
bash tools/fetch-llama.sh
gradle :app:assembleDebug
```

## Лицензии
Все зависимости приложения — MIT / Apache-2.0 / PSF / MPL-2.0 (Pyodide, без изменений). Модели наставника в APK не входят и скачиваются
учеником сам (Apache-2.0). См. [docs/LICENSES.md](docs/LICENSES.md).
