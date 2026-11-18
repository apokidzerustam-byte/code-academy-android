package app.codeacademy.runner

import android.app.Service
import android.content.Intent
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.HandlerThread
import android.os.IBinder
import android.os.Message
import android.os.Messenger
import android.os.Process
import android.os.SystemClock
import android.util.Log
import app.codeacademy.runner.RunnerProtocol as P
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import org.json.JSONObject
import java.util.concurrent.Executors
import java.util.concurrent.atomic.AtomicLong

/**
 * Процесс-раннер. Код ученика выполняется на отдельном потоке;
 * сторожевой таймер и команда «Стоп» уничтожают ВЕСЬ процесс —
 * это единственный надёжный способ прервать произвольный Python-код.
 */
open class RunnerService : Service() {

    private val worker = Executors.newSingleThreadExecutor()
    private lateinit var control: Handler
    private lateinit var messenger: Messenger
    private val activeRun = AtomicLong(NO_RUN)

    private var startError: String? = null
    private var startMs: Long = 0

    override fun onCreate() {
        super.onCreate()
        val t0 = SystemClock.elapsedRealtime()
        try {
            if (!Python.isStarted()) Python.start(AndroidPlatform(this))
        } catch (t: Throwable) {
            startError = Log.getStackTraceString(t).take(4000)
            Log.e(TAG, "Python не запустился", t)
        }
        startMs = SystemClock.elapsedRealtime() - t0
        val thread = HandlerThread("runner-control").apply { start() }
        control = Handler(thread.looper) { msg -> handle(msg); true }
        messenger = Messenger(control)
    }

    override fun onBind(intent: Intent?): IBinder = messenger.binder

    private fun handle(msg: Message) {
        when (msg.what) {
            P.MSG_PING -> reply(msg.replyTo, P.MSG_PONG, pingBundle(msg.data?.getString(P.KEY_PROBE_PATH)))
            P.MSG_STOP -> {
                val id = activeRun.get()
                if (id != NO_RUN) terminate(msg.replyTo, id, RunStatus.STOPPED)
            }
            P.MSG_RUN -> startRun(msg.replyTo, Bundle(msg.data))
        }
    }

    private fun startRun(replyTo: Messenger?, data: Bundle) {
        val runId = data.getLong(P.KEY_RUN_ID)
        if (startError != null) {
            reply(replyTo, P.MSG_RESULT, resultBundle(runId, RunStatus.UNAVAILABLE, stderr = startError!!))
            return
        }
        if (!activeRun.compareAndSet(NO_RUN, runId)) {
            reply(replyTo, P.MSG_RESULT, resultBundle(runId, RunStatus.ERROR, stderr = "Раннер занят"))
            return
        }
        val timeoutMs = data.getLong(P.KEY_TIMEOUT_MS, DEFAULT_TIMEOUT_MS)
        control.postDelayed({
            if (activeRun.get() == runId) terminate(replyTo, runId, RunStatus.TIMEOUT)
        }, timeoutMs)

        worker.execute {
            val bundle = try {
                val module = Python.getInstance().getModule("ca_runner")
                val json = module.callAttr(
                    "run",
                    data.getString(P.KEY_CODE, ""),
                    data.getString(P.KEY_SANDBOX_DIR),
                    data.getString(P.KEY_STDIN, ""),
                    data.getInt(P.KEY_MAX_OUTPUT, 65536),
                ).toString()
                val o = JSONObject(json)
                resultBundle(
                    runId,
                    RunStatus.valueOf(o.getString("status")),
                    o.getString("stdout"),
                    o.getString("stderr"),
                    o.getBoolean("truncated"),
                    o.getLong("durationMs"),
                )
            } catch (t: Throwable) {
                resultBundle(runId, RunStatus.ERROR, stderr = Log.getStackTraceString(t).take(4000))
            }
            if (activeRun.compareAndSet(runId, NO_RUN)) reply(replyTo, P.MSG_RESULT, bundle)
        }
    }

    /** Сообщает итог и уничтожает процесс: зависший Python-поток иначе не остановить. */
    private fun terminate(replyTo: Messenger?, runId: Long, status: RunStatus) {
        if (!activeRun.compareAndSet(runId, NO_RUN)) return
        reply(replyTo, P.MSG_RESULT, resultBundle(runId, status))
        SystemClock.sleep(50) // даём Binder доставить ответ
        Process.killProcess(Process.myPid())
    }

    private fun pingBundle(probePath: String?) = Bundle().apply {
        putBoolean(P.KEY_PYTHON_STARTED, startError == null)
        putString(P.KEY_START_ERROR, startError)
        putLong(P.KEY_START_MS, startMs)
        putInt(P.KEY_PID, Process.myPid())
        putInt(P.KEY_UID, Process.myUid())
        putBoolean(P.KEY_ISOLATED, if (Build.VERSION.SDK_INT >= 28) Process.isIsolated() else false)
        if (startError == null) {
            putString(P.KEY_PY_INFO, runCatching {
                Python.getInstance().getModule("ca_runner").callAttr("info").toString()
            }.getOrElse { "info() failed: $it" })
            if (probePath != null && activeRun.get() == NO_RUN) {
                putString(P.KEY_PROBE_RESULT, runCatching {
                    Python.getInstance().getModule("ca_runner").callAttr("kernel_probe", probePath).toString()
                }.getOrElse { "probe failed: $it" })
            }
        }
    }

    private fun resultBundle(
        runId: Long,
        status: RunStatus,
        stdout: String = "",
        stderr: String = "",
        truncated: Boolean = false,
        durationMs: Long = 0,
    ) = Bundle().apply {
        putLong(P.KEY_RUN_ID, runId)
        putString(P.KEY_STATUS, status.name)
        putString(P.KEY_STDOUT, stdout)
        putString(P.KEY_STDERR, stderr)
        putBoolean(P.KEY_TRUNCATED, truncated)
        putLong(P.KEY_DURATION_MS, durationMs)
    }

    private fun reply(to: Messenger?, what: Int, data: Bundle) {
        try {
            to?.send(Message.obtain(null, what).also { it.data = data })
        } catch (e: Exception) {
            Log.w(TAG, "Не удалось отправить ответ", e)
        }
    }

    companion object {
        private const val TAG = "CodeAcademyRunner"
        private const val NO_RUN = -1L
        const val DEFAULT_TIMEOUT_MS = 5_000L
    }
}

/** Тот же раннер в изолированном процессе (android:isolatedProcess="true"). */
class IsolatedRunnerService : RunnerService()
