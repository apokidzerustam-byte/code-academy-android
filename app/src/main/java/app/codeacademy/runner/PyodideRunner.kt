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
 * Уровень W: Python 3.13 (Pyodide, WebAssembly) в Web Worker внутри WebView.
 *
 * Изоляция: код ученика выполняется в рендер-процессе WebView — на Android 8+ это
 * отдельный изолированный процесс Chromium (SandboxedProcessService). Файловой системы
 * устройства у Pyodide нет (только память), сеть закрыта CSP и перехватом запросов,
 * мостов в Java нет (связь только через WebMessageListener главной страницы).
 * Таймаут и «Стоп» — terminate() воркера с перезапуском интерпретатора.
 */
class PyodideRunner(context: Context) : CodeRunner {

    private val app = context.applicationContext
    private val main = Handler(Looper.getMainLooper())
    private var webView: WebView? = null
    @Volatile private var ready = CompletableDeferred<RunnerInfo>()
    private val pending = ConcurrentHashMap<Long, CompletableDeferred<RunResult>>()
    @Volatile private var pendingProbe: CompletableDeferred<String>? = null
    private val ids = AtomicLong(1)
    @Volatile private var lastStartMs = 0L

    private val loader by lazy {
        WebViewAssetLoader.Builder()
            .addPathHandler("/assets/", WebViewAssetLoader.AssetsPathHandler(app))
            .build()
    }

    override suspend fun prepare(): RunnerInfo? {
        withContext(Dispatchers.Main) { if (webView == null) createWebView() }
        return withTimeoutOrNull(START_TIMEOUT_MS) { ready.await() }
    }

    override suspend fun run(
        code: String,
        timeoutMs: Long,
        stdin: String,
        project: String,
        files: Map<String, String>?,
    ): RunResult = send(code, timeoutMs, stdin, project, null, files)

    override suspend fun check(code: String, testsJson: String, timeoutMs: Long, project: String, files: Map<String, String>?): RunResult =
        send(code, timeoutMs, "", project, testsJson, null)

    private suspend fun send(
        code: String,
        timeoutMs: Long,
        stdin: String,
        project: String,
        tests: String?,
        files: Map<String, String>?,
    ): RunResult {
        val info = prepare()
            ?: return RunResult(RunStatus.UNAVAILABLE, stderr = "Интерпретатор не запустился за ${START_TIMEOUT_MS / 1000} с")
        if (!info.pythonStarted) return RunResult(RunStatus.UNAVAILABLE, stderr = info.startError ?: "")
        val id = ids.getAndIncrement()
        val d = CompletableDeferred<RunResult>()
        pending[id] = d
        val msg = JSONObject()
            .put("runId", id).put("code", code).put("stdin", stdin)
            .put("project", project.replace(Regex("[^A-Za-z0-9_-]"), "_"))
            .put("maxOutput", RunnerClient.MAX_OUTPUT_CHARS)
            .put("mode", if (tests == null) "run" else "check")
            .put("tests", tests ?: "")
        if (files != null) msg.put("files", JSONObject(files as Map<*, *>))
        js("caRun($msg)")
        return withTimeoutOrNull(timeoutMs) { d.await() }
            ?: RunResult(RunStatus.TIMEOUT).also { restartInterpreter(RunStatus.TIMEOUT) }
    }

    override fun stop() {
        restartInterpreter(RunStatus.STOPPED)
    }

    /** Только для тестов: что запрещено самой средой (в обход Python-хуков). */
    suspend fun kernelProbe(path: String): String? {
        if (prepare()?.pythonStarted != true) return null
        val d = CompletableDeferred<String>()
        pendingProbe = d
        js("caProbe(${JSONObject.quote(path)})")
        return withTimeoutOrNull(15_000) { d.await() }
    }

    override fun close() {
        main.post {
            webView?.destroy()
            webView = null
        }
    }

    /** Убивает воркер (это прерывает любой код, в т. ч. зависший в C) и запускает новый. */
    private fun restartInterpreter(status: RunStatus) {
        ready = CompletableDeferred()
        js("caKill()")
        pending.keys.toList().forEach { pending.remove(it)?.complete(RunResult(status)) }
    }

    private fun js(script: String) {
        main.post { webView?.evaluateJavascript(script, null) }
    }

