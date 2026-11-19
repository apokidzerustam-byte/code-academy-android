package app.codeacademy.data

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.Query
import androidx.room.Upsert
import kotlinx.coroutines.flow.Flow

@Dao
interface ProgressDao {
    @Query("SELECT * FROM lesson_progress")
    fun all(): Flow<List<LessonProgressEntity>>

    @Query("SELECT * FROM lesson_progress WHERE lessonKey = :key")
    suspend fun get(key: String): LessonProgressEntity?

    @Query("SELECT * FROM lesson_progress WHERE status != 'NOT_STARTED' ORDER BY updatedAt DESC LIMIT 1")
    fun lastActive(): Flow<LessonProgressEntity?>

    @Upsert
    suspend fun upsert(p: LessonProgressEntity)
}

@Dao
interface AttemptDao {
    @Insert
    suspend fun insert(a: AttemptEntity): Long

    @Query("SELECT * FROM attempt WHERE lessonKey = :lessonKey ORDER BY startedAt DESC")
    fun forLesson(lessonKey: String): Flow<List<AttemptEntity>>

    @Query("SELECT DISTINCT assignmentId FROM attempt WHERE lessonKey = :lessonKey AND passed = 1")
    suspend fun passedAssignments(lessonKey: String): List<String>

    @Query("SELECT COUNT(*) FROM attempt")
    fun count(): Flow<Int>

    @Query("SELECT * FROM attempt ORDER BY startedAt")
    fun all(): Flow<List<AttemptEntity>>

    @Query("SELECT COUNT(*) FROM attempt WHERE passed = 1")
    fun passedCount(): Flow<Int>

    @Query("SELECT COALESCE(SUM(hintsUsed), 0) FROM attempt")
    fun hintsTotal(): Flow<Int>

    @Query("SELECT errorType AS type, COUNT(*) AS n FROM attempt WHERE errorType IS NOT NULL GROUP BY errorType ORDER BY n DESC LIMIT 5")
    fun topErrors(): Flow<List<ErrorCount>>
}

data class ErrorCount(val type: String, val n: Int)

@Dao
interface SkillDao {
    @Query("SELECT * FROM skill_state")
    fun all(): Flow<List<SkillStateEntity>>

    @Query("SELECT * FROM skill_state WHERE skillId = :id")
    suspend fun get(id: String): SkillStateEntity?

    @Upsert
    suspend fun upsert(s: SkillStateEntity)
}

@Dao
interface ReviewDao {
    @Query("SELECT * FROM review_item WHERE dueEpochDay <= :today ORDER BY dueEpochDay")
    fun due(today: Long): Flow<List<ReviewItemEntity>>

    @Query("SELECT * FROM review_item WHERE skillId = :id")
    suspend fun get(id: String): ReviewItemEntity?

    @Query("SELECT * FROM review_item ORDER BY dueEpochDay")
    fun all(): Flow<List<ReviewItemEntity>>

    @Upsert
    suspend fun upsert(r: ReviewItemEntity)
}

@Dao
interface ActivityDao {
    @Query("SELECT * FROM daily_activity WHERE epochDay = :day")
    suspend fun get(day: Long): DailyActivityEntity?

    @Query("SELECT * FROM daily_activity WHERE epochDay >= :fromDay ORDER BY epochDay")
    fun since(fromDay: Long): Flow<List<DailyActivityEntity>>

    @Upsert
    suspend fun upsert(a: DailyActivityEntity)
}

@Dao
interface DraftDao {
    @Query("SELECT * FROM draft WHERE `key` = :key")
    suspend fun get(key: String): DraftEntity?

    @Upsert
    suspend fun upsert(d: DraftEntity)
}

@Dao
interface ProjectDao {
    @Query("SELECT * FROM project_file ORDER BY projectId, path")
    fun allFiles(): Flow<List<ProjectFileEntity>>

    @Query("SELECT * FROM project_file WHERE projectId = :id ORDER BY path")
    suspend fun files(id: String): List<ProjectFileEntity>

    @Query("SELECT * FROM project_file WHERE projectId = :id ORDER BY path")
    fun filesFlow(id: String): Flow<List<ProjectFileEntity>>

    @Upsert
    suspend fun upsert(f: ProjectFileEntity)

    @Query("DELETE FROM project_file WHERE projectId = :id AND path = :path")
    suspend fun deleteFile(id: String, path: String)

    @Query("DELETE FROM project_file WHERE projectId = :id")
    suspend fun deleteProject(id: String)
}
