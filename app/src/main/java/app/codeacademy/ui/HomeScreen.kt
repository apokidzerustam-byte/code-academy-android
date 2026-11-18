package app.codeacademy.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import app.codeacademy.content.Lesson
import app.codeacademy.content.LessonRef
import app.codeacademy.content.PackManifest
import app.codeacademy.data.LessonStatus

@Composable
fun HomeScreen(
    openProgram: () -> Unit,
    openLesson: (LessonRef) -> Unit,
    openStats: () -> Unit,
    openSettings: () -> Unit,
    openProjects: () -> Unit,
) {
    val c = LocalContainer.current
    var lessons by remember { mutableStateOf<List<Pair<PackManifest, Lesson>>>(emptyList()) }
    LaunchedEffect(Unit) { lessons = c.content.allLessons() }
    val progress by c.progress.lessons.collectAsStateWithLifecycle(emptyList())
    val last by c.progress.lastActive.collectAsStateWithLifecycle(null)
    val dueFlow = remember { c.progress.dueReviews() }
    val due by dueFlow.collectAsStateWithLifecycle(emptyList())
    val skills by c.progress.skills.collectAsStateWithLifecycle(emptyList())

    val statusByKey = progress.associate { it.lessonKey to it.status }
    val refs = lessons.map { (p, l) -> LessonRef(p.id, l.id) to l }
    val passed = refs.count { statusByKey[it.first.key] == LessonStatus.PASSED }
    val continueRef = last?.lessonKey?.let { k -> refs.firstOrNull { it.first.key == k } }
    val next = continueRef?.takeIf { statusByKey[it.first.key] != LessonStatus.PASSED }
        ?: refs.firstOrNull { statusByKey[it.first.key] != LessonStatus.PASSED }
    val weak = skills.filter { it.attempts > 0 && it.accuracy < 0.6 }

    Screen("Code Academy", onBack = null, actions = {
        IconButton(onClick = openSettings) { Icon(Icons.Filled.Settings, contentDescription = "Настройки") }
    }) { padding ->
        Column(
            Modifier.padding(padding).padding(16.dp).verticalScroll(rememberScrollState()),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Card(Modifier.fillMaxWidth().testTag("continue")) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    if (next != null) {
                        val started = statusByKey[next.first.key] == LessonStatus.IN_PROGRESS
                        Text(if (started) "Продолжить урок" else "Следующий урок", style = MaterialTheme.typography.labelLarge)
                        Text(next.second.title, style = MaterialTheme.typography.titleLarge)
                        Text(next.second.goal, style = MaterialTheme.typography.bodyMedium)
                        Button(onClick = { openLesson(next.first) }) { Text(if (started) "Продолжить" else "Начать") }
                    } else if (refs.isNotEmpty()) {
                        Text("Все доступные уроки пройдены", style = MaterialTheme.typography.titleMedium)
                        Text("Новые этапы появятся с обновлением контента.")
                    } else {
                        Text("Загрузка программы…")
                    }
                }
            }
            Card(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("Прогресс", style = MaterialTheme.typography.titleMedium)
                    Text("Пройдено уроков: $passed из ${refs.size}")
                    LinearProgressIndicator(
                        progress = { if (refs.isEmpty()) 0f else passed.toFloat() / refs.size },
                        modifier = Modifier.fillMaxWidth(),
                    )
                    Text("Повторить сегодня: ${due.size}")
                    if (weak.isNotEmpty()) Text("Слабые темы: " + weak.joinToString { it.skillId })
                }
            }
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedButton(onClick = openProgram, modifier = Modifier.testTag("open-program")) { Text("Программа") }
                OutlinedButton(onClick = openProjects, modifier = Modifier.testTag("open-projects")) { Text("Проекты") }
                OutlinedButton(onClick = openStats) { Text("Статистика") }
            }
        }
    }
}
