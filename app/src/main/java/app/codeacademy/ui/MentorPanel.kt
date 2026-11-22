package app.codeacademy.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AssistChip
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
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import app.codeacademy.mentor.Intent
import app.codeacademy.mentor.IntentClassifier
import app.codeacademy.mentor.LessonLink
import app.codeacademy.mentor.MentorContext
import app.codeacademy.mentor.MentorReply
import app.codeacademy.mentor.Source
import app.codeacademy.settings.Settings
import kotlinx.coroutines.Job
import kotlinx.coroutines.launch

/**
 * Панель ИИ-наставника под заданием, этапом проекта или в IDE.
 * context() вызывается в момент вопроса: наставник видит текущий код, ошибку и число подсказок.
 */
@OptIn(ExperimentalLayoutApi::class)
@Composable
fun MentorPanel(
    context: () -> MentorContext,
    onHintRevealed: (Int) -> Unit = {},
    openLesson: ((LessonLink) -> Unit)? = null,
    startOpen: Boolean = false,
    modifier: Modifier = Modifier,
) {
    val c = LocalContainer.current
    val settings by c.settings.settings.collectAsStateWithLifecycle(Settings())
    val scope = rememberCoroutineScope()
    var open by rememberSaveable { mutableStateOf(startOpen) }
    var question by rememberSaveable { mutableStateOf("") }
    var reply by remember { mutableStateOf<MentorReply?>(null) }
    var partial by remember { mutableStateOf<String?>(null) }
    // Ответ по материалам курса, который показывается сразу, пока нейросеть ещё считает.
    var instant by remember { mutableStateOf<MentorReply?>(null) }
    var elapsedMs by remember { mutableStateOf(0L) }
    var job by remember { mutableStateOf<Job?>(null) }
    // Проверка файлов модели — один раз на смену настроек, а не на каждую перерисовку.
    val model = remember(settings) { c.activeModel(settings) }

    // Панель открыта — ученик, скорее всего, сейчас спросит: модель загружается заранее, пока он набирает вопрос.
    LaunchedEffect(open, model?.id) {
        if (open && model != null) {
            try {
                c.mentor(settings)
                c.mentorClient.warmUp()
            } catch (e: kotlinx.coroutines.CancellationException) {
                throw e
            } catch (_: Exception) {
                // предзагрузка необязательна: настоящий вопрос сам загрузит модель и покажет причину сбоя
            }
        }
    }

    fun ask(q: String, forced: Intent?) {
        job?.cancel()
        reply = null
        instant = null
        partial = ""
        val j = scope.launch {
            val t0 = System.currentTimeMillis()
            val ctx = context()
            val mentor = c.mentor(settings)
            val intent = forced ?: IntentClassifier.classify(q, ctx.task?.isAnswerTask == true)
            val r = mentor.answer(q, ctx, intent, onPartial = { p -> partial = p }, onLite = { l ->
                instant = l
                l.revealedHint?.let(onHintRevealed)
            })
            elapsedMs = System.currentTimeMillis() - t0
            reply = r
            partial = null
            instant = null
            r.revealedHint?.let(onHintRevealed)
        }
        job = j
        j.invokeOnCompletion { if (job === j) { partial = null; instant = null } }
    }

    if (!open) {
        OutlinedButton(onClick = { open = true }, modifier = modifier.testTag("mentor-open")) { Text("Спросить наставника") }
        return
    }
    Card(modifier.fillMaxWidth().testTag("mentor-panel"), colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.secondaryContainer)) {
        Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Column(Modifier.weight(1f)) {
                    Text("Наставник", style = MaterialTheme.typography.titleMedium)
                    Text(
                        if (model != null) "Нейросеть на телефоне: ${model.title.substringBefore(" (")}" else "Лёгкий режим: материалы курса и разбор ошибок",
                        style = MaterialTheme.typography.labelSmall, modifier = Modifier.testTag("mentor-mode"),
                    )
                }
                TextButton(onClick = { job?.cancel(); c.mentorClient.stop(); open = false }) { Text("Свернуть") }
            }
            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                AssistChip(onClick = { ask("Почему ошибка?", Intent.EXPLAIN_ERROR) }, label = { Text("Почему ошибка?") }, modifier = Modifier.testTag("mentor-error"))
                AssistChip(onClick = { ask("Дай подсказку", Intent.HINT) }, label = { Text("Подсказка") }, modifier = Modifier.testTag("mentor-hint"))
                AssistChip(onClick = { ask(question.ifBlank { "" }, Intent.EXPLAIN_TOPIC) }, label = { Text("Объясни тему") }, modifier = Modifier.testTag("mentor-topic"))
                AssistChip(onClick = { ask("Проверь мой код", Intent.REVIEW) }, label = { Text("Проверь мой код") }, modifier = Modifier.testTag("mentor-review"))
                AssistChip(onClick = { ask("Дай упражнение", Intent.EXERCISE) }, label = { Text("Упражнение") }, modifier = Modifier.testTag("mentor-exercise"))
            }
            OutlinedTextField(
                value = question, onValueChange = { question = it.take(1000) },
                label = { Text("Вопрос наставнику") }, modifier = Modifier.fillMaxWidth().testTag("mentor-input"),
                maxLines = 4,
            )
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
                Button(enabled = question.isNotBlank() && partial == null, onClick = { ask(question, null) }, modifier = Modifier.testTag("mentor-ask")) {
                    Text("Спросить")
                }
                if (partial != null) {
                    CircularProgressIndicator(Modifier.size(20.dp))
                    Text(if (model != null) "думает…" else "ищу…", style = MaterialTheme.typography.bodySmall)
                    TextButton(onClick = { c.mentorClient.stop() }, modifier = Modifier.testTag("mentor-stop")) { Text("Стоп") }
                }
            }
            // Пока нейросеть считает, ученик уже читает ответ по материалам курса.
            if (partial != null) instant?.let { l ->
                Card(Modifier.fillMaxWidth().testTag("mentor-instant")) {
                    Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                        Text("Пока нейросеть думает — ответ по материалам курса:", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.outline)
                        MarkdownText(l.text)
                    }
                }
            }
            partial?.takeIf { it.isNotBlank() }?.let {
                Text("Нейросеть отвечает:", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.outline)
                MarkdownText(it)
            }
            reply?.let { r -> MentorReplyView(r, openLesson, timing = if (r.source == Source.LLM) timingLine(elapsedMs, c.mentorClient.lastStats) else null) }
        }
    }
}

