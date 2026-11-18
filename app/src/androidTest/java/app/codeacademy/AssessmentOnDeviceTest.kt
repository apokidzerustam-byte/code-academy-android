package app.codeacademy

import android.util.Log
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import app.codeacademy.assessment.AssessmentService
import app.codeacademy.content.ContentRepository
import app.codeacademy.content.LessonRef
import app.codeacademy.runner.CodeRunner
import app.codeacademy.runner.PyodideRunner
import app.codeacademy.runner.RunStatus
import app.codeacademy.runner.RunnerClient
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Assume.assumeTrue
import org.junit.Test
import org.junit.runner.RunWith

/** Автопроверка заданий образцового урока на устройстве, в обоих исполнителях. */
@RunWith(AndroidJUnit4::class)
class AssessmentOnDeviceTest {
    private val ctx = InstrumentationRegistry.getInstrumentation().targetContext
    private val content = ContentRepository(ctx.assets)
    private val service = AssessmentService()
    private val ref = LessonRef("python-basics", "py-01-print")

    private fun checkAll(runner: CodeRunner, level: String) = runBlocking {
        for (a in content.assignments(ref)) {
            val good = service.evaluate(runner, a, a.solution)
            Log.i("CAPROBE", "level=$level assess ${a.id}: good=${good.passed} ${good.failure ?: ""} ${good.report?.durationMs}ms")
            assertTrue("${a.id}: эталон не прошёл: $good", good.passed)
            val bad = service.evaluate(runner, a, a.starterCode ?: "неверный ответ")
            assertFalse("${a.id}: заготовка прошла", bad.passed)
        }
        val fix = content.assignments(ref).first { it.id == "a2-fix-quote" }
        val v = service.evaluate(runner, fix, fix.starterCode!!)
        assertEquals("SyntaxError", v.errorType)
    }

    @Test fun levelA() {
        val r = RunnerClient(ctx, isolated = false)
        try { checkAll(r, "A") } finally { r.close() }
    }

    @Test fun levelW() {
        val r = PyodideRunner(ctx)
        try {
            assumeTrue("Pyodide недоступен на этом WebView", runBlocking { r.prepare() }?.pythonStarted == true)
            checkAll(r, "W")
            val tests = runBlocking { service.testsJson(content.assignments(ref)[0]) }
            val hang = runBlocking { r.check("while True:\n    pass", tests, 2_000) }
            assertEquals(RunStatus.TIMEOUT, hang.status)
        } finally { r.close() }
    }
}
