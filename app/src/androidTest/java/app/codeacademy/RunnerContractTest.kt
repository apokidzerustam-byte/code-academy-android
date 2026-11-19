package app.codeacademy

import android.os.SystemClock
import android.util.Log
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import app.codeacademy.runner.RunResult
import app.codeacademy.runner.RunStatus
import app.codeacademy.runner.RunnerClient
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

/** Общий контракт раннера. Итоги замеров пишутся в logcat с тегом CAPROBE для отчёта CI. */
abstract class RunnerContractTest(private val isolated: Boolean) {

    private val ctx = InstrumentationRegistry.getInstrumentation().targetContext
    private val level = if (isolated) "B" else "A"
    protected lateinit var client: RunnerClient
    protected var info: RunnerInfo? = null

    @Before
    fun setUp(): Unit = runBlocking {
        client = RunnerClient(ctx, isolated)
        val t0 = SystemClock.elapsedRealtime()
        info = client.ping()
        probe("ping", "boundAndPingedMs=${SystemClock.elapsedRealtime() - t0} info=$info")
        assertNotNull("Раннер уровня $level не ответил на ping", info)
        if (isolated) assumeTrue("Python не стартует в isolatedProcess: ${info?.startError?.lineSequence()?.firstOrNull()}", info!!.pythonStarted)
        else assertTrue("Python не стартовал: ${info?.startError}", info!!.pythonStarted)
    }

    @After
    fun tearDown() = client.close()

    protected fun probe(name: String, msg: String) = Log.i("CAPROBE", "level=$level $name: $msg")

    private fun run(code: String, timeoutMs: Long = 5_000, stdin: String = ""): RunResult = runBlocking {
        val t0 = SystemClock.elapsedRealtime()
        client.run(code, timeoutMs, stdin, project = "test").also {
            probe("run", "wall=${SystemClock.elapsedRealtime() - t0}ms status=${it.status} code=${code.lineSequence().first().take(40)}")
        }
    }

    @Test fun isolationFlagMatchesMode() {
        assertEquals(isolated, info!!.isolated)
        if (isolated) assertTrue("isolated UID должен отличаться от UID приложения", info!!.uid != android.os.Process.myUid())
    }

    @Test fun printWorks() {
        val r = run("print(2 + 2)")
        assertEquals(r.stderr, RunStatus.OK, r.status)
        assertEquals("4\n", r.stdout)
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
        val r = run("print('Привет,', input())", stdin = "Аня\n")
        assertEquals("Привет, Аня\n", r.stdout)
    }

    @Test fun asyncioWorks() {
        val r = run("import asyncio\nasync def f():\n    return 7\nprint(asyncio.run(f()))")
        assertEquals(r.stderr, "7\n", r.stdout)
    }

    @Test fun infiniteLoopIsKilledAndRunnerRecovers() {
        val t0 = SystemClock.elapsedRealtime()
        val r = run("while True:\n    pass", timeoutMs = 2_000)
        val elapsed = SystemClock.elapsedRealtime() - t0
        probe("timeout", "elapsed=${elapsed}ms status=${r.status}")
        assertEquals(RunStatus.TIMEOUT, r.status)
        assertTrue("Остановка заняла $elapsed мс", elapsed < 6_000)
        val again = run("print('ok')")
        assertEquals(again.stderr, "ok\n", again.stdout)
    }

    @Test fun stopButtonKillsRun(): Unit = runBlocking {
        val job = async { client.run("while True:\n    pass", 30_000, project = "test") }
        delay(1_000)
        val t0 = SystemClock.elapsedRealtime()
        client.stop()
        val r = job.await()
        probe("stop", "elapsed=${SystemClock.elapsedRealtime() - t0}ms status=${r.status}")
        assertEquals(RunStatus.STOPPED, r.status)
    }

    /** Регрессия: новый клиент сразу после «Стоп» не должен попасть в умирающий процесс. */
    @Test fun newClientRightAfterStopWorks(): Unit = runBlocking {
        val job = async { client.run("while True:\n    pass", 30_000, project = "test") }
        delay(500)
        client.stop()
        assertEquals(RunStatus.STOPPED, job.await().status)
        val fresh = RunnerClient(ctx, isolated)
        try {
            val r = fresh.run("print('fresh')", project = "test")
            assertEquals(r.stderr, "fresh\n", r.stdout)
        } finally {
            fresh.close()
        }
    }

