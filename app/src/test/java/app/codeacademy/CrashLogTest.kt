package app.codeacademy

import app.codeacademy.mentor.CpuTopology
import app.codeacademy.mentor.PerfMode
import app.codeacademy.mentor.PerfPolicy
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File
import java.nio.file.Files

/** Журнал сбоев и режимы производительности: чистая логика без Android. */
class CrashLogTest {
    private fun tmp(): File = Files.createTempDirectory("crashlog").toFile().resolve("logs/crash.log")

    @Test fun entryHasTimeVersionDeviceProcessAndStack() {
        val e = CrashLog.entry(":mentor", "main", IllegalStateException("нет памяти"), "0.10.0-mvp.7", "ZTE NX729J, Android 14 (API 34)", 1_763_800_000_000)
        assertTrue(e.startsWith("2025-11-22T"))
        assertTrue(e.contains("0.10.0-mvp.7") && e.contains("ZTE NX729J") && e.contains("процесс: :mentor, поток: main"))
        assertTrue(e.contains("IllegalStateException: нет памяти") && e.contains("CrashLogTest"))
    }

    @Test fun appendKeepsEntriesInOrderAndCountsThem() {
        val f = tmp()
        assertEquals("", CrashLog.read(f))
        assertEquals(0, CrashLog.count(CrashLog.read(f)))
        CrashLog.append(f, "первая")
        CrashLog.append(f, "вторая")
        val text = CrashLog.read(f)
        assertTrue(text.indexOf("первая") < text.indexOf("вторая"))
        assertEquals(2, CrashLog.count(text))
        CrashLog.clear(f)
        assertEquals("", CrashLog.read(f))
        assertFalse(f.exists())
    }

    @Test fun oldEntriesAreDroppedWholeWhenTheLogIsTooBig() {
        val f = tmp()
        val big = "x".repeat(20_000)
        for (i in 1..5) CrashLog.append(f, "запись $i\n$big")
        val text = CrashLog.read(f)
        assertTrue("размер ${text.length}", text.length <= CrashLog.MAX_CHARS)
        assertTrue(text.contains("запись 5"))
        assertFalse("самая старая запись должна уйти целиком", text.contains("запись 1"))
        // Каждая оставшаяся запись целая: начинается со своей метки.
        assertTrue(text.startsWith("запись "))
    }

    @Test fun writeFailureNeverThrows() {
        // Родитель — обычный файл: каталог создать нельзя. Журнал не должен ронять приложение ещё раз.
        val dir = Files.createTempDirectory("crashlog-bad").toFile()
        val blocker = File(dir, "logs").also { it.writeText("не каталог") }
        CrashLog.append(File(blocker, "crash.log"), "запись")
        assertEquals("", CrashLog.read(File(blocker, "crash.log")))
    }

    @Test fun performanceModesDifferInTheDocumentedWay() {
        val eco = PerfPolicy.of(PerfMode.ECONOMY)
        val std = PerfPolicy.of(PerfMode.STANDARD)
        val ext = PerfPolicy.of(PerfMode.EXTENDED)
        // Экономичный: меньше потоков, быстрее выгружает, не грузит заранее, короче отвечает.
        assertTrue(eco.maxGenerationThreads < std.maxGenerationThreads && eco.idleUnloadMs < std.idleUnloadMs)
        assertFalse(eco.preload)
        assertTrue(std.preload && ext.preload)
        assertTrue(eco.answerLengthPercent < std.answerLengthPercent && std.answerLengthPercent < ext.answerLengthPercent)
        assertTrue(std.idleUnloadMs < ext.idleUnloadMs)
        // Стандартный совпадает с поведением до появления режимов: 4/6 потоков, 10 минут, длина без изменений.
        assertEquals(PerfPolicy(4, 6, 600_000L, true, 100), std)
        assertEquals(260, std.maxTokens(260))
        assertEquals(182, eco.maxTokens(260))
        assertEquals(338, ext.maxTokens(260))
        assertEquals(40, eco.maxTokens(20))
    }

    @Test fun economyModeCapsThreadsButNeverRaisesThem() {
        val gen2 = CpuTopology.threads(8, listOf(2016000L, 2016000, 2016000, 2803200, 2803200, 2803200, 2803200, 3360000))
        assertEquals(CpuTopology.Threads(4, 5, 5, 8), gen2)
        val eco = PerfPolicy.of(PerfMode.ECONOMY).threads(gen2)
        assertEquals(2, eco.generation)
        assertEquals(3, eco.prompt)
        // Слабый телефон с двумя быстрыми ядрами: режим не поднимает потоки выше подобранных.
        val weak = CpuTopology.Threads(2, 2, 2, 6)
        assertEquals(weak, PerfPolicy.of(PerfMode.EXTENDED).threads(weak))
        assertEquals(weak, PerfPolicy.of(PerfMode.ECONOMY).threads(weak).copy(prompt = 2))
    }

    @Test fun unknownModeNameMeansStandard() {
        assertEquals(PerfMode.STANDARD, PerfPolicy.parse(null))
        assertEquals(PerfMode.STANDARD, PerfPolicy.parse("TURBO"))
        assertEquals(PerfMode.ECONOMY, PerfPolicy.parse("ECONOMY"))
        for (m in PerfMode.values()) assertEquals(m, PerfPolicy.parse(m.name))
    }
}
