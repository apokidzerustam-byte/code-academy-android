package app.codeacademy.runner

import android.annotation.SuppressLint
import android.content.Context
import android.os.Build
import android.os.Handler
import android.os.Looper
import android.util.Log
import android.webkit.RenderProcessGoneDetail
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.webkit.WebViewAssetLoader
import androidx.webkit.WebViewCompat
import androidx.webkit.WebViewFeature
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeoutOrNull
import org.json.JSONObject
import java.io.ByteArrayInputStream
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.atomic.AtomicLong

/**
 * Песочница веб-раннера (assets/webrunner): HTML/CSS/JS ученика — в iframe с sandbox и CSP,
 * SQL (sql.js) и разбор Kotlin (tree-sitter) — в Web Worker. Всё работает в рендер-процессе
 * WebView; сеть закрыта CSP страницы и перехватом запросов, мостов в Java нет — только
 * WebMessageListener, принимающий сообщения лишь от страницы приложения.
 */
object WebSandbox {
    const val HOST = "appassets.androidplatform.net"
    const val ORIGIN = "https://$HOST"
    const val PAGE = "$ORIGIN/assets/webrunner/index.html"
    private const val TAG = "CodeAcademyWeb"

    /** Политика хост-страницы; iframe ученика наследует её и добавляет свою, ещё строже. */
    const val CSP =
        "default-src 'self' data: blob:; script-src 'self' 'unsafe-inline' 'unsafe-eval' 'wasm-unsafe-eval' blob:; " +
            "style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self' data:; media-src 'self' data: blob:; " +
            "connect-src 'self'; worker-src 'self'; frame-src 'self' about: data: blob:; form-action 'none'; base-uri 'none'"

    fun supported(): Boolean = WebViewFeature.isFeatureSupported(WebViewFeature.WEB_MESSAGE_LISTENER)

    /**
     * Создаёт WebView со страницей раннера. onGone вызывается, если рендер-процесс завершился
     * (падение или принудительная остановка зависшей страницы) — WebView после этого непригоден.
     */
    @SuppressLint("SetJavaScriptEnabled")
    fun create(context: Context, url: String, onMessage: (String) -> Unit, onGone: (WebView) -> Unit): WebView {
        val app = context.applicationContext
        val loader = WebViewAssetLoader.Builder()
            .addPathHandler("/assets/", WebViewAssetLoader.AssetsPathHandler(app))
            .build()
        val wv = WebView(context)
        wv.settings.apply {
            javaScriptEnabled = true
            allowFileAccess = false
            allowContentAccess = false
            domStorageEnabled = false
            databaseEnabled = false
            setSupportMultipleWindows(false)
            javaScriptCanOpenWindowsAutomatically = false
        }
        WebViewCompat.addWebMessageListener(wv, "caHost", setOf(ORIGIN)) { _, message, _, _, _ ->
            message.data?.let(onMessage)
        }
        wv.webViewClient = object : WebViewClient() {
            override fun shouldInterceptRequest(view: WebView, request: WebResourceRequest): WebResourceResponse =
                asset(loader, request) ?: blocked()

            // Ссылки внутри страницы ученика никуда не уводят хост-страницу.
            override fun shouldOverrideUrlLoading(view: WebView, request: WebResourceRequest): Boolean =
                request.url.host != HOST

            override fun onRenderProcessGone(view: WebView, detail: RenderProcessGoneDetail): Boolean {
                Log.w(TAG, "Рендер-процесс завершился (crash=${detail.didCrash()})")
                onGone(view)
                return true // приложение продолжает работу
            }
        }
        wv.loadUrl(url)
        return wv
    }

    private fun asset(loader: WebViewAssetLoader, request: WebResourceRequest): WebResourceResponse? {
        if (request.url.host != HOST) return null
        val r = loader.shouldInterceptRequest(request.url) ?: return null
        val path = request.url.path ?: ""
        r.mimeType = when {
            path.endsWith(".wasm") -> "application/wasm"
            path.endsWith(".js") -> "text/javascript"
            path.endsWith(".html") -> "text/html"
            path.endsWith(".json") -> "application/json"
            else -> r.mimeType ?: "application/octet-stream"
        }
        if (path.endsWith(".html") || path.endsWith(".js")) r.setEncoding("utf-8")
        r.responseHeaders = mapOf("Content-Security-Policy" to CSP, "X-Content-Type-Options" to "nosniff")
        return r
    }

