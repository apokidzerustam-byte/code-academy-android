package app.codeacademy

import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import app.codeacademy.assessment.CheckReport
import app.codeacademy.assessment.Verdict
import app.codeacademy.content.ContentRepository
import app.codeacademy.content.LessonRef
import app.codeacademy.data.AppDatabase
import app.codeacademy.data.LessonStatus
import app.codeacademy.data.ProgressRepository
import app.codeacademy.data.SkillStatus
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.runBlocking
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class ProgressDatabaseTest {
    private val ctx = InstrumentationRegistry.getInstrumentation().targetContext
    private val db = AppDatabase.inMemory(ctx)
    private val repo = ProgressRepository(db)
    private val content = ContentRepository(ctx.assets)
    private val ref = LessonRef("python-basics", "py-01-print")

    @After fun close() = db.close()

    private fun verdict(ok: Boolean) = Verdict(CheckReport(allPassed = ok, passed = if (ok) 1 else 0, total = 1))

    @Test fun contentPackIsBundledInAssets() = runBlocking {
        val packs = content.packs()
        assertTrue(packs.any { it.id == "python-basics" })
        assertEquals(3, content.assignments(ref).size)
        assertTrue(content.notes(ref).contains("print"))
    }

    @Test fun lessonPassesAfterCriteriaAndSkillsUpdate() = runBlocking {
        val lesson = content.lesson(ref)
        repo.openLesson(ref)
        assertEquals(LessonStatus.IN_PROGRESS, db.progress().get(ref.key)!!.status)
        repo.recordAttempt(ref, lesson, "a1-hello", "x", verdict(false), 0, 0, "W")
        repo.recordAttempt(ref, lesson, "a1-hello", "x", verdict(true), 1, 0, "W")
        assertEquals(LessonStatus.IN_PROGRESS, db.progress().get(ref.key)!!.status) // нужно 2 задания
        repo.recordAttempt(ref, lesson, "a2-fix-quote", "x", verdict(true), 0, 0, "W")
        assertEquals(LessonStatus.PASSED, db.progress().get(ref.key)!!.status)
        val skills = repo.skills.first()
        assertEquals(lesson.skills.toSet(), skills.map { it.skillId }.toSet())
        assertTrue(skills.all { it.status == SkillStatus.LEARNING }) // освоение — не за один день
        assertEquals(3, repo.attemptsCount.first())
        assertEquals(2, repo.passedCount.first())
    }

    @Test fun draftsSurvive() = runBlocking {
        repo.saveDraft("k", "print(1)", 2)
        val d = repo.draft("k")!!
        assertEquals("print(1)", d.content)
        assertEquals(2, d.hintsShown)
    }
}
