package app.codeacademy.assessment

import app.codeacademy.content.Assignment
import app.codeacademy.runner.CodeRunner
import app.codeacademy.runner.RunStatus
import app.codeacademy.runner.WebRunner
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonElement

@Serializable
data class CaseReport(
    val id: String? = null,
    /** Файл проекта, который проверял тест (учебные проекты). */
    val file: String? = null,
    /** Номер строки ответа (задания «предскажи результат»). */
    val line: Int? = null,
    val hidden: Boolean = false,
    val passed: Boolean = false,
    val hint: String? = null,
    val error: String? = null,
    val input: JsonElement? = null,
    val expected: JsonElement? = null,
    val actual: JsonElement? = null,
)

@Serializable
data class CheckReport(
    /** "answer" — построчная проверка ответа текстом. */
    val kind: String? = null,
    val allPassed: Boolean = false,
    val passed: Int = 0,
    val total: Int = 0,
    val cases: List<CaseReport> = emptyList(),
    val compileError: String? = null,
    val loadError: String? = null,
    val durationMs: Long = 0,
    /** Замечания линтера HTML/CSS: на результат не влияют. */
    val warnings: List<String> = emptyList(),
)

/** Итог проверки для экрана и статистики. */
data class Verdict(
    val report: CheckReport?,
    /** Проверка не состоялась: таймаут, остановка, падение раннера. */
    val failure: RunStatus? = null,
    val failureText: String = "",
) {
    val passed: Boolean get() = report?.allPassed == true

    /** Тип ошибки для истории ошибок и Error-Based Learning. */
    val errorType: String?
        get() = when {
            failure == RunStatus.TIMEOUT -> "Timeout"
            failure != null -> failure.name
            report == null -> null
            report.compileError != null -> errorName(report.compileError)
            report.loadError != null -> errorName(report.loadError)
            report.allPassed -> null
            else -> report.cases.firstOrNull { !it.passed }?.error?.let(::errorName) ?: "WrongResult"
        }

    private fun errorName(text: String): String =
        Regex("([A-Za-z]+Error|[A-Za-z]+Exception)").findAll(text).lastOrNull()?.value ?: "Error"
}

class AssessmentService(private val json: Json = Json { ignoreUnknownKeys = true }) {

    fun testsJson(a: Assignment): String = a.tests.toString()

    suspend fun evaluate(runner: CodeRunner, a: Assignment, code: String): Verdict {
        // Веб-проверка открывает страницу заново для каждого теста — ей нужно больше времени.
        // FastAPI: первый импорт fastapi/pydantic на слабом телефоне занимает несколько секунд.
        val kind = (a.tests["kind"] as? kotlinx.serialization.json.JsonPrimitive)?.content
        val timeout = when {
            runner is WebRunner -> 25_000L
            kind == "fastapi" -> 40_000L
            else -> 10_000L
        }
        val r = runner.check(code, testsJson(a), timeoutMs = timeout, project = "check-${a.id}")
        if (r.status != RunStatus.OK) return Verdict(null, r.status, r.stderr)
        val report = runCatching { json.decodeFromString(CheckReport.serializer(), r.stdout) }.getOrNull()
            ?: return Verdict(null, RunStatus.ERROR, "Некорректный отчёт проверки: ${r.stdout.take(200)}")
        return Verdict(report)
    }

    /**
     * Проверка этапа учебного проекта. Python: все файлы проекта передаются песочнице (kind=project),
     * HTML: страница-вход проверяется вместе с остальными файлами проекта.
     */
    suspend fun evaluateProject(
        runner: CodeRunner,
        language: String,
        tests: kotlinx.serialization.json.JsonObject,
        files: Map<String, String>,
        project: String,
    ): Verdict {
        val cases = (tests["cases"] as? kotlinx.serialization.json.JsonArray)?.size ?: 1
        val r = if (language == "python") {
            val code = kotlinx.serialization.json.JsonObject(files.mapValues { kotlinx.serialization.json.JsonPrimitive(it.value) }).toString()
            runner.check(code, tests.toString(), timeoutMs = 10_000L + 3_000L * cases, project = project)
        } else {
            val entry = (tests["entry"] as? kotlinx.serialization.json.JsonPrimitive)?.content ?: "index.html"
            val page = files[entry] ?: return Verdict(CheckReport(loadError = "В проекте нет файла $entry"))
            runner.check(page, tests.toString(), timeoutMs = 15_000L + 3_000L * cases, project = project, files = files)
        }
        if (r.status != RunStatus.OK) return Verdict(null, r.status, r.stderr)
        val report = runCatching { json.decodeFromString(CheckReport.serializer(), r.stdout) }.getOrNull()
            ?: return Verdict(null, RunStatus.ERROR, "Некорректный отчёт проверки: ${r.stdout.take(200)}")
        return Verdict(report)
    }
}
