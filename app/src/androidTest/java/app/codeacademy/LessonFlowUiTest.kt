package app.codeacademy

import android.util.Log
import androidx.compose.ui.test.hasTestTag
import androidx.compose.ui.test.hasText
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.compose.ui.test.performTextReplacement
import androidx.test.ext.junit.runners.AndroidJUnit4
import kotlinx.coroutines.runBlocking
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

/** Сквозной сценарий: Главная → Программа → Урок → Задание → решение → «Верно» → урок засчитан. */
@RunWith(AndroidJUnit4::class)
class LessonFlowUiTest {
    @get:Rule val rule = createAndroidComposeRule<MainActivity>()

    @Before fun clean() {
        val app = rule.activity.application as CodeAcademyApp
        runBlocking {
            app.container.db.clearAllTables()
            app.container.settings.setOnboardingDone(true)
            // UI-тест вводит текст в простое поле; CodeMirror проверяется в CodeEditorTest.
            app.container.settings.setPlainEditor(true)
        }
    }

    @Test fun solveFirstAssignmentEndToEnd() {
        rule.onNodeWithTag("open-program").performClick()
        rule.waitUntil(10_000) { rule.onAllNodes(hasTestTag("lesson-py-01-print")).fetchSemanticsNodes().isNotEmpty() }
        rule.onNodeWithTag("lesson-py-01-print").performScrollTo().performClick()
        rule.onNodeWithTag("tab-1").performClick()
        rule.waitUntil(10_000) { rule.onAllNodes(hasText("Текст берут в", substring = true)).fetchSemanticsNodes().isNotEmpty() }
        rule.onNodeWithTag("tab-2").performClick()
        rule.waitUntil(10_000) { rule.onAllNodes(hasTestTag("assignment-0")).fetchSemanticsNodes().isNotEmpty() }
        rule.onNodeWithTag("assignment-0").performClick()
        rule.waitUntil(10_000) { rule.onAllNodes(hasTestTag("code")).fetchSemanticsNodes().isNotEmpty() }

        // Неверное решение → видим ожидаемое и фактическое.
        rule.onNodeWithTag("code").performScrollTo().performTextReplacement("print(\"Привет, мир!\")\n")
        rule.onNodeWithTag("check").performScrollTo().performClick()
        val t0 = System.currentTimeMillis()
        rule.waitUntil(90_000) { rule.onAllNodes(hasTestTag("verdict")).fetchSemanticsNodes().isNotEmpty() }
        Log.i("CAPROBE", "ui first check (incl. interpreter start): ${System.currentTimeMillis() - t0}ms")
        rule.onNodeWithText("Ожидалось:", substring = true).performScrollTo().assertExists()

        // Подсказка по шагам.
        rule.onNodeWithTag("hint").performScrollTo().performClick()
        rule.onNodeWithText("1. Намёк", substring = true).performScrollTo().assertExists()

        // Верное решение.
        rule.onNodeWithTag("code").performScrollTo().performTextReplacement("print(\"Привет, мир!\")\nprint(\"Я учу Python\")\n")
        rule.onNodeWithTag("check").performScrollTo().performClick()
        val t1 = System.currentTimeMillis()
        rule.waitUntil(30_000) { rule.onAllNodes(hasText("Верно!", substring = true)).fetchSemanticsNodes().isNotEmpty() }
        Log.i("CAPROBE", "ui second check: ${System.currentTimeMillis() - t1}ms")

        // В статистике видна попытка, навык и подсказка.
        val app = rule.activity.application as CodeAcademyApp
        // Попытка записывается до показа вердикта, но проверяем с ожиданием на случай медленного эмулятора.
        rule.waitUntil(10_000) {
            runBlocking { app.container.db.attempts().passedAssignments("python-basics/py-01-print") } == listOf("a1-hello")
        }
    }

    @Test fun draftSurvivesActivityRecreation() {
        rule.onNodeWithTag("open-program").performClick()
        rule.waitUntil(10_000) { rule.onAllNodes(hasTestTag("lesson-py-01-print")).fetchSemanticsNodes().isNotEmpty() }
        rule.onNodeWithTag("lesson-py-01-print").performScrollTo().performClick()
        rule.onNodeWithTag("tab-2").performClick()
        rule.waitUntil(10_000) { rule.onAllNodes(hasTestTag("assignment-0")).fetchSemanticsNodes().isNotEmpty() }
        rule.onNodeWithTag("assignment-0").performClick()
        rule.waitUntil(10_000) { rule.onAllNodes(hasTestTag("code")).fetchSemanticsNodes().isNotEmpty() }
        rule.onNodeWithTag("code").performTextReplacement("print('черновик')")
        rule.mainClock.advanceTimeBy(1_000) // автосохранение через 600 мс (виртуальные часы Compose)
        rule.waitForIdle()
        val app = rule.activity.application as CodeAcademyApp
        rule.waitUntil(10_000) { runBlocking { app.container.progress.draft("python-basics/py-01-print/0")?.content } == "print('черновик')" }
        rule.activityRule.scenario.recreate()
        rule.waitUntil(10_000) { rule.onAllNodes(hasText("print('черновик')", substring = true)).fetchSemanticsNodes().isNotEmpty() }
    }
}
