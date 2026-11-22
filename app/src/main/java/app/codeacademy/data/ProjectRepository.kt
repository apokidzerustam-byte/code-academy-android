package app.codeacademy.data

import androidx.room.withTransaction
import app.codeacademy.runner.ProjectFiles
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

data class ProjectInfo(
    val id: String,
    val title: String,
    val updatedAt: Long,
    val fileCount: Int,
    /** Учебный проект, из которого создан ("packId/projectId"), или null — свой проект. */
    val course: String? = null,
)

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
                fileCount = files.count { it.path !in META_FILES && !it.path.endsWith("/.keep") },
                course = files.firstOrNull { it.path == COURSE }?.content?.trim()?.ifBlank { null },
            )
        }.sortedByDescending { it.updatedAt }
    }

    fun filesFlow(id: String): Flow<Map<String, String>> =
        db.projects().filesFlow(id).map { rows -> rows.filter { it.path !in META_FILES }.associate { it.path to it.content } }

    suspend fun files(id: String): Map<String, String> =
        db.projects().files(id).filter { it.path !in META_FILES }.associate { it.path to it.content }

    /** Учебный проект, к которому привязан проект ученика ("packId/projectId"). */
    suspend fun courseOf(id: String): String? =
        db.projects().files(id).firstOrNull { it.path == COURSE }?.content?.trim()?.ifBlank { null }

    /** Проект ученика для учебного проекта: уже начатый или новый (с файлами первого этапа). */
    suspend fun startCourse(courseKey: String, title: String, starter: Map<String, String>): String = db.withTransaction {
        val existing = db.projects().allFilesOnce().firstOrNull { it.path == COURSE && it.content.trim() == courseKey }
        if (existing != null) return@withTransaction existing.projectId
        val id = newId()
        val now = clock()
        db.projects().upsert(ProjectFileEntity(id, META, title.trim().ifBlank { "Проект" }, now))
        db.projects().upsert(ProjectFileEntity(id, COURSE, courseKey, now))
        for ((path, text) in starter) db.projects().upsert(ProjectFileEntity(id, ProjectFiles.safeRel(path), text, now))
        id
    }

    /** Добавляет файлы нового этапа; то, что ученик уже написал, не трогается. Возвращает добавленные пути. */
    suspend fun addMissingFiles(id: String, files: Map<String, String>): List<String> = db.withTransaction {
        val have = db.projects().files(id).map { it.path }.toSet()
        val now = clock()
        files.filterKeys { ProjectFiles.safeRel(it) !in have }.map { (path, text) ->
            ProjectFiles.safeRel(path).also { db.projects().upsert(ProjectFileEntity(id, it, text, now)) }
        }
    }

    /** Новый проект из архива ZIP (файлы проверены и прочитаны заранее). */
    suspend fun importFiles(title: String, files: Map<String, String>): String {
        val id = newId()
        val now = clock()
        db.withTransaction {
            db.projects().upsert(ProjectFileEntity(id, META, title.trim().ifBlank { "Проект" }, now))
            for ((path, text) in files) db.projects().upsert(ProjectFileEntity(id, path, text, now))
        }
        return id
    }

    private fun newId() = "p" + clock().toString(36) + (1000..9999).random()

    /** Новый проект из шаблона: python, web, sql или kotlin. */
    suspend fun create(title: String, template: String = "python"): String {
        val id = newId()
        val now = clock()
        val files = TEMPLATES[template] ?: TEMPLATES.getValue("python")
        db.withTransaction {
            db.projects().upsert(ProjectFileEntity(id, META, title.trim().ifBlank { "Проект" }, now))
            for ((path, text) in files) db.projects().upsert(ProjectFileEntity(id, path, text, now))
        }
        return id
    }

    suspend fun rename(id: String, title: String) =
        db.projects().upsert(ProjectFileEntity(id, META, title.trim().ifBlank { "Проект" }, clock()))

    suspend fun delete(id: String) = db.projects().deleteProject(id)

    suspend fun saveFile(id: String, path: String, content: String) {
        val rel = ProjectFiles.safeRel(path)
        require(rel !in META_FILES) { "Служебное имя" }
        db.projects().upsert(ProjectFileEntity(id, rel, content, clock()))
    }

    suspend fun deleteFile(id: String, path: String) = db.projects().deleteFile(id, path)

    /** Заменяет файлы проекта (после запуска программы или команд терминала); название сохраняется. */
    suspend fun replaceAll(id: String, files: Map<String, String>) = db.withTransaction {
        val now = clock()
        val current = db.projects().files(id).associateBy { it.path }
        for (path in current.keys) if (path !in META_FILES && path !in files) db.projects().deleteFile(id, path)
        for ((path, text) in files) {
            if (path in META_FILES) continue
            if (current[path]?.content != text) db.projects().upsert(ProjectFileEntity(id, path, text, now))
        }
    }

    companion object {
        const val META = ".project"
        /** Связь с учебным проектом: "packId/projectId". */
        const val COURSE = ".course"
        val META_FILES = setOf(META, COURSE)
        const val TEMPLATE = "# Мой проект\nname = input(\"Как вас зовут? \")\nprint(\"Привет,\", name)\n"

        val KOTLIN_WORKFLOW = """name: Kotlin
on: [push, workflow_dispatch]
jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with: { distribution: temurin, java-version: "17" }
      - name: Установить kotlinc
        run: |
          curl -sSLo kotlinc.zip https://github.com/JetBrains/kotlin/releases/download/v2.1.20/kotlin-compiler-2.1.20.zip
          unzip -q kotlinc.zip
      - name: Собрать
        run: ./kotlinc/bin/kotlinc *.kt -include-runtime -d app.jar
      - name: Запустить
        run: java -jar app.jar
"""

        val KOTLIN_README = """# Проект на Kotlin

В телефоне приложение проверяет синтаксис Kotlin. Собрать и запустить программу
можно бесплатно в GitHub Actions (нужен аккаунт на github.com).

С телефона:
1. На github.com нажмите «+» → «New repository», введите имя, «Create repository».
2. «Add file» → «Create new file». Имя: Main.kt. Скопируйте сюда текст Main.kt из проекта.
   Нажмите «Commit changes».
3. Снова «Add file» → «Create new file». Имя: .github/workflows/kotlin.yml
   Скопируйте текст файла .github/workflows/kotlin.yml из проекта. «Commit changes».
4. Вкладка «Actions» → запуск «Kotlin» → шаг «Запустить»: там вывод программы.

С компьютера проще: «Экспорт ZIP» в проекте, распакуйте архив и загрузите все файлы
(включая папку .github) через «Add file» → «Upload files».
"""

        /** Шаблоны проектов: имя → файлы. */
        val TEMPLATES: Map<String, Map<String, String>> = mapOf(
            "python" to mapOf("main.py" to TEMPLATE),
            "web" to mapOf(
                "index.html" to """<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <title>Моя страница</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <h1>Привет!</h1>
  <button id="btn">Нажми меня</button>
  <p id="out"></p>
  <script src="script.js"></script>
</body>
</html>
""",
                "style.css" to "body {\n  font-family: sans-serif;\n  margin: 16px;\n}\n\nh1 {\n  color: #3949ab;\n}\n",
                "script.js" to "let clicks = 0\ndocument.getElementById('btn').addEventListener('click', () => {\n  clicks++\n  document.getElementById('out').textContent = 'Нажатий: ' + clicks\n  console.log('клик', clicks)\n})\n",
            ),
            "sql" to mapOf(
                "schema.sql" to "-- Таблицы и данные: выполняются перед каждым запуском другого .sql файла\nCREATE TABLE users (\n  id INTEGER PRIMARY KEY,\n  name TEXT NOT NULL,\n  age INTEGER\n);\n\nINSERT INTO users (name, age) VALUES\n  ('Анна', 20),\n  ('Борис', 31),\n  ('Вера', 17);\n",
                "query.sql" to "SELECT name, age\nFROM users\nWHERE age >= 18\nORDER BY age;\n",
            ),
            "kotlin" to mapOf(
                "Main.kt" to "fun main() {\n    val name = \"Мир\"\n    println(\"Привет, \$name!\")\n}\n",
                // Компилятора Kotlin в телефоне нет: проект собирается и запускается в GitHub Actions.
                ".github/workflows/kotlin.yml" to KOTLIN_WORKFLOW,
                "README.md" to KOTLIN_README,
            ),
        )
    }
}
