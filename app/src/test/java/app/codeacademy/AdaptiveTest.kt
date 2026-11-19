package app.codeacademy

import app.codeacademy.data.ReviewItemEntity
import app.codeacademy.learning.Advisor
import app.codeacademy.learning.AttemptLite
import app.codeacademy.learning.Diagnostic
import app.codeacademy.learning.LessonWork
import app.codeacademy.learning.NextAction
import app.codeacademy.learning.PlanKind
import app.codeacademy.learning.PracticeResult
import app.codeacademy.learning.ReviewScheduler
import app.codeacademy.learning.Scoring
import app.codeacademy.learning.Thresholds
import app.codeacademy.learning.WeeklyPlanner
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/** Адаптивная методика на фиксированных историях (критерий этапа 6). */
class AdaptiveTest {
    private fun a(id: String, t: Long, passed: Boolean, hints: Int = 0) = AttemptLite(id, t, passed, hints)

    @Test fun assignmentScoreFromHistory() {
        assertEquals(100, Scoring.assignmentScore(listOf(a("x", 1, true))))
        // Две ошибки, потом решено — 80.
        assertEquals(80, Scoring.assignmentScore(listOf(a("x", 1, false), a("x", 2, false), a("x", 3, true))))
        // Намёк и направление не штрафуются, третья и четвёртая ступени — по −10.
        assertEquals(100, Scoring.assignmentScore(listOf(a("x", 1, true, hints = 2))))
        assertEquals(80, Scoring.assignmentScore(listOf(a("x", 1, true, hints = 4))))
        // Решение подсмотрено — не выше 40.
        assertEquals(40, Scoring.assignmentScore(listOf(a("x", 1, true, hints = 6))))
        // Не решено — 0; попытки после решения не портят балл; порядок по времени, а не по списку.
        assertEquals(0, Scoring.assignmentScore(listOf(a("x", 1, false), a("x", 2, false))))
        assertEquals(90, Scoring.assignmentScore(listOf(a("x", 5, false), a("x", 3, false), a("x", 4, true))))
        assertEquals(70, Scoring.assignmentScore(List(6) { a("x", it.toLong(), false) } + a("x", 9, true)))
    }

    @Test fun lessonScoreAndThresholds() {
        val history = listOf(
            a("a1", 1, true),                       // 100
            a("a2", 2, false), a("a2", 3, true),    // 90
            a("a3", 4, true, hints = 6),            // 40
        )
        assertEquals(77, Scoring.lessonScore(history))
        assertEquals(null, Scoring.lessonScore(emptyList()))
        assertEquals(NextAction.REEXPLAIN, Advisor.forLesson(59).action)
        assertEquals(NextAction.CONSOLIDATE, Advisor.forLesson(60).action)
        assertEquals(NextAction.CONSOLIDATE, Advisor.forLesson(77).action)
        assertEquals(NextAction.EXTRA_CHECK, Advisor.forLesson(80).action)
        assertEquals(NextAction.EXTRA_CHECK, Advisor.forLesson(89).action)
        assertEquals(NextAction.ADVANCE, Advisor.forLesson(90).action)
        assertEquals(NextAction.ADVANCE, Advisor.forLesson(100).action)
        // Пороги настраиваются.
        assertEquals(NextAction.REEXPLAIN, Advisor.forLesson(65, Thresholds(reexplain = 70, consolidate = 85, extraCheck = 95)).action)
        assertTrue(Advisor.forLesson(77).details.contains("77 %"))
    }

    @Test fun reviewHistoryFollowsIntervals() {
        // Каждый раз повторяем точно в срок и успешно: 1, 3, 7, 14, 30.
        var item: ReviewItemEntity? = null
        var day = 100L
        val intervals = mutableListOf<Int>()
        repeat(5) {
            item = ReviewScheduler.onPractice(item, "s", PracticeResult(true, 0, day))!!
            intervals += item!!.intervalDays
            day = item!!.dueEpochDay
        }
        assertEquals(listOf(1, 3, 7, 14, 30), intervals)
        // Ошибка на повторении — интервал сокращается на шаг (30 → 14), успех снова его растит.
        item = ReviewScheduler.onPractice(item, "s", PracticeResult(false, 0, day))!!
        assertEquals(14, item!!.intervalDays)
        item = ReviewScheduler.onPractice(item, "s", PracticeResult(true, 0, item!!.dueEpochDay))!!
        assertEquals(30, item!!.intervalDays)
        // Перерыв не наказывается: просроченное на 40 дней повторение просто считается от дня практики.
        val late = item!!.dueEpochDay + 40
        item = ReviewScheduler.onPractice(item, "s", PracticeResult(true, 0, late))!!
        assertEquals(late + item!!.intervalDays, item!!.dueEpochDay)
    }

    @Test fun diagnosticNeedsContinuousConfirmation() {
        assertEquals(0, Diagnostic.confirmedPrefix(emptyList()))
        assertEquals(2, Diagnostic.confirmedPrefix(listOf(listOf(true), listOf(true, true), listOf(false), listOf(true))))
        assertEquals(0, Diagnostic.confirmedPrefix(listOf(listOf(true, false), listOf(true))))
        assertEquals(0, Diagnostic.confirmedPrefix(listOf(emptyList(), listOf(true))))
        assertEquals(3, Diagnostic.confirmedPrefix(List(3) { listOf(true) }))
    }

