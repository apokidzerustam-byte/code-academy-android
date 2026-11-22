package app.codeacademy.editor

import android.annotation.SuppressLint
import android.os.Bundle
import android.view.ViewGroup
import android.webkit.JavascriptInterface
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Button
import android.widget.HorizontalScrollView
import android.widget.LinearLayout
import androidx.activity.ComponentActivity
import androidx.annotation.VisibleForTesting
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat
import androidx.webkit.WebViewAssetLoader
import org.json.JSONObject
import java.io.ByteArrayInputStream

/**
 * Прототип редактора: CodeMirror 6 из assets, без доступа к сети и файлам.
 * Панель символов над клавиатурой вставляет то, чего нет на экранной клавиатуре.
 */
class EditorActivity : ComponentActivity() {

    @VisibleForTesting lateinit var webView: WebView
    @Volatile var lastText: String = ""
        private set

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val loader = WebViewAssetLoader.Builder()
            .addPathHandler("/assets/", WebViewAssetLoader.AssetsPathHandler(this))
            .build()

        webView = WebView(this).apply {
            settings.javaScriptEnabled = true
            settings.allowFileAccess = false
            settings.allowContentAccess = false
            settings.domStorageEnabled = false
            addJavascriptInterface(Bridge(), "AndroidBridge")
            webViewClient = object : WebViewClient() {
                override fun shouldInterceptRequest(view: WebView, request: WebResourceRequest): WebResourceResponse =
                    // Всё, что не из локальных assets, блокируется: редактор работает офлайн.
                    loader.shouldInterceptRequest(request.url)
                        ?: WebResourceResponse("text/plain", "utf-8", 403, "Blocked", emptyMap(), ByteArrayInputStream(ByteArray(0)))

                // Рендер-процесс общий для всех WebView приложения: его остановка (зависшая страница ученика)
                // не должна ронять приложение — закрываем экран прототипа.
                override fun onRenderProcessGone(view: WebView, detail: android.webkit.RenderProcessGoneDetail): Boolean {
                    view.destroy()
                    finish()
                    return true
                }
            }
            loadUrl("https://appassets.androidplatform.net/assets/editor/index.html")
        }

        val bar = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
        SYMBOLS.forEach { s ->
            bar.addView(Button(this).apply {
                text = if (s == "\t") "Tab" else s
                isAllCaps = false
                minWidth = 0
                minimumWidth = 0
                setOnClickListener { insert(s) }
            })
        }
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            addView(webView, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f))
            addView(HorizontalScrollView(this@EditorActivity).apply { addView(bar) })
        }
        ViewCompat.setOnApplyWindowInsetsListener(root) { v, insets ->
            val bars = insets.getInsets(WindowInsetsCompat.Type.systemBars() or WindowInsetsCompat.Type.ime())
            v.setPadding(bars.left, bars.top, bars.right, bars.bottom)
            WindowInsetsCompat.CONSUMED
        }
        setContentView(root)
    }

    fun insert(text: String) {
        webView.evaluateJavascript("window.caEditor && window.caEditor.insert(${JSONObject.quote(text)})", null)
    }

    fun setText(text: String) {
        webView.evaluateJavascript("window.caEditor && window.caEditor.setText(${JSONObject.quote(text)})", null)
    }

    inner class Bridge {
        @JavascriptInterface
        fun onChange(text: String) {
            lastText = text
        }
    }

    companion object {
        val SYMBOLS = listOf("\t", "(", ")", "[", "]", "{", "}", ":", "\"", "'", "=", "<", ">", "+", "-", "*", "/", "#", "_", ".", ",")
    }
}
