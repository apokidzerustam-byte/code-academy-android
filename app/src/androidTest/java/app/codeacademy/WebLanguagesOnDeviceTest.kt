package app.codeacademy

import android.util.Log
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import app.codeacademy.assessment.AssessmentService
import app.codeacademy.content.ContentRepository
import app.codeacademy.content.LessonRef
import app.codeacademy.runner.CodeRunner
import app.codeacademy.runner.RunStatus
import app.codeacademy.runner.RunnerClient
import app.codeacademy.runner.WebRunner
import app.codeacademy.runner.WebRunnerHost
import app.codeacademy.ui.assignmentRunner
import kotlinx.coroutines.async
import kotlinx.coroutines.delay
import kotlinx.coroutines.runBlocking
import org.junit.AfterClass
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.BeforeClass
import org.junit.Test
import org.junit.runner.RunWith

/**
 * Этап 7 на устройстве: для каждого языка — запуск, ошибка, остановка; автопроверка всех заданий
 * новых пакетов (эталон проходит, типовые ошибки — нет) тем исполнителем, который выберет приложение.
 */
@RunWith(AndroidJUnit4::class)
class WebLanguagesOnDeviceTest {
    companion object {
        private val ctx = InstrumentationRegistry.getInstrumentation().targetContext
        private lateinit var host: WebRunnerHost

        @JvmStatic @BeforeClass fun start() {
            host = WebRunnerHost(ctx)
            val t0 = System.currentTimeMillis()
            assertTrue("веб-песочница не запустилась", runBlocking { host.prepare() })
            Log.i("CAPROBE", "webrunner: старт ${System.currentTimeMillis() - t0} мс")
        }

        @JvmStatic @AfterClass fun stop() = host.close()
    }

    private fun web(lang: String) = WebRunner(host, lang)

    @Test fun jsRunErrorStop() = runBlocking {
        val js = web("js")
        val ok = js.run("const a = [1, 2, 3]\nconsole.log(a.map(x => x * 2).join(' '))", 8_000)
        assertEquals(ok.stderr, RunStatus.OK, ok.status)
        assertEquals("2 4 6", ok.stdout.trim())

        val err = js.run("let total = 1\nconsole.log(totl)", 8_000)
        assertEquals(RunStatus.ERROR, err.status)
        assertTrue(err.stderr, "ReferenceError" in err.stderr && "строка 2" in err.stderr)

        val syn = js.run("function f( {", 8_000)
        assertEquals(RunStatus.SYNTAX_ERROR, syn.status)

        // Бесконечный цикл прерывается защитой (≈2 с), страница остаётся рабочей.
        val t0 = System.currentTimeMillis()
        val loop = js.run("let i = 0\nwhile (i < 5) { }", 10_000)
        val loopMs = System.currentTimeMillis() - t0
        assertEquals(loop.stderr, RunStatus.ERROR, loop.status)
        assertTrue(loop.stderr, "InfiniteLoopError" in loop.stderr)
        assertTrue("цикл остановлен за $loopMs мс", loopMs < 6_000)

        // «Стоп» во время работы: результат STOPPED сразу, следующий запуск работает.
        val running = async { js.run("setTimeout(() => console.log('поздно'), 5000)\nwhile (true) { }", 10_000) }
        delay(400)
        js.stop()
        assertEquals(RunStatus.STOPPED, running.await().status)
        val after = js.run("console.log('снова работает')", 10_000)
        assertEquals(after.stderr, RunStatus.OK, after.status)
        assertEquals("снова работает", after.stdout.trim())
        Log.i("CAPROBE", "js: цикл прерван за $loopMs мс")
    }

    @Test fun htmlRunAndLint() = runBlocking {
        val html = web("html")
        val r = html.run("<h1>Привет</h1>\n<p id=\"x\">5</p>\n<img src=\"a.png\">\n<script>console.log(+document.getElementById('x').textContent * 2)</script>", 8_000)
        assertEquals(r.stderr, RunStatus.OK, r.status)
        assertEquals("10", r.stdout.trim())
        assertTrue("нет предупреждения alt: ${r.stderr}", "alt" in r.stderr)
        // Сеть закрыта: fetch к внешнему сайту не проходит.
        val net = html.run("<script>fetch('https://example.com').then(() => console.log('сеть есть')).catch(() => console.log('сети нет'))</script>", 8_000)
        delay(1_500)
        assertTrue(net.stdout + net.stderr, "сеть есть" !in net.stdout)
    }

