package app.codeacademy

import android.util.Log
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import app.codeacademy.data.AppDatabase
import app.codeacademy.data.AttemptEntity
import app.codeacademy.data.BackupException
import app.codeacademy.data.BackupFormat
import app.codeacademy.data.BackupManager
import app.codeacademy.data.DailyActivityEntity
import app.codeacademy.data.DraftEntity
import app.codeacademy.data.LessonProgressEntity
import app.codeacademy.data.ProjectFileEntity
import app.codeacademy.data.ProjectRepository
import app.codeacademy.data.ReviewItemEntity
import app.codeacademy.data.SkillStateEntity
import java.io.ByteArrayInputStream
import java.io.ByteArrayOutputStream
import java.io.File
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.runBlocking
import org.junit.After
import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Assert.fail
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith

/** Тестовые данные для резервной копии: все таблицы, юникод, пустые значения, большой текст, «дыры» в id. */
object BackupFixture {
    val tricky = "Привет, мир! 🐍 «кавычки» \"двойные\" 'одинарные' \\ \t табуляция\nвторая строка\r\nCRLF ∑ 中文"

    suspend fun fill(db: AppDatabase) {
        db.progress().upsert(LessonProgressEntity("python-basics/py-01-print", "PASSED", 7, 123_456, 1_700_000_000_000, 1_700_000_100_000, 98_765, 1_700_000_100_001))
        db.progress().upsert(LessonProgressEntity("python-basics/py-02-variables", "IN_PROGRESS", 2, 0, null, null, 0, 5))
        val big = buildString { repeat(20_000) { append("print('строка $it')\n") } } // ≈ 400 КБ
        val ids = listOf(
            AttemptEntity(lessonKey = "python-basics/py-01-print", assignmentId = "a1", startedAt = 1, durationMs = 2, code = tricky,
                passed = true, testsPassed = 3, testsTotal = 3, hintsUsed = 0, errorType = null, runner = "W"),
            AttemptEntity(lessonKey = "python-basics/py-01-print", assignmentId = "a2", startedAt = 3, durationMs = 4, code = "x",
                passed = false, testsPassed = 0, testsTotal = 2, hintsUsed = 6, errorType = "NameError", runner = "A"),
            AttemptEntity(lessonKey = "project:python-basics/finance", assignmentId = "calculator", startedAt = Long.MAX_VALUE,
                durationMs = Long.MIN_VALUE, code = big, passed = true, testsPassed = 7, testsTotal = 7, hintsUsed = 1, errorType = null, runner = "W"),
        ).map { db.attempts().insert(it) }
        // «Дыра» в нумерации: удалённая попытка — после восстановления следующая получит тот же id, что и до.
        db.openHelper.writableDatabase.execSQL("DELETE FROM attempt WHERE id = ${ids[1]}")
        db.skills().upsert(SkillStateEntity("python.print", "MASTERED", 5, 4, 2, 20_000, 20_001, 1_700_000_000_000))
        db.skills().upsert(SkillStateEntity("python.if"))
        db.reviews().upsert(ReviewItemEntity("python.print", 2, 7, 20_007, "OK"))
        db.reviews().upsert(ReviewItemEntity("python.if", 0, 1, -1, null))
        db.activity().upsert(DailyActivityEntity(20_000, 3_600_000, 5, 2))
        db.drafts().upsert(DraftEntity("python-basics/py-02-variables/a1", tricky, 3, 9))
        db.projects().upsert(ProjectFileEntity("p1", ProjectRepository.META, "Мой «проект» 1", 10))
        db.projects().upsert(ProjectFileEntity("p1", ProjectRepository.COURSE, "python-basics/finance", 10))
        db.projects().upsert(ProjectFileEntity("p1", "main.py", tricky, 11))
        db.projects().upsert(ProjectFileEntity("p1", "data/notes.txt", "", 12))
        db.projects().upsert(ProjectFileEntity("p2", ProjectRepository.META, "Мой «проект» 1", 13)) // то же название
        db.projects().upsert(ProjectFileEntity("p2", "index.html", "<h1>Привет</h1>", 14))
    }

    val settings: Map<String, Any> = mapOf(
        "theme" to "DARK", "text_scale" to 1.25f, "plain_editor" to true, "session_minutes" to 90, "days_per_week" to 3,
        "a_long" to Long.MIN_VALUE, "a_double" to 0.1 + 0.2, "a_set" to setOf("б", "а", tricky), "empty" to "",
    )
}