@Composable
private fun MentorReplyView(r: MentorReply, openLesson: ((LessonLink) -> Unit)?, timing: String? = null) {
    Card(Modifier.fillMaxWidth().testTag("mentor-reply")) {
        Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            MarkdownText(r.text)
            if (openLesson != null) r.links.forEach { l ->
                OutlinedButton(onClick = { openLesson(l) }, modifier = Modifier.testTag("mentor-link")) { Text("Урок: ${l.title}") }
            }
            val source = if (r.source == Source.LLM) "Ответила нейросеть на телефоне — проверяйте её советы." else "Ответ по материалам курса."
            Text(source, style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.outline, modifier = Modifier.testTag("mentor-source"))
            r.note?.let { Text(it, style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.outline) }
            timing?.let { Text(it, style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.outline, modifier = Modifier.testTag("mentor-timing")) }
        }
    }
}

/** Где ушло время: загрузка модели, разбор запроса (сколько токенов взято из кэша) и скорость ответа. */
fun timingLine(totalMs: Long, st: app.codeacademy.mentor.GenStats?): String {
    val total = "%.1f".format(totalMs / 1000.0)
    st ?: return "Время ответа: $total с."
    val parts = mutableListOf("всего $total с")
    if (st.loadMs > 0) parts += "загрузка модели ${"%.1f".format(st.loadMs / 1000.0)} с"
    parts += "запрос ${st.promptTokens} ток. за ${"%.1f".format(st.promptMs / 1000.0)} с" + (if (st.cachedTokens > 0) " (${st.cachedTokens} из кэша)" else "")
    parts += "ответ ${st.generatedTokens} ток., ${"%.0f".format(st.tokensPerSecond)} ток/с"
    return parts.joinToString(" · ")
}

/** Текст последней ошибки для наставника: проверка (если не прошла), иначе консоль запуска. */
fun mentorError(v: app.codeacademy.assessment.Verdict?, console: String?): String? {
    if (v != null && !v.passed) {
        v.failure?.let { f -> return if (f == app.codeacademy.runner.RunStatus.TIMEOUT) "Timeout" else v.failureText.ifBlank { f.name } }
        val r = v.report
        if (r != null) {
            r.compileError?.let { return it }
            r.loadError?.let { return it }
            return r.cases.firstOrNull { !it.passed && it.error != null }?.error ?: "WrongResult"
        }
    }
    return console?.takeIf { Regex("Error|Traceback|Exception|Синтаксическая ошибка").containsMatchIn(it) }
}

/** Общий экран наставника: вопросы по темам курса и разбор вставленной ошибки. */
@Composable
fun MentorScreen(onBack: () -> Unit, openLesson: (LessonLink) -> Unit) {
    var code by rememberSaveable { mutableStateOf("") }
    var error by rememberSaveable { mutableStateOf("") }
    Screen("Наставник", onBack) { padding ->
        Column(
            Modifier.padding(padding).padding(16.dp).verticalScroll(rememberScrollState()),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Text(
                "Наставник объясняет темы курса, разбирает ошибки и подсказывает следующий шаг. Готовых решений он не даёт. " +
                    "Всё работает на телефоне: код и вопросы никуда не отправляются.",
                style = MaterialTheme.typography.bodyMedium,
            )
            OutlinedTextField(code, { code = it.take(8000) }, label = { Text("Код (необязательно)") }, modifier = Modifier.fillMaxWidth().testTag("mentor-code"), minLines = 3)
            OutlinedTextField(error, { error = it.take(4000) }, label = { Text("Текст ошибки (необязательно)") }, modifier = Modifier.fillMaxWidth(), minLines = 2)
            MentorPanel(
                context = { MentorContext(code = code, error = error.ifBlank { null }) },
                openLesson = openLesson, startOpen = true,
            )
        }
    }
}
