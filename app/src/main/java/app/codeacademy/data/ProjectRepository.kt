package app.codeacademy.data

import androidx.room.withTransaction
import app.codeacademy.runner.ProjectFiles
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

data class ProjectInfo(val id: String, val title: String, val updatedAt: Long, val fileCount: Int)

/**
 * Учебные проекты (ProjectManager). Хранятся в таблице project_file; название — в служебном файле
 * ".project" (не показывается ученику и не передаётся в песочницу). Новой таблицы и миграции не нужно.
 */
class ProjectRepository(private val db: AppDatabase, private val clock: () -> Long = System::currentTimeMillis) {

    val projects: Flow<List<ProjectInfo>> = db.projects().allFiles().map { rows ->
        rows.groupBy { it.projectId }.map { (id, files) ->
            ProjectInfo(
                id = id,
                title = files.firstOrNull { it.path == META }?.content?.ifBlank { null } ?: id,
                updatedAt = files.maxOf { it.updatedAt },
                fileCount = files.count { it.path != META && !it.path.endsWith("/.keep") },
            )
        }.sortedByDescending { it.updatedAt }
    }

    fun filesFlow(id: String): Flow<Map<String, String>> =
        db.projects().filesFlow(id).map { rows -> rows.filter { it.path != META }.associate { it.path to it.content } }

    suspend fun files(id: String): Map<String, String> =
        db.projects().files(id).filter { it.path != META }.associate { it.path to it.content }

    suspend fun create(title: String): String {
        val id = "p" + clock().toString(36) + (1000..9999).random()
        val now = clock()
        db.withTransaction {
            db.projects().upsert(ProjectFileEntity(id, META, title.trim().ifBlank { "Проект" }, now))
            db.projects().upsert(ProjectFileEntity(id, "main.py", TEMPLATE, now))
        }
        return id
    }

    suspend fun rename(id: String, title: String) =
        db.projects().upsert(ProjectFileEntity(id, META, title.trim().ifBlank { "Проект" }, clock()))

    suspend fun delete(id: String) = db.projects().deleteProject(id)

    suspend fun saveFile(id: String, path: String, content: String) {
        val rel = ProjectFiles.safeRel(path)
        require(rel != META) { "Служебное имя" }
        db.projects().upsert(ProjectFileEntity(id, rel, content, clock()))
    }

    suspend fun deleteFile(id: String, path: String) = db.projects().deleteFile(id, path)

    /** Заменяет файлы проекта (после запуска программы или команд терминала); название сохраняется. */
    suspend fun replaceAll(id: String, files: Map<String, String>) = db.withTransaction {
        val now = clock()
        val current = db.projects().files(id).associateBy { it.path }
        for (path in current.keys) if (path != META && path !in files) db.projects().deleteFile(id, path)
        for ((path, text) in files) {
            if (path == META) continue
            if (current[path]?.content != text) db.projects().upsert(ProjectFileEntity(id, path, text, now))
        }
    }

    companion object {
        const val META = ".project"
        const val TEMPLATE = "# Мой проект\nname = input(\"Как вас зовут? \")\nprint(\"Привет,\", name)\n"
    }
}
