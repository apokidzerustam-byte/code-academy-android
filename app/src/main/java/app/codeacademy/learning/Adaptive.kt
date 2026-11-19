package app.codeacademy.learning

/**
 * Адаптивная методика (раздел 10 ТЗ): оценка урока по попыткам, рекомендация по порогам,
 * диагностика для опытных, недельный план. Только чистая логика — проверяется unit-тестами
 * на фиксированных историях.
 */

/** Попытка в виде, нужном для оценки (без кода и прочих полей БД). */
data class AttemptLite(
    val assignmentId: String,
    val startedAt: Long,
    val passed: Boolean,
    val hintsUsed: Int,
    val durationMs: Long = 0,
)

object Scoring {
    /** Подсказка 6-й ступени = показано решение. */
    const val SOLUTION_HINT = 6

    /**
     * Балл за задание 0–100. Учитываются точность (решено ли), попытки до решения,
     * подсказки и самостоятельность (просмотр решения). Не решено — 0.
     *  - решено с первой попытки без подсказок — 100;
     *  - каждая неудачная попытка до решения — −10 (не больше −30);
     *  - подсказки сверх двух первых (намёк и направление бесплатны) — −10 за ступень;
     *  - после просмотра решения балл не выше 40.
     */
    fun assignmentScore(attempts: List<AttemptLite>): Int {
        if (attempts.isEmpty()) return 0
        val sorted = attempts.sortedBy { it.startedAt }
        val firstPass = sorted.indexOfFirst { it.passed }
        if (firstPass < 0) return 0
        val upToPass = sorted.subList(0, firstPass + 1)
        val maxHints = upToPass.maxOf { it.hintsUsed }
        var score = 100 - minOf(firstPass, 3) * 10 - maxOf(0, maxHints - 2) * 10
        if (maxHints >= SOLUTION_HINT) score = minOf(score, 40)
        return score.coerceIn(0, 100)
    }

    /** Балл урока — среднее по заданиям, к которым ученик приступал; null — ещё не приступал. */
    fun lessonScore(attempts: List<AttemptLite>): Int? {
        val byTask = attempts.groupBy { it.assignmentId }
        if (byTask.isEmpty()) return null
        return byTask.values.map { assignmentScore(it) }.average().let { Math.round(it).toInt() }
    }
}

/** Рекомендация после заданий урока. */
data class Recommendation(val action: NextAction, val title: String, val details: String)

object Advisor {
    fun forLesson(score: Int, t: Thresholds = Thresholds()): Recommendation = when (SkillRules.nextAction(score, t)) {
        NextAction.REEXPLAIN -> Recommendation(
            NextAction.REEXPLAIN, "Стоит пересмотреть объяснение",
            "Результат $score %. Посмотрите урок ещё раз и откройте конспект, затем вернитесь к заданиям.",
        )
        NextAction.CONSOLIDATE -> Recommendation(
            NextAction.CONSOLIDATE, "Закрепим тему",
            "Результат $score %. Решите оставшиеся задания урока — лучше без подсказок.",
        )
        NextAction.EXTRA_CHECK -> Recommendation(
            NextAction.EXTRA_CHECK, "Почти готово: дополнительная проверка",
            "Результат $score %. Решите ещё одно задание без подсказок, чтобы подтвердить понимание.",
        )
        NextAction.ADVANCE -> Recommendation(
            NextAction.ADVANCE, "Можно идти дальше",
            "Результат $score %. Переходите к следующему уроку — эта тема вернётся на повторении через день.",
        )
    }
}

object Diagnostic {
    /** Ответ на «что выведет программа» — как в проверке заданий: построчно, без пробелов в конце строк. */
    fun answerMatches(expected: String, given: String): Boolean {
        fun norm(t: String) = t.replace("\r\n", "\n").trim().lines().map { it.trimEnd() }
        return given.isNotBlank() && norm(expected) == norm(given)
    }

    /**
     * Сколько уроков подряд с начала курса подтверждено диагностикой. Пропуск возможен только
     * по непрерывной цепочке: ошибка в уроке k означает, что уроки после k тоже нужно пройти
     * (они опираются на k). Для подтверждения урока нужны все его вопросы.
     */
    fun confirmedPrefix(answersByLesson: List<List<Boolean>>): Int {
        var n = 0
        for (answers in answersByLesson) {
            if (answers.isEmpty() || !answers.all { it }) break
            n++
        }
        return n
    }
}

