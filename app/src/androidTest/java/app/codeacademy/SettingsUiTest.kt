package app.codeacademy

import androidx.compose.ui.test.hasTestTag
import androidx.compose.ui.test.hasText
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithContentDescription
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.test.ext.junit.runners.AndroidJUnit4
import app.codeacademy.mentor.PerfMode
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.runBlocking
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

/** Этап 10: режим производительности и журнал сбоев на экране настроек. */
@RunWith(AndroidJUnit4::class)
class SettingsUiTest {
    @get:Rule val rule = createAndroidComposeRule<MainActivity>()
    private val app get() = rule.activity.application as CodeAcademyApp

    @Before fun prepare() {
        runBlocking {
            app.container.settings.setOnboardingDone(true)
            app.container.settings.setPerfMode(PerfMode.STANDARD)
        }
        CrashLog.clear(app.crashLogFile)
    }

    @After fun cleanUp() {
        runBlocking { app.container.settings.setPerfMode(PerfMode.STANDARD) }
        CrashLog.clear(app.crashLogFile)
    }

    private fun waitTag(tag: String, ms: Long = 15_000) =
        rule.waitUntil(ms) { rule.onAllNodes(hasTestTag(tag)).fetchSemanticsNodes().isNotEmpty() }

    private fun settingsShown() = rule.onAllNodes(hasTestTag("theme-system")).fetchSemanticsNodes().isNotEmpty()

    /** Открывает настройки; после пересоздания Activity навигация уже восстановила экран настроек — тогда ничего не нажимается. */
    private fun openSettings() {
        rule.waitUntil(15_000) { settingsShown() || rule.onAllNodes(androidx.compose.ui.test.hasContentDescription("Настройки")).fetchSemanticsNodes().isNotEmpty() }
        if (!settingsShown()) rule.onNodeWithContentDescription("Настройки").performClick()
        waitTag("theme-system")
    }

    @Test fun performanceModeIsChosenAndSaved() {
        openSettings()
        for ((tag, mode) in listOf("perf-economy" to PerfMode.ECONOMY, "perf-extended" to PerfMode.EXTENDED, "perf-standard" to PerfMode.STANDARD)) {
            rule.onNodeWithTag(tag).performScrollTo().performClick()
            rule.waitUntil(5_000) { runBlocking { app.container.settings.settings.first().perfMode } == mode }
            assertEquals(mode, runBlocking { app.container.settings.settings.first().perfMode })
        }
        // Выбор доходит до наставника: при создании наставника контейнер запоминает режим для процесса нейросети.
        rule.onNodeWithTag("perf-economy").performScrollTo().performClick()
        rule.waitUntil(5_000) { runBlocking { app.container.settings.settings.first().perfMode } == PerfMode.ECONOMY }
        runBlocking { app.container.mentor(app.container.settings.settings.first()) }
        assertEquals(PerfMode.ECONOMY, app.container.perfMode)
    }

    @Test fun crashHandlerWritesToTheLogWithoutKillingTheProcess() {
        assertNotNull("обработчик сбоев не установлен", Thread.getDefaultUncaughtExceptionHandler())
        app.crashHandler(null).uncaughtException(Thread.currentThread(), IllegalStateException("тест-сбой журнала"))
        val text = CrashLog.read(app.crashLogFile)
        assertTrue(text, text.contains("IllegalStateException: тест-сбой журнала") && text.contains(BuildConfig.VERSION_NAME))
        assertTrue(text, text.contains("процесс: "))
    }

    @Test fun crashLogIsShownCopiedAndCleared() {
        openSettings()
        rule.onNodeWithTag("crash-status").performScrollTo()
        assertTrue(rule.onAllNodes(hasText("Сбоев не было", substring = true)).fetchSemanticsNodes().isNotEmpty())
        CrashLog.append(app.crashLogFile, CrashLog.note("main", "проверочная запись журнала", BuildConfig.VERSION_NAME, "тестовое устройство", System.currentTimeMillis()))
        // Экран читает журнал при открытии: переоткрываем настройки.
        rule.activityRule.scenario.recreate()
        openSettings()
        rule.onNodeWithTag("crash-status").performScrollTo()
        assertTrue(rule.onAllNodes(hasText("Записей: 1", substring = true)).fetchSemanticsNodes().isNotEmpty())
        rule.onNodeWithTag("crash-show").performScrollTo().performClick()
        waitTag("crash-text")
        assertTrue(rule.onAllNodes(hasText("проверочная запись журнала", substring = true)).fetchSemanticsNodes().isNotEmpty())
        rule.onNodeWithTag("crash-clear").performScrollTo().performClick()
        rule.waitUntil(5_000) { rule.onAllNodes(hasText("Сбоев не было", substring = true)).fetchSemanticsNodes().isNotEmpty() }
        assertEquals("", CrashLog.read(app.crashLogFile))
    }
}
