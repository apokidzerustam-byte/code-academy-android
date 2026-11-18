package app.codeacademy

import android.util.Log
import androidx.compose.ui.test.hasTestTag
import androidx.compose.ui.test.hasText
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performImeAction
import androidx.compose.ui.test.performScrollTo
import androidx.compose.ui.test.performTextInput
import androidx.compose.ui.test.performTextReplacement
import androidx.test.ext.junit.runners.AndroidJUnit4
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.runBlocking
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

/** IDE: создать проект → запустить с вводом → терминал: ls, mkdir, echo > файл, python. */
@RunWith(AndroidJUnit4::class)
class IdeUiTest {
    @get:Rule val rule = createAndroidComposeRule<MainActivity>()
    private val app get() = rule.activity.application as CodeAcademyApp

    @Before fun clean() = runBlocking {
        app.container.db.clearAllTables()
        app.container.settings.setPlainEditor(true)
    }

    private fun waitText(t: String, ms: Long = 30_000) =
        rule.waitUntil(ms) { rule.onAllNodes(hasText(t, substring = true)).fetchSemanticsNodes().isNotEmpty() }

    @Test fun createRunAndUseTerminal() {
        rule.onNodeWithTag("open-projects").performClick()
        rule.onNodeWithTag("new-project").performClick()
        rule.onNodeWithTag("project-title").performTextInput("Приветствие")
        rule.onNodeWithTag("create-project").performClick()
        rule.waitUntil(10_000) { rule.onAllNodes(hasTestTag("code")).fetchSemanticsNodes().isNotEmpty() }

        rule.onNodeWithTag("stdin").performScrollTo().performTextReplacement("Аня")
        rule.onNodeWithTag("ide-run").performScrollTo().performClick()
        val t0 = System.currentTimeMillis()
        waitText("Привет, Аня", 90_000)
        Log.i("CAPROBE", "ide first run: ${System.currentTimeMillis() - t0}ms")

        rule.onNodeWithTag("ide-terminal-tab").performScrollTo().performClick()
        fun cmd(line: String) {
            rule.onNodeWithTag("term-input").performScrollTo().performTextReplacement(line)
            rule.onNodeWithTag("term-input").performImeAction()
        }
        cmd("mkdir data")
        cmd("echo привет > data/note.txt")
        cmd("cat data/note.txt")
        waitText("~ $ cat data/note.txt\nпривет")
        cmd("ls")
        waitText("data/  main.py")
        cmd("python main.py")
        waitText("EOFError", 30_000) // без ввода input() получает конец ввода — это видно ученику

        // Файл из терминала сохранён в проекте.
        rule.waitUntil(10_000) {
            runBlocking {
                app.container.db.projects().allFiles().first().any { it.path == "data/note.txt" && it.content == "привет\n" }
            }
        }
    }
}
