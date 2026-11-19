package app.codeacademy.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.FilterChip
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import app.codeacademy.AppContainer
import app.codeacademy.content.Assignment
import app.codeacademy.content.Lesson
import app.codeacademy.content.LessonRef
import app.codeacademy.content.PackManifest
import app.codeacademy.data.AttemptEntity
import app.codeacademy.data.LessonProgressEntity
import app.codeacademy.data.LessonStatus
import app.codeacademy.data.ReviewItemEntity
import app.codeacademy.data.SkillStatus
import app.codeacademy.learning.AttemptLite
import app.codeacademy.learning.DayPlan
import app.codeacademy.learning.Diagnostic
import app.codeacademy.learning.LessonWork
import app.codeacademy.learning.PlanKind
import app.codeacademy.learning.Scoring
import app.codeacademy.learning.WeeklyPlanner
import kotlinx.coroutines.launch
import java.time.LocalDate
import java.time.format.TextStyle
import java.util.Locale

/** Курс целиком: уроки по порядку с заданиями и названиями навыков. */
data class CourseData(
    val lessons: List<CourseLesson>,
    val skillTitles: Map<String, String>,
) {
    fun lessonOfSkill(skill: String) = lessons.firstOrNull { skill in it.lesson.skills }
    fun title(skill: String) = skillTitles[skill] ?: skill
}

data class CourseLesson(
    val pack: PackManifest,
    val lesson: Lesson,
    val assignments: List<Assignment>,
    val audioMinutes: Double,
) {
    val ref get() = LessonRef(pack.id, lesson.id)
}

suspend fun loadCourse(c: AppContainer): CourseData {
    val all = c.content.allLessons()
    val lessons = all.map { (p, l) ->
        val ref = LessonRef(p.id, l.id)
        val audio = c.content.narration(ref)?.scenes?.sumOf { it.durationMs }?.div(60_000.0) ?: 3.0
        CourseLesson(p, l, c.content.assignments(ref), audio)
    }
    return CourseData(lessons, all.map { it.first }.distinctBy { it.id }.flatMap { it.skills.entries }.associate { it.key to it.value })
}

/** Курс читается из assets один раз за запуск приложения (он не меняется). */
@Composable
fun rememberCourse(): CourseData? {
    val c = LocalContainer.current
    var course by remember { mutableStateOf(c.courseCache) }
    LaunchedEffect(Unit) {
        if (course == null) course = loadCourse(c).also { c.courseCache = it }
    }
    return course
}

fun AttemptEntity.lite() = AttemptLite(assignmentId, startedAt, passed, hintsUsed, durationMs)

/** Балл урока по попыткам (null — заданий ещё не решали). */
fun lessonScores(attempts: List<AttemptEntity>): Map<String, Int?> =
    attempts.groupBy { it.lessonKey }.mapValues { (_, a) -> Scoring.lessonScore(a.map { it.lite() }) }

/** Недельный план из курса, прогресса и расписания повторений. */
fun buildPlan(
    course: CourseData,
    progress: List<LessonProgressEntity>,
    reviews: List<ReviewItemEntity>,
    passedByLesson: Map<String, Set<String>>,
    today: Long,
    sessionMinutes: Int,
    daysPerWeek: Int,
): List<DayPlan> {
    val byKey = progress.associateBy { it.lessonKey }
    val work = course.lessons.filter { !LessonStatus.isDone(byKey[it.ref.key]?.status) }.map { cl ->
        val w = WeeklyPlanner.estimate(cl.ref.key, cl.lesson.title, cl.audioMinutes, cl.assignments.size)
        // Решённые задания уже не планируются; объяснение — если урок ещё не досмотрен (90 % озвучки).
        val left = cl.assignments.count { it.id !in passedByLesson[cl.ref.key].orEmpty() }
        val watched = (byKey[cl.ref.key]?.scenePositionMs ?: 0) >= cl.audioMinutes * 60_000 * 0.9
        LessonWork(w.lessonKey, w.title, if (watched) 0 else w.theoryMinutes, if (left == 0) 0 else left * 8)
    }
    return WeeklyPlanner.plan(today, sessionMinutes, daysPerWeek, work) { from, to ->
        reviews.count { it.dueEpochDay <= to && (from == null || it.dueEpochDay >= from) }
    }
}

