package app.codeacademy

import app.codeacademy.content.Assignment
import app.codeacademy.content.Lesson
import app.codeacademy.content.PackManifest
import app.codeacademy.content.Scenario
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonPrimitive
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File

/** Все контент-пакеты репозитория читаются моделями приложения (то же, что увидит устройство). */
class ContentParsingTest {
    private val json = Json { ignoreUnknownKeys = true }
    private val packsDir = File("../content/packs")

    @Test fun allPacksParse() {
        val packs = packsDir.listFiles { f -> File(f, "pack.json").exists() }.orEmpty()
        assertTrue("нет пакетов в ${packsDir.absolutePath}", packs.isNotEmpty())
        for (p in packs) {
            val pack = json.decodeFromString(PackManifest.serializer(), File(p, "pack.json").readText())
            for (lid in pack.lessons) {
                val dir = File(p, "lessons/$lid")
                val lesson = json.decodeFromString(Lesson.serializer(), File(dir, "lesson.json").readText())
                assertEquals(lid, lesson.id)
                val scen = json.decodeFromString(Scenario.serializer(), File(dir, lesson.scenario).readText())
                assertTrue(scen.scenes.isNotEmpty())
                assertTrue(File(dir, lesson.notes).readText().isNotBlank())
                lesson.assignments.forEach {
                    val a = json.decodeFromString(Assignment.serializer(), File(dir, it).readText())
                    assertEquals(5, a.hints.size)
                    val kind = a.tests["kind"]!!.jsonPrimitive.content
                    assertTrue(kind in setOf("stdout", "function", "answer", "fastapi", "web", "sql", "kotlin"))
                    assertEquals(kind == "answer", a.isAnswerTask)
                }
            }
        }
    }
}
