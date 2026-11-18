# ARCHITECTURE

## Слои
- **UI** — Jetpack Compose + Material 3, MVVM, одна Activity, Navigation Compose.
- **Домен** — движки на чистом Kotlin (тестируются без Android).
- **Данные** — Room + DataStore + файловая система приложения + контент-пакеты.
- **Исполнение** — `CodeRunner`:
  - **W** (по умолчанию): Pyodide 0.29.5 / Python 3.13 в Web Worker WebView — изолированный процесс рендерера Chromium, без сети и файлов устройства.
  - **A** («ограниченный режим»): Chaquopy / Python 3.13 в процессе `:runner` — для asyncio, потоков, FastAPI-сервера и устройств со старым WebView.
  - Одна песочница `ca_runner.py` для обоих: запуск (`run`) и автопроверка (`check`).

## 22 модуля ТЗ → Gradle-модули
| Модуль ТЗ | Где |
| --- | --- |
| AppCore, NavigationManager | `:app` |
| CourseEngine, LessonManager, ContentManager | `:core:content` (чтение/валидация пакетов), `:feature:course`, `:feature:lesson` |
| VideoManager, AudioManager | `:feature:lesson` — плеер анимированного урока: сценарий + аудио (Media3) + субтитры VTT |
| IDEManager, TerminalManager | `:feature:ide` (CodeMirror 6 в WebView), `:feature:terminal` |
| CodeExecutionEngine, SecurityManager | `:core:runner` (CodeRunner W/A, политика песочницы) |
| AssignmentEngine, TestEngine | `:core:assessment` (вызов `ca_runner.check`, подсказки 6 ступеней) |
| ProgressManager, KnowledgeMapManager, ReviewEngine, AnalyticsManager | `:core:learning` (чистый Kotlin) |
| ProjectManager, BackupManager | `:core:projects`, `:core:backup` |
| TutorEngine | `:core:tutor` (правила разбора ошибок; позже — llama.cpp) |
| DatabaseManager, SettingsManager | `:core:database` (Room), `:core:settings` (DataStore) |

## Контент
`content/schema/*.schema.json` — формат; `content/packs/<pack>/` — этапы курса; `tools/validate_content.py` — проверка в CI (эталоны проходят тесты, типовые ошибки ловятся, код из уроков запускается). Озвучка — голосом автора (Chatterbox) в CI, аудио поставляется вместе с пакетом.

## Схема процессов
```
Приложение (UI, Room) ──CodeRunner──┬─► WebView renderer (изолированный) ─► Worker: Pyodide + ca_runner   [W]
                                    └─► :runner (Binder)                   ─► Chaquopy + ca_runner          [A]
```
