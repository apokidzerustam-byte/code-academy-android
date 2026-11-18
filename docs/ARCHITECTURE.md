# ARCHITECTURE

Полная схема — в техническом отчёте (Claude Docs). Кратко:

- **UI** — Jetpack Compose, MVVM, feature-модули (home, course, lesson, ide, assignment, review, …).
- **Домен** — движки на чистом Kotlin: CourseEngine, AssignmentEngine, TestEngine, ReviewEngine, ProgressManager…
- **Данные** — Room + DataStore + контент-пакеты (JSON/Markdown/аудио/VTT/тесты).
- **Исполнение** — отдельный процесс-раннер, связь только через Binder (Messenger):

```
MainActivity / IDE ──RunnerClient──► Binder ──► RunnerService (:runner)          уровень A
                                              └► IsolatedRunnerService (:iso_runner) уровень B
                                                   └─ Chaquopy → ca_runner.run(code)
```

### Протокол раннера
`MSG_RUN(code, stdin, timeoutMs, sandboxDir)` → `MSG_RESULT(status, stdout, stderr, truncated, durationMs)`.
`MSG_STOP` и сторожевой таймер уничтожают процесс раннера целиком; клиент переподключается к новому процессу.

### Уровни изоляции
| | A (`:runner`) | B (`isolatedProcess`) |
| --- | --- | --- |
| UID | приложения | отдельный, без разрешений |
| Файлы приложения | закрыты только Python-хуками | закрыты ядром (SELinux `isolated_app`) |
| Сеть | закрыта Python-хуками | закрыта ядром |
| Файлы проекта ученика | папка проекта | пока нет (план: передача дескрипторов) |
| Граница безопасности | **нет** (защита от ошибок) | да |