private fun dayName(epochDay: Long, today: Long): String = when (epochDay - today) {
    0L -> "Сегодня"
    1L -> "Завтра"
    else -> LocalDate.ofEpochDay(epochDay).let {
        it.dayOfWeek.getDisplayName(TextStyle.FULL, Locale("ru")).replaceFirstChar { c -> c.uppercase() } + ", " + it.dayOfMonth
    }
}

// ───────────────────────────── Диагностика ─────────────────────────────

/**
 * Диагностика для опытных: по одному вопросу «что выведет программа» на урок, по порядку.
 * Первая ошибка (или «Не знаю») завершает тест: дальше уроки опираются на этот.
 */
@Composable
fun DiagnosticScreen(onBack: () -> Unit, onFinish: () -> Unit) {
    val c = LocalContainer.current
    val scope = rememberCoroutineScope()
    val course = rememberCourse()
    var index by rememberSaveable { mutableStateOf(0) }
    var answer by rememberSaveable { mutableStateOf("") }
    var finished by rememberSaveable { mutableStateOf(false) }
    // Ответы строкой «1101» — переживают поворот экрана вместе с номером вопроса.
    var resultsRaw by rememberSaveable { mutableStateOf("") }
    val results = resultsRaw.map { it == '1' }
    // Цепочка уроков подряд; урок без вопроса обрывает её (иначе можно «перепрыгнуть» непроверенный урок).
    val questions = course?.lessons.orEmpty()
        .map { cl -> cl to cl.assignments.firstOrNull { it.type == "predict" } }
        .takeWhile { it.second != null }.map { it.first to it.second!! }
    var saved by rememberSaveable { mutableStateOf(false) }

    fun finish() {
        finished = true
        val n = Diagnostic.confirmedPrefix(resultsRaw.map { listOf(it == '1') })
        // В области приложения: уход с экрана не должен отменить запись результата.
        c.appScope.launch {
            c.progress.testOut(questions.take(n).map { it.first.ref to it.first.lesson })
            c.settings.setOnboardingDone(true)
            saved = true
        }
    }
    LaunchedEffect(course) { if (course != null && questions.isEmpty() && !finished) finish() }

    Screen("Диагностика", onBack) { padding ->
        Column(Modifier.padding(padding).padding(16.dp).verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            if (course == null) { Text("Загрузка…"); return@Column }
            if (!finished && index < questions.size) {
                val (cl, q) = questions[index]
                Text("Вопрос ${index + 1} из ${questions.size} · ${cl.lesson.title}", style = MaterialTheme.typography.labelLarge,
                    modifier = Modifier.testTag("diag-progress"))
                Text("Что выведет программа? Каждую строку вывода — с новой строки.", style = MaterialTheme.typography.titleMedium)
                CodeBlock(q.code ?: q.starterCode.orEmpty())
                OutlinedTextField(answer, { answer = it }, label = { Text("Ваш ответ") }, minLines = 3,
                    textStyle = MaterialTheme.typography.bodyLarge.copy(fontFamily = FontFamily.Monospace),
                    modifier = Modifier.fillMaxWidth().testTag("diag-answer"))
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Button(enabled = answer.isNotBlank(), onClick = {
                        val expected = (q.tests["expected_answer"] as? kotlinx.serialization.json.JsonPrimitive)?.content.orEmpty()
                        val ok = Diagnostic.answerMatches(expected, answer)
                        resultsRaw += if (ok) "1" else "0"
                        answer = ""
                        if (ok && index + 1 < questions.size) index++ else finish()
                    }, modifier = Modifier.testTag("diag-submit")) { Text("Ответить") }
                    OutlinedButton(onClick = { resultsRaw += "0"; answer = ""; finish() }, modifier = Modifier.testTag("diag-dontknow")) { Text("Не знаю") }
                }
                Text("Тест закончится на первом неверном ответе — темы дальше опираются на эту.",
                    style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.outline)
            } else {
                val n = Diagnostic.confirmedPrefix(results.map { listOf(it) })
                Text("Подтверждено уроков: $n из ${questions.size}", style = MaterialTheme.typography.titleLarge,
                    modifier = Modifier.testTag("diag-result"))
                if (n > 0) {
                    Text("Эти уроки отмечены как пройденные. Завтра появится короткое повторение по их темам — " +
                        "одного теста мало, чтобы считать навык освоенным.")
                    questions.take(n).forEach { Text("✓ " + it.first.lesson.title) }
                }
                questions.getOrNull(n)?.let { Text("Начнём с урока «${it.first.lesson.title}».", style = MaterialTheme.typography.titleMedium) }
                Button(enabled = saved, onClick = onFinish, modifier = Modifier.testTag("diag-done")) { Text("К обучению") }
            }
        }
    }
}

