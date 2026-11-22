package app.codeacademy.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.key
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp
import app.codeacademy.assessment.Verdict
import app.codeacademy.content.CourseProject
import app.codeacademy.content.ProjectRef
import app.codeacademy.runner.CodeRunner
import app.codeacademy.runner.RunStatus
import app.codeacademy.settings.Settings
import kotlinx.coroutines.launch
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive

/** Предел снимка проекта в попытке: строки таблицы должны помещаться в окно курсора Android (2 МБ). */
const val MAX_SNAPSHOT_CHARS = 400_000

/** Номер текущего этапа: первый не пройденный; null — все пройдены. */
fun currentMilestone(project: CourseProject, passed: Set<String>): Int? =
    project.milestones.indexOfFirst { it.id !in passed }.takeIf { it >= 0 }

/**
 * Задание этапа учебного проекта над редактором IDE: условие, подсказки, «Проверить этап»,
 * переход к следующему этапу (его новые файлы добавляются, код ученика не трогается).
 */
@OptIn(ExperimentalLayoutApi::class)
@Composable
fun ProjectTaskPanel(
    projectId: String,
    courseKey: String,
    settings: Settings,
    files: () -> Map<String, String>,
    /** Сохранить файлы перед проверкой. */
    save: suspend (Map<String, String>) -> Unit,
    onFilesAdded: (Map<String, String>) -> Unit,
    enabled: Boolean,
) {
    val c = LocalContainer.current
    val scope = rememberCoroutineScope()
    val ref = remember(courseKey) { ProjectRef.parse(courseKey) }
    var project by remember { mutableStateOf<CourseProject?>(null) }
    var passed by remember { mutableStateOf<Set<String>?>(null) }
    var loadError by remember { mutableStateOf<String?>(null) }
    var expanded by rememberSaveable { mutableStateOf(true) }
    LaunchedEffect(courseKey) {
        if (ref == null) { loadError = "Учебный проект не найден"; return@LaunchedEffect }
        val loaded = runCatching { c.content.project(ref) }.getOrNull()
        if (loaded == null) { loadError = "Учебный проект «$courseKey» не найден в установленных пакетах"; return@LaunchedEffect }
        val done = c.progress.passedMilestones(ref)
        // Этап мог быть пройден, а «Дальше» не нажато: файлы текущего этапа добавляются при открытии.
        currentMilestone(loaded, done)?.let { i ->
            val starter = loaded.milestones[i].starterFiles
            val added = c.projects.addMissingFiles(projectId, starter)
            if (added.isNotEmpty()) onFilesAdded(starter.filterKeys { it in added })
        }
        project = loaded
        passed = done
    }
    loadError?.let { Text(it, color = MaterialTheme.colorScheme.error); return }
    val p = project ?: return
    val done = passed ?: return
    val idx = currentMilestone(p, done)
    val kindTitle = if (p.isThrough) "Сквозной проект" else "Мини-проект"

    Card(Modifier.fillMaxWidth().testTag("project-task"), colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.secondaryContainer)) {
        Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text("$kindTitle · этапов пройдено: ${done.count { id -> p.milestones.any { it.id == id } }} из ${p.milestones.size}",
                style = MaterialTheme.typography.labelLarge)
            if (idx == null) {
                Text("Проект завершён ✓", style = MaterialTheme.typography.titleMedium, modifier = Modifier.testTag("project-done"))
                Text(if (p.isThrough) "Следующие этапы появятся вместе с новыми разделами курса. Проект можно продолжать развивать самостоятельно."
                     else "Можно улучшать проект дальше или экспортировать его в ZIP.")
                return@Column
            }
            val m = p.milestones[idx]
            key(m.id) {
                var hints by rememberSaveable { mutableStateOf(0) }
                var solution by rememberSaveable { mutableStateOf(false) }
                var verdict by remember { mutableStateOf<Verdict?>(null) }
                var busy by remember { mutableStateOf(false) }
                var runner by remember { mutableStateOf<CodeRunner?>(null) }
                val startedAt = remember { System.currentTimeMillis() }

                Text("Этап ${idx + 1} из ${p.milestones.size}. ${m.title}", style = MaterialTheme.typography.titleMedium,
                    modifier = Modifier.testTag("milestone-title"))
                TextButton(onClick = { expanded = !expanded }) { Text(if (expanded) "Скрыть условие" else "Показать условие") }
                if (expanded) {
                    MarkdownText(m.statement)
                    Text("Цель: ${m.goal}", style = MaterialTheme.typography.bodySmall)
                }
                FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Button(enabled = enabled && !busy, onClick = {
                        scope.launch {
                            busy = true
                            val snapshot = files()
                            save(snapshot)
                            val lang = if (p.language == "python") "W" else p.language
                            val (name, r) = resolveRunner(c, settings.runner, lang)
                            runner = r
                            val v = c.assessment.evaluateProject(r, p.language, m.tests, snapshot, "check-$projectId")
                            // Не попытка: проверка не состоялась или в проекте нет нужного файла (ни одного теста не выполнено).
                            val counts = v.report?.let { it.total > 0 && (it.cases.isNotEmpty() || it.compileError != null) } ?: (v.failure == RunStatus.TIMEOUT)
                            if (counts) {
                                // Снимок проекта — только если он не слишком большой (строка БД должна читаться целиком).
                                val filesJson = JsonObject(snapshot.mapValues { JsonPrimitive(it.value) }).toString()
                                    .takeIf { it.length <= MAX_SNAPSHOT_CHARS } ?: "{}"
                                c.appScope.launch {
                                    c.progress.recordMilestone(ref!!, p.skills, m.id, filesJson, v, if (solution) 6 else hints, startedAt, name)
                                }.join()
                            }
                            verdict = v
                            runner = null
                            busy = false
                        }
                    }, modifier = Modifier.testTag("check-milestone")) { Text("Проверить этап") }
                    if (busy) {
                        OutlinedButton(onClick = { runner?.stop() }) { Text("Стоп") }
                        CircularProgressIndicator(Modifier.padding(4.dp))
                    }
                }
                verdict?.let { v ->
                    VerdictView(v, m.explanation)
                    if (v.passed) {
                        val next = p.milestones.getOrNull(idx + 1)
                        Button(onClick = {
                            scope.launch {
                                if (next != null) {
                                    val added = c.projects.addMissingFiles(projectId, next.starterFiles)
                                    if (added.isNotEmpty()) onFilesAdded(next.starterFiles.filterKeys { it in added })
                                }
                                passed = done + m.id
                            }
                        }, modifier = Modifier.testTag("next-milestone")) {
                            Text(if (next != null) "Дальше: этап ${idx + 2}. ${next.title}" else "Завершить проект")
                        }
                    }
                }
                Text("Подсказки", style = MaterialTheme.typography.labelLarge)
                for (i in 0 until hints) {
                    Text("${i + 1}. ${HINT_TITLES.getOrElse(i) { "Подсказка" }}: ${m.hints[i]}", style = MaterialTheme.typography.bodyMedium)
                }
                if (hints < m.hints.size) {
                    OutlinedButton(onClick = { hints++ }, modifier = Modifier.testTag("milestone-hint")) {
                        Text("Подсказка ${hints + 1} из ${m.hints.size + 1}: ${HINT_TITLES.getOrElse(hints) { "ещё подсказка" }}")
                    }
                } else if (!solution) {
                    OutlinedButton(onClick = { solution = true }) { Text("Подсказка ${m.hints.size + 1} из ${m.hints.size + 1}: пример решения") }
                } else {
                    Text("Пример решения (попробуйте сначала понять, а не копировать):", style = MaterialTheme.typography.labelLarge)
                    for ((path, text) in m.solutionFiles) {
                        Text(path, style = MaterialTheme.typography.labelMedium)
                        CodeBlock(text)
                    }
                }
                MentorPanel(
                    context = {
                        app.codeacademy.mentor.MentorContext(
                            task = app.codeacademy.mentor.MentorContent.task(p, idx),
                            code = files().entries.joinToString("\n") { (path, text) -> "# файл: $path\n$text" }.take(20_000),
                            error = mentorError(verdict, null), attempts = if (verdict != null) 1 else 0,
                            hintsShown = if (solution) m.hints.size else hints,
                        )
                    },
                    onHintRevealed = { level -> if (level > hints) hints = level.coerceAtMost(m.hints.size) },
                )
            }
        }
    }
}
