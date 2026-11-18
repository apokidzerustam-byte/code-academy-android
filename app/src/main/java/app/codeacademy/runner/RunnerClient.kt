package app.codeacademy.runner

import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.ServiceConnection
import android.os.Bundle
import android.os.Handler
import android.os.HandlerThread
import android.os.IBinder
import android.os.Message
import android.os.Messenger
import app.codeacademy.runner.RunnerProtocol as P
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.withTimeoutOrNull
import java.io.File
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.atomic.AtomicLong

/**
 * Клиент раннера в основном процессе приложения.
 * [isolated] = false → уровень A (:runner), true → уровень B (isolatedProcess).
 */
class RunnerClient(context: Context, val isolated: Boolean) {

    private val app = context.applicationContext
    private val replyThread = HandlerThread("runner-replies").apply { start() }
    private val pendingRuns = ConcurrentHashMap<Long, CompletableDeferred<RunResult>>()
    private var pendingPing: CompletableDeferred<RunnerInfo>? = null
    private val runIds = AtomicLong(1)
    private val bindLock = Mutex()

    @Volatile private var service: Messenger? = null
    @Volatile private var connection: ServiceConnection? = null

    private val replyHandler = Handler(replyThread.looper) { msg ->
        when (msg.what) {
            P.MSG_RESULT -> {
                val d = msg.data
                pendingRuns.remove(d.getLong(P.KEY_RUN_ID))?.complete(d.toResult())
            }
            P.MSG_PONG -> pendingPing?.complete(msg.data.toInfo())
        }
        true
    }
    private val replies = Messenger(replyHandler)

    private val serviceClass =
        if (isolated) IsolatedRunnerService::class.java else RunnerService::class.java

    /** Папка учебного проекта. Только уровень A: изолированный процесс к файлам доступа не имеет. */
    fun sandboxDir(project: String): File? =
        if (isolated) null else File(app.filesDir, "projects/$project").apply { mkdirs() }

    private suspend fun ensureBound(): Messenger? = bindLock.withLock {
        service?.let { return it }
        val ready = CompletableDeferred<Messenger?>()
        val conn = object : ServiceConnection {
            override fun onServiceConnected(name: ComponentName?, binder: IBinder) {
                binder.linkToDeath({ onRunnerDied() }, 0)
                val m = Messenger(binder)
                service = m
                ready.complete(m)
            }

            override fun onServiceDisconnected(name: ComponentName?) = onRunnerDied()
            override fun onBindingDied(name: ComponentName?) = onRunnerDied()
            override fun onNullBinding(name: ComponentName?) { ready.complete(null) }
        }
        connection = conn
        if (!app.bindService(Intent(app, serviceClass), conn, Context.BIND_AUTO_CREATE)) {
            connection = null
            return null
        }
        withTimeoutOrNull(BIND_TIMEOUT_MS) { ready.await() }
    }

    private fun onRunnerDied() {
        service = null
        connection?.let { runCatching { app.unbindService(it) } }
        connection = null
        // Ответ TIMEOUT/STOPPED отправляется до самоуничтожения раннера и уже стоит
        // в очереди replyThread; даём ему прийти первым. Кто остался без ответа — упал (например, OOM).
        replyHandler.postDelayed({
            pendingRuns.keys.toList().forEach { id ->
                pendingRuns.remove(id)?.complete(
                    RunResult(RunStatus.CRASHED, stderr = "Процесс выполнения завершился аварийно")
                )
            }
        }, DEATH_GRACE_MS)
    }

    /** [probePath] — только для тестов: проверка ограничений ядра (см. ca_runner.kernel_probe). */
    suspend fun ping(probePath: String? = null): RunnerInfo? {
        val m = ensureBound() ?: return null
        val d = CompletableDeferred<RunnerInfo>()
        pendingPing = d
        m.send(Message.obtain(null, P.MSG_PING).also {
            it.replyTo = replies
            if (probePath != null) it.data = Bundle().apply { putString(P.KEY_PROBE_PATH, probePath) }
        })
        return withTimeoutOrNull(BIND_TIMEOUT_MS) { d.await() }
    }

    suspend fun run(
        code: String,
        timeoutMs: Long = RunnerService.DEFAULT_TIMEOUT_MS,
        stdin: String = "",
        project: String = "default",
    ): RunResult {
        val m = ensureBound()
            ?: return RunResult(RunStatus.UNAVAILABLE, stderr = "Не удалось подключиться к раннеру")
        val id = runIds.getAndIncrement()
        val d = CompletableDeferred<RunResult>()
        pendingRuns[id] = d
        val data = Bundle().apply {
            putLong(P.KEY_RUN_ID, id)
            putString(P.KEY_CODE, code)
            putString(P.KEY_STDIN, stdin)
            putLong(P.KEY_TIMEOUT_MS, timeoutMs)
            putString(P.KEY_SANDBOX_DIR, sandboxDir(project)?.absolutePath)
            putInt(P.KEY_MAX_OUTPUT, 65536)
        }
        try {
            m.send(Message.obtain(null, P.MSG_RUN).also { it.data = data; it.replyTo = replies })
        } catch (e: Exception) {
            pendingRuns.remove(id)
            onRunnerDied()
            return RunResult(RunStatus.CRASHED, stderr = e.toString())
        }
        // Страховка на случай, если раннер не ответил даже после своего таймаута.
        return withTimeoutOrNull(timeoutMs + CLIENT_GRACE_MS) { d.await() }
            ?: RunResult(RunStatus.TIMEOUT).also { pendingRuns.remove(id); onRunnerDied() }
    }

    fun stop() {
        service?.runCatching { send(Message.obtain(null, P.MSG_STOP).also { it.replyTo = replies }) }
    }

    fun close() {
        connection?.let { runCatching { app.unbindService(it) } }
        connection = null
        service = null
        replyThread.quitSafely()
    }

    private fun Bundle.toResult() = RunResult(
        status = RunStatus.valueOf(getString(P.KEY_STATUS, RunStatus.ERROR.name)),
        stdout = getString(P.KEY_STDOUT, ""),
        stderr = getString(P.KEY_STDERR, ""),
        truncated = getBoolean(P.KEY_TRUNCATED),
        durationMs = getLong(P.KEY_DURATION_MS),
    )

    private fun Bundle.toInfo() = RunnerInfo(
        pythonStarted = getBoolean(P.KEY_PYTHON_STARTED),
        startError = getString(P.KEY_START_ERROR),
        startMs = getLong(P.KEY_START_MS),
        pid = getInt(P.KEY_PID),
        uid = getInt(P.KEY_UID),
        isolated = getBoolean(P.KEY_ISOLATED),
        pyInfo = getString(P.KEY_PY_INFO),
        kernelProbe = getString(P.KEY_PROBE_RESULT),
    )

    companion object {
        private const val BIND_TIMEOUT_MS = 20_000L
        private const val CLIENT_GRACE_MS = 3_000L
        private const val DEATH_GRACE_MS = 300L
    }
}
