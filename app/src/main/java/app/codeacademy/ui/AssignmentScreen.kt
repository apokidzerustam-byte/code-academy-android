package app.codeacademy.ui

import android.os.SystemClock
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.unit.dp
import app.codeacademy.AppContainer
import app.codeacademy.assessment.Verdict
import app.codeacademy.content.Assignment
import app.codeacademy.content.Lesson
import app.codeacademy.content.LessonRef
import app.codeacademy.runner.CodeRunner
import app.codeacademy.runner.RunResult
import app.codeacademy.runner.RunStatus
import app.codeacademy.runner.WebRunner
import app.codeacademy.settings.RunnerMode
import app.codeacademy.settings.Settings
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive

internal val HINT_TITLES = listOf("Намёк", "Направление", "Концепция", "Где искать", "Алгоритм")

/**
 * W по умолчанию; в режиме AUTO при недоступном W — переход на A. Задания «предскажи результат»
 * проверяются Python-песочницей при любом языке урока (код не выполняется — сравнивается текст).
 */
suspend fun resolveRunner(c: AppContainer, mode: RunnerMode, lessonRunner: String, answerTask: Boolean = false): Pair<String, CodeRunner> {
    val lr = if (answerTask && lessonRunner in WebRunner.LANGS) "W" else lessonRunner
    val first = c.runner(mode, lr)
    if (first.first == "W" && mode == RunnerMode.AUTO && first.second.prepare()?.pythonStarted != true) {
        return c.runner(mode, lr, wAvailable = false)
    }
    return first
}

/**
 * Исполнитель задания: веб-задания несут свой язык (в уроке JavaScript бывает задание со страницей HTML),
 * остальные — язык урока.
 */
fun assignmentRunner(a: app.codeacademy.content.Assignment, lessonRunner: String): String {
    val t = a.tests
    val kind = (t["kind"] as? kotlinx.serialization.json.JsonPrimitive)?.content
    if (kind == "web") return (t["lang"] as? kotlinx.serialization.json.JsonPrimitive)?.content ?: "html"
    return lessonRunner
}

/** Язык подсветки редактора для языка урока. */
fun editorLanguage(lessonRunner: String): String = when (lessonRunner) {
    "html" -> "html"
    "js" -> "javascript"
    "sql" -> "sql"
    "kotlin" -> "kotlin"
    else -> "python"
}

/** Как называется исполнитель на экране. */
fun runnerTitle(name: String): String = when (name) {
    "W" -> "Режим выполнения: изолированный (W)"
    "A" -> "Режим выполнения: ограниченный (A)"
    "html", "js" -> "Выполнение: песочница браузера, без интернета"
    "sql" -> "Выполнение: SQLite в песочнице, новая база при каждом запуске"
    "kotlin" -> "Kotlin: проверка синтаксиса и устройства кода (запуск — через GitHub Actions)"
    else -> name
}

/** Таблицы и данные для запуска SQL-задания — из первого открытого теста. */
private fun sqlSetup(a: Assignment): String =
    runCatching {
        a.tests["cases"]!!.jsonArray.map { it.jsonObject }.firstOrNull { it["hidden"]?.jsonPrimitive?.contentOrNull != "true" }
            ?.get("setup")?.jsonPrimitive?.contentOrNull
    }.getOrNull().orEmpty()

private fun formatOutput(r: RunResult): String = buildString {
    if (r.status != RunStatus.OK) append("[${statusText(r.status)}]\n")
    append(r.stdout)
    if (r.stderr.isNotBlank()) append(if (r.stdout.isEmpty() || r.stdout.endsWith("\n")) "" else "\n").append(r.stderr)
    if (r.truncated) append("\n(вывод обрезан)")
}.ifBlank { "(программа ничего не вывела)" }

