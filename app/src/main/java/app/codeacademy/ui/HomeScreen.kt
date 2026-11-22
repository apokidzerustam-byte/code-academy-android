package app.codeacademy.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
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
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import app.codeacademy.content.Lesson
import app.codeacademy.content.LessonRef
import app.codeacademy.content.PackManifest
import app.codeacademy.data.LessonStatus
import kotlinx.coroutines.launch

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun HomeScreen(
    openProgram: () -> Unit,
    openLesson: (LessonRef) -> Unit,
    openStats: () -> Unit,
    openSettings: () -> Unit,
    openProjects: () -> Unit,
    openDiagnostic: () -> Unit = {},
    openReview: () -> Unit = {},
    openMap: () -> Unit = {},
    openPlan: () -> Unit = {},
    openMentor: () -> Unit = {},
) {
    val c = LocalContainer.current
    var lessons by remember { mutableStateOf<List<Pair<PackManifest, Lesson>>>(emptyList()) }
    LaunchedEffect(Unit) { lessons = c.content.allLessons() }
    val progress by c.progress.lessons.collectAsStateWithLifecycle(emptyList())
    val last by c.progress.lastActive.collectAsStateWithLifecycle(null)
    val dueFlow = remember { c.progress.dueReviews() }
    val due by dueFlow.collectAsStateWithLifecycle(emptyList())
    val skills by c.progress.skills.collectAsStateWithLifecycle(emptyList())
    val settings by c.settings.settings.collectAsStateWithLifecycle(null)
    val reviews by c.progress.reviews.collectAsStateWithLifecycle(emptyList())
    val attempts by c.progress.attempts.collectAsStateWithLifecycle(emptyList())
    val course = rememberCourse()
    val scope = rememberCoroutineScope()

    val statusByKey = progress.associate { it.lessonKey to it.status }
    val refs = lessons.map { (p, l) -> LessonRef(p.id, l.id) to l }
    val passed = refs.count { LessonStatus.isDone(statusByKey[it.first.key]) }
    val continueRef = last?.lessonKey?.let { k -> refs.firstOrNull { it.first.key == k } }
    val next = continueRef?.takeIf { !LessonStatus.isDone(statusByKey[it.first.key]) }
        ?: refs.firstOrNull { !LessonStatus.isDone(statusByKey[it.first.key]) }
    val today = java.time.LocalDate.now().toEpochDay()
    val todayPlan = remember(course, progress, reviews, attempts, settings, today) {
        val s = settings
        if (course != null && s != null) {
            val passedBy = attempts.filter { it.passed }.groupBy { it.lessonKey }.mapValues { (_, a) -> a.map { it.assignmentId }.toSet() }
            buildPlan(course, progress, reviews, passedBy, today, s.sessionMinutes, s.daysPerWeek)
                .firstOrNull()?.takeIf { it.epochDay == today }
        } else null
    }
    val progressLoaded by c.progress.lessons.collectAsStateWithLifecycle<List<app.codeacademy.data.LessonProgressEntity>?>(null)
    val weak = skills.filter { it.attempts > 0 && it.accuracy < 0.6 }

    Screen("Code Academy", onBack = null, actions = {
        IconButton(onClick = openSettings) { Icon(Icons.Filled.Settings, contentDescription = "Настройки") }
    }) { padding ->
        Column(
            Modifier.padding(padding).padding(16.dp).verticalScroll(rememberScrollState()),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            // Карточка выбора — только когда прогресс уже прочитан и пуст (без мигания у тех, кто учится).
            if (settings?.onboardingDone == false && progressLoaded?.isEmpty() == true) {
                StartChoiceCard(onZero = { scope.launch { c.settings.setOnboardingDone(true) } }, onDiagnostic = openDiagnostic)
            }
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
                    if (weak.isNotEmpty()) Text("Слабые темы: " + weak.joinToString { course?.title(it.skillId) ?: it.skillId })
                }
            }
            if (todayPlan != null && course != null && todayPlan.items.isNotEmpty()) {
                Card(Modifier.fillMaxWidth().testTag("today-plan")) {
                    Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                        Text("Сегодня по плану · ${todayPlan.minutes} мин", style = MaterialTheme.typography.titleMedium)
                        todayPlan.items.forEach { PlanItemRow(it, course, openLesson, openReview) }
                    }
                }
            }
            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedButton(onClick = openReview, modifier = Modifier.testTag("open-review")) { Text("Повторение (${due.size})") }
                OutlinedButton(onClick = openMap, modifier = Modifier.testTag("open-map")) { Text("Карта знаний") }
                OutlinedButton(onClick = openPlan, modifier = Modifier.testTag("open-plan")) { Text("План") }
                OutlinedButton(onClick = openMentor, modifier = Modifier.testTag("open-mentor")) { Text("Наставник") }
            }
            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedButton(onClick = openProgram, modifier = Modifier.testTag("open-program")) { Text("Программа") }
                OutlinedButton(onClick = openProjects, modifier = Modifier.testTag("open-projects")) { Text("Проекты") }
                OutlinedButton(onClick = openStats) { Text("Статистика") }
            }
        }
    }
}