    @Test fun memoryBombDoesNotKillApp() {
        val r = run("x = bytearray(16 * 1024 ** 3)", timeoutMs = 5_000)
        probe("memoryBomb", "status=${r.status} err=${r.stderr.lineSequence().lastOrNull { it.isNotBlank() }}")
        // Главное — приложение живо и следующий запуск работает; сама попытка может закончиться
        // ошибкой, падением процесса исполнителя или таймаутом (на медленном эмуляторе).
        assertTrue(r.status.toString(), r.status in setOf(RunStatus.ERROR, RunStatus.CRASHED, RunStatus.TIMEOUT))
        assertEquals("ok\n", run("print('ok')").stdout)
    }

    @Test fun networkBlocked() {
        val r = run("import urllib.request\nurllib.request.urlopen('http://example.com', timeout=3).read()")
        probe("network", "status=${r.status} err=${r.stderr.lineSequence().lastOrNull { it.isNotBlank() }}")
        assertEquals(RunStatus.ERROR, r.status)
    }

    @Test fun appPrivateFileNotReadable() {
        val secret = File(ctx.filesDir, "secret_progress.txt").apply { writeText("TOP-SECRET") }
        val r = run("print(open(${pyStr(secret.absolutePath)}).read())")
        probe("appFile", "status=${r.status} err=${r.stderr.lineSequence().lastOrNull { it.isNotBlank() }}")
        assertEquals(RunStatus.ERROR, r.status)
        assertFalse(r.stdout.contains("TOP-SECRET"))
    }

    @Test fun javaBridgeBlocked() {
        val r = run("from java import jclass\nprint(jclass('java.lang.System').getProperty('user.name'))")
        assertEquals(RunStatus.ERROR, r.status)
    }

    @Test fun outputCapped() {
        val r = run("print('x' * 200000)")
        assertEquals(r.stderr, RunStatus.OK, r.status)
        assertTrue(r.truncated)
        assertEquals(RunnerClient.MAX_OUTPUT_CHARS, r.stdout.length)
    }

    @Test fun manyPrintLinesCapped() {
        val r = run("for i in range(100000):\n    print(i)")
        assertEquals(r.stderr, RunStatus.OK, r.status)
        assertTrue(r.truncated)
    }

    protected fun pyStr(s: String) = "'" + s.replace("\\", "\\\\").replace("'", "\\'") + "'"
}

@RunWith(AndroidJUnit4::class)
class RunnerLevelATest : RunnerContractTest(isolated = false) {
    @Test fun projectFilesWork() {
        val r = runBlocking {
            client.run("open('data.txt','w').write('42')\nimport os\nprint(open('data.txt').read(), os.listdir('.'))", project = "files")
        }
        assertEquals(r.stderr, "42 ['data.txt']\n", r.stdout)
    }
}

@RunWith(AndroidJUnit4::class)
class RunnerLevelBTest : RunnerContractTest(isolated = true) {
    /** Главный вопрос уровня B: запрещает ли ЯДРО доступ к файлам приложения и сети. */
    @Test fun kernelDeniesAppFilesAndNetwork(): Unit = runBlocking {
        val ctx = InstrumentationRegistry.getInstrumentation().targetContext
        val secret = File(ctx.filesDir, "secret_kernel.txt").apply { writeText("x") }
        val kp = client.ping(secret.absolutePath)?.kernelProbe
        probe("kernel", "$kp")
        assertNotNull(kp)
        assertTrue(kp, kp!!.contains("\"file\": \"DENIED"))
        assertTrue(kp, kp.contains("\"net\": \"DENIED"))
    }
}

/** Для сравнения: в уровне A ядро НЕ защищает — только Python-хуки. Фиксируем это в логе. */
@RunWith(AndroidJUnit4::class)
class RunnerLevelAKernelProbe {
    @Test fun recordKernelBehaviour(): Unit = runBlocking {
        val ctx = InstrumentationRegistry.getInstrumentation().targetContext
        val secret = File(ctx.filesDir, "secret_kernel.txt").apply { writeText("x") }
        val c = RunnerClient(ctx, isolated = false)
        try {
            Log.i("CAPROBE", "level=A kernel: ${c.ping(secret.absolutePath)?.kernelProbe}")
        } finally {
            c.close()
        }
    }
}
