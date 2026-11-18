package app.codeacademy

import android.util.Log
import android.webkit.WebView
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performTextReplacement
import androidx.test.ext.junit.runners.AndroidJUnit4
import app.codeacademy.ui.CodeEditor
import app.codeacademy.ui.EditorController
import app.codeacademy.ui.richEditorSupported
import org.junit.Assert.assertEquals
import org.junit.Assume.assumeTrue
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit

@RunWith(AndroidJUnit4::class)
class CodeEditorTest {
    @get:Rule val rule = createComposeRule()

    @Volatile private var latest = ""

    private fun jsText(c: EditorController): String {
        val latch = CountDownLatch(1)
        var out = ""
        rule.runOnUiThread {
            val wv: WebView = c.webView!!
            wv.evaluateJavascript("caEditor.getText()") { out = it; latch.countDown() }
        }
        latch.await(5, TimeUnit.SECONDS)
        return out
    }

    @Test fun richEditorSyncsBothWays() {
        assumeTrue("WebView без WEB_MESSAGE_LISTENER — используется простое поле", richEditorSupported())
        val c = EditorController()
        var external: ((String) -> Unit)? = null
        rule.setContent {
            var v by remember { mutableStateOf("x = 1") }
            external = { v = it }
            CodeEditor(v, { v = it; latest = it }, controller = c)
        }
        val t0 = System.currentTimeMillis()
        rule.waitUntil(20_000) { c.isRich && jsText(c) == "\"x = 1\"" }
        Log.i("CAPROBE", "editor rich ready+sync ${System.currentTimeMillis() - t0}ms")
        // Панель символов → редактор → приложение.
        rule.onNodeWithTag("sym-(").performClick()
        rule.waitUntil(5_000) { latest.contains("(") }
        org.junit.Assert.assertTrue(latest, latest.contains("x = 1") && latest.count { it == '(' } == 1)
        // Приложение → редактор (например, сброс к заготовке).
        rule.runOnIdle { external!!("print('новый')") }
        rule.waitUntil(5_000) { jsText(c) == "\"print('новый')\"" }
        rule.onNodeWithTag("sym-Tab").performClick()
        rule.waitUntil(5_000) { latest.contains("    ") }
    }

    @Test fun plainEditorInsertsAtCursor() {
        val c = EditorController()
        rule.setContent {
            var v by remember { mutableStateOf("") }
            CodeEditor(v, { v = it; latest = it }, plain = true, controller = c)
        }
        rule.onNodeWithTag("code").performTextReplacement("print")
        rule.onNodeWithTag("sym-(").performClick()
        rule.onNodeWithTag("sym-\"").performClick()
        rule.runOnIdle { assertEquals("print(\"", latest) }
        rule.onNodeWithTag("sym-Tab").performClick()
        rule.runOnIdle { assertEquals("print(\"    ", latest) }
    }
}