class MemorySettings(var values: Map<String, Any> = emptyMap()) : BackupManager.SettingsStore {
    override suspend fun snapshot() = values
    override suspend fun replaceAll(values: Map<String, Any>) { this.values = values.toMap() }
    override suspend fun clearAll() { values = emptyMap() }
}

@RunWith(AndroidJUnit4::class)
class BackupOnDeviceTest {
    private val ctx = InstrumentationRegistry.getInstrumentation().targetContext
    private val name = "backup-test.db"
    private lateinit var db: AppDatabase
    private lateinit var settings: MemorySettings
    private lateinit var backup: BackupManager

    @Before fun setUp() {
        ctx.deleteDatabase(name)
        db = AppDatabase.create(ctx, name)
        settings = MemorySettings()
        backup = BackupManager(db, settings, "test", clock = { 1_763_800_000_000 })
    }

    @After fun tearDown() {
        db.close()
        ctx.deleteDatabase(name)
    }

    private fun export(): ByteArray = ByteArrayOutputStream().also { runBlocking { backup.export(it) } }.toByteArray()

    private suspend fun dump() = backup.dumpDatabase() + byteArrayOf(0) + backup.dumpSettings()

    private suspend fun rowCount(): Int =
        listOf("lesson_progress", "attempt", "skill_state", "review_item", "daily_activity", "project_file", "draft").sumOf { t ->
            db.openHelper.readableDatabase.query("SELECT COUNT(*) FROM $t").use { it.moveToFirst(); it.getInt(0) }
        }

    @Test fun exportWipeImportIsByteIdentical() = runBlocking<Unit> {
        BackupFixture.fill(db)
        settings.values = BackupFixture.settings
        val before = dump()
        val zipA = export()
        val nextIdBefore = db.openHelper.readableDatabase.query("SELECT seq FROM sqlite_sequence WHERE name = 'attempt'").use { it.moveToFirst(); it.getLong(0) } + 1

        backup.wipe()
        assertEquals("после удаления в таблицах остались строки", 0, rowCount())
        assertTrue(settings.values.isEmpty())
        assertFalse(before.contentEquals(dump()))

        val sum = backup.restore(ByteArrayInputStream(zipA))
        assertEquals(2, sum.projects)
        assertEquals(2, sum.attempts)
        assertArrayEquals("данные после восстановления отличаются", before, dump())
        assertEquals(BackupFixture.settings, settings.values)

        // Повторный экспорт — те же байты файлов данных.
        val a = BackupFormat.readZip(ByteArrayInputStream(zipA))
        val b = BackupFormat.readZip(ByteArrayInputStream(export()))
        for (entry in listOf(BackupFormat.DB, BackupFormat.SETTINGS)) assertArrayEquals(entry, a.getValue(entry), b.getValue(entry))
        assertEquals(a.keys, b.keys)
        // Копии проектов для чтения на компьютере: одинаковые названия разведены по папкам.
        assertTrue(a.keys.toString(), "projects/Мой _проект_ 1/main.py" in a && "projects/Мой _проект_ 1 (2)/index.html" in a)
        assertFalse(a.keys.any { it.endsWith(ProjectRepository.META) || it.endsWith(ProjectRepository.COURSE) })

        // Автонумерация продолжается как до копии; Room-наблюдатели видят восстановленные данные.
        val newId = db.attempts().insert(AttemptEntity(lessonKey = "x", assignmentId = "y", startedAt = 0, durationMs = 0, code = "",
            passed = false, testsPassed = 0, testsTotal = 0, hintsUsed = 0, errorType = null, runner = "W"))
        assertEquals(nextIdBefore, newId)
        assertEquals(2, db.progress().all().first().size)
        Log.i("CAPROBE", "backup: ${zipA.size} байт, данные совпали байт в байт (${before.size} байт дампа)")
    }

