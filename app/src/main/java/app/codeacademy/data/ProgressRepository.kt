package app.codeacademy.data

import app.codeacademy.assessment.Verdict
import app.codeacademy.content.Lesson
import app.codeacademy.content.LessonRef
import app.codeacademy.learning.PracticeResult
import app.codeacademy.learning.ReviewScheduler
import app.codeacademy.learning.SkillRules
import androidx.room.withTransaction
import kotlinx.coroutines.flow.Flow
import java.time.LocalDate

/** Прогресс ученика: уроки, попытки, навыки, повторения, активность. */
class ProgressRepository(private val db: AppDatabase, private val clock: () -> Long = System::currentTimeMillis) {

    private fun today(): Long = LocalDate.now().toEpochDay()

    val lessons: Flow<List<LessonProgressEntity>> = db.progress().all()
    val lastActive: Flow<LessonProgressEntity?> = db.progress().lastActive()
    val skills: Flow<List<SkillStateEntity>> = db.skills().all()
    val attempts: Flow<List<AttemptEntity>> = db.attempts().all()
    val reviews: Flow<List<ReviewItemEntity>> = db.reviews().all()
    fun attemptsFor(ref: LessonRef): Flow<List<AttemptEntity>> = db.attempts().forLesson(ref.key)

    /**
     * Уроки, подтверждённые диагностикой: отмечаются как пройденные, а их навыки — «изучаются»
     * с повторением уже завтра. Так пропуск возможен, но освоение подтверждается практикой.
     */
    suspend fun testOut(lessons: List<Pair<LessonRef, Lesson>>) = db.withTransaction {
        val now = clock()
        val tomorrow = today() + 1
        for ((ref, lesson) in lessons) {
            val cur = db.progress().get(ref.key) ?: LessonProgressEntity(ref.key)
            if (!LessonStatus.isDone(cur.status)) {
                db.progress().upsert(cur.copy(status = LessonStatus.TESTED_OUT, passedAt = now, updatedAt = now))
            }
            for (skill in lesson.skills) {
                val s = db.skills().get(skill) ?: SkillStateEntity(skill)
                if (s.status == SkillStatus.NOT_STUDIED) db.skills().upsert(s.copy(status = SkillStatus.LEARNING, lastPracticedAt = now))
                if (db.reviews().get(skill) == null) {
                    db.reviews().upsert(ReviewItemEntity(skill, step = 0, intervalDays = 1, dueEpochDay = tomorrow, lastResult = "TEST"))
                }
            }
        }
    }
    fun dueReviews(): Flow<List<ReviewItemEntity>> = db.reviews().due(today())
    val attemptsCount: Flow<Int> = db.attempts().count()
    val passedCount: Flow<Int> = db.attempts().passedCount()
    val hintsTotal: Flow<Int> = db.attempts().hintsTotal()
    val topErrors: Flow<List<ErrorCount>> = db.attempts().topErrors()
    fun activitySince(days: Long): Flow<List<DailyActivityEntity>> = db.activity().since(today() - days)

    suspend fun openLesson(ref: LessonRef) = db.withTransaction {
        val now = clock()
        val cur = db.progress().get(ref.key) ?: LessonProgressEntity(ref.key)
        db.progress().upsert(
            cur.copy(
                status = if (cur.status == LessonStatus.NOT_STARTED) LessonStatus.IN_PROGRESS else cur.status,
                startedAt = cur.startedAt ?: now,
                updatedAt = now,
            )
        )
    }

    suspend fun lessonProgress(ref: LessonRef): LessonProgressEntity? = db.progress().get(ref.key)

    /** positionMs — позиция на общей шкале урока (LessonTimeline). */
    suspend fun saveScene(ref: LessonRef, sceneIndex: Int, positionMs: Long) = db.withTransaction {
        val cur = db.progress().get(ref.key) ?: LessonProgressEntity(ref.key, status = LessonStatus.IN_PROGRESS)
        db.progress().upsert(cur.copy(sceneIndex = sceneIndex, scenePositionMs = positionMs, updatedAt = clock()))
    }

    suspend fun addActiveTime(ref: LessonRef?, ms: Long) {
        if (ms <= 0) return
        db.withTransaction { addActiveTimeTx(ref, ms) }
    }

    private suspend fun addActiveTimeTx(ref: LessonRef?, ms: Long) {
        val day = today()
        val a = db.activity().get(day) ?: DailyActivityEntity(day)
        db.activity().upsert(a.copy(activeMs = a.activeMs + ms))
        if (ref != null) {
            db.progress().get(ref.key)?.let { db.progress().upsert(it.copy(timeSpentMs = it.timeSpentMs + ms)) }
        }
    }

    suspend fun draft(key: String): DraftEntity? = db.drafts().get(key)

    suspend fun saveDraft(key: String, content: String, hintsShown: Int) =
        db.drafts().upsert(DraftEntity(key, content, hintsShown, clock()))

    /**
     * Записывает попытку, обновляет навыки урока и расписание повторений,
     * отмечает урок пройденным при выполнении критериев.
     */
    suspend fun recordAttempt(
        ref: LessonRef,
        lesson: Lesson,
        assignmentId: String,
        code: String,
        verdict: Verdict,
        hintsUsed: Int,
        startedAt: Long,
        runner: String,
    ) = db.withTransaction {
        val now = clock()
        val day = today()
        db.attempts().insert(
            AttemptEntity(
                lessonKey = ref.key, assignmentId = assignmentId, startedAt = startedAt,
                durationMs = now - startedAt, code = code, passed = verdict.passed,
                testsPassed = verdict.report?.passed ?: 0, testsTotal = verdict.report?.total ?: 0,
                hintsUsed = hintsUsed, errorType = verdict.errorType, runner = runner,
            )
        )
        for (skill in lesson.skills) {
            val review = db.reviews().get(skill)
            val result = PracticeResult(verdict.passed, hintsUsed, day, isReview = ReviewScheduler.isDue(review, day))
            val s = db.skills().get(skill) ?: SkillStateEntity(skill)
            db.skills().upsert(SkillRules.apply(s, result, now))
            ReviewScheduler.onPractice(review, skill, result)?.let { db.reviews().upsert(it) }
            if (result.isReview) {
                val a = db.activity().get(day) ?: DailyActivityEntity(day)
                db.activity().upsert(a.copy(reviewsDone = a.reviewsDone + 1))
            }
        }
        if (verdict.passed) {
            val a = db.activity().get(day) ?: DailyActivityEntity(day)
            db.activity().upsert(a.copy(tasksSolved = a.tasksSolved + 1))
        }
        val passed = db.attempts().passedAssignments(ref.key).size
        if (passed >= lesson.passCriteria.minAssignmentsPassed) {
            val cur = db.progress().get(ref.key) ?: LessonProgressEntity(ref.key)
            if (cur.status != LessonStatus.PASSED) {
                db.progress().upsert(cur.copy(status = LessonStatus.PASSED, passedAt = now, updatedAt = now))
            }
        } else {
            db.progress().get(ref.key)?.let { db.progress().upsert(it.copy(updatedAt = now)) }
        }
    }

    suspend fun passedAssignments(ref: LessonRef): List<String> = db.attempts().passedAssignments(ref.key)
}