enum class PlanKind { REVIEW, THEORY, PRACTICE }

data class PlanItem(val kind: PlanKind, val minutes: Int, val title: String, val lessonKey: String? = null)

data class DayPlan(val epochDay: Long, val items: List<PlanItem>) {
    val minutes get() = items.sumOf { it.minutes }
}

/** Оценка работы по уроку: объяснение (видео + конспект) и практика. */
data class LessonWork(val lessonKey: String, val title: String, val theoryMinutes: Int, val practiceMinutes: Int)

object WeeklyPlanner {
    /** Длительность занятия: 30, 60 (рекомендуется) или 90 минут. */
    val SESSION_OPTIONS = listOf(30, 60, 90)
    private const val REVIEW_MIN_PER_SKILL = 3

    /**
     * Дни занятий равномерно по неделе, начиная с сегодняшнего: 3 дня — через день и т. п.
     * Пропущенный день не наказывается: план просто строится заново от сегодняшнего дня.
     */
    fun studyDays(startEpochDay: Long, daysPerWeek: Int): List<Long> {
        val d = daysPerWeek.coerceIn(1, 7)
        return (0 until d).map { i -> startEpochDay + (i * 7) / d }
    }

    /**
     * План на неделю. Доли ТЗ: ~10 % — повторение, остальное — объяснение и практика
     * (практика естественно занимает 60–70 %, потому что у урока она длиннее объяснения).
     * Урок можно разбивать между днями: объяснение одного дня, практика — следующего.
     */
    fun plan(
        startEpochDay: Long,
        sessionMinutes: Int,
        daysPerWeek: Int,
        lessons: List<LessonWork>,
        dueReviewsByDay: (Long) -> Int,
    ): List<DayPlan> {
        val queue = ArrayDeque<Pair<LessonWork, PlanKind>>()
        lessons.forEach { queue.add(it to PlanKind.THEORY); queue.add(it to PlanKind.PRACTICE) }
        // Сколько минут текущей части урока ещё осталось.
        var remaining = queue.firstOrNull()?.let { (l, k) -> if (k == PlanKind.THEORY) l.theoryMinutes else l.practiceMinutes } ?: 0
        val days = studyDays(startEpochDay, daysPerWeek)
        return days.map { day ->
            val items = mutableListOf<PlanItem>()
            var budget = sessionMinutes
            val due = dueReviewsByDay(day)
            if (due > 0) {
                val reviewMinutes = (due * REVIEW_MIN_PER_SKILL).coerceIn(5, maxOf(5, sessionMinutes / 10 + 5))
                items += PlanItem(PlanKind.REVIEW, reviewMinutes, "Повторение: навыков $due")
                budget -= reviewMinutes
            }
            while (budget >= 5 && queue.isNotEmpty()) {
                val (lesson, kind) = queue.first()
                val take = minOf(budget, remaining)
                val title = (if (kind == PlanKind.THEORY) "Урок: " else "Практика: ") + lesson.title
                items += PlanItem(kind, take, title, lesson.lessonKey)
                budget -= take
                remaining -= take
                if (remaining <= 0) {
                    queue.removeFirst()
                    remaining = queue.firstOrNull()?.let { (l, k) -> if (k == PlanKind.THEORY) l.theoryMinutes else l.practiceMinutes } ?: 0
                }
            }
            if (queue.isEmpty() && budget >= 10 && items.none { it.kind == PlanKind.REVIEW }) {
                items += PlanItem(PlanKind.REVIEW, minOf(budget, 15), "Повторение слабых тем")
            }
            DayPlan(day, mergeAdjacent(items))
        }
    }

    private fun mergeAdjacent(items: List<PlanItem>): List<PlanItem> {
        val out = mutableListOf<PlanItem>()
        for (i in items) {
            val last = out.lastOrNull()
            if (last != null && last.kind == i.kind && last.lessonKey == i.lessonKey) out[out.lastIndex] = last.copy(minutes = last.minutes + i.minutes)
            else out += i
        }
        return out
    }

    /** Оценка объёма урока: объяснение = озвучка × 1,5 + 3 мин на конспект; практика = 8 мин на задание. */
    fun estimate(lessonKey: String, title: String, audioMinutes: Double, assignments: Int) = LessonWork(
        lessonKey, title,
        theoryMinutes = (audioMinutes * 1.5 + 3).toInt().coerceAtLeast(5),
        practiceMinutes = (assignments * 8).coerceAtLeast(8),
    )
}