// ───────────────────────────── Карта знаний ─────────────────────────────

private data class StatusLook(val label: String, val color: Color)

@Composable
private fun skillLook(status: String): StatusLook = when (status) {
    SkillStatus.LEARNING -> StatusLook("изучается", Color(0xFF1E88E5))
    SkillStatus.NEEDS_REVIEW -> StatusLook("требует повторения", Color(0xFFE53935))
    SkillStatus.MASTERED -> StatusLook("освоено", Color(0xFF43A047))
    SkillStatus.CONFIRMED -> StatusLook("подтверждено", Color(0xFF2E7D32))
    else -> StatusLook("не изучено", MaterialTheme.colorScheme.outline)
}

@Composable
private fun StatusChip(status: String) {
    val look = skillLook(status)
    Text(
        look.label, color = Color.White, style = MaterialTheme.typography.labelSmall,
        modifier = Modifier.background(look.color, RoundedCornerShape(50)).padding(horizontal = 8.dp, vertical = 2.dp),
    )
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun KnowledgeMapScreen(onBack: () -> Unit, openLesson: (LessonRef) -> Unit) {
    val c = LocalContainer.current
    val course = rememberCourse()
    val skills by c.progress.skills.collectAsStateWithLifecycle(emptyList())
    val reviews by c.progress.reviews.collectAsStateWithLifecycle(emptyList())
    val progress by c.progress.lessons.collectAsStateWithLifecycle(emptyList())
    val byId = skills.associateBy { it.skillId }
    val reviewById = reviews.associateBy { it.skillId }
    val statusByKey = progress.associate { it.lessonKey to it.status }
    val today = LocalDate.now().toEpochDay()

    Screen("Карта знаний", onBack) { padding ->
        Column(Modifier.padding(padding).padding(16.dp).verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            FlowRow(horizontalArrangement = Arrangement.spacedBy(6.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                listOf(SkillStatus.NOT_STUDIED, SkillStatus.LEARNING, SkillStatus.NEEDS_REVIEW, SkillStatus.MASTERED, SkillStatus.CONFIRMED)
                    .forEach { StatusChip(it) }
            }
            Text("«Освоено» — успех в разные дни с точностью от 80 %. «Подтверждено» — успешное повторение через неделю и позже.",
                style = MaterialTheme.typography.bodySmall)
            if (course == null) { Text("Загрузка…"); return@Column }
            val total = course.lessons.sumOf { it.lesson.skills.size }
            val good = course.lessons.flatMap { it.lesson.skills }.count { byId[it]?.status in setOf(SkillStatus.MASTERED, SkillStatus.CONFIRMED) }
            Text("Освоено навыков: $good из $total", style = MaterialTheme.typography.titleMedium, modifier = Modifier.testTag("map-summary"))
            course.lessons.forEach { cl ->
                Card(Modifier.fillMaxWidth().testTag("map-${cl.lesson.id}")) {
                    Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text(cl.lesson.title, style = MaterialTheme.typography.titleSmall, modifier = Modifier.weight(1f))
                            TextButton(onClick = { openLesson(cl.ref) }) { Text("Урок") }
                        }
                        val prereq = cl.lesson.prerequisites.mapNotNull { p -> course.lessons.firstOrNull { it.lesson.id == p }?.lesson?.title }
                        if (prereq.isNotEmpty()) {
                            val ready = cl.lesson.prerequisites.all { p ->
                                course.lessons.firstOrNull { it.lesson.id == p }?.let { LessonStatus.isDone(statusByKey[it.ref.key]) } ?: true
                            }
                            Text((if (ready) "Опирается на: " else "Сначала пройдите: ") + prereq.joinToString(),
                                style = MaterialTheme.typography.bodySmall,
                                color = if (ready) MaterialTheme.colorScheme.outline else MaterialTheme.colorScheme.error)
                        }
                        HorizontalDivider()
                        cl.lesson.skills.forEach { sk ->
                            val st = byId[sk]
                            Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.semantics {
                                contentDescription = "${course.title(sk)}: ${skillLookLabel(st?.status ?: SkillStatus.NOT_STUDIED)}"
                            }) {
                                Column(Modifier.weight(1f)) {
                                    Text(course.title(sk), style = MaterialTheme.typography.bodyMedium)
                                    val details = buildList {
                                        if (st != null && st.attempts > 0) add("точность ${(st.accuracy * 100).toInt()} %, попыток ${st.attempts}")
                                        reviewById[sk]?.let { r ->
                                            add(if (r.dueEpochDay <= today) "повторить сегодня" else "повторение: ${dayName(r.dueEpochDay, today).lowercase()}")
                                        }
                                    }
                                    if (details.isNotEmpty()) Text(details.joinToString(" · "), style = MaterialTheme.typography.bodySmall)
                                }
                                StatusChip(st?.status ?: SkillStatus.NOT_STUDIED)
                            }
                        }
                    }
                }
            }
        }
    }
}

