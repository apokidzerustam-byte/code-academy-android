package app.codeacademy

import android.util.Log
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import app.codeacademy.assessment.AssessmentService
import app.codeacademy.content.ContentRepository
import app.codeacademy.content.LessonRef
import app.codeacademy.runner.CodeRunner
import app.codeacademy.runner.PyodideRunner
import app.codeacademy.runner.RunnerClient
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertTrue
import org.junit.Assume.assumeTrue
import org.junit.Test
import org.junit.runner.RunWith

/**
 * Весь пилотный пакет на устройстве: каждое эталонное решение проходит автопроверку,
 * каждое типовое неверное решение — нет. Проверяется в обоих исполнителях
 * (валидатор в CI делает то же на CPython; здесь — Chaquopy и Pyodide, как у ученика).
 */
@RunWith(AndroidJUnit4::class)
class PilotContentOnDeviceTest {
    private val ctx = InstrumentationRegistry.getInstrumentation().targetContext
    private val content = ContentRepository(ctx.assets)
    private val service = AssessmentService()

    private fun checkPack(runner: CodeRunner, level: String) = runBlocking {
        val problems = mutableListOf<String>()
        var checked = 0
        val t0 = System.currentTimeMillis()
        for ((pack, lesson) in content.allLessons()) {
            if (pack.id != "python-basics") continue // другие языки — WebLanguagesOnDeviceTest
            val ref = LessonRef(pack.id, lesson.id)
            for (a in content.assignments(ref)) {
                val good = service.evaluate(runner, a, a.solution)
                if (!good.passed) problems += "${lesson.id}/${a.id}: эталон не прошёл (${good.failure ?: good.errorType})"
                for (w in a.wrongSolutions) {
                    val bad = service.evaluate(runner, a, w.answer ?: w.code)
                    if (bad.passed) problems += "${lesson.id}/${a.id}: прошло неверное решение «${w.why}»"
                }
                checked++
            }
        }
        Log.i("CAPROBE", "level=$level pilot: $checked заданий за ${System.currentTimeMillis() - t0} мс, проблем ${problems.size}")
        problems.forEach { Log.e("CAPROBE", it) }
        assertTrue("$checked заданий, проблемы:\n" + problems.joinToString("\n"), problems.isEmpty() && checked >= 30)
    }

    @Test fun levelA() {
        val r = RunnerClient(ctx, isolated = false)
        try { checkPack(r, "A") } finally { r.close() }
    }

    @Test fun levelW() {
        val r = PyodideRunner(ctx)
        try {
            assumeTrue("Pyodide недоступен на этом WebView", runBlocking { r.prepare() }?.pythonStarted == true)
            checkPack(r, "W")
        } finally { r.close() }
    }
}