    @Test fun damagedOrForeignBackupChangesNothing() = runBlocking<Unit> {
        BackupFixture.fill(db)
        settings.values = BackupFixture.settings
        val zip = export()
        val before = dump()

        fun rezip(change: (MutableMap<String, ByteArray>) -> Unit): ByteArray {
            val e = BackupFormat.readZip(ByteArrayInputStream(zip)).toMutableMap()
            change(e)
            return ByteArrayOutputStream().also { BackupFormat.writeZip(it, e.toList(), 0) }.toByteArray()
        }
        val tampered = rezip { e ->
            val d = e.getValue(BackupFormat.DB).copyOf()
            d[d.size / 2] = (d[d.size / 2] + 1).toByte()
            e[BackupFormat.DB] = d
        }
        val newer = rezip { e ->
            e[BackupFormat.MANIFEST] = e.getValue(BackupFormat.MANIFEST).toString(Charsets.UTF_8)
                .replace("\"formatVersion\":1", "\"formatVersion\":99").toByteArray()
        }
        val noManifest = rezip { it.remove(BackupFormat.MANIFEST) }
        val badRowButValidSum = rezip { e ->
            // Строка не той длины, контрольная сумма пересчитана: ошибка обнаружится внутри транзакции → откат.
            val text = e.getValue(BackupFormat.DB).toString(Charsets.UTF_8).replaceFirst("\"rows\":[[", "\"rows\":[[1,")
            val bytes = text.toByteArray()
            e[BackupFormat.DB] = bytes
            val m = e.getValue(BackupFormat.MANIFEST).toString(Charsets.UTF_8)
            val old = Regex("\"data/database.json\":\\{\"sha256\":\"([0-9a-f]+)\",\"size\":(\\d+)\\}").find(m)!!
            e[BackupFormat.MANIFEST] = m.replace(old.value,
                "\"data/database.json\":{\"sha256\":\"${BackupFormat.sha256(bytes)}\",\"size\":${bytes.size}}").toByteArray()
        }
        for ((label, bytes) in listOf("повреждённая" to tampered, "новее" to newer, "без манифеста" to noManifest,
            "битая строка" to badRowButValidSum, "не ZIP" to "просто текст".toByteArray())) {
            try {
                backup.restore(ByteArrayInputStream(bytes))
                fail("$label: восстановление должно отказать")
            } catch (e: BackupException) {
                Log.i("CAPROBE", "backup $label: ${e.message}")
            }
            assertArrayEquals("$label: данные изменились", before, dump())
        }
    }

    @Test fun projectsBackupRestoresCourseLink() = runBlocking<Unit> {
        val repo = ProjectRepository(db)
        val id = repo.startCourse("python-basics/finance", "Мои задачи и финансы", mapOf("main.py" to "print(1)\n"))
        assertEquals(id, repo.startCourse("python-basics/finance", "другое", emptyMap()))
        val zip = export()
        backup.wipe()
        assertTrue(repo.projects.first().isEmpty())
        backup.restore(ByteArrayInputStream(zip))
        val p = repo.projects.first().single()
        assertEquals("python-basics/finance", p.course)
        assertEquals(mapOf("main.py" to "print(1)\n"), repo.files(id))
    }
}

/**
 * Две фазы вокруг настоящего `pm clear` (скрипт ci/backup-clear-test.sh). В обычном прогоне тестов пропускается.
 * Работает с НАСТОЯЩИМИ базой и настройками приложения.
 */
@RunWith(AndroidJUnit4::class)
class BackupClearDataTest {
    private val ctx = InstrumentationRegistry.getInstrumentation().targetContext
    private val phase = InstrumentationRegistry.getArguments().getString("backupPhase")
    private val zipFile = File(ctx.filesDir, "ci-backup.zip")
    private val dumpFile = File(ctx.filesDir, "ci-dump.bin")

    @Test fun phase() = runBlocking<Unit> {
        org.junit.Assume.assumeTrue("только из ci/backup-clear-test.sh", phase != null)
        val c = (ctx.applicationContext as CodeAcademyApp).container
        suspend fun dump() = c.backup.dumpDatabase() + byteArrayOf(0) + c.backup.dumpSettings()
        when (phase) {
            "1" -> {
                c.backup.wipe()
                BackupFixture.fill(c.db)
                c.settings.replaceAll(BackupFixture.settings)
                zipFile.outputStream().use { c.backup.export(it) }
                dumpFile.writeBytes(dump())
                Log.i("CAPROBE", "backup phase 1: копия ${zipFile.length()} байт, дамп ${dumpFile.length()} байт")
            }
            "2" -> {
                val empty = c.backup.dumpDatabase().toString(Charsets.UTF_8)
                assertFalse("после pm clear данные остались", empty.contains("python-basics/py-01-print"))
                assertTrue("после pm clear настройки остались", c.settings.snapshot().isEmpty())
                val sum = zipFile.inputStream().use { c.backup.restore(it) }
                assertArrayEquals("после pm clear и восстановления данные отличаются", dumpFile.readBytes(), dump())
                Log.i("CAPROBE", "backup phase 2: восстановлено ${sum.tables}, совпало байт в байт")
            }
            else -> fail("неизвестная фаза $phase")
        }
    }
}