private fun JsonElement?.show(): String = when (this) {
    null -> "—"
    is JsonPrimitive -> contentOrNull ?: toString()
    else -> toString()
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun AssignmentScreen(
    ref: LessonRef,
    index: Int,
    settings: Settings,
    onBack: () -> Unit,
    openAssignment: (LessonRef, Int) -> Unit = { _, _ -> },
    openLesson: (LessonRef) -> Unit = {},
) {
    val course = rememberCourse()
    val c = LocalContainer.current
    val scope = rememberCoroutineScope()
    var lesson by remember { mutableStateOf<Lesson?>(null) }
    var a by remember { mutableStateOf<Assignment?>(null) }
    // rememberSaveable: при пересоздании экрана код берётся из сохранённого состояния, а не из более старого черновика в БД.
    var code by rememberSaveable { mutableStateOf("") }
    var restored by rememberSaveable { mutableStateOf(false) }
    var loaded by remember { mutableStateOf(false) }
    var hintsShown by remember { mutableStateOf(0) }
    var solutionShown by remember { mutableStateOf(false) }
    var askSolution by remember { mutableStateOf(false) }
    var busy by remember { mutableStateOf<String?>(null) }
    var output by remember { mutableStateOf<String?>(null) }
    var verdict by remember { mutableStateOf<Verdict?>(null) }
    var attempts by remember { mutableStateOf(0) }
    var runnerName by remember { mutableStateOf("") }
    var activeRunner by remember { mutableStateOf<CodeRunner?>(null) }
    val preview = remember { WebPreviewController() }
    var showPreview by remember { mutableStateOf(false) }
    val draftKey = "${ref.key}/$index"
    val startedAt = remember { System.currentTimeMillis() }

    LaunchedEffect(ref, index) {
        lesson = c.content.lesson(ref)
        val asg = c.content.assignments(ref)[index]
        a = asg
        val d = c.progress.draft(draftKey)
        if (!restored) {
            code = d?.content ?: if (asg.isAnswerTask) "" else asg.starterCode.orEmpty()
            restored = true
        }
        hintsShown = d?.hintsShown?.coerceAtMost(asg.hints.size) ?: 0
        solutionShown = (d?.hintsShown ?: 0) >= 6
        loaded = true
    }
    // Автосохранение черновика (раздел 6 ТЗ).
    LaunchedEffect(code, hintsShown, solutionShown) {
        if (!loaded) return@LaunchedEffect
        delay(600)
        c.progress.saveDraft(draftKey, code, if (solutionShown) 6 else hintsShown)
    }
    DisposableEffect(ref) {
        val t0 = SystemClock.elapsedRealtime()
        onDispose { c.appScope.launch { c.progress.addActiveTime(ref, SystemClock.elapsedRealtime() - t0) } }
    }
    // Черновик сохраняется и при уходе с экрана/пересоздании, а не только по таймеру.
    val latestCode = rememberUpdatedState(code)
    val latestHints = rememberUpdatedState(if (solutionShown) 6 else hintsShown)
    DisposableEffect(draftKey) {
        onDispose {
            if (loaded) {
                val text = latestCode.value
                val hints = latestHints.value
                c.appScope.launch { c.progress.saveDraft(draftKey, text, hints) }
            }
        }
    }

    val asg = a
    Screen(asg?.title ?: "Задание", onBack) { padding ->
        if (asg == null || lesson == null) return@Screen
        Column(
            Modifier.padding(padding).imePadding().padding(16.dp).verticalScroll(rememberScrollState()),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Text(assignmentTypeName(asg.type), style = MaterialTheme.typography.labelLarge)
            MarkdownText(asg.statement)
            if (asg.constraints.isNotEmpty()) {
                Text("Ограничения: " + asg.constraints.joinToString(" "), style = MaterialTheme.typography.bodySmall)
            }
            asg.code?.let { CodeBlock(it) }

            if (asg.isAnswerTask) {
                OutlinedTextField(
                    value = code,
                    onValueChange = { code = it },
                    label = { Text(if (asg.type == "predict" || asg.type == "review") "Ваш ответ (каждая строка вывода — с новой строки)" else "Ваш ответ (команда — как в терминале)") },
                    textStyle = MaterialTheme.typography.bodyMedium.copy(fontFamily = FontFamily.Monospace),
                    modifier = Modifier.fillMaxWidth().heightIn(min = 140.dp).testTag("code"),
                )
            } else if (loaded) {
                CodeEditor(value = code, onValueChange = { code = it }, plain = settings.plainEditor, height = 240.dp,
                    readOnly = busy != null, language = editorLanguage(assignmentRunner(asg, lesson!!.runner)))
            }

            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                if (!asg.isAnswerTask) {
                    OutlinedButton(enabled = busy == null, onClick = {
                        scope.launch {
                            busy = "Выполняется…"
                            val (name, runner) = resolveRunner(c, settings.runner, assignmentRunner(asg, lesson!!.runner))
                            runnerName = name
                            activeRunner = runner
                            val r = when {
                                // Страница видна ученику: запуск в предпросмотре, вывод кликов дописывается в консоль.
                                name == "html" -> {
                                    showPreview = true
                                    preview.onOutput = { _, text -> output = (output.orEmpty() + text).takeLast(20_000) }
                                    preview.run("html", code)
                                }
                                runner is WebRunner -> runner.runWith(code, 8_000, "", null, setup = if (name == "sql") sqlSetup(asg) else "")
                                else -> runner.run(code, if ("fastapi" in code) 20_000 else 5_000, "", "a-${asg.id}")
                            }
                            output = formatOutput(r)
                            activeRunner = null
                            busy = null
                        }
                    }, modifier = Modifier.testTag("run")) { Text("Запустить") }
                }
                Button(enabled = busy == null && code.isNotBlank(), onClick = {
                    scope.launch {
                        busy = "Проверка…"
                        val (name, runner) = resolveRunner(c, settings.runner, assignmentRunner(asg, lesson!!.runner), asg.isAnswerTask)
                        runnerName = name
                        activeRunner = runner
                        val submitted = code
                        val v = c.assessment.evaluate(runner, asg, submitted)
                        val used = if (solutionShown) 6 else hintsShown
                        if (v.failure == null || v.failure == RunStatus.TIMEOUT) {
                            // Запись в области приложения: не теряется, если ученик уйдёт с экрана.
                            c.appScope.launch {
                                c.progress.recordAttempt(ref, lesson!!, asg.id, submitted, v, used, startedAt, name)
                            }.join()
                        }
                        verdict = v
                        attempts++
                        activeRunner = null
                        busy = null
                    }
                }, modifier = Modifier.testTag("check")) { Text("Проверить") }
                if (busy != null) {
                    OutlinedButton(onClick = { activeRunner?.stop(); preview.stop() }, modifier = Modifier.testTag("stop")) { Text("Стоп") }
                    CircularProgressIndicator(Modifier.padding(4.dp))
                    Text(busy!!)
                }
            }
            if (runnerName.isNotEmpty()) {
                Text(
                    runnerTitle(runnerName),
                    style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.outline,
                )
            }
            if (showPreview) {
                Text("Страница", style = MaterialTheme.typography.titleSmall)
                WebPreview(preview, height = 300.dp)
            }
            output?.let {
                Text("Консоль", style = MaterialTheme.typography.titleSmall)
                CodeBlock(it, Modifier.testTag("console"))
            }
            verdict?.let { VerdictView(it, asg) }
            verdict?.takeIf { !it.passed }?.errorType?.let { et ->
                ErrorAdvice(et, lesson!!, course, ref, asg.id, openAssignment)
            }

            Text("Подсказки", style = MaterialTheme.typography.titleMedium)
            for (i in 0 until hintsShown) {
                Card(Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(12.dp)) {
                        Text("${i + 1}. ${HINT_TITLES.getOrElse(i) { "Подсказка" }}", style = MaterialTheme.typography.labelLarge)
                        Text(asg.hints[i])
                    }
                }
            }
            if (hintsShown < asg.hints.size) {
                OutlinedButton(onClick = { hintsShown++ }, modifier = Modifier.testTag("hint")) {
                    Text("Подсказка ${hintsShown + 1} из ${asg.hints.size + 1}: ${HINT_TITLES.getOrElse(hintsShown) { "ещё подсказка" }}")
                }
            } else if (!solutionShown) {
                OutlinedButton(onClick = { if (attempts > 0 || verdict != null) solutionShown = true else askSolution = true },
                    modifier = Modifier.testTag("solution")) { Text("Подсказка ${asg.hints.size + 1} из ${asg.hints.size + 1}: решение") }
            }
            if (solutionShown) {
                Text("Решение", style = MaterialTheme.typography.titleSmall)
                CodeBlock(asg.solution)
                Text(asg.explanation, style = MaterialTheme.typography.bodyMedium)
            }
            val l = lesson!!
            MentorPanel(
                context = {
                    app.codeacademy.mentor.MentorContext(
                        lesson = app.codeacademy.mentor.LessonLink(ref.packId, ref.lessonId, l.title),
                        lessonSkills = l.skills, commonMistakes = l.commonMistakes,
                        task = app.codeacademy.mentor.MentorContent.task(asg, assignmentRunner(asg, l.runner)),
                        code = code, error = mentorError(verdict, output), attempts = attempts,
                        hintsShown = if (solutionShown) asg.hints.size else hintsShown,
                    )
                },
                // Подсказка от наставника — та же ступень лестницы: учитывается в статистике.
                onHintRevealed = { level -> if (level > hintsShown) hintsShown = level.coerceAtMost(asg.hints.size) },
                openLesson = { openLesson(LessonRef(it.packId, it.lessonId)) },
            )
        }
    }

    if (askSolution) {
        AlertDialog(
            onDismissRequest = { askSolution = false },
            title = { Text("Показать решение?") },
            text = { Text("Вы ещё не отправляли решение. Попробуйте сначала сами — так навык закрепится лучше. Использование решения учитывается в статистике, но результат не обнуляет.") },
            confirmButton = { TextButton(onClick = { solutionShown = true; askSolution = false }) { Text("Показать") } },
            dismissButton = { TextButton(onClick = { askSolution = false }) { Text("Попробую сам") } },
        )
    }
}

