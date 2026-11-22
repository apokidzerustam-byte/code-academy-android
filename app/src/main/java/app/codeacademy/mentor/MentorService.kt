package app.codeacademy.mentor

import android.app.Service
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.HandlerThread
import android.os.IBinder
import android.os.Message
import android.os.Messenger
import android.os.PowerManager
import android.os.RemoteException
import android.util.Log
import java.io.File
import java.util.concurrent.Executors
import java.util.concurrent.atomic.AtomicLong

/** Сообщения между приложением и процессом :mentor. */
object MentorProtocol {
    const val MSG_GENERATE = 1
    const val MSG_STOP = 2
    const val MSG_UNLOAD = 3
    /** Загрузить модель заранее и прогреть общее начало запроса (ученик открыл панель наставника, но ещё не спросил). */
    const val MSG_LOAD = 4
    const val MSG_PIECE = 11
    const val MSG_DONE = 12
    const val MSG_ERROR = 13

    const val KEY_ID = "id"
    const val KEY_MODEL = "model"
    const val KEY_PROMPT = "prompt"
    const val KEY_MAX_TOKENS = "maxTokens"
    const val KEY_INFO = "info"
    const val KEY_LOAD_MS = "loadMs"
    const val KEY_TEXT = "text"
    const val KEY_STATS = "stats"
    const val KEY_HOT = "hot"
    /** Имя режима производительности (PerfMode) на момент запроса. */
    const val KEY_PERF = "perf"
}

/**
 * Процесс локальной нейросети. Модель (GGUF) загружается из filesDir/models, считается на CPU
 * в фоновом потоке. Нехватка памяти или сбой в llama.cpp завершают только этот процесс.
 * Генерация прекращается при перегреве (PowerManager, Android 10+) и по команде «Стоп».
 * У приложения нет разрешения INTERNET — у этого процесса тоже.
 */
class MentorService : Service() {
    private val worker = Executors.newSingleThreadExecutor()
    private lateinit var control: Handler
    private lateinit var messenger: Messenger
    @Volatile private var llm: NativeLlm? = null
    @Volatile private var loadedPath: String? = null
    @Volatile private var loadedPerf: PerfMode? = null
    /** Через сколько простоя выгружать модель — по режиму последнего запроса. */
    @Volatile private var idleMs = IDLE_UNLOAD_MS
    @Volatile private var loadMs = 0L
    @Volatile private var info = ""
    @Volatile private var hot = false
    private val activeId = AtomicLong(0)
    private var thermalListener: Any? = null

    private val unloadIdle = Runnable { worker.execute { unload() } }

    override fun onCreate() {
        super.onCreate()
        val t = HandlerThread("mentor-control").apply { start() }
        control = Handler(t.looper) { m -> handle(m); true }
        messenger = Messenger(control)
        if (Build.VERSION.SDK_INT >= 29) {
            val pm = getSystemService(Context.POWER_SERVICE) as PowerManager
            hot = pm.currentThermalStatus >= PowerManager.THERMAL_STATUS_SEVERE
            val l = PowerManager.OnThermalStatusChangedListener { status ->
                hot = status >= PowerManager.THERMAL_STATUS_SEVERE
                if (hot) llm?.stop()
            }
            pm.addThermalStatusListener(l)
            thermalListener = l
        }
    }

    override fun onBind(intent: Intent?): IBinder = messenger.binder

    /**
     * Модель держится в памяти 10 минут, чтобы не загружаться заново на каждый вопрос, но при нехватке памяти
     * в системе выгружается сразу (после текущей генерации): иначе Android завершил бы процесс вместе с моделью.
     */
    override fun onTrimMemory(level: Int) {
        super.onTrimMemory(level)
        // 10 — RUNNING_LOW, 15 — RUNNING_CRITICAL (на новых версиях Android не приходят), 60 и выше — система уже вытесняет
        // процессы из кэша. Уровень 40 (процесс просто ушёл в кэш, когда ученик переключился в другое приложение) не учитывается:
        // иначе модель выгружалась бы при каждом коротком переходе, а загрузка занимает секунды.
        if (level == 10 || level == 15 || level >= 60) {
            control.removeCallbacks(unloadIdle)
            runCatching { worker.execute { unload() } }
        }
    }

    override fun onDestroy() {
        if (Build.VERSION.SDK_INT >= 29) {
            (thermalListener as? PowerManager.OnThermalStatusChangedListener)?.let {
                (getSystemService(Context.POWER_SERVICE) as PowerManager).removeThermalStatusListener(it)
            }
        }
        llm?.stop()
        worker.execute { unload() }
        worker.shutdown()
        super.onDestroy()
    }

    private fun handle(m: Message) {
        val P = MentorProtocol
        when (m.what) {
            P.MSG_GENERATE -> {
                val data = m.data
                val reply = m.replyTo ?: return
                val id = data.getLong(P.KEY_ID)
                activeId.set(id)
                control.removeCallbacks(unloadIdle)
                worker.execute { generate(reply, id, data) }
            }
            P.MSG_STOP -> {
                // Отмена, пришедшая во время загрузки модели, тоже действует: колбэк сверяет activeId.
                activeId.set(0)
                llm?.stop()
            }
            P.MSG_UNLOAD -> { llm?.stop(); runCatching { worker.execute { unload() } } }
            P.MSG_LOAD -> {
                val path = m.data.getString(P.KEY_MODEL)
                val prefix = m.data.getString(P.KEY_PROMPT).orEmpty()
                val perf = PerfPolicy.parse(m.data.getString(P.KEY_PERF))
                control.removeCallbacks(unloadIdle)
                runCatching { worker.execute { preload(path, prefix, perf) } }
            }
        }
    }

