# ARCHITECTURE

## Слои
- **UI** — Jetpack Compose + Material 3, MVVM, одна Activity, Navigation Compose.
- **Домен** — движки на чистом Kotlin (тестируются без Android).
- **Данные** — Room + DataStore + файловая система приложения + контент-пакеты.
- **Исполнение** — `CodeRunner`:
  - **W** (по умолчанию): Pyodide 0.29.5 / Python 3.13 в Web Worker WebView — изолированный процесс рендерера Chromium, без сети и файлов устройства.
  - **A** («ограниченный режим»): Chaquopy / Python 3.13 в процессе `:runner` — для asyncio, потоков, FastAPI-сервера и устройств со старым WebView.
  - Одна песочница `ca_runner.py` для обоих: запуск (`run`) и автопроверка (`check`, виды stdout / function / answer / fastapi).
  - **Веб-раннер** (`assets/webrunner`, исходники в `web-runner/`): одна невидимая WebView с хост-страницей
    (WebViewAssetLoader, CSP, WebMessageListener только для своего origin). HTML/CSS/JS — iframe `sandbox` + CSP
    `connect-src 'none'`, циклы инструментированы (acorn); SQL — Web Worker с sql.js; Kotlin — Web Worker с tree-sitter.
    Зависшая страница: таймаут → `caStop()` → проверка ответа → остановка рендер-процесса (API 29+) или пересоздание WebView.
  - Язык задания: веб-задание несёт свой `tests.lang`; FastAPI и «предскажи результат» — всегда Python.

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
                                    ├─► :runner (Binder)                   ─► Chaquopy + ca_runner (+FastAPI) [A]
                                    └─► WebView renderer: хост webrunner   ─► iframe (HTML/CSS/JS) | Worker sql.js | Worker tree-sitter
Приложение ──Mentor──► LiteMentor (правила, конспекты, подсказки) ──► SolutionGuard ──► ответ
                  └──► MentorClient ──Messenger──► :mentor (MentorService) ─► JNI libmentor ─► llama.cpp (CPU) ─► GGUF из files/models
```

## Учебные проекты и резервная копия (этап 8)
- Контент: `content/packs/<pack>/projects/<id>/project.json` (схема `project.schema.json`): этапы с условием, файлами этапа,
  тестами всего проекта, эталоном и типовыми ошибками. Python — `ca_runner.check(kind=project)`, HTML — веб-раннер с файлами проекта.
- Приложение: `ProjectRepository.startCourse/addMissingFiles` (связь через `.course`), `AssessmentService.evaluateProject`,
  `ui/ProjectTaskPanel` в IDE, `ProgressRepository.recordMilestone`.
- `data/Backup.kt`: `BackupFormat` (формат, ZIP, проверки) и `BackupManager` (дамп всех таблиц через SupportSQLite, восстановление
  одной транзакцией, удаление данных). Наблюдатели Room узнают об изменениях по завершении транзакции.
- CI: `ci/backup-clear-test.sh` — фаза 1 (данные + копия) → `pm clear` → фаза 2 (данных нет → восстановление → сравнение).

## ИИ-наставник (этап 9)
- Пакет `mentor/`, чистый Kotlin (проверяется JVM-тестами без Android):
  - `IntentClassifier` — намерение по основам русских слов (просьба о решении проверяется первой);
  - `ErrorExplainer` — каталог правил для ошибок Python/JS/SQL/Kotlin: тип + сообщение + строка → объяснение,
    «что проверить», навык (→ урок); опечатки в именах — расстояние редактирования с перестановкой;
  - `KnowledgeBase` — BM25 по разделам конспектов и частым ошибкам всех уроков (в памяти, строится один раз);
  - `LiteMentor` — лёгкий режим: подсказка следующей ступени лестницы, разбор ошибки, тема из конспекта, простые
    проверки кода, упражнения урока, советы по структуре;
  - `SolutionGuard` — защита от выдачи решения: новые строки эталона, 6-граммы токенов эталона, исправленный отступ,
    много нового кода, имена и значения эталона, ожидаемый вывод «предскажи»;
  - `Mentor` + `PromptBuilder` — нейросетевой режим: ChatML для Qwen2.5-Coder, в промпт не попадает эталон,
    текст ученика не может открыть служебную метку; ответ показывается построчно только после защиты,
    при утечке или уходе с русского заменяется ответом лёгкого режима. Просьбы о решении и упражнения модель не получает.
- Android: `MentorService` (процесс `:mentor`, фоновый поток, выгрузка через 3 мин простоя, остановка при перегреве
  PowerManager ≥ SEVERE, путь модели только внутри files/models), `MentorClient` (Messenger, отмена, гибель процесса →
  лёгкий режим), `NativeLlm` (JNI), `ModelManager` (импорт файла из «Загрузок» с SHA-256, проверки памяти/места/ABI).
- Нативная часть: `app/src/main/cpp` — `mentor_core` (llama.cpp: batch_ext + `llama_process`, сэмплер с штрафом
  повторов, abort-callback, только целые символы UTF-8), `mentor_jni`, `mentor_cli` (то же ядро для CI).
  llama.cpp b12628 подтягивается `tools/fetch-llama.sh` (фиксированный коммит), варианты CPU-бэкенда грузятся
  из папки библиотек (`GGML_BACKEND_DL`, `useLegacyPackaging`).
- UI: `MentorPanel` в задании, этапе проекта и IDE; экран «Наставник»; раздел настроек с установкой модели по шагам.
