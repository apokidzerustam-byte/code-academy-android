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
    ): RunResult

    fun stop()
    fun close()
}
