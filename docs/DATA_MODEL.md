# DATA_MODEL — локальные данные (Room / SQLite)

Всё хранится на устройстве, без аккаунта и облака (раздел 14 ТЗ). Контент (уроки, задания, тесты) — в контент-пакетах (файлы), в БД — только состояние ученика.

## Таблицы

| Таблица | Ключ | Поля | Зачем |
| --- | --- | --- | --- |
| `installed_pack` | `packId` | version, installedAt, sizeBytes, sha256 | Какие этапы скачаны/импортированы |
| `lesson_progress` | `lessonId` | packId, status (NOT_STARTED/IN_PROGRESS/PASSED), sceneIndex, scenePositionMs, startedAt, passedAt, timeSpentMs | Продолжение урока с того же места |
| `attempt` | `id` | lessonId, assignmentId, startedAt, durationMs, code (сжатый), passed, testsPassed, testsTotal, hintsUsed (0–6), errorType, runner (W/A) | История попыток, статистика, точность |
| `error_log` | `id` | attemptId, skillId, errorType (SyntaxError, NameError, логическая…), message | История ошибок, Error-Based Learning |
| `skill_state` | `skillId` | status (NOT_STUDIED/LEARNING/NEEDS_REVIEW/MASTERED/CONFIRMED), accuracy, attempts, lastPracticedAt | Карта знаний |
| `review_item` | `id` | skillId, intervalDays, ease, dueAt, lastResult, streak | Интервальное повторение |
| `project` | `id` | title, kind (MINI/THROUGH/FINAL), createdAt, updatedAt, runner | Учебные проекты |
| `project_file` | (`projectId`, `path`) | content, updatedAt | Файлы проекта (автосохранение) |
| `achievement` | `id` | unlockedAt | Достижения за реальные навыки |
| `daily_activity` | `date` | minutes, tasksSolved, reviewsDone | Серии, недельные цели (без наказания за перерывы) |
| `note` | `id` | lessonId, text, createdAt | Заметки ученика |

Настройки (тема, размер текста, режим производительности, IDE) — DataStore, не Room.

## Правила адаптации (раздел 10 ТЗ, пороги настраиваемые)

| Точность по навыку | Действие |
| --- | --- |
| < 60 % | Повторное объяснение (сцена урока + конспект) |
| 60–79 % | Закрепление: доп. задания того же навыка |
| 80–89 % | Дополнительная проверка (скрытые тесты, «Без подсказок») |
| 90–100 % | Переход дальше + повторение по расписанию |

«Освоено» не выставляется по одному тесту: нужно ≥ 2 успешных попытки в разные дни; «Подтверждено» — успешное повторение после интервала ≥ 7 дней.

## Интервальное повторение
Стартовые интервалы 1 → 3 → 7 → 14 → 30 дней. Ошибка — шаг назад (минимум 1 день). Успех без подсказок — следующий интервал; успех с подсказками ≥ 3-й ступени — интервал не растёт. Подсказки учитываются в статистике, но не обнуляют результат.

## Экспорт / импорт
ZIP: `progress.json` (все таблицы, версия схемы), `projects/<id>/…` (файлы проектов), `manifest.json` (версия приложения, дата, sha256). Импорт — с проверкой версии схемы и миграцией.
