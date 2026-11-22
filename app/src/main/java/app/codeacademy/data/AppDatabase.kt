package app.codeacademy.data

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase

@Database(
    entities = [
        LessonProgressEntity::class, AttemptEntity::class, SkillStateEntity::class,
        ReviewItemEntity::class, DailyActivityEntity::class, ProjectFileEntity::class, DraftEntity::class,
    ],
    version = 1,
    exportSchema = true,
)
abstract class AppDatabase : RoomDatabase() {
    abstract fun progress(): ProgressDao
    abstract fun attempts(): AttemptDao
    abstract fun skills(): SkillDao
    abstract fun reviews(): ReviewDao
    abstract fun activity(): ActivityDao
    abstract fun drafts(): DraftDao
    abstract fun projects(): ProjectDao

    companion object {
        const val NAME = "code_academy.db"

        fun create(context: Context, name: String = NAME): AppDatabase =
            Room.databaseBuilder(context, AppDatabase::class.java, name).build()

        fun inMemory(context: Context): AppDatabase =
            Room.inMemoryDatabaseBuilder(context, AppDatabase::class.java).build()
    }
}
