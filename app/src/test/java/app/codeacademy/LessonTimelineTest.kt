package app.codeacademy

import app.codeacademy.content.Scenario
import app.codeacademy.content.Scene
import app.codeacademy.content.SceneAction
import app.codeacademy.lesson.Cue
import app.codeacademy.lesson.LessonTimeline
import app.codeacademy.lesson.NarrationMeta
import app.codeacademy.lesson.SceneAudio
import kotlinx.serialization.json.Json
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File

class LessonTimelineTest {
    private fun act(type: String, text: String? = null, lines: List<Int> = emptyList(), md: String? = null,
                    stream: String = "stdout", cue: Int? = null) =
        SceneAction(type = type, text = text, lines = lines, md = md, stream = stream, cue = cue)

    private val scenario = Scenario(scenes = listOf(
        Scene("a", "Первая", "Пишем код. Запускаем его.", actions = listOf(
            act("type", "print(1)\n"), act("highlight", lines = listOf(1)), act("run"), act("output", "1\n"),
        )),
        Scene("b", "Вторая", "Ошибка! Смотрим сообщение.", actions = listOf(
            act("clear"), act("type", "print(\n"), act("run"),
            act("output", "SyntaxError\n", stream = "stderr", cue = 1), act("note", md = "**Важно**"),
        )),
    ))

    @Test fun phrasesMatchPythonRules() {
        assertEquals(listOf("Привет!", "Как дела?", "Хорошо…", "Пока."), LessonTimeline.splitPhrases("Привет! Как дела? Хорошо… Пока."))
        val long = "Слово, ".repeat(60) + "конец."
        val parts = LessonTimeline.splitPhrases(long)
        assertTrue(parts.all { it.length <= 220 })
        assertEquals(long.trim(), parts.joinToString(" "))
    }

    @Test fun withoutAudioUsesEstimatedTimingAndShowsCaptions() {
        val tl = LessonTimeline(scenario)
        assertFalse(tl.hasAudio)
        assertEquals(2, tl.scenes.size)
        assertEquals(tl.scenes[0].endMs, tl.scenes[1].startMs)
        assertEquals(tl.totalMs, tl.scenes[1].endMs)
        assertEquals("Пишем код.", tl.frame(10).caption)
        assertEquals("Запускаем его.", tl.frame(tl.scenes[0].cues[1].startMs + 5).caption)
    }

    @Test fun typingIsGradualAndStateCarriesOver() {
        val tl = LessonTimeline(scenario)
        val type = tl.scenes[0].actions[0]
        val mid = tl.frame(type.startMs + type.durationMs / 2)
        assertTrue(mid.typing)
        assertTrue(mid.code.length in 1 until "print(1)\n".length)
        val endA = tl.frame(tl.scenes[0].endMs - 1)
        assertEquals("print(1)\n", endA.code)
        assertEquals("1\n", endA.output)
        assertFalse(endA.outputIsError)
        assertEquals(setOf(1), endA.highlight)
        // Начало второй сцены: подсветка сброшена, код ещё старый (clear начнётся после вступления).
        val startB = tl.frame(tl.scenes[1].startMs)
        assertEquals(1, startB.sceneIndex)
        assertEquals(emptySet<Int>(), startB.highlight)
        assertEquals("print(1)\n", startB.code)
        val endB = tl.frame(tl.totalMs)
        assertEquals("print(\n", endB.code)
        assertTrue(endB.outputIsError)
        assertEquals("**Важно**", endB.note)
        assertFalse(endB.running)
    }

    @Test fun runShowsRunningUntilOutput() {
        val tl = LessonTimeline(scenario)
        val run = tl.scenes[0].actions[2]
        val f = tl.frame(tl.scenes[0].startMs + run.startMs + 1)
        assertTrue(f.running)
        assertEquals("", f.output)
    }

    @Test fun audioTimingAndCueAnchors() {
        val meta = NarrationMeta(scenes = listOf(
            SceneAudio("a", "a.m4a", 4000, cues = listOf(Cue(0, 1500, "Пишем код."), Cue(1800, 3800, "Запускаем его."))),
            SceneAudio("b", "b.m4a", 6000, cues = listOf(Cue(0, 1000, "Ошибка!"), Cue(3000, 5800, "Смотрим сообщение."))),
        ))
        val tl = LessonTimeline(scenario, meta)
        assertTrue(tl.hasAudio)
        assertEquals(10_000, tl.totalMs)
        assertEquals("b.m4a", tl.scenes[1].audioFile)
        // output с cue = 1 начинается ровно с фразы «Смотрим сообщение.»
        val out = tl.scenes[1].actions.first { it.action.type == "output" }
        assertEquals(3000, out.startMs)
        // Действия до опорной точки укладываются до неё, всё — до конца сцены.
        assertTrue(tl.scenes[1].actions.takeWhile { it !== out }.all { it.endMs <= 3000 })
        assertTrue(tl.scenes.all { s -> s.actions.all { it.endMs <= s.durationMs } })
        assertEquals("Смотрим сообщение.", tl.frame(4000 + 3500).caption)
        assertNull(tl.frame(4000 + 2600).caption) // пауза между фразами
        assertEquals(1, tl.sceneAt(4000))
        assertEquals(0, tl.sceneAt(3999))
        assertEquals(1, tl.sceneAt(99_999))
    }

    @Test fun realLessonScenarioIsConsistent() {
        val dir = File("../content/packs/python-basics/lessons/py-01-print")
        val json = Json { ignoreUnknownKeys = true }
        val scen = json.decodeFromString(Scenario.serializer(), File(dir, "scenario.json").readText())
        val meta = File(dir, "audio/narration.json").takeIf { it.exists() }
            ?.let { json.decodeFromString(NarrationMeta.serializer(), it.readText()) }
        val tl = LessonTimeline(scen, meta)
        assertTrue(tl.totalMs > 60_000)
        // Фразы Kotlin и Python совпадают (иначе cue указывали бы не на те фразы).
        meta?.scenes?.forEach { s ->
            val scene = scen.scenes.first { it.id == s.id }
            assertEquals(s.cues.map { it.text }, LessonTimeline.splitPhrases(scene.narration))
        }
        val end = tl.frame(tl.totalMs)
        assertEquals("print(\"Привет, мир!\")\n", end.code)
        // Каждый кадр строится без исключений.
        var t = 0L
        while (t <= tl.totalMs) { tl.frame(t); t += 250 }
    }
}
