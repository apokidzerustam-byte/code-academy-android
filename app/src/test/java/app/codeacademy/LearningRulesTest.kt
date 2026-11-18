package app.codeacademy

import app.codeacademy.data.SkillStateEntity
import app.codeacademy.data.SkillStatus
import app.codeacademy.learning.NextAction
import app.codeacademy.learning.PracticeResult
import app.codeacademy.learning.ReviewScheduler
import app.codeacademy.learning.SkillRules
import app.codeacademy.learning.Thresholds
import org.junit.Assert.assertEquals
import org.junit.Test

class LearningRulesTest {

    private fun ok(day: Long, hints: Int = 0, review: Boolean = false) = PracticeResult(true, hints, day, review)
    private fun fail(day: Long) = PracticeResult(false, 0, day)

    @Test fun intervalsFollowSpec() {
        var item = ReviewScheduler.schedule(null, "s", ok(100))
        val seen = mutableListOf(item.intervalDays)
        repeat(4) { item = ReviewScheduler.schedule(item, "s", ok(item.dueEpochDay)); seen += item.intervalDays }
        assertEquals(listOf(1, 3, 7, 14, 30), seen)
    }

    @Test fun intervalsGrowBeyond30ButAreCapped() {
        assertEquals(60, ReviewScheduler.intervalFor(5))
        assertEquals(120, ReviewScheduler.intervalFor(6))
        assertEquals(180, ReviewScheduler.intervalFor(10))
    }

    @Test fun failureStepsBackButNeverBelowOneDay() {
        var item = ReviewScheduler.schedule(null, "s", ok(0))
        item = ReviewScheduler.schedule(item, "s", ok(1))      // 3 дня
        item = ReviewScheduler.schedule(item, "s", fail(4))    // назад к 1
        assertEquals(1, item.intervalDays)
        item = ReviewScheduler.schedule(item, "s", fail(5))
        assertEquals(1, item.intervalDays)
        assertEquals(6L, item.dueEpochDay)
    }

    @Test fun heavyHintsKeepInterval() {
        var item = ReviewScheduler.schedule(null, "s", ok(0))
        item = ReviewScheduler.schedule(item, "s", ok(1))           // 3
        item = ReviewScheduler.schedule(item, "s", ok(4, hints = 3)) // остаётся 3
        assertEquals(3, item.intervalDays)
        item = ReviewScheduler.schedule(item, "s", ok(7, hints = 2)) // растёт до 7
        assertEquals(7, item.intervalDays)
    }

    @Test fun thresholdsMatchSpec() {
        assertEquals(NextAction.REEXPLAIN, SkillRules.nextAction(59))
        assertEquals(NextAction.CONSOLIDATE, SkillRules.nextAction(60))
        assertEquals(NextAction.CONSOLIDATE, SkillRules.nextAction(79))
        assertEquals(NextAction.EXTRA_CHECK, SkillRules.nextAction(80))
        assertEquals(NextAction.EXTRA_CHECK, SkillRules.nextAction(89))
        assertEquals(NextAction.ADVANCE, SkillRules.nextAction(90))
        assertEquals(NextAction.REEXPLAIN, SkillRules.nextAction(69, Thresholds(reexplain = 70)))
    }

    @Test fun oneSuccessIsNotMastery() {
        val s = SkillRules.apply(SkillStateEntity("s"), ok(10), 0)
        assertEquals(SkillStatus.LEARNING, s.status)
        val same = SkillRules.apply(s, ok(10), 0) // тот же день не считается вторым
        assertEquals(SkillStatus.LEARNING, same.status)
    }

    @Test fun masteryThenConfirmationAfterSevenDays() {
        var s = SkillRules.apply(SkillStateEntity("s"), ok(10), 0)
        s = SkillRules.apply(s, ok(11), 0)
        assertEquals(SkillStatus.MASTERED, s.status)
        assertEquals(11L, s.masteredEpochDay)
        s = SkillRules.apply(s, ok(15, review = true), 0)  // рано
        assertEquals(SkillStatus.MASTERED, s.status)
        s = SkillRules.apply(s, ok(18, review = true), 0)
        assertEquals(SkillStatus.CONFIRMED, s.status)
    }

    @Test fun lowAccuracyBlocksMastery() {
        var s = SkillStateEntity("s")
        s = SkillRules.apply(s, fail(1), 0)
        s = SkillRules.apply(s, fail(1), 0)
        s = SkillRules.apply(s, ok(1), 0)
        s = SkillRules.apply(s, ok(2), 0)  // 2 дня, но точность 50 %
        assertEquals(SkillStatus.LEARNING, s.status)
    }

    @Test fun failingMasteredSkillNeedsReview() {
        var s = SkillRules.apply(SkillStateEntity("s"), ok(1), 0)
        s = SkillRules.apply(s, ok(2), 0)
        s = SkillRules.apply(s, fail(3), 0)
        assertEquals(SkillStatus.NEEDS_REVIEW, s.status)
    }
}
