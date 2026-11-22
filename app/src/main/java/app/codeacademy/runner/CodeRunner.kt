package app.codeacademy.runner

/** Общий интерфейс исполнителей кода ученика (уровень A — Chaquopy, уровень W — Pyodide). */
interface CodeRunner {
    /** Подготовка (запуск интерпретатора). null — исполнитель недоступен. */
    suspend fun prepare(): RunnerInfo?

    suspend fun run(
        code: String,
        timeoutMs: Long = RunnerService.DEFAULT_TIMEOUT_MS,
        stdin: String = "",
        project: String = "default",
        /** Файлы проекта {путь: текст}; null — не трогать папку проекта. Результат вернёт файлы после запуска. */
        files: Map<String, String>? = null,
    ): RunResult

    /**
     * Автопроверка задания (ca_runner.check). При успехе status = OK, а stdout — JSON-отчёт.
     * TIMEOUT/STOPPED/CRASHED — проверка не завершилась.
     */
    suspend fun check(
        code: String,
        testsJson: String,
        timeoutMs: Long = 10_000,
        project: String = "check",
        /** Файлы веб-проекта (страница проверяется вместе с CSS и JS); Python-проект передаёт файлы в code. */
        files: Map<String, String>? = null,
    ): RunResult

    fun stop()
    fun close()
}
