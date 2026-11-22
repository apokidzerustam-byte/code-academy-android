package app.codeacademy.mentor

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
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.withTimeout
import org.json.JSONObject
import java.util.concurrent.atomic.AtomicLong
import kotlin.coroutines.resume
import kotlin.coroutines.resumeWithException

/** Статистика последней генерации (для настроек и тестов). */
data class GenStats(
    val promptTokens: Int, val generatedTokens: Int, val promptMs: Long, val genMs: Long, val stopped: Boolean,
    /** Сколько токенов начала запроса взято из памяти контекста без пересчёта. */
    val cachedTokens: Int = 0,
    /** Сколько ушло на загрузку модели в этом запросе (0 — модель уже была в памяти). */
    val loadMs: Long = 0,
) {
    val tokensPerSecond: Double get() = if (genMs > 0) generatedTokens * 1000.0 / genMs else 0.0
}

/** Клиент процесса :mentor: LlmEngine для наставника. Запросы выполняются по одному. */
class MentorClient(
    private val context: Context,
    /** Что дописать к запросу после метки ассистента (зависит от модели). */
    private val promptSuffix: () -> String = { "" },
    private val modelPath: () -> String?,
) : LlmEngine {
    private val ids = AtomicLong(0)
    private val thread = HandlerThread("mentor-client").apply { start() }
    @Volatile private var service: Messenger? = null
    @Volatile private var connecting: CompletableDeferred<Messenger>? = null
    @Volatile private var pending: Pending? = null
    @Volatile var lastStats: GenStats? = null
        private set

    /** Описание модели, число потоков и возможности процессора — для проверки на телефоне. */
    @Volatile var lastInfo: String = ""
        private set

    private class Pending(val id: Long, val onPiece: (String) -> Boolean, val done: (Result<String>) -> Unit) {
        val text = StringBuilder()
    }

    private val replies = Messenger(Handler(thread.looper) { m -> onReply(m); true })

    private val connection = object : ServiceConnection {
        override fun onServiceConnected(name: ComponentName?, binder: IBinder?) {
            val m = Messenger(binder)
            service = m
            connecting?.complete(m)
        }

        override fun onServiceDisconnected(name: ComponentName?) {
            service = null
            connecting = null
            failPending("Процесс нейросети завершился — вероятно, не хватило памяти. Ответил лёгкий режим.")
        }

        override fun onBindingDied(name: ComponentName?) {
            onServiceDisconnected(name)
            runCatching { context.unbindService(this) }
        }
    }

    private suspend fun connect(): Messenger {
        service?.let { return it }
        val d = synchronized(this) {
            connecting ?: CompletableDeferred<Messenger>().also {
                connecting = it
                val ok = context.bindService(Intent(context, MentorService::class.java), connection, Context.BIND_AUTO_CREATE)
                if (!ok) { connecting = null; it.completeExceptionally(IllegalStateException("служба наставника недоступна")) }
            }
        }
        return withTimeout(15_000) { d.await() }
    }

    override suspend fun generate(prompt: String, maxTokens: Int, onPiece: (String) -> Boolean): String {
        val path = modelPath() ?: throw IllegalStateException("модель не установлена")
        val svc = connect()
        val id = ids.incrementAndGet()
        // Один запрос за раз: прежний (если остался) завершается ошибкой, а не висит.
        failPending("запрос заменён новым")
        return suspendCancellableCoroutine { cont ->
            pending = Pending(id, onPiece) { r ->
                if (cont.isActive) r.fold({ cont.resume(it) }, { cont.resumeWithException(it) })
            }
            cont.invokeOnCancellation { stop() }
            val b = Bundle().apply {
                putLong(MentorProtocol.KEY_ID, id)
                putString(MentorProtocol.KEY_MODEL, path)
                putString(MentorProtocol.KEY_PROMPT, prompt + promptSuffix())
                putInt(MentorProtocol.KEY_MAX_TOKENS, maxTokens)
            }
            try {
                svc.send(Message.obtain(null, MentorProtocol.MSG_GENERATE).apply { data = b; replyTo = replies })
            } catch (e: Exception) {
                pending = null
                cont.resumeWithException(IllegalStateException("служба наставника недоступна: ${e.message}"))
            }
        }
    }

    fun stop() {
        runCatching { service?.send(Message.obtain(null, MentorProtocol.MSG_STOP)) }
    }

    /** Заранее загрузить выбранную модель и прогреть начало запроса; результат не нужен, ошибки игнорируются. */
    suspend fun warmUp() {
        val path = modelPath() ?: return
        val svc = runCatching { connect() }.getOrNull() ?: return
        val b = Bundle().apply {
            putString(MentorProtocol.KEY_MODEL, path)
            putString(MentorProtocol.KEY_PROMPT, PromptBuilder.PREFIX)
        }
        runCatching { svc.send(Message.obtain(null, MentorProtocol.MSG_LOAD).apply { data = b }) }
    }

    /** Выгрузить модель из памяти (например, после удаления файла). */
    fun unload() {
        runCatching { service?.send(Message.obtain(null, MentorProtocol.MSG_UNLOAD)) }
    }

    private fun onReply(m: Message) {
        val p = pending ?: return
        val data = m.data
        if (data.getLong(MentorProtocol.KEY_ID) != p.id) return
        when (m.what) {
            MentorProtocol.MSG_PIECE -> {
                val piece = data.getString(MentorProtocol.KEY_TEXT).orEmpty()
                p.text.append(piece)
                if (!p.onPiece(piece)) stop()
            }
            MentorProtocol.MSG_DONE -> {
                lastStats = data.getString(MentorProtocol.KEY_STATS)?.let { parseStats(it, data.getLong(MentorProtocol.KEY_LOAD_MS, 0)) }
                data.getString(MentorProtocol.KEY_INFO)?.let { lastInfo = it }
                pending = null
                if (data.getBoolean(MentorProtocol.KEY_HOT)) {
                    p.done(Result.failure(IllegalStateException("Телефон перегрелся — нейросеть остановлена, ответил лёгкий режим.")))
                } else p.done(Result.success(p.text.toString()))
            }
            MentorProtocol.MSG_ERROR -> {
                pending = null
                p.done(Result.failure(IllegalStateException(data.getString(MentorProtocol.KEY_TEXT) ?: "ошибка нейросети")))
            }
        }
    }

    private fun failPending(msg: String) {
        val p = pending ?: return
        pending = null
        p.done(Result.failure(IllegalStateException(msg)))
    }

    private fun parseStats(json: String, loadMs: Long): GenStats? = runCatching {
        val o = JSONObject(json)
        GenStats(o.getInt("promptTokens"), o.getInt("generatedTokens"), o.getLong("promptMs"), o.getLong("genMs"), o.getBoolean("stopped"),
            cachedTokens = o.optInt("cachedTokens", 0), loadMs = loadMs)
    }.getOrNull()
}
