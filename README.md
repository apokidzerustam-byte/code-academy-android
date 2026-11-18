# Code Academy Android

Бесплатная офлайн-академия программирования для Android: уроки, IDE, запуск кода, автопроверка, адаптивное повторение.

**Статус: этап 0 — технические прототипы.** Это ещё не учебное приложение. Подробности — в [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md).

## Что внутри
| Папка | Назначение |
| --- | --- |
| `app/` | Прототип: раннер Python (уровни изоляции A и B), прототип редактора CodeMirror |
| `app/src/main/python/ca_runner.py` | Учебная песочница Python |
| `harness-tests/` | Тесты песочницы на обычном Python (pytest) |
| `editor-web/` | Исходники редактора CodeMirror 6 (собираются в assets) |
| `probe-fastapi/` | Зонд: работает ли FastAPI в Chaquopy |
| `content-pipeline/` | Производство контента (озвучка Piper), в APK не входит |
| `docs/` | Статус, архитектура, решения, тест-отчёт, лицензии |

## Сборка
Сборка идёт в GitHub Actions (`.github/workflows/android.yml`): APK скачивается из артефактов прогона.

Локально (JDK 17, Android SDK, Python 3.13, Node 22, Gradle 8.14):
```
cd editor-web && npm install && npm run build && cd ..
gradle :app:assembleDebug
```

## Лицензии
Все зависимости приложения — MIT / Apache-2.0 / PSF. См. [docs/LICENSES.md](docs/LICENSES.md).
