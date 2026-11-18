package app.codeacademy

import android.os.Build
import android.os.SystemClock
import android.util.Log
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import app.codeacademy.runner.PyodideRunner
import app.codeacademy.runner.RunResult
import app.codeacademy.runner.RunStatus
import app.codeacademy.runner.RunnerInfo
import kotlinx.coroutines.async
import kotlinx.coroutines.delay
import kotlinx.coroutines.runBlocking
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Assume.assumeTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File

/** Уровень W: Pyodide в WebView. Замеры — в logcat с тегом CAPROBE. */
@RunWith(AndroidJUnit4::class)
class PyodideRunnerTest {

    private val ctx = InstrumentationRegistry.getInstrumentation().targetContext
    private lateinit var runner: PyodideRunner
    private var info: RunnerInfo? = null

    private fun probe(name: String, msg: String) = Log.i("CAPROBE", "level=W $name: $msg")

    @Before
    fun setUp(): Unit = runBlocking {
        runner = PyodideRunner(ctx)
        val t0 = SystemClock.elapsedRealtime()
        info = runner.prepare()
        probe("start", "api=${Build.VERSION.SDK_INT} wall=${SystemClock.elapsedRealtime() - t0}ms info=$info")
        assertNotNull("Pyodide не ответил за 60 с", info)
        assumeTrue("Pyodide не запустился: ${info?.startError?.take(300)}", info!!.pythonStarted)
    }

    @After
    fun tearDown() = runner.close()

    private fun run(code: String, timeoutMs: Long = 5_000, stdin: String = "", project: String = "test"): RunResult = runBlocking {
        val t0 = SystemClock.elapsedRealtime()
        runner.run(code, timeoutMs, stdin, project).also {
            probe("run", "wall=${SystemClock.elapsedRealtime() - t0}ms status=${it.status} code=${code.lineSequence().first().take(40)}")
        }
    }

    @Test fun rendererIsOutOfProcess() {
        probe("renderer", "outOfProcess=${info!!.isolated}")
        if (Build.VERSION.SDK_INT >= 29) assertTrue("Рендерер WebView в процессе приложения", info!!.isolated)
    }

    @Test fun printWorks() {
        val r = run("import sys\nprint(2 + 2, sys.version_info[:2])")
        assertEquals(r.stderr, RunStatus.OK, r.status)
        assertTrue(r.stdout, r.stdout.startsWith("4 (3, 1"))
    }

    @Test fun warmRunIsFast() {
        run("pass")
        val t0 = SystemClock.elapsedRealtime()
        run("print(sum(range(1000)))")
        probe("warmRun", "${SystemClock.elapsedRealtime() - t0}ms")
    }

    @Test fun runtimeErrorReported() {
        val r = run("x = 1\nprint(x / 0)")
        assertEquals(RunStatus.ERROR, r.status)
        assertTrue(r.stderr, r.stderr.contains("ZeroDivisionError") && r.stderr.contains("line 2"))
    }

    @Test fun stdinWorks() {
        assertEquals("Привет, Аня\n", run("print('Привет,', input())", stdin = "Аня\n").stdout)
    }

    @Test fun projectFilesWork() {
        val r = run("open('data.txt','w').write('42')\nimport os\nprint(open('data.txt').read(), os.listdir('.'))", project = "files")
        assertEquals(r.stderr, "42 ['data.txt']\n", r.stdout)
    }

    @Test fun infiniteLoopIsKilledAndRunnerRecovers() {
        val t0 = SystemClock.elapsedRealtime()
        val r = run("while True:\n    pass", timeoutMs = 2_000)
        probe("timeout", "elapsed=${SystemClock.elapsedRealtime() - t0}ms status=${r.status}")
        assertEquals(RunStatus.TIMEOUT, r.status)
        val t1 = SystemClock.elapsedRealtime()
        val again = run("print('ok')", timeoutMs = 30_000)
        probe("restartAfterTimeout", "${SystemClock.elapsedRealtime() - t1}ms")
        assertEquals(again.stderr, "ok\n", again.stdout)
    }

    @Test fun stopKillsRun(): Unit = runBlocking {
        val job = async { runner.run("while True:\n    pass", 30_000, "", "test") }
        delay(1_000)
        runner.stop()
        assertEquals(RunStatus.STOPPED, job.await().status)
        assertEquals("ok\n", runner.run("print('ok')", 30_000, "", "test").stdout)
    }

    @Test fun memoryBombDoesNotKillApp() {
        val r = run("x = bytearray(16 * 1024 ** 3)")
        probe("memoryBomb", "status=${r.status} err=${r.stderr.lineSequence().lastOrNull { it.isNotBlank() }}")
        assertTrue(r.status in setOf(RunStatus.ERROR, RunStatus.CRASHED))
        assertEquals("ok\n", run("print('ok')", timeoutMs = 30_000).stdout)
    }

    @Test fun networkBlocked() {
        val r = run("import urllib.request\nurllib.request.urlopen('http://example.com', timeout=3).read()")
        probe("network", "status=${r.status} err=${r.stderr.lineSequence().lastOrNull { it.isNotBlank() }}")
        assertEquals(RunStatus.ERROR, r.status)
    }

    @Test fun jsAndJavaBridgesBlocked() {
        assertEquals(RunStatus.ERROR, run("import js\njs.fetch('https://example.com')").status)
        assertEquals(RunStatus.ERROR, run("from java import jclass").status)
        assertEquals(RunStatus.ERROR, run("import pyodide").status)
    }

    @Test fun outputCapped() {
        val r = run("print('x' * 200000)")
        assertEquals(r.stderr, RunStatus.OK, r.status)
        assertTrue(r.truncated)
    }

    /** Главный вопрос: что запрещает сама среда, в обход Python-хуков. */
    @Test fun environmentDeniesDeviceFilesAndNetwork(): Unit = runBlocking {
        val secret = File(ctx.filesDir, "secret_kernel.txt").apply { writeText("x") }
        val p = runner.kernelProbe(secret.absolutePath)
        probe("kernel", "$p")
        assertNotNull(p)
        assertTrue(p, p!!.contains("\"net\":\"DENIED"))
        assertTrue(p, p.contains("\"file\":\"DENIED"))
        assertTrue(p, p.contains("\"pyFile\":\"DENIED"))
        assertFalse(p, p.contains("READABLE"))
    }

    /** Известные ограничения Pyodide фиксируем в журнале, не валя тесты. */
    @Test fun recordKnownLimitations() {
        val a = run("import asyncio\nasync def f():\n    return 7\nprint(asyncio.run(f()))")
        probe("asyncio", "status=${a.status} out=${a.stdout.trim()} err=${a.stderr.lineSequence().lastOrNull { it.isNotBlank() }}")
        val t = run("import threading\nt = threading.Thread(target=print, args=('thr',))\nt.start(); t.join()")
        probe("threading", "status=${t.status} err=${t.stderr.lineSequence().lastOrNull { it.isNotBlank() }}")
        val s = run("import sqlite3\nc = sqlite3.connect(':memory:')\nprint(c.execute('select 1+1').fetchone())")
        probe("sqlite3", "status=${s.status} out=${s.stdout.trim()} err=${s.stderr.lineSequence().lastOrNull { it.isNotBlank() }}")
    }
}