private fun statusText(s: RunStatus) = when (s) {
    RunStatus.TIMEOUT -> "Превышено время выполнения — возможно, бесконечный цикл"
    RunStatus.STOPPED -> "Остановлено"
    RunStatus.CRASHED -> "Выполнение аварийно завершилось (например, не хватило памяти)"
    RunStatus.UNAVAILABLE -> "Исполнитель недоступен"
    RunStatus.SYNTAX_ERROR -> "Синтаксическая ошибка"
    RunStatus.ERROR -> "Ошибка"
    RunStatus.EXIT -> "Программа завершилась с кодом ошибки"
    RunStatus.OK -> "OK"
}

@Composable
private fun VerdictView(v: Verdict, asg: Assignment) = VerdictView(v, asg.explanation)

/** Результат проверки: задания и этапы учебных проектов. */
@Composable
internal fun VerdictView(v: Verdict, explanation: String) {
    val ok = v.passed
    Card(
        Modifier.fillMaxWidth().testTag("verdict"),
        colors = CardDefaults.cardColors(
            containerColor = if (ok) MaterialTheme.colorScheme.primaryContainer else MaterialTheme.colorScheme.errorContainer,
        ),
    ) {
        Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            val r = v.report
            when {
                v.failure != null -> Text("Проверка не завершена: ${statusText(v.failure)}. ${v.failureText}".trim())
                r == null -> Text("Нет результата проверки")
                r.compileError != null -> {
                    Text("Код не запускается — синтаксическая ошибка:", style = MaterialTheme.typography.titleSmall)
                    CodeBlock(r.compileError)
                }
                r.loadError != null -> {
                    Text("Ошибка при запуске кода:", style = MaterialTheme.typography.titleSmall)
                    CodeBlock(r.loadError)
                }
                r.kind == "answer" -> {
                    val lines = r.cases.filter { it.line != null }
                    val right = lines.count { it.passed }
                    Text(
                        if (ok) "Верно! Все строки совпали." else "Верных строк: $right из ${lines.size}",
                        style = MaterialTheme.typography.titleSmall,
                    )
                    r.cases.filter { !it.passed }.forEach { cs ->
                        val mine = cs.actual.show().takeIf { cs.actual != null && it != "null" }
                        if (cs.line != null) {
                            Text("Строка ${cs.line}: " + (mine?.let { "«$it»" } ?: "(нет в ответе)"),
                                style = MaterialTheme.typography.bodyLarge)
                        }
                        cs.hint?.let { Text("→ $it") }
                    }
                    if (ok) Text(explanation)
                }
                else -> {
                    Text(
                        if (ok) "Верно! Пройдено тестов: ${r.passed} из ${r.total}" else "Пройдено тестов: ${r.passed} из ${r.total}",
                        style = MaterialTheme.typography.titleSmall,
                    )
                    r.cases.filter { !it.passed }.forEach { cs ->
                        if (cs.hidden) {
                            Text("Скрытый тест не пройден." + (cs.hint?.let { " Подсказка: $it" } ?: ""))
                        } else {
                            cs.file?.let { Text("Файл: $it", style = MaterialTheme.typography.labelLarge) }
                            if (cs.input != null && cs.input.show().isNotBlank()) Text("Входные данные: ${cs.input.show()}")
                            if (cs.expected != null) {
                                Text("Ожидалось:")
                                CodeBlock(cs.expected.show())
                            }
                            if (cs.actual != null) {
                                Text("Получено:")
                                CodeBlock(cs.actual.show().ifEmpty { "(пусто)" })
                            }
                            cs.hint?.takeIf { it.isNotBlank() }?.let { Text("Подсказка: $it") }
                        }
                        cs.error?.let { CodeBlock(it) }
                    }
                    if (ok) Text(explanation)
                }
            }
            if (r != null && r.warnings.isNotEmpty()) {
                Text("Замечания (на оценку не влияют):", style = MaterialTheme.typography.labelLarge)
                r.warnings.take(8).forEach { Text("• $it", style = MaterialTheme.typography.bodySmall) }
            }
        }
    }
}