    private fun blocked() = WebResourceResponse(
        "text/plain", "utf-8", 403, "Blocked", mapOf("X-CA-Blocked" to "1"), ByteArrayInputStream(ByteArray(0)),
    )

    /**
     * Останавливает зависший рендер-процесс (Android 10+). Сигнал получат все WebView приложения
     * в этом процессе — каждая обрабатывает onRenderProcessGone и пересоздаётся.
     */
    fun terminateRenderer(wv: WebView): Boolean =
        Build.VERSION.SDK_INT >= 29 && WebViewFeature.isFeatureSupported(WebViewFeature.GET_WEB_VIEW_RENDERER) &&
            runCatching { WebViewCompat.getWebViewRenderProcess(wv)?.terminate() == true }.getOrDefault(false)

    /** Результат запуска из JSON страницы. */
    fun parseResult(o: JSONObject): RunResult {
        if (o.optBoolean("stopped")) return RunResult(RunStatus.STOPPED)
        val r = o.optString("result").takeIf { it.isNotEmpty() }?.let { runCatching { JSONObject(it) }.getOrNull() }
            ?: return RunResult(RunStatus.ERROR, stderr = o.optString("error", "Нет результата"))
        return RunResult(
            runCatching { RunStatus.valueOf(r.getString("status")) }.getOrDefault(RunStatus.ERROR),
            r.optString("stdout"), r.optString("stderr"), r.optBoolean("truncated"), r.optLong("durationMs"),
        )
    }
}

/**
 * Одна невидимая WebView с хост-страницей для проверок и запусков без предпросмотра.
 * Общая для всех языков: SQL и Kotlin работают в своих воркерах, HTML/JS — в iframe.
 */
class WebRunnerHost(context: Context) {
    private val app = context.applicationContext
    private val main = Handler(Looper.getMainLooper())
    private var webView: WebView? = null
    @Volatile private var ready = CompletableDeferred<Boolean>()
    private val pending = ConcurrentHashMap<Long, CompletableDeferred<RunResult>>()
    @Volatile private var pong: CompletableDeferred<Unit>? = null
    private val ids = AtomicLong(1)

    suspend fun prepare(): Boolean {
        val deadline = System.currentTimeMillis() + START_TIMEOUT_MS
        while (true) {
            withContext(Dispatchers.Main) { if (webView == null) create() }
            // Страницу могли пересоздать, пока ждали: ждём актуальную «готовность».
            val r = ready
            val ok = withTimeoutOrNull(500) { r.await() }
            if (ok != null && r === ready) return ok
            if (System.currentTimeMillis() > deadline) return false
        }
    }

    private fun create() {
        if (!WebSandbox.supported()) {
            ready.complete(false)
            return
        }
        webView = WebSandbox.create(app, WebSandbox.PAGE, ::onMessage) { view ->
            view.destroy()
            if (webView === view) {
                webView = null
                ready = CompletableDeferred()
                failAll(RunResult(RunStatus.CRASHED, stderr = "Страница завершилась аварийно (например, не хватило памяти)"))
            }
        }.also {
            // Размер «экрана» для вёрстки страницы ученика при проверке (WebView не прикреплена к окну).
            it.layout(0, 0, 720, 1280)
        }
    }

    suspend fun request(msg: JSONObject, timeoutMs: Long): RunResult {
        if (!prepare()) {
            return RunResult(RunStatus.UNAVAILABLE, stderr = "Песочница браузера недоступна — обновите «Android System WebView»")
        }
        val id = ids.getAndIncrement()
        val d = CompletableDeferred<RunResult>()
        pending[id] = d
        msg.put("runId", id)
        js("caRun($msg)")
        val r = withTimeoutOrNull(timeoutMs) { d.await() }
        if (r != null) return r
        pending.remove(id)
        stopPage()
        return RunResult(RunStatus.TIMEOUT)
    }

