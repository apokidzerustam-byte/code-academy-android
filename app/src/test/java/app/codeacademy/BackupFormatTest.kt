package app.codeacademy

import app.codeacademy.content.CourseProject
import app.codeacademy.data.BackupException
import app.codeacademy.data.BackupFormat
import app.codeacademy.data.ProjectRepository
import app.codeacademy.data.ProjectZip
import app.codeacademy.data.ProjectZipException
import app.codeacademy.ui.currentMilestone
import app.codeacademy.ui.writeProjectZip
import kotlinx.serialization.json.Json
import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.ByteArrayInputStream
import java.io.ByteArrayOutputStream
import java.io.File
import java.util.zip.ZipEntry
import java.util.zip.ZipOutputStream

class BackupFormatTest {
    private val values: Map<String, Any> = mapOf(
        "b" to true, "i" to Int.MIN_VALUE, "l" to Long.MAX_VALUE, "f" to 0.1f, "d" to 0.1 + 0.2,
        "s" to "строка «с» \"кавычками\"\n🐍", "set" to setOf("в", "а", "б"), "empty" to "",
    )

    @Test fun settingsRoundTripAllTypes() {
        val bytes = BackupFormat.encodeSettings(values)
        assertEquals(values, BackupFormat.decodeSettings(bytes))
        // Детерминированно: порядок ключей и элементов набора не влияет на байты.
        assertArrayEquals(bytes, BackupFormat.encodeSettings(values.toList().reversed().toMap()))
    }

    @Test fun damagedSettingsRejected() {
        assertThrows(BackupException::class.java) { BackupFormat.decodeSettings("{\"x\":{\"type\":\"int\",\"value\":\"abc\"}}".toByteArray()) }
        assertThrows(BackupException::class.java) { BackupFormat.decodeSettings("не json".toByteArray()) }
    }

    private fun manifest(db: ByteArray, set: ByteArray, formatVersion: Int = 1, dbVersion: Int = 1) =
        """{"format":"code-academy-backup","formatVersion":$formatVersion,"dbVersion":$dbVersion,"entries":{""" +
            """"data/database.json":{"sha256":"${BackupFormat.sha256(db)}","size":${db.size}},""" +
            """"data/settings.json":{"sha256":"${BackupFormat.sha256(set)}","size":${set.size}}}}"""

    @Test fun verifyChecksManifestAndSums() {
        val db = "{\"tables\":[]}".toByteArray()
        val set = "{}".toByteArray()
        val ok = mapOf(BackupFormat.MANIFEST to manifest(db, set).toByteArray(), BackupFormat.DB to db, BackupFormat.SETTINGS to set)
        BackupFormat.verify(ok, 1)
        fun bad(e: Map<String, ByteArray>, word: String) {
            val ex = assertThrows(BackupException::class.java) { BackupFormat.verify(e, 1) }
            assertTrue(ex.message, ex.message!!.contains(word))
        }
        bad(ok - BackupFormat.MANIFEST, "manifest")
        bad(ok + (BackupFormat.DB to "{\"tables\":[1]}".toByteArray()), "контрольная сумма")
        bad(ok + (BackupFormat.MANIFEST to manifest(db, set, formatVersion = 2).toByteArray()), "обновите")
        bad(ok + (BackupFormat.MANIFEST to manifest(db, set, dbVersion = 5).toByteArray()), "обновите")
        bad(ok + (BackupFormat.MANIFEST to "{\"format\":\"zip\"}".toByteArray()), "не резервная копия")
        bad(ok - BackupFormat.SETTINGS, "settings")
    }

    @Test fun zipIsDeterministicAndRoundTrips() {
        val entries = listOf("a.txt" to "один".toByteArray(), "dir/b.bin" to ByteArray(300) { it.toByte() })
        val one = ByteArrayOutputStream().also { BackupFormat.writeZip(it, entries, 1_700_000_000_000) }.toByteArray()
        val two = ByteArrayOutputStream().also { BackupFormat.writeZip(it, entries, 1_700_000_000_000) }.toByteArray()
        assertArrayEquals(one, two)
        val back = BackupFormat.readZip(ByteArrayInputStream(one))
        assertEquals(entries.map { it.first }, back.keys.toList())
        entries.forEach { (n, b) -> assertArrayEquals(b, back.getValue(n)) }
        assertThrows(BackupException::class.java) { BackupFormat.readZip(ByteArrayInputStream("не zip".toByteArray())) }
    }
}

class ProjectZipTest {
    private fun zip(vararg entries: Pair<String, ByteArray>): ByteArray = ByteArrayOutputStream().also { o ->
        ZipOutputStream(o).use { z -> for ((n, b) in entries) { z.putNextEntry(ZipEntry(n)); z.write(b); z.closeEntry() } }
    }.toByteArray()

    @Test fun exportImportRoundTrip() {
        val files = mapOf("main.py" to "print('привет')\n", "data/notes.txt" to "", ".github/workflows/k.yml" to "name: K\n")
        val bytes = ByteArrayOutputStream().also { writeProjectZip(files + (ProjectRepository.COURSE to "a/b"), it) }.toByteArray()
        assertEquals(files, ProjectZip.read(ByteArrayInputStream(bytes)))
    }

    @Test fun githubStyleTopFolderStripped() {
        val r = ProjectZip.read(ByteArrayInputStream(zip("repo-main/main.py" to "x".toByteArray(), "repo-main/lib/u.py" to "y".toByteArray(),
            "__MACOSX/repo-main/._main.py" to byteArrayOf(0, 1))))
        assertEquals(setOf("main.py", "lib/u.py"), r.keys)
        assertEquals("", ProjectZip.commonTopFolder(listOf("a/x", "b/y")))
        assertEquals("", ProjectZip.commonTopFolder(listOf("a/x", "a")))
    }

    @Test fun unsafeOrBinaryRejected() {
        assertThrows(ProjectZipException::class.java) { ProjectZip.read(ByteArrayInputStream(zip("../evil.py" to "x".toByteArray(), "ok.py" to "y".toByteArray()))) }
        assertThrows(ProjectZipException::class.java) { ProjectZip.read(ByteArrayInputStream(zip("img.png" to byteArrayOf(-1, -40, 0, 1)))) }
        assertThrows(ProjectZipException::class.java) { ProjectZip.read(ByteArrayInputStream(zip("big.txt" to ByteArray(300 * 1024) { 'a'.code.toByte() }))) }
        assertThrows(ProjectZipException::class.java) { ProjectZip.read(ByteArrayInputStream(zip())) }
        assertThrows(ProjectZipException::class.java) { ProjectZip.read(ByteArrayInputStream(zip("a" to "1".toByteArray(), "a/b" to "2".toByteArray()))) }
    }

    @Test fun currentMilestoneIsFirstNotPassed() {
        val json = Json { ignoreUnknownKeys = true }
        val p = json.decodeFromString(CourseProject.serializer(), File("../content/packs/python-basics/projects/finance/project.json").readText())
        assertEquals(0, currentMilestone(p, emptySet()))
        assertEquals(1, currentMilestone(p, setOf("calculator")))
        assertNull(currentMilestone(p, setOf("calculator", "expenses")))
        assertTrue(p.isThrough)
    }
}
