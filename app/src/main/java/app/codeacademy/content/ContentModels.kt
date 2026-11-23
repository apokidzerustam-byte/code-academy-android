package app.codeacademy.content

import kotlinx.serialization.Serializable
import kotlinx.serialization.json.JsonObject

/** Модели контент-пакета. Формат задан JSON Schema в content/schema. */

@Serializable
data class PackManifest(
    val id: String,
    val version: String,
    val stage: Int,
    val title: String,
    val description: String = "",
    val language: String,
    val minAppVersion: Int = 1,
    val requiresPacks: List<String> = emptyList(),
    val lessons: List<String>,
    /** Названия навыков для карты знаний. */
    val skills: Map<String, String> = emptyMap(),
    /** Учебные проекты пакета: projects/<id>/project.json. */
    val projects: List<String> = emptyList(),
)

/** Неверное решение этапа проекта (для валидатора и тестов на устройстве). */
@Serializable
data class WrongProjectSolution(val files: Map<String, String>, val why: String)

/** Этап учебного проекта: условие, новые файлы, тесты всего проекта. */
@Serializable
data class Milestone(
    val id: String,
    val title: String,
    val afterLesson: String? = null,
    val statement: String,
    val goal: String,
    /** Добавляются в начале этапа; файлы ученика не перезаписываются. */
    val starterFiles: Map<String, String> = emptyMap(),
    val hints: List<String>,
    val tests: kotlinx.serialization.json.JsonObject,
    val solutionFiles: Map<String, String>,
    val explanation: String,
    val criteria: List<String>,
    val wrongSolutions: List<WrongProjectSolution> = emptyList(),
)

/** Учебный проект: мини-проект (mini) или сквозной проект курса (through). */
@Serializable
data class CourseProject(
    val id: String,
    val kind: String,
    val title: String,
    val summary: String,
    /** python или html. */
    val language: String,
    val afterLesson: String? = null,
    val skills: List<String> = emptyList(),
    val milestones: List<Milestone>,
) {
    val isThrough: Boolean get() = kind == "through"
}

/** Ссылка на учебный проект: "packId/projectId". */
data class ProjectRef(val packId: String, val projectId: String) {
    val key: String get() = "$packId/$projectId"
    /** Ключ попыток в таблице attempt (этапы — как задания). */
    val attemptKey: String get() = "project:$key"

    companion object {
        fun parse(key: String): ProjectRef? =
            key.trim().split('/').takeIf { it.size == 2 && it.all(String::isNotBlank) }?.let { ProjectRef(it[0], it[1]) }
    }
}

@Serializable
data class Lesson(
    val id: String,
    val title: String,
    val goal: String,
    val skills: List<String>,
    val prerequisites: List<String> = emptyList(),
    val runner: String = "W",
    val scenario: String,
    val notes: String,
    val assignments: List<String>,
    val passCriteria: PassCriteria,
    val commonMistakes: List<CommonMistake>,
)

@Serializable
data class PassCriteria(val minAssignmentsPassed: Int, val minScorePercent: Int = 80)

@Serializable
data class CommonMistake(val mistake: String, val fix: String, val errorType: String? = null)

@Serializable
data class Scenario(val voice: String = "author", val scenes: List<Scene>)

@Serializable
data class Scene(
    val id: String,
    val title: String? = null,
    val narration: String,
    val stress: Map<String, String> = emptyMap(),
    val actions: List<SceneAction>,
)

@Serializable
data class SceneAction(
    val type: String,
    val file: String = "main.py",
    val text: String? = null,
    val lines: List<Int> = emptyList(),
    val stdin: String? = null,
    val md: String? = null,
    val ms: Long = 0,
    /** stdout | stderr (сообщение об ошибке). */
    val stream: String = "stdout",
    /** Номер фразы озвучки (с 0), с которой начинается действие; null — сразу после предыдущего. */
    val cue: Int? = null,
)

@Serializable
data class Assignment(
    val id: String,
    val type: String,
    val title: String,
    val statement: String,
    val goal: String,
    val input: String,
    val expectedResult: String,
    val constraints: List<String>,
    val starterCode: String? = null,
    val code: String? = null,
    val hints: List<String>,
    val tests: JsonObject,
    val solution: String,
    val explanation: String,
    val criteria: List<String>,
    /** Типовые неверные решения (для автопроверки контента). */
    val wrongSolutions: List<WrongSolution> = emptyList(),
) {
    /**
     * Ответ вводят текстом, код не выполняется: «предскажи результат», разбор кода и вопросы с проверкой `answer`
     * (например, команда терминала, которую ученик записывает как ответ).
     */
    val isAnswerTask: Boolean
        get() = type == "predict" || type == "review" || (tests["kind"] as? kotlinx.serialization.json.JsonPrimitive)?.content == "answer"
}

/** Урок вместе с путями его файлов внутри пакета. */
data class LessonRef(val packId: String, val lessonId: String) {
    val key: String get() = "$packId/$lessonId"
}

@Serializable
data class WrongSolution(val code: String, val why: String, val answer: String? = null)

