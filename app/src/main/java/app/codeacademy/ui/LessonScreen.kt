package app.codeacademy.ui

import android.os.SystemClock
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Tab
import androidx.compose.material3.TabRow
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import app.codeacademy.content.Assignment
import app.codeacademy.content.Lesson
import app.codeacademy.content.LessonRef
import app.codeacademy.content.Scenario
import app.codeacademy.data.LessonStatus
import kotlinx.coroutines.launch

private val TYPE_NAMES = mapOf(
    "write" to "Напиши сам", "complete" to "Дополни код", "fix" to "Найди ошибку", "predict" to "Предскажи результат",
    "optimize" to "Оптимизируй", "function" to "Напиши функцию", "multi_file" to "Несколько файлов",
    "review" to "Разбери код", "design" to "Спроектируй", "mini_project" to "Мини-проект",
)

fun assignmentTypeName(type: String) = TYPE_NAMES[type] ?: type

@Composable
fun LessonScreen(ref: LessonRef, onBack: () -> Unit, openAssignment: (Int) -> Unit) {
    val c = LocalContainer.current
    val scope = rememberCoroutineScope()
    var lesson by remember { mutableStateOf<Lesson?>(null) }
    var scenario by remember { mutableStateOf<Scenario?>(null) }
    var notes by remember { mutableStateOf("") }
    var assignments by remember { mutableStateOf<List<Assignment>>(emptyList()) }
    var passed by remember { mutableStateOf<List<String>>(emptyList()) }
    var tab by rememberSaveable { mutableStateOf(0) }
    val progress by c.progress.lessons.collectAsStateWithLifecycle(emptyList())
    val status = progress.firstOrNull { it.lessonKey == ref.key }?.status

    LaunchedEffect(ref) {
        lesson = c.content.lesson(ref)
        scenario = c.content.scenario(ref)
        notes = c.content.notes(ref)
        assignments = c.content.assignments(ref)
        c.progress.openLesson(ref)
    }
    LaunchedEffect(progress) { passed = c.progress.passedAssignments(ref) }
    DisposableEffect(ref) {
        val t0 = SystemClock.elapsedRealtime()
        onDispose { scope.launch { c.progress.addActiveTime(ref, SystemClock.elapsedRealtime() - t0) } }
    }

    Screen(lesson?.title ?: "Урок", onBack) { padding ->
        Column(Modifier.padding(padding)) {
            TabRow(selectedTabIndex = tab) {
                listOf("Урок", "Конспект", "Задания").forEachIndexed { i, t ->
                    Tab(selected = tab == i, onClick = { tab = i }, text = { Text(t) }, modifier = Modifier.testTag("tab-$i"))
                }
            }
            Column(
                Modifier.padding(16.dp).verticalScroll(rememberScrollState()),
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                val l = lesson ?: return@Column
                when (tab) {
                    0 -> {
                        Text("Цель: ${l.goal}", style = MaterialTheme.typography.bodyLarge)
                        if (status == LessonStatus.PASSED) Text("✓ Урок пройден", color = MaterialTheme.colorScheme.primary)
                        Text(
                            "Анимированный урок с озвучкой появится на этапе 4. Ниже — его сценарий.",
                            style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.outline,
                        )
                        scenario?.scenes?.forEach { scene ->
                            Card(Modifier.fillMaxWidth()) {
                                Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                                    scene.title?.let { Text(it, style = MaterialTheme.typography.titleMedium) }
                                    Text(scene.narration, style = MaterialTheme.typography.bodyMedium)
                                    scene.actions.forEach { a ->
                                        when (a.type) {
                                            "type" -> CodeBlock(a.text.orEmpty())
                                            "output" -> {
                                                Text("Вывод:", style = MaterialTheme.typography.labelMedium)
                                                CodeBlock(a.text.orEmpty())
                                            }
                                            "note" -> MarkdownText(a.md.orEmpty())
                                        }
                                    }
                                }
                            }
                        }
                        Text("Типичные ошибки", style = MaterialTheme.typography.titleMedium)
                        l.commonMistakes.forEach { m ->
                            Text("• ${m.mistake}\n   → ${m.fix}", style = MaterialTheme.typography.bodyMedium)
                        }
                    }
                    1 -> MarkdownText(notes)
                    2 -> {
                        Text(
                            "Для прохождения урока нужно решить ${l.passCriteria.minAssignmentsPassed} из ${assignments.size}.",
                            style = MaterialTheme.typography.bodyMedium,
                        )
                        assignments.forEachIndexed { i, a ->
                            Card(Modifier.fillMaxWidth().clickable { openAssignment(i) }.testTag("assignment-$i")) {
                                Column(Modifier.padding(12.dp)) {
                                    Text((if (a.id in passed) "✓ " else "") + a.title, style = MaterialTheme.typography.titleMedium)
                                    Text(assignmentTypeName(a.type), style = MaterialTheme.typography.labelMedium)
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
