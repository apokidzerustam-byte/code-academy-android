package app.codeacademy

import android.util.Log
import androidx.compose.ui.test.hasTestTag
import androidx.compose.ui.test.hasText
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.compose.ui.test.performScrollToNode
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import app.codeacademy.assessment.AssessmentService
import app.codeacademy.content.ContentRepository
import app.codeacademy.runner.CodeRunner
import app.codeacademy.runner.PyodideRunner
import app.codeacademy.runner.RunnerClient
import app.codeacademy.runner.WebRunner
import app.codeacademy.runner.WebRunnerHost
import app.codeacademy.runner.WebSandbox
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

/** Все этапы учебных проектов на устройстве: эталон проходит, заготовка и типовые ошибки — нет. */
@RunWith(AndroidJUnit4::class)
class CourseProjectsOnDeviceTest {
    private val ctx = InstrumentationRegistry.getInstrumentation().targetContext

    @Test fun allMilestonesInAppRunners() = runBlocking<Unit> {
        val content = ContentRepository(ctx.assets)
        val service = AssessmentService()
        val projects = content.allProjects()
        assertTrue("учебных проектов: ${projects.size}", projects.size >= 5)
        assertTrue(projects.any { it.second.isThrough })
        val runners = mutableListOf<Pair<String, CodeRunner>>()
        val a = RunnerClient(ctx, isolated = false)
        runners += "A" to a
        val w = PyodideRunner(ctx)
        if (w.prepare()?.pythonStarted == true) runners += "W" to w
        val web = if (WebSandbox.supported()) WebRunnerHost(ctx).takeIf { it.prepare() } else null
        val problems = mutableListOf<String>()
        var checked = 0
        try {
            for ((ref, p) in projects) {
                val list = if (p.language == "python") runners else listOfNotNull(web?.let { "html" to WebRunner(it, "html") })
                for ((name, r) in list) {
                    var prev = emptyMap<String, String>()
                    for (m in p.milestones) {
                        val start = prev + m.starterFiles.filterKeys { it !in prev }
                        val t0 = System.currentTimeMillis()
                        val good = service.evaluateProject(r, p.language, m.tests, m.solutionFiles, "check-proj")
                        if (!good.passed) problems += "${ref.key}/${m.id} [$name]: эталон не прошёл: ${good.failure} ${good.failureText.take(200)} " +
                            "${good.report?.compileError ?: good.report?.loadError ?: good.report?.cases?.firstOrNull { !it.passed }}"
                        if (start.isNotEmpty() && service.evaluateProject(r, p.language, m.tests, start, "check-proj").passed) {
                            problems += "${ref.key}/${m.id} [$name]: заготовка прошла"
                        }
                        for (wr in m.wrongSolutions) {
                            if (service.evaluateProject(r, p.language, m.tests, wr.files, "check-proj").passed) {
                                problems += "${ref.key}/${m.id} [$name]: прошло неверное решение «${wr.why}»"
                            }
                        }
                        checked++
                        Log.i("CAPROBE", "project ${ref.key}/${m.id} [$name]: ${System.currentTimeMillis() - t0} мс")
                        prev = m.solutionFiles
                    }
                }
            }
        } finally {
            a.close(); w.close(); web?.close()
        }
        problems.forEach { Log.e("CAPROBE", it) }
        Log.e("CAPROBE", "проекты: проверено этапов×исполнителей $checked, проблем ${problems.size}; веб ${web != null}, W ${runners.size > 1}")
        assertTrue("проблемы:\n" + problems.joinToString("\n"), problems.isEmpty())
    }
}

/** Интерфейс: учебный проект → этап 1 проверен → переход к этапу 2 → проект завершён. */
@RunWith(AndroidJUnit4::class)
class ProjectsUiTest {
    @get:Rule val rule = createAndroidComposeRule<MainActivity>()
    private val app get() = rule.activity.application as CodeAcademyApp

    @Before fun clean() {
        runBlocking {
            app.container.db.clearAllTables()
            app.container.settings.setOnboardingDone(true)
            app.container.settings.setPlainEditor(true)
        }
    }

    private fun waitTag(tag: String, ms: Long = 30_000) =
        rule.waitUntil(ms) { rule.onAllNodes(hasTestTag(tag)).fetchSemanticsNodes().isNotEmpty() }

    @Test fun milestoneFlow() {
        try {
            flow()
        } catch (t: Throwable) {
            Log.e("CAPROBE", "ProjectsUiTest failed: " + Log.getStackTraceString(t).take(4000))
            throw t
        }
    }

    private fun openCourse() {
        waitTag("projects-list")
        rule.waitUntil(10_000) {
            runCatching { rule.onNodeWithTag("projects-list").performScrollToNode(hasTestTag("start-shopping")) }.isSuccess
        }
        rule.onNodeWithTag("start-shopping").performClick()
        waitTag("check-milestone")
    }

    /** Назад со страницы IDE: экран сохраняет файлы при уходе — ждём, пока запись закончится. */
    private fun backFromIde() {
        rule.onNode(androidx.compose.ui.test.hasContentDescription("Назад")).performClick()
        waitTag("projects-list")
        Thread.sleep(1_500)
    }

    private fun checkAndNext() {
        rule.onNodeWithTag("check-milestone").performScrollTo().performClick()
        val t0 = System.currentTimeMillis()
        waitTag("next-milestone", 120_000)
        Log.i("CAPROBE", "project ui: этап проверен за ${System.currentTimeMillis() - t0} мс")
        rule.onNodeWithTag("next-milestone").performScrollTo().performClick()
    }

    private fun flow() {
        val c = app.container
        val shop = runBlocking { c.content.allProjects().first { it.first.projectId == "shopping" }.second }
        rule.onNodeWithTag("open-projects").performScrollTo().performClick()
        // «Начать» создаёт проект с заготовкой этапа 1: в нём подсказка-комментарий, тесты не проходят.
        openCourse()
        val id = runBlocking { c.projects.projects.first().single { it.course == "python-basics/shopping" }.id }
        assertEquals(shop.milestones[0].starterFiles, runBlocking { c.projects.files(id) })
        backFromIde()
        // Ученик «написал» решение этапа 1.
        runBlocking { c.projects.replaceAll(id, shop.milestones[0].solutionFiles) }
        openCourse()
        checkAndNext()
        rule.waitUntil(10_000) { rule.onAllNodes(hasText("Этап 2 из 2", substring = true)).fetchSemanticsNodes().isNotEmpty() }
        backFromIde()
        runBlocking { c.projects.replaceAll(id, shop.milestones[1].solutionFiles) }
        openCourse()
        checkAndNext()
        waitTag("project-done")
        val passed = runBlocking { c.progress.passedMilestones(app.codeacademy.content.ProjectRef("python-basics", "shopping")) }
        assertEquals(setOf("collect", "unique"), passed)
        // Попытки этапов видны в статистике навыков.
        assertTrue(runBlocking { c.progress.skills.first() }.any { it.skillId == "python.lists" && it.successes >= 2 })
    }
}