    /**
     * Загрузка модели и прогрев общего начала запроса: пока ученик набирает вопрос, телефон успевает загрузить файл
     * (секунды) и посчитать правила наставника, и первый ответ не тратит на это время. Ошибки не сообщаются:
     * настоящий запрос повторит загрузку и покажет причину.
     */
    private fun preload(path: String?, prefix: String, perf: PerfMode) {
        try {
            if (hot || path == null) return
            val engine = ensureLoaded(path, perf)
            // Один токен: запрос разбирается, и его начало остаётся в кэше контекста для следующих вопросов.
            if (prefix.isNotEmpty()) engine.generate(prefix, 1, temperature = 0.3f, seed = 42) { false }
        } catch (t: Throwable) {
            Log.w(TAG, "предзагрузка не удалась", t)
        } finally {
            control.removeCallbacks(unloadIdle)
            control.postDelayed(unloadIdle, idleMs)
        }
    }

    private fun generate(reply: Messenger, id: Long, data: Bundle) {
        val P = MentorProtocol
        try {
            if (hot) {
                send(reply, P.MSG_ERROR, id, Bundle().apply {
                    putString(P.KEY_TEXT, "Телефон перегрет — нейросеть приостановлена, отвечает лёгкий режим. Дайте телефону остыть.")
                    putBoolean(P.KEY_HOT, true)
                })
                return
            }
            val path = data.getString(P.KEY_MODEL) ?: error("не указан файл модели")
            val perf = PerfPolicy.parse(data.getString(P.KEY_PERF))
            val wasLoaded = llm != null && loadedPath == path && loadedPerf == perf
            val engine = ensureLoaded(path, perf)
            val loadedNow = if (wasLoaded) 0L else loadMs
            val stats = engine.generate(data.getString(P.KEY_PROMPT).orEmpty(), data.getInt(P.KEY_MAX_TOKENS, 320).coerceIn(16, 1024),
                temperature = 0.3f, seed = 42) cb@{ piece ->
                if (activeId.get() != id || hot) return@cb false
                send(reply, P.MSG_PIECE, id, Bundle().apply { putString(P.KEY_TEXT, piece) })
            }
            send(reply, P.MSG_DONE, id, Bundle().apply {
                putString(P.KEY_STATS, stats)
                putString(P.KEY_INFO, info)
                putLong(P.KEY_LOAD_MS, loadedNow)
                putBoolean(P.KEY_HOT, hot)
            })
        } catch (t: Throwable) {
            Log.e(TAG, "генерация не удалась", t)
            send(reply, P.MSG_ERROR, id, Bundle().apply { putString(P.KEY_TEXT, t.message ?: t.javaClass.simpleName) })
        } finally {
            control.removeCallbacks(unloadIdle)
            control.postDelayed(unloadIdle, idleMs)
        }
    }

    /** Модель загружается заново, если сменился файл или режим производительности (число потоков задаётся при загрузке). */
    private fun ensureLoaded(path: String, perf: PerfMode): NativeLlm {
        val policy = PerfPolicy.of(perf)
        idleMs = policy.idleUnloadMs
        llm?.let { if (loadedPath == path && loadedPerf == perf) return it }
        unload()
        val f = File(path)
        require(f.isFile && f.canonicalPath.startsWith(File(filesDir, "models").canonicalPath + File.separator)) { "файл модели не найден" }
        NativeLlm.init(applicationInfo.nativeLibraryDir)
        val threads = policy.threads(CpuTopology.detect())
        val t0 = System.currentTimeMillis()
        val engine = NativeLlm.load(f.path, N_CTX, threads.generation, threads.prompt)
        loadMs = System.currentTimeMillis() - t0
        info = "${engine.description}\nЯдер: ${threads.cores}, быстрых: ${threads.fastCores}; загрузка модели ${loadMs} мс\n" +
            "Процессор: ${CpuTopology.features(NativeLlm.systemInfo()).joinToString(", ").ifBlank { "нет сведений" }}"
        Log.i(TAG, info)
        llm = engine
        loadedPath = path
        loadedPerf = perf
        return engine
    }

    private fun unload() {
        llm?.close()
        llm = null
        loadedPath = null
        loadedPerf = null
    }

    private fun send(to: Messenger, what: Int, id: Long, b: Bundle): Boolean = try {
        b.putLong(MentorProtocol.KEY_ID, id)
        to.send(Message.obtain(null, what).apply { data = b })
        true
    } catch (e: RemoteException) {
        false // приложение закрылось — генерацию можно прекратить
    }

    companion object {
        private const val TAG = "CodeAcademyMentor"
        /** Контекст: промпт с конспектом и кодом на кириллице может занимать 1500–2500 токенов. */
        const val N_CTX = 4096
        /** Модель выгружается из памяти через 10 минут без запросов (повторная загрузка занимает секунды). */
        const val IDLE_UNLOAD_MS = 600_000L
    }
}
