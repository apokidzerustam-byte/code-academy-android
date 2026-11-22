package app.codeacademy.mentor

import app.codeacademy.content.Assignment
import app.codeacademy.content.CourseProject
import app.codeacademy.content.Lesson
import app.codeacademy.content.Milestone
import kotlinx.serialization.json.JsonPrimitive

/** Перевод моделей курса в контекст наставника. */
object MentorContent {
    /** Язык по исполнителю урока/задания: W и A — Python. */
    fun language(runner: String): String = when (runner) {
        "html", "js", "sql", "kotlin" -> runner
        else -> "python"
    }

    fun mainFile(language: String) = when (language) {
        "html" -> "index.html"
        "js" -> "script.js"
        "sql" -> "query.sql"
        "kotlin" -> "Main.kt"
        else -> "main.py"
    }

    fun task(a: Assignment, runner: String): TaskContext {
        val lang = language(runner)
        val file = mainFile(lang)
        val expected = if (a.isAnswerTask) (a.tests["expected_answer"] as? JsonPrimitive)?.content ?: a.solution else null
        return TaskContext(
            id = a.id, title = a.title, statement = a.statement + "\n" + a.input + "\n" + a.expectedResult, type = a.type, language = lang,
            hints = a.hints,
            starterFiles = buildMap {
                a.starterCode?.let { put(file, it) }
                // В «предскажи» и «исправь» код задания виден ученику — он не раскрывает ответ.
                a.code?.let { put("task-code", it) }
            },
            solutionFiles = if (a.isAnswerTask) emptyMap() else mapOf(file to a.solution),
            expectedAnswer = expected,
        )
    }

    /**
     * Этап проекта. Видимые ученику файлы — заготовки этого этапа и решения предыдущих этапов
     * (их ученик уже написал сам); «новое» решение — только то, что добавляет этот этап.
     */
    fun task(p: CourseProject, index: Int): TaskContext {
        val m: Milestone = p.milestones[index]
        val earlier = p.milestones.take(index).flatMap { it.solutionFiles.entries + it.starterFiles.entries }
            .associate { it.key + "#prev" + it.value.hashCode() to it.value }
        return TaskContext(
            id = "${p.id}/${m.id}", title = "${p.title}: ${m.title}", statement = m.statement + "\n" + m.goal, type = "milestone",
            language = if (p.language == "html") "html" else "python", hints = m.hints,
            starterFiles = m.starterFiles + earlier, solutionFiles = m.solutionFiles,
        )
    }

    fun lessonDoc(packId: String, lesson: Lesson, notes: String, assignments: List<Assignment>) = LessonDoc(
        link = LessonLink(packId, lesson.id, lesson.title), skills = lesson.skills, notes = notes,
        commonMistakes = lesson.commonMistakes, assignments = assignments.map { Triple(it.id, it.type, it.title) },
    )
}
