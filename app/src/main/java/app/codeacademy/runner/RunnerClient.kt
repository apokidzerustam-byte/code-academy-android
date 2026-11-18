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
import android.os.RemoteException
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
 *
 * Важно: после TIMEOUT/STOPPED процесс раннера уничтожает себя. Клиент сразу
 * забывает это соединение и перед следующим запуском ждёт фактической гибели
 * процесса, чтобы не отправить код в умирающий процесс.
 */
class RunnerClient(context: Context, val isolated: Boolean) : CodeRunner {

    private val app = context.applicationContext
    private val replyThread = HandlerThread("runner-replies").apply { start() }
    private val pendingRuns = ConcurrentHashMap<Long, CompletableDeferred<RunResult>>()
    @Volatile private var pendingPing: CompletableDeferred<RunnerInfo>? = null
    private val runIds = AtomicLong(1)
    private val bindLock = Mutex()

    /** Одно подключение к одному процессу раннера. */
    private inner class Conn : ServiceConnection {
        val ready = CompletableDeferred<Messenger?>()
        val died = CompletableDeferred<Unit>()
        @Volatile var messenger: Messenger? = null

        override fun onServiceConnected(name: ComponentName?, binder: IBinder) {
            try {
                binder.linkToDeath({ onRunnerDied(this) }, 0)
            } catch (e: RemoteException) {
                // Привязались к процессу, который уже умирает.
                died.complete(Unit)
                ready.complete(null)
                return
            }
            messenger = Messenger(binder)
            ready.complete(messenger)
        }

        override fun onServiceDisconnected(name: ComponentName?) = onRunnerDied(this)
        override fun onBindingDied(name: ComponentName?) = onRunnerDied(this)
        override fun onNullBinding(name: ComponentName?) {
            ready.complete(null)
        }
    }

    @Volatile private var conn: Conn? = null

    private val replyHandler = Handler(replyThread.looper) { msg ->
        when (msg.what) {
            P.MSG_RESULT -> {
                val r = msg.data.toResult()
                if (r.status == RunStatus.TIMEOUT || r.status == RunStatus.STOPPED) retireCurrent()
                pendingRuns.remove(msg.data.getLong(P.KEY_RUN_ID))?.complete(r)
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

    /** Текущий процесс раннера обречён: отвязываемся и запоминаем, чью гибель ждать. */
    private fun retireCurrent() {
        val c = conn ?: return
        conn = null
        dying[isolated] = c.died
        runCatching { app.unbindService(c) }
    }

    private suspend fun ensureBound(): Messenger? = bindLock.withLock {
        conn?.messenger?.let { return it }
        // Ожидание общее для всех клиентов процесса: процесс раннера один на приложение,
        // и новый клиент не должен подключиться к процессу, который сейчас самоуничтожается.
        dying[isolated]?.let { d ->
            withTimeoutOrNull(DEATH_WAIT_MS) { d.await() }
            dying.remove(isolated, d)
        }
        val c = Conn()
        conn = c
        if (!app.bindService(Intent(app, serviceClass), c, Context.BIND_AUTO_CREATE)) {
            conn = null
            return null
        }
        val m = withTimeoutOrNull(BIND_TIMEOUT_MS) { c.ready.await() }
        if (m == null) {
            if (conn === c) conn = null
            runCatching { app.unbindService(c) }
        }
        m
    }

    private fun onRunnerDied(c: Conn) {
        c.died.complete(Unit)
        if (conn !== c) return // поздний сигнал от старого соединения — новое не трогаем
        conn = null
        runCatching { app.unbindService(c) }
        // Ответ TIMEOUT/STOPPED уже мог встать в очередь replyThread — даём ему прийти первым.
        // Список фиксируем сейчас: запуски, начатые на новом соединении, не трогаем.
        val dead = pendingRuns.keys.toList()
        replyHandler.postDelayed({
            dead.forEach { id ->
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
        try {
            m.send(Message.obtain(null, P.MSG_PING).also {
                it.replyTo = replies
                if (probePath != null) it.data = Bundle().apply { putString(P.KEY_PROBE_PATH, probePath) }
            })
        } catch (e: RemoteException) {
            conn?.let { onRunnerDied(it) }
            return null
        }
        return withTimeoutOrNull(BIND_TIMEOUT_MS) { d.await() }
    }

    override suspend fun prepare(): RunnerInfo? = ping()

    override suspend fun run(
        code: String,
        timeoutMs: Long,
        stdin: String,
        project: String,
        files: Map<String, String>?,
    ): RunResult {
        val dir = sandboxDir(project)
        if (files != null && dir != null) {
            runCatching { ProjectFiles.write(dir, files) }.onFailure {
                return RunResult(RunStatus.ERROR, stderr = it.message ?: it.toString())
            }
        }
        val r = send(code, timeoutMs, stdin, project, mode = "run", tests = null)
        return if (files != null && dir != null) r.copy(files = ProjectFiles.read(dir)) else r
    }

    override suspend fun check(code: String, testsJson: String, timeoutMs: Long, project: String): RunResult =
        send(code, timeoutMs, "", project, mode = "check", tests = testsJson)

    private suspend fun send(
        code: String,
        timeoutMs: Long,
        stdin: String,
        project: String,
        mode: String,
        tests: String?,
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
            putInt(P.KEY_MAX_OUTPUT, MAX_OUTPUT_CHARS)
            putString(P.KEY_MODE, mode)
            putString(P.KEY_TESTS, tests)
        }
        try {
            m.send(Message.obtain(null, P.MSG_RUN).also { it.data = data; it.replyTo = replies })
        } catch (e: RemoteException) {
            pendingRuns.remove(id)
            conn?.let { onRunnerDied(it) }
            return RunResult(RunStatus.CRASHED, stderr = e.toString())
        }
        // Страховка на случай, если раннер не ответил даже после своего таймаута.
        return withTimeoutOrNull(timeoutMs + CLIENT_GRACE_MS) { d.await() }
            ?: RunResult(RunStatus.TIMEOUT).also { pendingRuns.remove(id); retireCurrent() }
    }

    override fun stop() {
        conn?.messenger?.runCatching { send(Message.obtain(null, P.MSG_STOP).also { it.replyTo = replies }) }
    }

    override fun close() {
        conn?.let { runCatching { app.unbindService(it) } }
        conn = null
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
        /** Процессы раннера (по уровню), которые должны умереть после TIMEOUT/STOPPED. */
        private val dying = ConcurrentHashMap<Boolean, CompletableDeferred<Unit>>()
        private const val BIND_TIMEOUT_MS = 20_000L
        private const val CLIENT_GRACE_MS = 3_000L
        private const val DEATH_GRACE_MS = 300L
        private const val DEATH_WAIT_MS = 3_000L
        /** На поток (stdout/stderr). Держит ответ Binder заметно ниже лимита транзакции. */
        const val MAX_OUTPUT_CHARS = 16_384
    }
}