    @Test fun sqlRunErrorStop() = runBlocking {
        val sql = web("sql")
        val ok = sql.runWith("SELECT name FROM t ORDER BY name;", 10_000, "", null,
            setup = "CREATE TABLE t (name TEXT); INSERT INTO t VALUES ('Борис'), ('Анна');")
        assertEquals(ok.stderr, RunStatus.OK, ok.status)
        assertTrue(ok.stdout, ok.stdout.indexOf("Анна") in 0 until ok.stdout.indexOf("Борис"))

        val err = sql.run("SELECT titel FROM t;", 10_000)
        assertTrue(err.stderr, err.status != RunStatus.OK && "SQLError" in err.stderr)

        // Бесконечный рекурсивный запрос: таймаут останавливает воркер, следующий запрос работает.
        val t0 = System.currentTimeMillis()
        val hang = sql.run("WITH RECURSIVE c(x) AS (SELECT 1 UNION ALL SELECT x + 1 FROM c) SELECT count(*) FROM c;", 3_000)
        assertEquals(RunStatus.TIMEOUT, hang.status)
        val after = sql.run("SELECT 1 + 1 AS s;", 10_000)
        assertEquals(after.stderr, RunStatus.OK, after.status)
        assertTrue(after.stdout, "2" in after.stdout)
        Log.i("CAPROBE", "sql: зависший запрос остановлен за ${System.currentTimeMillis() - t0} мс")
    }

    @Test fun kotlinSyntax() = runBlocking {
        val kt = web("kotlin")
        val ok = kt.run("fun main() {\n    val n = 3\n    println(\"n = \$n\")\n}\n", 10_000)
        assertEquals(ok.stderr, RunStatus.OK, ok.status)
        assertTrue(ok.stdout, "Синтаксис в порядке" in ok.stdout)
        val bad = kt.run("fun main() {\n    println(\"привет\"\n}\n", 10_000)
        assertEquals(RunStatus.SYNTAX_ERROR, bad.status)
        assertTrue(bad.stderr, "строка" in bad.stderr)
    }

    /** Все задания новых пакетов: исполнитель — как в приложении (веб-язык задания или Python A для FastAPI и ответов). */
    @Test fun newPacksAutocheck() = runBlocking {
        val content = ContentRepository(ctx.assets)
        val service = AssessmentService()
        val python = RunnerClient(ctx, isolated = false)
        val problems = mutableListOf<String>()
        val perLang = sortedMapOf<String, Int>()
        try {
            for ((pack, lesson) in content.allLessons()) {
                if (pack.id == "python-basics") continue // проверяется PilotContentOnDeviceTest
                val ref = LessonRef(pack.id, lesson.id)
                for (a in content.assignments(ref)) {
                    val lang = if (a.isAnswerTask) "A" else assignmentRunner(a, lesson.runner)
                    val runner: CodeRunner = if (lang in WebRunner.LANGS) web(lang) else python
                    val t0 = System.currentTimeMillis()
                    val good = service.evaluate(runner, a, a.solution)
                    if (!good.passed) problems += "${lesson.id}/${a.id} [$lang]: эталон не прошёл (${good.failure ?: good.errorType}: " +
                        "${good.failureText.take(200)} ${good.report?.loadError ?: good.report?.compileError ?: ""})"
                    for (w in a.wrongSolutions) {
                        val bad = service.evaluate(runner, a, w.answer ?: w.code)
                        if (bad.passed) problems += "${lesson.id}/${a.id} [$lang]: прошло неверное решение «${w.why}»"
                    }
                    perLang[lang] = (perLang[lang] ?: 0) + 1
                    Log.i("CAPROBE", "${lesson.id}/${a.id} [$lang]: ${System.currentTimeMillis() - t0} мс")
                }
            }
        } finally {
            python.close()
        }
        Log.i("CAPROBE", "новые пакеты: $perLang, проблем ${problems.size}")
        problems.forEach { Log.e("CAPROBE", it) }
        assertTrue("проблемы:\n" + problems.joinToString("\n"), problems.isEmpty())
        // Не меньше трёх автопроверяемых заданий на каждый язык этапа 7 (FastAPI — исполнитель A).
        for (l in listOf("html", "js", "sql", "kotlin")) assertTrue("$l: ${perLang[l]} заданий", (perLang[l] ?: 0) >= 3)
        assertTrue("FastAPI/ответы: ${perLang["A"]}", (perLang["A"] ?: 0) >= 3)
    }
}
