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
)

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
) {
    /** «Предскажи результат»: ученик вводит текст, код не выполняется. */
    val isAnswerTask: Boolean get() = type == "predict" || type == "review"
}

/** Урок вместе с путями его файлов внутри пакета. */
data class LessonRef(val packId: String, val lessonId: String) {
    val key: String get() = "$packId/$lessonId"
}
