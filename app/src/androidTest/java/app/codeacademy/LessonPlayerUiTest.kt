package app.codeacademy

import android.util.Log
import androidx.compose.ui.test.SemanticsNodeInteractionsProvider
import androidx.compose.ui.test.hasAnyAncestor
import androidx.compose.ui.test.hasTestTag
import androidx.compose.ui.test.hasText
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.compose.ui.test.printToLog
import androidx.test.ext.junit.runners.AndroidJUnit4
import app.codeacademy.content.LessonRef
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

/** Анимированный урок: сцены, анимация кода и вывода, звук, скорость, сохранение позиции. */
@RunWith(AndroidJUnit4::class)
class LessonPlayerUiTest {
    @get:Rule val rule = createAndroidComposeRule<MainActivity>()
    private val app get() = rule.activity.application as CodeAcademyApp

    @Before fun clean() {
        runBlocking { app.container.db.clearAllTables(); app.container.settings.setOnboardingDone(true) }
    }

    private fun SemanticsNodeInteractionsProvider.has(tag: String, text: String) =
        onAllNodes(hasText(text, substring = true) and hasAnyAncestor(hasTestTag(tag))).fetchSemanticsNodes().isNotEmpty()

    private fun openLesson() {
        rule.onNodeWithTag("open-program").performClick()
        rule.waitUntil(10_000) { rule.onAllNodes(hasTestTag("lesson-py-01-print")).fetchSemanticsNodes().isNotEmpty() }
        rule.onNodeWithTag("lesson-py-01-print").performScrollTo().performClick()
        rule.waitUntil(10_000) { rule.onAllNodes(hasTestTag("lesson-player")).fetchSemanticsNodes().isNotEmpty() }
    }

    private fun sceneIs(n: Int) =
        rule.onAllNodes(hasTestTag("player-scene") and hasText("Сцена $n из", substring = true)).fetchSemanticsNodes().isNotEmpty()

    @Test fun playAnimatedLesson() {
        val hasAudio = runBlocking { app.container.content.narration(LessonRef("python-basics", "py-01-print")) }
            ?.scenes?.isNotEmpty() == true
        Log.i("CAPROBE", "player: audio=$hasAudio")
        openLesson()
        assertTrue(sceneIs(1))

        // Сразу к сцене «Запуск», скорость 2×.
        rule.onNodeWithTag("player-next").performScrollTo().performClick()
        rule.onNodeWithTag("player-next").performScrollTo().performClick()
        runCatching { rule.waitUntil(5_000) { sceneIs(3) } }.onFailure {
            rule.onNodeWithTag("lesson-player").printToLog("CAPROBE")
            throw it
        }
        repeat(3) { rule.onNodeWithTag("player-speed").performScrollTo().performClick() }
        rule.waitUntil(3_000) { rule.has("player-speed", "2×") || rule.onAllNodes(hasTestTag("player-speed") and hasText("2×")).fetchSemanticsNodes().isNotEmpty() }
        val t0 = System.currentTimeMillis()
        playUntil(40_000) {
            (!hasAudio || rule.onAllNodes(hasTestTag("player-audio-on")).fetchSemanticsNodes().isNotEmpty()) &&
                rule.has("player-output", "Привет, мир!")
        }
        Log.i("CAPROBE", "player: output after ${System.currentTimeMillis() - t0}ms (audio=$hasAudio)")
        assertTrue(rule.onAllNodes(hasText("Привет, мир!", substring = true) and hasAnyAncestor(hasTestTag("player-code"))).fetchSemanticsNodes().isNotEmpty())

        // Перемотка по сценам к сцене с ошибкой (во время проигрывания сцена могла смениться).
        // «Назад» в середине сцены сначала возвращает к её началу (как в обычных плеерах) — поэтому до 10 нажатий.
        repeat(10) {
            if (!sceneIs(6)) {
                val before = (1..7).first { sceneIs(it) }
                rule.onNodeWithTag(if (before < 6) "player-next" else "player-prev").performScrollTo().performClick()
                rule.waitForIdle()
            }
        }
        assertTrue(sceneIs(6))
        playUntil(60_000) { rule.has("player-output", "SyntaxError") }

        // Позиция сохраняется: после выхода и возврата — та же сцена.
        rule.runOnUiThread { rule.activity.onBackPressedDispatcher.onBackPressed() }
        rule.waitUntil(5_000) { rule.onAllNodes(hasTestTag("lesson-py-01-print")).fetchSemanticsNodes().isNotEmpty() }
        rule.onNodeWithTag("lesson-py-01-print").performScrollTo().performClick()
        rule.waitUntil(10_000) { sceneIs(6) || sceneIs(7) }
    }

    /**
     * Воспроизведение в реальном времени: часы плеера обновляют экран каждый кадр, поэтому Compose
     * никогда не «простаивает». Кадры двигаем вручную и проверяем условие, затем ставим паузу.
     */
    private fun playUntil(timeoutMs: Long, cond: () -> Boolean) {
        rule.onNodeWithTag("player-play").performScrollTo().performClick()
        rule.mainClock.autoAdvance = false
        try {
            val end = System.currentTimeMillis() + timeoutMs
            while (true) {
                rule.mainClock.advanceTimeByFrame()
                if (cond()) break
                if (System.currentTimeMillis() > end) throw AssertionError("условие не выполнено за $timeoutMs мс")
                Thread.sleep(30)
            }
            rule.onNodeWithTag("player-play").performClick() // пауза
            repeat(3) { rule.mainClock.advanceTimeByFrame() }
        } finally {
            rule.mainClock.autoAdvance = true
        }
    }

    @Test fun subtitlesToggle() {
        openLesson()
        val hasAudio = runBlocking { app.container.content.narration(LessonRef("python-basics", "py-01-print")) }
            ?.scenes?.isNotEmpty() == true
        // Без озвучки субтитры включены сразу, с озвучкой — по кнопке.
        if (hasAudio) rule.onNodeWithTag("player-cc").performScrollTo().performClick()
        // Без воспроизведения: в начале урока — первая фраза озвучки.
        rule.waitUntil(5_000) { rule.has("lesson-player", "Привет!") }
        rule.onNodeWithTag("player-cc").performScrollTo().performClick()
        rule.waitUntil(5_000) { rule.onAllNodes(hasTestTag("player-caption")).fetchSemanticsNodes().isEmpty() }
        rule.onNodeWithTag("player-cc").performScrollTo().performClick()
        rule.waitUntil(5_000) { rule.onAllNodes(hasTestTag("player-caption")).fetchSemanticsNodes().isNotEmpty() }
    }
}
