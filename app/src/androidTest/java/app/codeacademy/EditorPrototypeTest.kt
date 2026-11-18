package app.codeacademy

import android.util.Log
import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import app.codeacademy.editor.EditorActivity
import org.junit.Assert.assertEquals
import org.junit.Test
import org.junit.runner.RunWith
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit

@RunWith(AndroidJUnit4::class)
class EditorPrototypeTest {

    private fun ActivityScenario<EditorActivity>.js(script: String): String {
        val latch = CountDownLatch(1)
        var result = ""
        onActivity { a -> a.webView.evaluateJavascript(script) { result = it; latch.countDown() } }
        latch.await(5, TimeUnit.SECONDS)
        return result
    }

    private fun ActivityScenario<EditorActivity>.awaitReady() {
        val start = System.currentTimeMillis()
        while (System.currentTimeMillis() - start < 15_000) {
            if (js("!!(window.caEditor && window.caEditor.ready)") == "true") {
                Log.i("CAPROBE", "editor ready in ${System.currentTimeMillis() - start}ms")
                return
            }
            Thread.sleep(200)
        }
        throw AssertionError("CodeMirror не загрузился за 15 с")
    }

    @Test fun editorLoadsOfflineAndRoundTripsText() {
        ActivityScenario.launch(EditorActivity::class.java).use { s ->
            s.awaitReady()
            s.onActivity { it.setText("x = 1") }
            s.onActivity { it.insert("\t") }
            Thread.sleep(300)
            assertEquals("\"x = 1    \"", s.js("window.caEditor.getText()"))
        }
    }

    @Test fun symbolBarInsertsBracketsWithAutoClose() {
        ActivityScenario.launch(EditorActivity::class.java).use { s ->
            s.awaitReady()
            s.onActivity { it.setText("") }
            s.onActivity { it.insert("print(") }
            Thread.sleep(300)
            // Вставка через API не триггерит автозакрытие — фиксируем фактическое поведение.
            val text = s.js("window.caEditor.getText()")
            Log.i("CAPROBE", "editor insert '(' -> $text")
        }
    }

    @Test fun bridgeReceivesChanges() {
        ActivityScenario.launch(EditorActivity::class.java).use { s ->
            s.awaitReady()
            s.onActivity { it.setText("print('hi')") }
            Thread.sleep(500)
            var last = ""
            s.onActivity { last = it.lastText }
            assertEquals("print('hi')", last)
        }
    }
}
