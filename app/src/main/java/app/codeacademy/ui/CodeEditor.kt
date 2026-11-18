package app.codeacademy.ui

import android.annotation.SuppressLint
import android.os.Handler
import android.os.Looper
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.luminance
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.TextRange
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.input.TextFieldValue
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.webkit.WebViewAssetLoader
import androidx.webkit.WebViewCompat
import androidx.webkit.WebViewFeature
import org.json.JSONObject
import java.io.ByteArrayInputStream

/** Управление редактором из кода (панель символов, тесты). */
class EditorController {
    internal var webView: WebView? = null
    internal var ready = false
    internal var plainInsert: ((String) -> Unit)? = null
    private val main = Handler(Looper.getMainLooper())

    private fun js(script: String) = main.post { webView?.evaluateJavascript(script, null) }

    fun insert(text: String) {
        plainInsert?.let { it(text); return }
        if (ready) js("caEditor.insert(${JSONObject.quote(text)})")
    }

    fun undo() { if (ready) js("caEditor.undo()") }
    fun redo() { if (ready) js("caEditor.redo()") }

    /** Режим CodeMirror (а не простое поле). */
    val isRich: Boolean get() = plainInsert == null && webView != null
}

val EDITOR_SYMBOLS = listOf("Tab", "(", ")", ":", "\"", "'", "[", "]", "{", "}", "=", "+", "-", "*", "/", "#", "<", ">", "_", ".", ",")

private const val ORIGIN = "https://appassets.androidplatform.net"

/** Поддерживает ли WebView безопасный канал сообщений для CodeMirror. */
fun richEditorSupported(): Boolean =
    runCatching { WebViewFeature.isFeatureSupported(WebViewFeature.WEB_MESSAGE_LISTENER) }.getOrDefault(false)

/**
 * Редактор кода (IDEManager): CodeMirror 6 с подсветкой, автоотступами, закрытием скобок,
 * отменой/повтором и панелью символов. При [plain] или старом WebView — простое поле ввода.
 */
@Composable
fun CodeEditor(
    value: String,
    onValueChange: (String) -> Unit,
    modifier: Modifier = Modifier,
    language: String = "python",
    plain: Boolean = false,
    height: Dp = 280.dp,
    controller: EditorController = remember { EditorController() },
    label: String = "Код",
) {
    val useRich = !plain && remember { richEditorSupported() }
    Column(modifier) {
        if (useRich) RichEditor(value, onValueChange, language, height, controller)
        else PlainEditor(value, onValueChange, height, controller, label)
        SymbolBar(controller)
    }
}

@Composable
private fun SymbolBar(controller: EditorController) {
    Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()).testTag("symbol-bar")) {
        for (s in EDITOR_SYMBOLS) {
            TextButton(onClick = { controller.insert(if (s == "Tab") "\t" else s) }, modifier = Modifier.testTag("sym-$s")) {
                Text(s, fontFamily = FontFamily.Monospace)
            }
        }
        TextButton(onClick = { controller.undo() }) { Text("↶") }
        TextButton(onClick = { controller.redo() }) { Text("↷") }
    }
}

@Composable
private fun PlainEditor(value: String, onValueChange: (String) -> Unit, height: Dp, controller: EditorController, label: String) {
    var tfv by remember { mutableStateOf(TextFieldValue(value)) }
    if (tfv.text != value) tfv = TextFieldValue(value, TextRange(value.length))
    val latest by rememberUpdatedState(tfv)
    val latestChange by rememberUpdatedState(onValueChange)
    DisposableEffect(controller) {
        controller.plainInsert = { s ->
            val t = latest
            val ins = if (s == "\t") "    " else s
            val text = t.text.replaceRange(t.selection.min, t.selection.max, ins)
            val pos = t.selection.min + ins.length
            tfv = TextFieldValue(text, TextRange(pos))
            latestChange(text)
        }
        onDispose { controller.plainInsert = null }
    }
    OutlinedTextField(
        value = tfv,
        onValueChange = { tfv = it; if (it.text != value) onValueChange(it.text) },
        label = { Text(label) },
        textStyle = MaterialTheme.typography.bodyMedium.copy(fontFamily = FontFamily.Monospace),
        modifier = Modifier.fillMaxWidth().heightIn(min = height).testTag("code"),
    )
}

@SuppressLint("SetJavaScriptEnabled")
@Composable
private fun RichEditor(value: String, onValueChange: (String) -> Unit, language: String, height: Dp, controller: EditorController) {
    val dark = MaterialTheme.colorScheme.background.luminance() < 0.5f
    val fontPx = with(LocalDensity.current) { 15f * fontScale }
    val latestValue by rememberUpdatedState(value)
    val latestOnChange by rememberUpdatedState(onValueChange)
    // Последний текст, известный редактору: не отправляем его обратно (нет петли обновлений).
    val lastFromEditor = remember { arrayOf<String?>(null) }

    fun setup(wv: WebView) {
        wv.evaluateJavascript(
            "caEditor.setLanguage(${JSONObject.quote(language)});caEditor.setTheme($dark);" +
                "caEditor.setFontSize($fontPx);caEditor.setText(${JSONObject.quote(latestValue)});", null,
        )
        lastFromEditor[0] = latestValue
    }

    AndroidView(
        modifier = Modifier.fillMaxWidth().height(height).padding(vertical = 4.dp).testTag("code-editor"),
        factory = { ctx ->
            val loader = WebViewAssetLoader.Builder()
                .addPathHandler("/assets/", WebViewAssetLoader.AssetsPathHandler(ctx))
                .build()
            WebView(ctx).apply {
                settings.javaScriptEnabled = true
                settings.allowFileAccess = false
                settings.allowContentAccess = false
                WebViewCompat.addWebMessageListener(this, "caEditorHost", setOf(ORIGIN)) { view, message, _, _, _ ->
                    val o = runCatching { JSONObject(message.data ?: "") }.getOrNull() ?: return@addWebMessageListener
                    when (o.optString("type")) {
                        "ready" -> { controller.ready = true; setup(view) }
                        "change" -> {
                            val text = o.optString("text")
                            lastFromEditor[0] = text
                            if (text != latestValue) latestOnChange(text)
                        }
                    }
                }
                webViewClient = object : WebViewClient() {
                    override fun shouldInterceptRequest(view: WebView, request: WebResourceRequest): WebResourceResponse =
                        loader.shouldInterceptRequest(request.url)
                            ?: WebResourceResponse("text/plain", "utf-8", 403, "Blocked", emptyMap(), ByteArrayInputStream(ByteArray(0)))
                }
                controller.webView = this
                loadUrl("$ORIGIN/assets/editor/index.html")
            }
        },
        update = { wv ->
            if (controller.ready && value != lastFromEditor[0]) {
                lastFromEditor[0] = value
                wv.evaluateJavascript("caEditor.setText(${JSONObject.quote(value)})", null)
            }
        },
    )
    LaunchedEffect(dark, fontPx) {
        if (controller.ready) controller.webView?.evaluateJavascript("caEditor.setTheme($dark);caEditor.setFontSize($fontPx)", null)
    }
    DisposableEffect(Unit) {
        onDispose {
            controller.webView?.evaluateJavascript("caEditor.flush()", null)
            controller.webView?.destroy()
            controller.webView = null
            controller.ready = false
        }
    }
}
