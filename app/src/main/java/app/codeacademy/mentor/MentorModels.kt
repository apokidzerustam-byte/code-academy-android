package app.codeacademy.mentor

import app.codeacademy.content.CommonMistake

/** Что хочет ученик. Определяется по тексту запроса или по нажатой кнопке. */
enum class Intent {
    SOLUTION_REQUEST, EXPLAIN_ERROR, HINT, EXPLAIN_TOPIC, REVIEW, EXERCISE, ARCHITECTURE, OTHER,
}

/** Откуда ответ: правила и материалы курса или локальная нейросеть. */
enum class Source { LITE, LLM }

/**
 * Задание или этап проекта. Эталонное решение используется только защитой от выдачи решения:
 * в запрос к модели оно не попадает.
 */
data class TaskContext(
    val id: String,
    val title: String,
    val statement: String,
    /** write | fix | predict | review | milestone */
    val type: String,
    /** python | js | html | sql | kotlin */
    val language: String,
    val hints: List<String>,
    val starterFiles: Map<String, String>,
    val solutionFiles: Map<String, String>,
    /** Для «предскажи результат»: верный ответ (его тоже нельзя выдавать). */
    val expectedAnswer: String? = null,
    /** Задание с проверкой `answer` любого вида (например, команда терминала): ответ вводят текстом. */
    val answerOnly: Boolean = false,
) {
    val isAnswerTask: Boolean get() = type == "predict" || type == "review" || answerOnly
    /** Нужно проследить выполнение кода (а не вспомнить команду): «предскажи» и разбор кода. */
    val isTrace: Boolean get() = type == "predict" || type == "review"
}

/** Ссылка на урок курса. */
data class LessonLink(val packId: String, val lessonId: String, val title: String) {
    val key: String get() = "$packId/$lessonId"
}

/** Всё, что наставник знает о текущей ситуации. Остаётся на устройстве. */
data class MentorContext(
    val lesson: LessonLink? = null,
    val lessonSkills: List<String> = emptyList(),
    val commonMistakes: List<CommonMistake> = emptyList(),
    val task: TaskContext? = null,
    /** Код или ответ ученика (для проектов — файлы, склеенные с заголовками). */
    val code: String = "",
    /** Последняя ошибка: traceback, сообщение проверки, stderr. */
    val error: String? = null,
    /** Сколько раз ученик отправлял решение на проверку. */
    val attempts: Int = 0,
    /** Сколько подсказок уже открыто (0..hints.size). */
    val hintsShown: Int = 0,
    /** Язык кода, если задания нет (IDE, общий экран): python | js | html | sql | kotlin. */
    val language: String? = null,
) {
    val codeLanguage: String get() = task?.language ?: language ?: "python"
}

/** Ответ наставника. */
data class MentorReply(
    val text: String,
    val intent: Intent,
    val source: Source,
    /** Номер подсказки задания (1..), которую открыл этот ответ: экран увеличивает счётчик подсказок. */
    val revealedHint: Int? = null,
    val links: List<LessonLink> = emptyList(),
    /** Ответ модели был заменён: в нём было решение или он ушёл с русского языка. */
    val replaced: Boolean = false,
    val note: String? = null,
)
