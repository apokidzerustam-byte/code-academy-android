package app.codeacademy

import app.codeacademy.data.ProjectRepository
import app.codeacademy.ui.assignmentRunner
import app.codeacademy.ui.runTarget
import app.codeacademy.ui.writeProjectZip
import app.codeacademy.ui.zipName
import app.codeacademy.content.Assignment
import kotlinx.serialization.json.Json
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.ByteArrayInputStream
import java.io.ByteArrayOutputStream
import java.io.File
import java.util.zip.ZipInputStream

class ProjectTemplatesTest {
    @Test fun everyTemplateHasRunnableEntry() {
        for ((name, files) in ProjectRepository.TEMPLATES) {
            val first = files.keys.first()
            assertTrue("$name: нет файла для запуска", runTarget(files.keys, first) != null)
        }
    }

    /** Шаблон Kotlin складывается в build/kotlin-template: CI выполняет его сценарий Actions по-настоящему. */
    @Test fun kotlinTemplateForActions() {
        val files = ProjectRepository.TEMPLATES.getValue("kotlin")
        val wf = files.getValue(".github/workflows/kotlin.yml")
        assertTrue(wf.contains("kotlinc") && wf.contains("java -jar app.jar"))
        assertTrue(files.getValue("README.md").contains(".github/workflows/kotlin.yml"))
        val out = File("build/kotlin-template")
        out.deleteRecursively()
        for ((path, text) in files) File(out, path).apply { parentFile?.mkdirs() }.writeText(text)
    }

    @Test fun zipContainsProjectFilesOnly() {
        val files = mapOf("Main.kt" to "fun main() {}\n", ".github/workflows/kotlin.yml" to "name: K\n",
            ProjectRepository.META to "мета", "data/.keep" to "", "Привет.txt" to "текст")
        val bytes = ByteArrayOutputStream().also { writeProjectZip(files, it) }.toByteArray()
        val names = mutableMapOf<String, String>()
        ZipInputStream(ByteArrayInputStream(bytes)).use { z ->
            while (true) {
                val e = z.nextEntry ?: break
                names[e.name] = z.readBytes().toString(Charsets.UTF_8)
            }
        }
        assertEquals(setOf("Main.kt", ".github/workflows/kotlin.yml", "Привет.txt"), names.keys)
        assertEquals("текст", names["Привет.txt"])
        assertEquals("мой-проект.zip", zipName("  Мой проект! "))
        assertEquals("project.zip", zipName("***"))
    }

    @Test fun webAssignmentUsesItsOwnLanguage() {
        val json = Json { ignoreUnknownKeys = true }
        fun asg(tests: String) = json.decodeFromString(Assignment.serializer(), """
            {"id":"a","type":"write","title":"t","statement":"s","goal":"g","input":"i","expectedResult":"e","constraints":[],
             "hints":["1","2","3","4","5"],"tests":$tests,"solution":"x","explanation":"x","criteria":[]}""")
        assertEquals("html", assignmentRunner(asg("""{"kind":"web","lang":"html","cases":[]}"""), "js"))
        assertEquals("js", assignmentRunner(asg("""{"kind":"web","lang":"js","cases":[]}"""), "js"))
        assertEquals("html", assignmentRunner(asg("""{"kind":"web","cases":[]}"""), "js"))
        assertEquals("sql", assignmentRunner(asg("""{"kind":"sql","cases":[]}"""), "sql"))
        assertEquals("A", assignmentRunner(asg("""{"kind":"fastapi","cases":[]}"""), "A"))
    }
}