    fun stop() {
        failAll(RunResult(RunStatus.STOPPED))
        main.post {
            val wv = webView ?: return@post
            // Зависшая страница не выполнит caStop() — тогда останавливаем её принудительно.
            var answered = false
            wv.evaluateJavascript("caStop();1") { answered = true }
            main.postDelayed({ if (!answered && webView === wv) killPage(wv) }, 1_500)
        }
    }

    /** Отвязать страницу сразу (новые запросы создадут новую) и остановить её рендер-процесс. Только главный поток. */
    private fun killPage(wv: WebView) {
        if (webView === wv) {
            webView = null
            ready = CompletableDeferred()
        }
        failAll(RunResult(RunStatus.CRASHED, stderr = "Страница перезапущена: она перестала отвечать"))
        if (!WebSandbox.terminateRenderer(wv)) wv.destroy()
    }

    /** «Стоп» на странице; если страница не отвечает — останавливаем рендер-процесс. */
    private suspend fun stopPage() {
        js("caStop()")
        val p = CompletableDeferred<Unit>()
        pong = p
        js("window.caHost&&caHost.postMessage(JSON.stringify({type:'pong'}))")
        if (withTimeoutOrNull(2_000) { p.await() } == null) {
            Log.w("CodeAcademyWeb", "Страница не отвечает — перезапуск")
            withContext(Dispatchers.Main) { webView?.let(::killPage) }
        }
    }

    private fun failAll(r: RunResult) {
        pending.keys.toList().forEach { pending.remove(it)?.complete(r) }
    }

    private fun js(script: String) {
        main.post { webView?.evaluateJavascript(script, null) }
    }

    private fun onMessage(data: String) {
        val o = runCatching { JSONObject(data) }.getOrNull() ?: return
        when (o.optString("type")) {
            "ready" -> ready.complete(o.optBoolean("ok"))
            "pong" -> pong?.complete(Unit)
            "result" -> {
                val id = o.optLong("runId")
                val d = pending.remove(id) ?: return
                d.complete(
                    if (o.has("check")) RunResult(RunStatus.OK, stdout = o.getString("check"))
                    else WebSandbox.parseResult(o)
                )
            }
        }
    }

    fun close() {
        main.post {
            webView?.destroy()
            webView = null
        }
    }

    companion object {
        private const val START_TIMEOUT_MS = 30_000L
    }
}

/**
 * Исполнитель для одного языка поверх общей песочницы: "html", "js", "sql" или "kotlin".
 * Для Kotlin «запуск» — проверка синтаксиса: компилятора Kotlin внутри приложения нет.
 */
class WebRunner(private val host: WebRunnerHost, val lang: String) : CodeRunner {

    override suspend fun prepare(): RunnerInfo? {
        val ok = host.prepare()
        return RunnerInfo(
            pythonStarted = ok,
            startError = if (ok) null else "Песочница браузера недоступна",
            startMs = 0, pid = -1, uid = -1, isolated = true, pyInfo = "webrunner:$lang",
        )
    }

    override suspend fun run(
        code: String,
        timeoutMs: Long,
        stdin: String,
        project: String,
        files: Map<String, String>?,
    ): RunResult = runWith(code, timeoutMs, stdin, files, setup = "")

    /** Запуск с подготовкой базы (SQL-задания: таблицы и данные из теста). */
    suspend fun runWith(code: String, timeoutMs: Long, stdin: String, files: Map<String, String>?, setup: String, entry: String? = null): RunResult {
        val msg = JSONObject()
            .put("lang", lang).put("mode", "run").put("code", code).put("stdin", stdin)
            .put("setup", setup).put("maxOutput", RunnerClient.MAX_OUTPUT_CHARS)
        entry?.let { msg.put("entry", it) }
        if (files != null) msg.put("files", JSONObject(files as Map<*, *>))
        return host.request(msg, timeoutMs)
    }

    override suspend fun check(code: String, testsJson: String, timeoutMs: Long, project: String): RunResult {
        val msg = JSONObject().put("lang", lang).put("mode", "check").put("code", code).put("tests", testsJson)
        return host.request(msg, timeoutMs)
    }

    override fun stop() = host.stop()

    override fun close() = Unit // хост общий для всех языков

    companion object {
        val LANGS = setOf("html", "js", "sql", "kotlin")
    }
}