    @Test fun diagnosticAnswerCheck() {
        assertTrue(Diagnostic.answerMatches("8\n10\n", "8\n10"))
        assertTrue(Diagnostic.answerMatches("8\n10\n", "  8  \r\n10  \n\n"))
        assertTrue(!Diagnostic.answerMatches("8\n10\n", "10\n8"))
        assertTrue(!Diagnostic.answerMatches("8\n", ""))
        assertTrue(!Diagnostic.answerMatches("Привет, мир\n", "Привет,мир"))
        // Правила те же, что в проверке заданий: текст целиком без пробелов по краям.
        assertTrue(Diagnostic.answerMatches("  ПРИВЕТ\n", "ПРИВЕТ"))
    }

    @Test fun studyDaysSpreadOverWeek() {
        assertEquals(listOf(0L, 1, 2, 3, 4, 5, 6), WeeklyPlanner.studyDays(0, 7))
        assertEquals(listOf(10L, 12, 14), WeeklyPlanner.studyDays(10, 3))
        assertEquals(5, WeeklyPlanner.studyDays(0, 5).distinct().size)
        assertTrue(WeeklyPlanner.studyDays(0, 5).all { it in 0..6 })
    }

    @Test fun weeklyPlanFillsSessionsInOrder() {
        val lessons = listOf(
            LessonWork("l1", "Первый", theoryMinutes = 10, practiceMinutes = 30),
            LessonWork("l2", "Второй", theoryMinutes = 10, practiceMinutes = 30),
            LessonWork("l3", "Третий", theoryMinutes = 10, practiceMinutes = 30),
        )
        // Срок 4 навыков — день 1 (не учебный): они переносятся на день 2.
        val plan = WeeklyPlanner.plan(0, 60, 3, lessons) { from, to -> if (from != null && 1L in from..to) 4 else 0 }
        assertEquals(3, plan.size)
        // День 1: весь первый урок (10 + 30) и начало второго (20 мин).
        assertEquals(listOf(PlanKind.THEORY, PlanKind.PRACTICE, PlanKind.THEORY, PlanKind.PRACTICE), plan[0].items.map { it.kind })
        assertEquals(60, plan[0].minutes)
        // День 2: сначала повторение, потом продолжение.
        assertEquals(PlanKind.REVIEW, plan[1].items.first().kind)
        assertEquals(11, plan[1].items.first().minutes) // 4 × 3 = 12, но не больше ~10 % занятия (6 + 5)
        assertTrue(plan.all { it.minutes <= 60 })
        // Порядок уроков не нарушается, каждая минута урока запланирована ровно один раз.
        val planned = plan.flatMap { it.items }.filter { it.lessonKey != null }
        assertEquals(listOf("l1", "l2", "l3"), planned.map { it.lessonKey }.distinct())
        assertEquals(120, planned.sumOf { it.minutes })
        // Практика занимает основную часть учебного времени (ориентир ТЗ 60–70 %).
        val practice = planned.filter { it.kind == PlanKind.PRACTICE }.sumOf { it.minutes }.toDouble() / planned.sumOf { it.minutes }
        assertTrue(practice in 0.6..0.8)
    }

    @Test fun planWhenCourseDoneSuggestsReview() {
        val plan = WeeklyPlanner.plan(0, 30, 2, emptyList()) { _, _ -> 0 }
        assertTrue(plan.all { d -> d.items.single().kind == PlanKind.REVIEW })
    }

    @Test fun repeatedSuccessRaisesScoreAndAdvanceNeedsPassCriteria() {
        val peeked = listOf(a("x", 1, true, hints = 6))
        assertEquals(40, Scoring.assignmentScore(peeked))
        assertEquals(90, Scoring.assignmentScore(peeked + a("x", 5, true)))
        assertEquals(40, Scoring.assignmentScore(peeked + a("x", 5, true, hints = 4)))
        // Одно идеально решённое задание из трёх нужных — ещё не «можно идти дальше».
        assertEquals(NextAction.EXTRA_CHECK, Advisor.forLesson(100, solved = 1, required = 3).action)
        assertEquals(NextAction.ADVANCE, Advisor.forLesson(100, solved = 3, required = 3).action)
        assertEquals(NextAction.REEXPLAIN, Advisor.forLesson(40, solved = 1, required = 3).action)
    }

    @Test fun zeroMinuteParts() {
        val plan = WeeklyPlanner.plan(0, 60, 1, listOf(LessonWork("l", "Л", theoryMinutes = 0, practiceMinutes = 20))) { _, _ -> 0 }
        assertEquals(listOf(PlanKind.PRACTICE, PlanKind.REVIEW), plan[0].items.map { it.kind })
    }

    @Test fun lessonEstimate() {
        val w = WeeklyPlanner.estimate("k", "Т", audioMinutes = 4.0, assignments = 4)
        assertEquals(9, w.theoryMinutes)
        assertEquals(32, w.practiceMinutes)
    }
}
