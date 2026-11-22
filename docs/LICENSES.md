# LICENSES

| Компонент | Лицензия | В APK |
| --- | --- | --- |
| Chaquopy 17 | MIT | да |
| CPython 3.13 | PSF | да |
| AndroidX / Jetpack Compose / Kotlin coroutines | Apache-2.0 | да |
| CodeMirror 6 | MIT | да |
| esbuild | MIT | нет (сборка) |
| FastAPI 0.125 / Starlette / pydantic 1.10 / httpx 0.28 / anyio | MIT / BSD-3 | да (режим A) |
| sql.js 1.13 (SQLite) | MIT (SQLite — public domain) | да |
| web-tree-sitter 0.20.8, tree-sitter-kotlin (tree-sitter-wasms 0.1.12) | MIT | да |
| acorn 8.14, acorn-walk 8.3 | MIT | да |
| Kotlin compiler (kotlinc 2.1.20) | Apache-2.0 | нет (CI и шаблон GitHub Actions) |
| Pyodide 0.29.5 | MPL-2.0 | да (без изменений) |
| Piper TTS | GPL-3.0-or-later | нет (конвейер контента) |
| Chatterbox Multilingual | MIT | нет (конвейер контента); аудио содержит водяной знак Perth |
| Голоса Piper ru_RU-denis, ru_RU-dmitri | датасет CC0 | аудио уроков |
| llama.cpp / ggml (b12628, коммит 8a97fa9) | MIT | да (libmentor, libllama, libggml*) |
| Qwen3-4B-Instruct-2507, Qwen3-1.7B (GGUF, квантование unsloth), Qwen2.5-Coder-0.5B/1.5B-Instruct GGUF | Apache-2.0 | нет: ученик скачивает файл сам, приложение проверяет SHA-256 |

Версии зависимостей Gradle и Python-пакетов CI формирует для каждой сборки (`dependencies.txt`, артефакт `code-academy-audit`; прикладывается к релизу). Иконка приложения — оригинальная (вектор «</>»), сторонних изображений в приложении нет.