private fun skillLookLabel(status: String) = when (status) {
    SkillStatus.LEARNING -> "изучается"
    SkillStatus.NEEDS_REVIEW -> "требует повторения"
    SkillStatus.MASTERED -> "освоено"
    SkillStatus.CONFIRMED -> "подтверждено"
    else -> "не изучено"
}

// ───────────────────────────── Повторение ─────────────────────────────

/**
 * Задание для повторения навыка: из урока, где навык изучается; предпочтительно то,
 * которое дольше всего не решали (повторение — это вспомнить, а не повторить вчерашнее).
 */
fun pickReviewAssignment(cl: CourseLesson, attempts: List<AttemptEntity>): Int {
    val last = attempts.filter { it.lessonKey == cl.ref.key }.groupBy { it.assignmentId }.mapValues { (_, a) -> a.maxOf { it.startedAt } }
    return cl.assignments.indices.minByOrNull { i -> last[cl.assignments[i].id] ?: Long.MIN_VALUE } ?: 0
}

@Composable
fun ReviewScreen(onBack: () -> Unit, openAssignment: (LessonRef, Int) -> Unit) {
    val c = LocalContainer.current
    val course = rememberCourse()
    val reviews by c.progress.reviews.collectAsStateWithLifecycle(emptyList())
    val skills by c.progress.skills.collectAsStateWithLifecycle(emptyList())
    val attempts by c.progress.attempts.collectAsStateWithLifecycle(emptyList())
    val today = LocalDate.now().toEpochDay()
    val due = reviews.filter { it.dueEpochDay <= today }
    val weak = skills.filter { it.attempts > 0 && it.accuracy < 0.6 && due.none { d -> d.skillId == it.skillId } }

    Screen("Повторение", onBack) { padding ->
        Column(Modifier.padding(padding).padding(16.dp).verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            if (course == null) { Text("Загрузка…"); return@Column }
            Text("Сегодня: ${due.size}", style = MaterialTheme.typography.titleLarge, modifier = Modifier.testTag("review-count"))
            if (due.isEmpty()) Text("На сегодня повторений нет. Интервалы: 1, 3, 7, 14 и 30 дней — после ошибки интервал сокращается.")
            due.forEach { r -> ReviewRow(course, r.skillId, "интервал ${r.intervalDays} дн.", attempts, openAssignment) }
            if (weak.isNotEmpty()) {
                Text("Слабые темы", style = MaterialTheme.typography.titleMedium)
                weak.forEach { s -> ReviewRow(course, s.skillId, "точность ${(s.accuracy * 100).toInt()} %", attempts, openAssignment) }
            }
            val upcoming = reviews.filter { it.dueEpochDay in (today + 1)..(today + 7) }.groupBy { it.dueEpochDay }.toSortedMap()
            if (upcoming.isNotEmpty()) {
                Text("На неделе", style = MaterialTheme.typography.titleMedium)
                upcoming.forEach { (day, list) -> Text("${dayName(day, today)}: ${list.joinToString { course.title(it.skillId) }}") }
            }
        }
    }
}

@Composable
private fun ReviewRow(course: CourseData, skill: String, note: String, attempts: List<AttemptEntity>, open: (LessonRef, Int) -> Unit) {
    val cl = course.lessonOfSkill(skill) ?: return
    Card(Modifier.fillMaxWidth()) {
        Row(Modifier.padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f)) {
                Text(course.title(skill), style = MaterialTheme.typography.titleSmall)
                Text("${cl.lesson.title} · $note", style = MaterialTheme.typography.bodySmall)
            }
            Button(onClick = { open(cl.ref, pickReviewAssignment(cl, attempts)) }, modifier = Modifier.testTag("review-$skill")) { Text("Повторить") }
        }
    }
}