/** Ошибка → навык урока, где она разбирается (Error-Based Learning, раздел 10 ТЗ). */
private val ERROR_SKILL = mapOf(
    "SyntaxError" to "python.errors.syntax", "NameError" to "python.errors.name", "TypeError" to "python.errors.type",
    "ValueError" to "python.errors.value", "IndexError" to "python.errors.index", "IndentationError" to "python.errors.indentation",
)

/** Причина ошибки и упражнение, которое тренирует именно её. */
@Composable
private fun ErrorAdvice(
    errorType: String,
    lesson: Lesson,
    course: CourseData?,
    ref: LessonRef,
    currentId: String,
    open: (LessonRef, Int) -> Unit,
) {
    val skillLesson = ERROR_SKILL[errorType]?.let { course?.lessonOfSkill(it) }
    val mistake = lesson.commonMistakes.firstOrNull { it.errorType == errorType }
        ?: skillLesson?.lesson?.commonMistakes?.firstOrNull { it.errorType == errorType }
    val exercise = skillLesson?.let { cl ->
        cl.assignments.indexOfFirst { it.type == "fix" && !(cl.ref == ref && it.id == currentId) }.takeIf { it >= 0 }?.let { cl to it }
    }
    if (mistake == null && exercise == null) return
    Card(
        Modifier.fillMaxWidth().testTag("error-advice"),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.tertiaryContainer),
    ) {
        Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Text("Разбор ошибки $errorType", style = MaterialTheme.typography.titleSmall)
            mistake?.let {
                Text("Частая причина: ${it.mistake}", style = MaterialTheme.typography.bodyMedium)
                Text("Как исправить: ${it.fix}", style = MaterialTheme.typography.bodyMedium)
            }
            exercise?.let { (cl, i) ->
                OutlinedButton(onClick = { open(cl.ref, i) }, modifier = Modifier.testTag("error-exercise")) {
                    Text("Упражнение: ${cl.assignments[i].title}")
                }
            }
        }
    }
}

