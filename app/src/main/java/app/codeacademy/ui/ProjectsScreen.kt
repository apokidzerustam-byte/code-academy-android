package app.codeacademy.ui

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.FilterChip
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.compose.material3.AssistChip
import androidx.compose.material3.OutlinedButton
import androidx.compose.runtime.LaunchedEffect
import app.codeacademy.content.CourseProject
import app.codeacademy.content.ProjectRef
import app.codeacademy.data.ProjectInfo
import app.codeacademy.data.ProjectZip
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.text.DateFormat
import java.util.Date

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun ProjectsScreen(onBack: () -> Unit, openProject: (String) -> Unit) {
    val c = LocalContainer.current
    val scope = rememberCoroutineScope()
    val projects by c.projects.projects.collectAsStateWithLifecycle(emptyList())
    var creating by remember { mutableStateOf(false) }
    var deleting by remember { mutableStateOf<ProjectInfo?>(null) }
    var message by remember { mutableStateOf<String?>(null) }
    var course by remember { mutableStateOf<List<Pair<ProjectRef, CourseProject>>>(emptyList()) }
    LaunchedEffect(Unit) { course = runCatching { c.content.allProjects() }.getOrDefault(emptyList()) }
    val attempts by c.progress.attempts.collectAsStateWithLifecycle(emptyList())
    val passed = remember(attempts) {
        attempts.filter { it.passed && it.lessonKey.startsWith("project:") }
            .groupBy({ it.lessonKey.removePrefix("project:") }, { it.assignmentId }).mapValues { it.value.toSet() }
    }
    val context = androidx.compose.ui.platform.LocalContext.current
    // Импорт проекта из ZIP (например, экспортированного раньше или скачанного с GitHub).
    val importZip = androidx.activity.compose.rememberLauncherForActivityResult(
        androidx.activity.result.contract.ActivityResultContracts.OpenDocument(),
    ) { uri ->
        if (uri != null) scope.launch {
            val name = runCatching {
                context.contentResolver.query(uri, arrayOf(android.provider.OpenableColumns.DISPLAY_NAME), null, null, null)
                    ?.use { if (it.moveToFirst()) it.getString(0) else null }
            }.getOrNull()?.removeSuffix(".zip")?.ifBlank { null } ?: "Импортированный проект"
            val res = withContext(Dispatchers.IO) {
                runCatching {
                    val r = context.contentResolver.openInputStream(uri)?.use { ProjectZip.readWithReport(it) }
                        ?: throw java.io.IOException("не удалось открыть файл")
                    c.projects.importFiles(name, r.files) to r
                }
            }
            val ok = res.getOrNull()
            if (ok != null) {
                val sk = ok.second.skipped
                message = "Проект «$name» импортирован: файлов ${ok.second.files.size}." +
                    (if (sk.isNotEmpty()) " Пропущены не текстовые файлы (${sk.size}): ${sk.take(5).joinToString()}" + (if (sk.size > 5) "…" else "") else "")
                withContext(Dispatchers.Main.immediate) { openProject(ok.first) }
            } else {
                message = "Импорт не удался: ${res.exceptionOrNull()?.message}"
            }
        }
    }

    Screen("Проекты", onBack) { padding ->
        LazyColumn(
            Modifier.padding(padding).testTag("projects-list"), contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            item {
                FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Button(onClick = { creating = true }, modifier = Modifier.testTag("new-project")) { Text("Новый проект") }
                    OutlinedButton(onClick = { importZip.launch(arrayOf("application/zip", "application/x-zip-compressed", "application/octet-stream")) },
                        modifier = Modifier.testTag("import-project")) { Text("Импорт ZIP") }
                }
            }
            message?.let { m -> item { Text(m, modifier = Modifier.testTag("projects-message")) } }
            if (course.isNotEmpty()) {
                item { Text("Учебные проекты", style = MaterialTheme.typography.titleLarge) }
                items(course, key = { it.first.key }) { (ref, cp) ->
                    val done = passed[ref.key].orEmpty().count { id -> cp.milestones.any { it.id == id } }
                    val started = projects.firstOrNull { it.course == ref.key }
                    Card(Modifier.fillMaxWidth().testTag("course-${ref.projectId}")) {
                        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                Text(cp.title, style = MaterialTheme.typography.titleMedium, modifier = Modifier.weight(1f))
                                AssistChip(onClick = {}, label = { Text(if (cp.isThrough) "Сквозной" else "Мини-проект") })
                            }
                            Text(cp.summary, style = MaterialTheme.typography.bodyMedium)
                            Text(
                                if (done == cp.milestones.size) "Все этапы пройдены ✓ (${cp.milestones.size})"
                                else "Этапов: ${cp.milestones.size}, пройдено: $done",
                                style = MaterialTheme.typography.bodySmall,
                            )
                            Button(onClick = {
                                scope.launch {
                                    // Новый проект после удаления старого: этапы уже могли быть пройдены. Тогда берём
                                    // СОБСТВЕННЫЙ код ученика из последнего пройденного этапа (снимок в попытке),
                                    // а файлы этапов — только недостающие.
                                    val done = passed[ref.key].orEmpty()
                                    val upTo = currentMilestone(cp, done) ?: (cp.milestones.size - 1)
                                    val own = cp.milestones.take(upTo + 1).lastOrNull { it.id in done }
                                        ?.let { c.progress.passedSnapshot(ref, it.id) }.orEmpty()
                                    val starter = cp.milestones.take(upTo + 1).fold(own) { acc, m ->
                                        acc + m.starterFiles.filterKeys { it !in acc }
                                    }
                                    val id = started?.id ?: c.projects.startCourse(ref.key, cp.title, starter)
                                    withContext(Dispatchers.Main.immediate) { openProject(id) }
                                }
                            }, modifier = Modifier.testTag("start-${ref.projectId}")) { Text(if (started != null) "Продолжить" else "Начать") }
                        }
                    }
                }
            }
            item { Text("Мои проекты", style = MaterialTheme.typography.titleLarge) }
            val own = projects
            if (own.isEmpty()) item { Text("Проектов пока нет. Создайте свой или начните учебный проект выше.") }
            items(own, key = { it.id }) { p ->
                Card(Modifier.fillMaxWidth().clickable { openProject(p.id) }.testTag("project-${p.title}")) {
                    Row(Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
                        Column(Modifier.weight(1f)) {
                            Text(p.title, style = MaterialTheme.typography.titleMedium)
                            Text(
                                (if (p.course != null) "Учебный проект · " else "") +
                                    "Файлов: ${p.fileCount} · изменён ${DateFormat.getDateTimeInstance(DateFormat.SHORT, DateFormat.SHORT).format(Date(p.updatedAt))}",
                                style = MaterialTheme.typography.bodySmall,
                            )
                        }
                        TextButton(onClick = { deleting = p }) { Text("Удалить") }
                    }
                }
            }
        }
    }

    if (creating) {
        var title by remember { mutableStateOf("") }
        var template by remember { mutableStateOf("python") }
        AlertDialog(
            onDismissRequest = { creating = false },
            title = { Text("Новый проект") },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedTextField(title, { title = it }, label = { Text("Название") }, singleLine = true,
                        modifier = Modifier.testTag("project-title"))
                    Text("Шаблон", style = MaterialTheme.typography.labelLarge)
                    FlowRow(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                        for ((id, name) in listOf("python" to "Python", "web" to "Веб-страница", "sql" to "SQL", "kotlin" to "Kotlin")) {
                            FilterChip(selected = template == id, onClick = { template = id }, label = { Text(name) },
                                modifier = Modifier.testTag("template-$id"))
                        }
                    }
                }
            },
            confirmButton = {
                TextButton(onClick = {
                    creating = false
                    scope.launch {
                        val id = c.projects.create(title, template)
                        // Навигация — строго в главном потоке (после транзакции Room продолжение может прийти из другого).
                        withContext(Dispatchers.Main.immediate) { openProject(id) }
                    }
                }, modifier = Modifier.testTag("create-project")) { Text("Создать") }
            },
            dismissButton = { TextButton(onClick = { creating = false }) { Text("Отмена") } },
        )
    }
    deleting?.let { p ->
        AlertDialog(
            onDismissRequest = { deleting = null },
            title = { Text("Удалить «${p.title}»?") },
            text = { Text("Все файлы проекта будут удалены без возможности восстановления." +
                (if (p.course != null) " Пройденные этапы учебного проекта сохранятся, но код придётся начать заново." else "")) },
            confirmButton = {
                TextButton(onClick = { deleting = null; scope.launch { c.projects.delete(p.id) } }) { Text("Удалить") }
            },
            dismissButton = { TextButton(onClick = { deleting = null }) { Text("Отмена") } },
        )
    }
}
