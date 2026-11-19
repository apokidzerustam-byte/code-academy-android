package app.codeacademy.data

import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey

object LessonStatus {
    const val NOT_STARTED = "NOT_STARTED"
    const val IN_PROGRESS = "IN_PROGRESS"
    const val PASSED = "PASSED"
    /** Подтверждён диагностикой; закрепляется повторением (освоение не подтверждается одним тестом). */
    const val TESTED_OUT = "TESTED_OUT"

    fun isDone(status: String?) = status == PASSED || status == TESTED_OUT
}

object SkillStatus {
    const val NOT_STUDIED = "NOT_STUDIED"
    const val LEARNING = "LEARNING"
    const val NEEDS_REVIEW = "NEEDS_REVIEW"
    const val MASTERED = "MASTERED"
    const val CONFIRMED = "CONFIRMED"
}

/** Ключ урока — "packId/lessonId". */
@Entity(tableName = "lesson_progress")
data class LessonProgressEntity(
    @PrimaryKey val lessonKey: String,
    val status: String = LessonStatus.NOT_STARTED,
    val sceneIndex: Int = 0,
    val scenePositionMs: Long = 0,
    val startedAt: Long? = null,
    val passedAt: Long? = null,
    val timeSpentMs: Long = 0,
    val updatedAt: Long = 0,
)

@Entity(tableName = "attempt", indices = [Index("lessonKey"), Index("assignmentId")])
data class AttemptEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val lessonKey: String,
    val assignmentId: String,
    val startedAt: Long,
    val durationMs: Long,
    val code: String,
    val passed: Boolean,
    val testsPassed: Int,
    val testsTotal: Int,
    val hintsUsed: Int,
    val errorType: String?,
    val runner: String,
)

@Entity(tableName = "skill_state")
data class SkillStateEntity(
    @PrimaryKey val skillId: String,
    val status: String = SkillStatus.NOT_STUDIED,
    val attempts: Int = 0,
    val successes: Int = 0,
    val successDays: Int = 0,
    val lastSuccessEpochDay: Long? = null,
    val masteredEpochDay: Long? = null,
    val lastPracticedAt: Long? = null,
) {
    val accuracy: Double get() = if (attempts == 0) 0.0 else successes.toDouble() / attempts
}

@Entity(tableName = "review_item", indices = [Index("dueEpochDay")])
data class ReviewItemEntity(
    @PrimaryKey val skillId: String,
    val step: Int,
    val intervalDays: Int,
    val dueEpochDay: Long,
    val lastResult: String? = null,
)

@Entity(tableName = "daily_activity")
data class DailyActivityEntity(
    @PrimaryKey val epochDay: Long,
    val activeMs: Long = 0,
    val tasksSolved: Int = 0,
    val reviewsDone: Int = 0,
)

@Entity(tableName = "project_file", primaryKeys = ["projectId", "path"])
data class ProjectFileEntity(
    val projectId: String,
    val path: String,
    val content: String,
    val updatedAt: Long,
)

/** Черновик кода задания: автосохранение, чтобы после закрытия приложения продолжить с того же места. */
@Entity(tableName = "draft")
data class DraftEntity(
    @PrimaryKey val key: String,
    val content: String,
    val hintsShown: Int,
    val updatedAt: Long,
)