    @SuppressLint("SetJavaScriptEnabled")
    private fun createWebView() {
        if (!WebViewFeature.isFeatureSupported(WebViewFeature.WEB_MESSAGE_LISTENER)) {
            ready.complete(info(false, "WebView не поддерживает WEB_MESSAGE_LISTENER — обновите Android System WebView"))
            return
        }
        val wv = WebView(app)
        wv.settings.apply {
            javaScriptEnabled = true
            allowFileAccess = false
            allowContentAccess = false
            domStorageEnabled = false
            databaseEnabled = false
        }
        WebViewCompat.addWebMessageListener(wv, "caHost", setOf(ORIGIN)) { _, message, _, _, _ ->
            onMessage(message.data)
        }
        wv.webViewClient = object : WebViewClient() {
            override fun shouldInterceptRequest(view: WebView, request: WebResourceRequest): WebResourceResponse =
                assetResponse(request) ?: blocked()

            override fun onRenderProcessGone(view: WebView, detail: RenderProcessGoneDetail): Boolean {
                Log.w(TAG, "Рендер-процесс завершился (crash=${detail.didCrash()})")
                view.destroy()
                if (webView === view) webView = null
                ready = CompletableDeferred()
                pending.keys.toList().forEach {
                    pending.remove(it)?.complete(RunResult(RunStatus.CRASHED, stderr = "Процесс выполнения завершился аварийно"))
                }
                return true // приложение продолжает работу
            }
        }
        webView = wv
        wv.loadUrl("$ORIGIN/assets/pyrunner/index.html")
    }

    private fun assetResponse(request: WebResourceRequest): WebResourceResponse? {
        if (request.url.host != HOST) return null
        val r = loader.shouldInterceptRequest(request.url) ?: return null
        val path = request.url.path ?: ""
        r.mimeType = when {
            path.endsWith(".wasm") -> "application/wasm"
            path.endsWith(".js") || path.endsWith(".mjs") -> "text/javascript"
            path.endsWith(".html") -> "text/html"
            path.endsWith(".json") -> "application/json"
            path.endsWith(".zip") -> "application/zip"
            else -> r.mimeType ?: "application/octet-stream"
        }
        r.responseHeaders = mapOf(
            // Сеть закрыта для страницы и воркера; разрешены только свои assets.
            "Content-Security-Policy" to CSP,
            "Cross-Origin-Opener-Policy" to "same-origin",
            "Cross-Origin-Embedder-Policy" to "require-corp",
            "Cross-Origin-Resource-Policy" to "same-origin",
        )
        return r
    }

    private fun blocked() = WebResourceResponse(
        "text/plain", "utf-8", 403, "Blocked", mapOf("X-CA-Blocked" to "1"), ByteArrayInputStream(ByteArray(0)),
    )

    private fun onMessage(data: String?) {
        val o = runCatching { JSONObject(data ?: return) }.getOrNull() ?: return
        when (o.optString("type")) {
            "ready" -> {
                lastStartMs = o.optLong("startMs")
                ready.complete(
                    if (o.optBoolean("ok")) info(true, null, o.optString("pyInfo"), o.optBoolean("crossOriginIsolated"))
                    else info(false, o.optString("error"))
                )
            }
            "result" -> {
                if (o.has("check")) {
                    pending.remove(o.optLong("runId"))?.complete(RunResult(RunStatus.OK, stdout = o.getString("check")))
                    return
                }
                val r = runCatching { JSONObject(o.getString("result")) }.getOrNull()
                val res = if (r == null) RunResult(RunStatus.ERROR, stderr = o.optString("error"))
                else RunResult(
                    RunStatus.valueOf(r.getString("status")),
                    r.getString("stdout"), r.getString("stderr"),
                    r.getBoolean("truncated"), r.getLong("durationMs"),
                )
                val files = o.optString("files").takeIf { it.isNotEmpty() }?.let { s ->
                    runCatching { JSONObject(s).let { j -> j.keys().asSequence().associateWith { k -> j.getString(k) } } }.getOrNull()
                }
                pending.remove(o.optLong("runId"))?.complete(res.copy(files = files))
            }
            "probe" -> pendingProbe?.complete(o.optString("result"))
        }
    }

    private fun info(ok: Boolean, error: String?, pyInfo: String? = null, coi: Boolean = false) = RunnerInfo(
        pythonStarted = ok,
        startError = error,
        startMs = lastStartMs,
        pid = -1,
        uid = -1,
        isolated = rendererOutOfProcess(),
        pyInfo = pyInfo?.let { "$it crossOriginIsolated=$coi" },
    )

    /** true, если рендерер WebView работает в отдельном (изолированном) процессе. */
    private fun rendererOutOfProcess(): Boolean {
        val wv = webView ?: return false
        return if (Build.VERSION.SDK_INT >= 29 &&
            WebViewFeature.isFeatureSupported(WebViewFeature.GET_WEB_VIEW_RENDERER)
        ) {
            runCatching { WebViewCompat.getWebViewRenderProcess(wv) != null }.getOrDefault(false)
        } else {
            false // на API 26–28 проверить программно нельзя
        }
    }

    companion object {
        private const val TAG = "CodeAcademyPyodide"
        private const val HOST = "appassets.androidplatform.net"
        private const val ORIGIN = "https://$HOST"
        private const val START_TIMEOUT_MS = 60_000L
        private const val CSP =
            "default-src 'self'; script-src 'self' 'unsafe-eval' 'wasm-unsafe-eval'; " +
                "connect-src 'self'; worker-src 'self'; style-src 'self' 'unsafe-inline'"
    }
}
