package app.codeacademy.ui

import android.webkit.WebView
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.key
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import app.codeacademy.runner.RunResult
import app.codeacademy.runner.RunStatus
import app.codeacademy.runner.RunnerClient
import app.codeacademy.runner.WebSandbox
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.withTimeoutOrNull
import org.json.JSONObject

/** Управление видимым предпросмотром страницы ученика (HTML/CSS/JS). */
class WebPreviewController {
    internal var webView: WebView? = null
    internal var ready = CompletableDeferred<Unit>()
    private var pending: CompletableDeferred<RunResult>? = null
    private var runSeq = 0L
    /** Вывод страницы после загрузки (клики, таймеры): поток stdout/stderr и текст. */
    var onOutput: ((String, String) -> Unit)? = null

    suspend fun run(lang: String, code: String, files: Map<String, String>? = null, entry: String? = null, stdin: String = "",
                    timeoutMs: Long = 10_000): RunResult {
        if (!WebSandbox.supported()) return RunResult(RunStatus.UNAVAILABLE, stderr = "Предпросмотр недоступен — обновите «Android System WebView»")
        // Страница может появиться (или пересоздаться) уже после вызова: ждём ту «готовность», что актуальна сейчас.
        val deadline = System.currentTimeMillis() + 15_000
        while (true) {
            val r = ready
            if (withTimeoutOrNull(250) { r.await() } != null && r === ready && webView != null) break
            if (System.currentTimeMillis() > deadline) return RunResult(RunStatus.UNAVAILABLE, stderr = "Предпросмотр не загрузился")
        }
        pending?.complete(RunResult(RunStatus.STOPPED))
        val d = CompletableDeferred<RunResult>()
        pending = d
        val id = ++runSeq
        val msg = JSONObject().put("runId", id).put("lang", lang).put("mode", "run").put("code", code).put("stdin", stdin)
            .put("maxOutput", RunnerClient.MAX_OUTPUT_CHARS)
        entry?.let { msg.put("entry", it) }
        if (files != null) msg.put("files", JSONObject(files as Map<*, *>))
        webView?.evaluateJavascript("caRun($msg)", null)
        val r = withTimeoutOrNull(timeoutMs) { d.await() }
        if (r == null) {
            stop()
            return RunResult(RunStatus.TIMEOUT)
        }
        return r
    }

    fun stop() {
        pending?.complete(RunResult(RunStatus.STOPPED))
        pending = null
        val wv = webView ?: return
        // Зависшая страница не выполнит caStop(): если ответа нет, останавливаем рендер-процесс (страница пересоздастся).
        var answered = false
        wv.evaluateJavascript("caStop();1") { answered = true }
        wv.postDelayed({ if (!answered && webView === wv) WebSandbox.terminateRenderer(wv) }, 3_500)
    }

    internal fun onMessage(data: String) {
        val o = runCatching { JSONObject(data) }.getOrNull() ?: return
        when (o.optString("type")) {
            "ready" -> ready.complete(Unit)
            "result" -> if (o.optLong("runId") == runSeq) pending?.complete(WebSandbox.parseResult(o))?.also { pending = null }
            "event" -> if (o.optLong("runId") == runSeq) {
                val e = o.optJSONObject("event") ?: return
                // Вывод до окончания загрузки придёт в результате запуска; здесь — только последующий.
                if (pending == null) {
                    val text = if (e.optString("t") == "error") e.optString("text") + (e.optInt("line").takeIf { it > 0 }?.let { " (строка $it)" } ?: "") + "\n"
                    else e.optString("text")
                    onOutput?.invoke(if (e.optString("t") == "error") "stderr" else e.optString("stream"), text)
                }
            }
        }
    }
}

/** Видимая страница ученика. Работает в той же песочнице, что и проверки (iframe sandbox + CSP). */
@Composable
fun WebPreview(controller: WebPreviewController, modifier: Modifier = Modifier, height: Dp = 320.dp) {
    var generation by remember { mutableStateOf(0) }
    val ctl by rememberUpdatedState(controller)
    key(generation) {
        AndroidView(
            modifier = modifier.fillMaxWidth().height(height)
                .border(1.dp, MaterialTheme.colorScheme.outlineVariant).testTag("web-preview"),
            factory = { ctx ->
                if (ctl.ready.isCompleted) ctl.ready = CompletableDeferred() // пересоздание после падения
                WebSandbox.create(ctx, WebSandbox.PAGE + "?preview=1", { ctl.onMessage(it) }) { view ->
                    if (ctl.webView === view) ctl.webView = null
                    ctl.stop()
                    view.destroy()
                    generation++
                }.also { ctl.webView = it }
            },
        )
    }
    DisposableEffect(Unit) {
        onDispose {
            ctl.stop()
            ctl.webView?.destroy()
            ctl.webView = null
        }
    }
}
