package app.codeacademy.assessment

import app.codeacademy.content.Assignment
import app.codeacademy.runner.CodeRunner
import app.codeacademy.runner.RunStatus
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonElement

@Serializable
data class CaseReport(
    val id: String? = null,
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
        val r = runner.check(code, testsJson(a), timeoutMs = 10_000, project = "check-${a.id}")
        if (r.status != RunStatus.OK) return Verdict(null, r.status, r.stderr)
        val report = runCatching { json.decodeFromString(CheckReport.serializer(), r.stdout) }.getOrNull()
            ?: return Verdict(null, RunStatus.ERROR, "Некорректный отчёт проверки: ${r.stdout.take(200)}")
        return Verdict(report)
    }
}
