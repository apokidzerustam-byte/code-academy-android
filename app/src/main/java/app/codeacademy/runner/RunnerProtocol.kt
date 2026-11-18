package app.codeacademy.runner

/** Протокол обмена сообщениями между приложением и процессом-раннером (Messenger/Binder). */
object RunnerProtocol {
    const val MSG_RUN = 1
    const val MSG_STOP = 2
    const val MSG_RESULT = 3
    const val MSG_PING = 4
    const val MSG_PONG = 5

    const val KEY_RUN_ID = "runId"
    const val KEY_CODE = "code"
    const val KEY_STDIN = "stdin"
    const val KEY_TIMEOUT_MS = "timeoutMs"
    const val KEY_SANDBOX_DIR = "sandboxDir"
    const val KEY_MAX_OUTPUT = "maxOutput"

    const val KEY_STATUS = "status"
    const val KEY_STDOUT = "stdout"
    const val KEY_STDERR = "stderr"
    const val KEY_TRUNCATED = "truncated"
    const val KEY_DURATION_MS = "durationMs"

    const val KEY_PYTHON_STARTED = "pythonStarted"
    const val KEY_START_ERROR = "startError"
    const val KEY_START_MS = "startMs"
    const val KEY_PID = "pid"
    const val KEY_UID = "uid"
    const val KEY_ISOLATED = "isolated"
    const val KEY_PY_INFO = "pyInfo"
    const val KEY_PROBE_PATH = "probePath"
    const val KEY_PROBE_RESULT = "probeResult"
}

enum class RunStatus {
    OK, ERROR, SYNTAX_ERROR, EXIT,
    /** Превышен лимит времени — процесс раннера уничтожен. */
    TIMEOUT,
    /** Остановлено пользователем — процесс раннера уничтожен. */
    STOPPED,
    /** Процесс раннера упал (например, нехватка памяти). */
    CRASHED,
    /** Python не удалось запустить в этом режиме. */
    UNAVAILABLE,
}

data class RunResult(
    val status: RunStatus,
    val stdout: String = "",
    val stderr: String = "",
    val truncated: Boolean = false,
    val durationMs: Long = 0,
)

data class RunnerInfo(
    val pythonStarted: Boolean,
    val startError: String?,
    val startMs: Long,
    val pid: Int,
    val uid: Int,
    val isolated: Boolean,
    val pyInfo: String?,
    val kernelProbe: String? = null,
)
