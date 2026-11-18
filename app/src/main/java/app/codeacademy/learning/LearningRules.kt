package app.codeacademy.learning

import app.codeacademy.data.ReviewItemEntity
import app.codeacademy.data.SkillStateEntity
import app.codeacademy.data.SkillStatus

/** Результат одной попытки по навыку. */
data class PracticeResult(
    val passed: Boolean,
    /** Сколько ступеней подсказок открыто (0–6; 6 = показано решение). */
    val hintsUsed: Int,
    val epochDay: Long,
    val isReview: Boolean = false,
)

/**
 * Интервальное повторение (раздел 10 ТЗ): 1 → 3 → 7 → 14 → 30 дней.
 * Ошибка — шаг назад; успех с подсказками ≥ 3-й ступени — интервал не растёт;
 * подсказки учитываются, но не обнуляют результат.
 */
object ReviewScheduler {
    val INTERVALS = listOf(1, 3, 7, 14, 30)
    private const val MAX_INTERVAL = 180

    fun intervalFor(step: Int): Int =
        if (step < INTERVALS.size) INTERVALS[step]
        else (INTERVALS.last().toLong() shl (step - INTERVALS.size + 1)).coerceAtMost(MAX_INTERVAL.toLong()).toInt()

    fun schedule(current: ReviewItemEntity?, skillId: String, r: PracticeResult): ReviewItemEntity {
        val step = current?.step ?: -1
        val next = when {
            !r.passed -> (step - 1).coerceAtLeast(0)
            r.hintsUsed >= 3 -> step.coerceAtLeast(0)
            else -> step + 1
        }
        val interval = intervalFor(next)
        return ReviewItemEntity(
            skillId = skillId,
            step = next,
            intervalDays = interval,
            dueEpochDay = r.epochDay + interval,
            lastResult = if (r.passed) "PASS" else "FAIL",
        )
    }
}

/** Пороги адаптации (настраиваемые, раздел 10 ТЗ). */
data class Thresholds(val reexplain: Int = 60, val consolidate: Int = 80, val extraCheck: Int = 90)

enum class NextAction { REEXPLAIN, CONSOLIDATE, EXTRA_CHECK, ADVANCE }

object SkillRules {

    fun nextAction(accuracyPercent: Int, t: Thresholds = Thresholds()): NextAction = when {
        accuracyPercent < t.reexplain -> NextAction.REEXPLAIN
        accuracyPercent < t.consolidate -> NextAction.CONSOLIDATE
        accuracyPercent < t.extraCheck -> NextAction.EXTRA_CHECK
        else -> NextAction.ADVANCE
    }

    /**
     * «Освоено» — не по одному тесту: ≥ 2 успешных дня и точность ≥ 80 %.
     * «Подтверждено» — успешное повторение не раньше чем через 7 дней после освоения.
     */
    fun apply(s: SkillStateEntity, r: PracticeResult, now: Long): SkillStateEntity {
        val attempts = s.attempts + 1
        val successes = s.successes + if (r.passed) 1 else 0
        val newDay = r.passed && s.lastSuccessEpochDay != r.epochDay
        val successDays = s.successDays + if (newDay) 1 else 0
        val accuracy = successes.toDouble() / attempts
        var mastered = s.masteredEpochDay
        val status = when {
            !r.passed && (s.status == SkillStatus.MASTERED || s.status == SkillStatus.CONFIRMED) -> SkillStatus.NEEDS_REVIEW
            s.status == SkillStatus.MASTERED && r.passed && r.isReview &&
                mastered != null && r.epochDay - mastered >= 7 -> SkillStatus.CONFIRMED
            s.status == SkillStatus.CONFIRMED && r.passed -> SkillStatus.CONFIRMED
            successDays >= 2 && accuracy >= 0.8 -> {
                if (mastered == null || s.status == SkillStatus.NEEDS_REVIEW) mastered = r.epochDay
                SkillStatus.MASTERED
            }
            s.status == SkillStatus.NEEDS_REVIEW && !r.passed -> SkillStatus.NEEDS_REVIEW
            else -> SkillStatus.LEARNING
        }
        return s.copy(
            status = status,
            attempts = attempts,
            successes = successes,
            successDays = successDays,
            lastSuccessEpochDay = if (r.passed) r.epochDay else s.lastSuccessEpochDay,
            masteredEpochDay = mastered,
            lastPracticedAt = now,
        )
    }
}
