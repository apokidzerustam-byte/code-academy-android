package app.codeacademy

import androidx.compose.ui.test.hasTestTag
import androidx.compose.ui.test.hasText
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.compose.ui.test.performTextReplacement
import androidx.test.ext.junit.runners.AndroidJUnit4
import app.codeacademy.data.LessonStatus
import app.codeacademy.data.ReviewItemEntity
import app.codeacademy.data.SkillStateEntity
import app.codeacademy.data.SkillStatus
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import java.time.LocalDate

/** Этап 6: диагностика, карта знаний, повторение, недельный план. */
@RunWith(AndroidJUnit4::class)
class AdaptiveUiTest {
    @get:Rule val rule = createAndroidComposeRule<MainActivity>()
    private val app get() = rule.activity.application as CodeAcademyApp

    @Before fun clean() {
        runBlocking {
            app.container.db.clearAllTables()
            app.container.settings.setOnboardingDone(false)
            app.container.settings.setSessionMinutes(60)
            app.container.settings.setDaysPerWeek(5)
        }
    }

    private fun waitTag(tag: String, ms: Long = 10_000) =
        rule.waitUntil(ms) { rule.onAllNodes(hasTestTag(tag)).fetchSemanticsNodes().isNotEmpty() }

    private fun waitText(t: String, ms: Long = 10_000) =
        rule.waitUntil(ms) { rule.onAllNodes(hasText(t, substring = true)).fetchSemanticsNodes().isNotEmpty() }

    @Test fun diagnosticConfirmsPrefixAndSchedulesReview() {
        waitTag("start-choice")
        rule.onNodeWithTag("start-diagnostic").performClick()
        waitTag("diag-answer")
        waitText("Вопрос 1 из 10")
        // Урок 1 — верно (лишние пробелы в конце строк не мешают), урок 2 — неверно.
        rule.onNodeWithTag("diag-answer").performTextReplacement("10 - 4  \n6\nГотово\n")
        rule.onNodeWithTag("diag-submit").performClick()
        waitText("Вопрос 2 из 10")
        rule.onNodeWithTag("diag-answer").performTextReplacement("5\n10")
        rule.onNodeWithTag("diag-submit").performClick()
        waitText("Подтверждено уроков: 1 из 10")
        rule.waitUntil(5_000) {
            runBlocking {
                app.container.db.progress().get("python-basics/py-01-print")?.status == LessonStatus.TESTED_OUT &&
                    app.container.settings.settings.first().onboardingDone
            }
        }
        runBlocking {
            assertEquals(null, app.container.db.progress().get("python-basics/py-02-variables")?.status?.takeIf { it == LessonStatus.TESTED_OUT })
            val review = app.container.db.reviews().get("python.print")!!
            assertEquals(LocalDate.now().toEpochDay() + 1, review.dueEpochDay)
            assertEquals(SkillStatus.LEARNING, app.container.db.skills().get("python.print")!!.status)
            assertTrue(app.container.settings.settings.first().onboardingDone)
        }
        rule.onNodeWithTag("diag-done").performClick()
        // Главная: карточка выбора скрыта, следующий урок — второй.
        waitText("Переменные")
        assertTrue(rule.onAllNodes(hasTestTag("start-choice")).fetchSemanticsNodes().isEmpty())
    }

    @Test fun startFromZeroHidesChoice() {
        waitTag("start-choice")
        rule.onNodeWithTag("start-zero").performClick()
        rule.waitUntil(5_000) { rule.onAllNodes(hasTestTag("start-choice")).fetchSemanticsNodes().isEmpty() }
    }

    @Test fun knowledgeMapReviewAndPlan() {
        val today = LocalDate.now().toEpochDay()
        runBlocking {
            app.container.settings.setOnboardingDone(true)
            app.container.db.reviews().upsert(ReviewItemEntity("python.variables", 0, 1, today))
            app.container.db.skills().upsert(SkillStateEntity("python.variables", SkillStatus.NEEDS_REVIEW, 3, 1))
        }
        waitTag("open-map")
        rule.onNodeWithTag("open-map").performScrollTo().performClick()
        waitTag("map-summary")
        waitText("требует повторения")
        rule.onNodeWithTag("map-py-02-variables").performScrollTo()
        rule.activity.runOnUiThread { rule.activity.onBackPressedDispatcher.onBackPressed() }

        waitTag("open-review")
        rule.onNodeWithTag("open-review").performScrollTo().performClick()
        waitText("Сегодня: 1")
        rule.onNodeWithTag("review-python.variables").performScrollTo().performClick()
        waitTag("check") // открылось задание урока «Переменные»
        rule.activity.runOnUiThread { rule.activity.onBackPressedDispatcher.onBackPressed() }
        rule.activity.runOnUiThread { rule.activity.onBackPressedDispatcher.onBackPressed() }

        waitTag("open-plan")
        rule.onNodeWithTag("open-plan").performScrollTo().performClick()
        waitTag("plan-day-0")
        rule.onNodeWithTag("session-30").performClick()
        rule.onNodeWithTag("days-7").performScrollTo().performClick()
        rule.waitUntil(5_000) { rule.onAllNodes(hasTestTag("plan-day-6")).fetchSemanticsNodes().isNotEmpty() }
        waitText("Сегодня · 30 мин")
        waitText("Повторение: навыков 1")
        runBlocking {
            val s = app.container.settings.settings.first()
            assertEquals(30, s.sessionMinutes)
            assertEquals(7, s.daysPerWeek)
        }
    }
}
