package app.codeacademy.ui

import kotlinx.coroutines.CoroutineStart
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.sync.Mutex
import androidx.compose.ui.platform.LocalContext
import androidx.compose.material3.Button
import app.codeacademy.lesson.LessonTimeline
import app.codeacademy.learning.Advisor
import app.codeacademy.learning.NextAction
import app.codeacademy.learning.Scoring
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.OutlinedButton
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
    var lesson by remember { mutableStateOf<Lesson?>(null) }
    var scenario by remember { mutableStateOf<Scenario?>(null) }
    var timeline by remember { mutableStateOf<LessonTimeline?>(null) }
    var resumeMs by remember { mutableStateOf(0L) }
    var finished by remember { mutableStateOf(false) }
    // Сохранения позиции идут строго по очереди: старая позиция не перезапишет новую.
    val saveMutex = remember { Mutex() }
    val context = LocalContext.current
    val audio = remember(ref) { NarrationAudio(context.applicationContext) { c.content.audioAsset(ref, it) } }
    // Позиция живёт на уровне экрана: при переключении вкладок плеер продолжает с того же места.
    var positionMs by rememberSaveable(ref) { mutableStateOf<Long?>(null) }
    var notes by remember { mutableStateOf("") }
    var assignments by remember { mutableStateOf<List<Assignment>>(emptyList()) }
    var passed by remember { mutableStateOf<List<String>>(emptyList()) }
    val attemptsFlow = remember(ref) { c.progress.attemptsFor(ref) }
    val lessonAttempts by attemptsFlow.collectAsStateWithLifecycle(emptyList())
    var tab by rememberSaveable { mutableStateOf(0) }
    val progress by c.progress.lessons.collectAsStateWithLifecycle(emptyList())
    val status = progress.firstOrNull { it.lessonKey == ref.key }?.status

    LaunchedEffect(ref) {
        lesson = c.content.lesson(ref)
        scenario = c.content.scenario(ref)
        // Сначала позиция, потом шкала: плеер появляется вместе с timeline и запоминает начальную позицию.
        resumeMs = positionMs ?: c.progress.lessonProgress(ref)?.scenePositionMs ?: 0L
        positionMs = resumeMs
        timeline = LessonTimeline(scenario!!, c.content.narration(ref))
        notes = c.content.notes(ref)
        assignments = c.content.assignments(ref)
        c.progress.openLesson(ref)
    }
    LaunchedEffect(progress) { passed = c.progress.passedAssignments(ref) }
    DisposableEffect(ref) {
        val t0 = SystemClock.elapsedRealtime()
        onDispose { c.appScope.launch { c.progress.addActiveTime(ref, SystemClock.elapsedRealtime() - t0) } }
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
                        if (status == LessonStatus.TESTED_OUT) Text("✓ Подтверждено диагностикой — задания помогут закрепить", color = MaterialTheme.colorScheme.primary)
                        timeline?.let { tl ->
                            LessonPlayer(
                                timeline = tl, audio = audio, initialMs = positionMs ?: resumeMs,
                                onProgress = { i, ms ->
                                    positionMs = ms
                                    c.appScope.launch(start = CoroutineStart.UNDISPATCHED) { saveMutex.withLock { c.progress.saveScene(ref, i, ms) } }
                                },
                                onFinished = { finished = true },
                            )
                        }
                        if (finished) {
                            Button(onClick = { tab = 2 }, modifier = Modifier.testTag("to-assignments")) { Text("К заданиям →") }
                        }
                        Text("Текст урока", style = MaterialTheme.typography.titleMedium)
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
                        // Адаптация по порогам 60/80/90 (раздел 10 ТЗ): что делать дальше.
                        Scoring.lessonScore(lessonAttempts.map { it.lite() })?.let { score ->
                            val rec = Advisor.forLesson(score, solved = passed.size, required = l.passCriteria.minAssignmentsPassed)
                            Card(
                                Modifier.fillMaxWidth().testTag("recommendation"),
                                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.secondaryContainer),
                            ) {
                                Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                                    Text(rec.title, style = MaterialTheme.typography.titleMedium)
                                    Text(rec.details, style = MaterialTheme.typography.bodyMedium)
                                    when (rec.action) {
                                        NextAction.REEXPLAIN -> OutlinedButton(onClick = { tab = 0 }) { Text("Пересмотреть урок") }
                                        NextAction.CONSOLIDATE, NextAction.EXTRA_CHECK -> {
                                            val nextIdx = assignments.indexOfFirst { it.id !in passed }
                                            if (nextIdx >= 0) OutlinedButton(onClick = { openAssignment(nextIdx) }) { Text("Следующее задание") }
                                        }
                                        NextAction.ADVANCE -> {}
                                    }
                                }
                            }
                        }
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