// ───────────────────────────── Недельный план ─────────────────────────────

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun PlanScreen(onBack: () -> Unit, openLesson: (LessonRef) -> Unit, openReview: () -> Unit) {
    val c = LocalContainer.current
    val scope = rememberCoroutineScope()
    val course = rememberCourse()
    val settings by c.settings.settings.collectAsStateWithLifecycle(null)
    val progress by c.progress.lessons.collectAsStateWithLifecycle(emptyList())
    val reviews by c.progress.reviews.collectAsStateWithLifecycle(emptyList())
    val attempts by c.progress.attempts.collectAsStateWithLifecycle(emptyList())
    val today = LocalDate.now().toEpochDay()

    Screen("План на неделю", onBack) { padding ->
        Column(Modifier.padding(padding).padding(16.dp).verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            val s = settings
            if (course == null || s == null) { Text("Загрузка…"); return@Column }
            Text("Длительность занятия", style = MaterialTheme.typography.titleSmall)
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                WeeklyPlanner.SESSION_OPTIONS.forEach { m ->
                    FilterChip(selected = s.sessionMinutes == m, onClick = { scope.launch { c.settings.setSessionMinutes(m) } },
                        label = { Text(if (m == 60) "$m мин (рекомендуется)" else "$m мин") }, modifier = Modifier.testTag("session-$m"))
                }
            }
            Text("Дней в неделю", style = MaterialTheme.typography.titleSmall)
            FlowRow(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                (1..7).forEach { d ->
                    FilterChip(selected = s.daysPerWeek == d, onClick = { scope.launch { c.settings.setDaysPerWeek(d) } },
                        label = { Text("$d") }, modifier = Modifier.testTag("days-$d"))
                }
            }
            Text("Пропустили день — ничего страшного: план каждый раз строится заново от сегодняшнего дня.",
                style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.outline)
            val plan = remember(course, progress, reviews, attempts, s.sessionMinutes, s.daysPerWeek, today) {
                val passedBy = attempts.filter { it.passed }.groupBy { it.lessonKey }.mapValues { (_, a) -> a.map { it.assignmentId }.toSet() }
                buildPlan(course, progress, reviews, passedBy, today, s.sessionMinutes, s.daysPerWeek)
            }
            plan.forEach { day ->
                Card(Modifier.fillMaxWidth().testTag("plan-day-${day.epochDay - today}")) {
                    Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                        Text("${dayName(day.epochDay, today)} · ${day.minutes} мин", style = MaterialTheme.typography.titleSmall)
                        day.items.forEach { item -> PlanItemRow(item, course, openLesson, openReview) }
                    }
                }
            }
        }
    }
}

@Composable
fun PlanItemRow(item: app.codeacademy.learning.PlanItem, course: CourseData, openLesson: (LessonRef) -> Unit, openReview: () -> Unit) {
    val icon = when (item.kind) { PlanKind.REVIEW -> "↻"; PlanKind.THEORY -> "▶"; PlanKind.PRACTICE -> "✎" }
    Row(verticalAlignment = Alignment.CenterVertically) {
        Text("$icon ${item.title} · ${item.minutes} мин", modifier = Modifier.weight(1f), style = MaterialTheme.typography.bodyMedium)
        val target = item.lessonKey?.let { k -> course.lessons.firstOrNull { it.ref.key == k } }
        if (item.kind == PlanKind.REVIEW) TextButton(onClick = openReview) { Text("Открыть") }
        else if (target != null) TextButton(onClick = { openLesson(target.ref) }) { Text("Открыть") }
    }
}

/** Карточка выбора старта на главной (раздел 10 ТЗ: «Я начинаю с нуля» или тест). */
@Composable
fun StartChoiceCard(onZero: () -> Unit, onDiagnostic: () -> Unit) {
    Card(Modifier.fillMaxWidth().testTag("start-choice")) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text("С чего начнём?", style = MaterialTheme.typography.titleLarge)
            Text("Если вы уже знаете основы Python, пройдите короткую диагностику: подтверждённые уроки отметятся пройденными.")
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Button(onClick = onZero, modifier = Modifier.testTag("start-zero")) { Text("Я начинаю с нуля") }
                OutlinedButton(onClick = onDiagnostic, modifier = Modifier.testTag("start-diagnostic")) { Text("Диагностика") }
            }
        }
    }
}
