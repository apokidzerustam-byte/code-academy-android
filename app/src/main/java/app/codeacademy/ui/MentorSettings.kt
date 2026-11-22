package app.codeacademy.ui

import android.content.Intent
import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalClipboardManager
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import app.codeacademy.mentor.CpuTopology
import app.codeacademy.mentor.Intent as MentorIntent
import app.codeacademy.mentor.MentorContext
import app.codeacademy.mentor.ModelCatalog
import app.codeacademy.mentor.ModelInfo
import app.codeacademy.mentor.ModelManager
import app.codeacademy.mentor.Source
import app.codeacademy.settings.Settings
import kotlinx.coroutines.launch

/** Настройки наставника: режим, установка модели по шагам, проверка скорости. */
@OptIn(ExperimentalLayoutApi::class)
@Composable
fun MentorSettingsSection() {
    val c = LocalContainer.current
    val scope = rememberCoroutineScope()
    val s by c.settings.settings.collectAsStateWithLifecycle(Settings())
    var refresh by remember { mutableIntStateOf(0) }
    val installed = remember(refresh) { c.models.installed() }
    var importing by remember { mutableStateOf<Float?>(null) }
    var message by remember { mutableStateOf<String?>(null) }
    var testResult by remember { mutableStateOf<String?>(null) }
    var showSteps by remember { mutableStateOf<String?>(null) }

    val picker = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri: Uri? ->
        if (uri == null) return@rememberLauncherForActivityResult
        scope.launch {
            importing = 0f
            message = "Проверяю и копирую файл…"
            when (val r = c.models.import(uri) { p -> importing = p }) {
                is ModelManager.ImportResult.Ok -> {
                    c.settings.setMentorModel(r.model.id)
                    if (c.models.blocker(r.model) == null) c.settings.setMentorNeural(true)
                    message = "Модель «${r.model.title}» установлена и проверена. Файл из «Загрузок» теперь можно удалить."
                }
                is ModelManager.ImportResult.Failed -> message = r.message
            }
            importing = null
            refresh++
        }
    }

    Text("ИИ-наставник", style = MaterialTheme.typography.titleMedium)
    Text(
        "Лёгкий режим работает всегда: разбор ошибок, подсказки по шагам, поиск по конспектам. " +
            "Нейросетевой режим отвечает своими словами, но требует модель (0,5–1,1 ГБ) и 6–8 ГБ памяти. " +
            "Модель работает только на телефоне: у приложения нет доступа в интернет, код никуда не отправляется. Готовых решений наставник не даёт.",
        style = MaterialTheme.typography.bodySmall,
    )
    val active = c.activeModel(s)
    Row(verticalAlignment = Alignment.CenterVertically) {
        Text("Нейросетевой режим", Modifier.weight(1f))
        Switch(
            checked = s.mentorNeural && active != null,
            enabled = installed.any { c.models.blocker(it) == null },
            onCheckedChange = { v -> scope.launch { c.settings.setMentorNeural(v) } },
            modifier = Modifier.testTag("mentor-neural"),
        )
    }
    Text(
        "Память телефона: ${"%.1f".format(c.models.totalRamMb / 1024.0)} ГБ · свободно на диске: ${"%.1f".format(c.models.freeSpaceBytes / 1e9)} ГБ",
        style = MaterialTheme.typography.labelSmall,
    )

    for (m in ModelCatalog.models) {
        val isInstalled = m in installed
        val blocker = c.models.blocker(m)
        Card(Modifier.fillMaxWidth()) {
            Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                Text(m.title, style = MaterialTheme.typography.titleSmall)
                Text(
                    (if (isInstalled) "Установлена" + (if (active == m) " · используется" else "") else "Не установлена") +
                        " · рекомендуется от ${m.recommendedRamMb / 1000} ГБ памяти · лицензия ${m.license}",
                    style = MaterialTheme.typography.labelSmall,
                )
                blocker?.let { Text(it, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodySmall) }
                FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    if (!isInstalled) {
                        OutlinedButton(onClick = { showSteps = if (showSteps == m.id) null else m.id }, modifier = Modifier.testTag("mentor-steps-${m.id}")) {
                            Text("Как установить")
                        }
                    } else {
                        if (active != m && blocker == null) OutlinedButton(onClick = { scope.launch { c.settings.setMentorModel(m.id); c.settings.setMentorNeural(true) } }) {
                            Text("Использовать")
                        }
                        TextButton(onClick = {
                            c.mentorClient.unload()
                            c.models.delete(m)
                            scope.launch { if (s.mentorModel == m.id) c.settings.setMentorModel(null) }
                            refresh++
                        }) { Text("Удалить") }
                    }
                }
                if (showSteps == m.id && !isInstalled) InstallSteps(m, importing == null) { picker.launch(arrayOf("*/*")) }
            }
        }
    }
    importing?.let { LinearProgressIndicator(progress = { it }, modifier = Modifier.fillMaxWidth()) }
    message?.let { Text(it, style = MaterialTheme.typography.bodyMedium, modifier = Modifier.testTag("mentor-import-message")) }
    if (active != null) {
        OutlinedButton(onClick = {
            scope.launch {
                testResult = "Генерирую…"
                val r = c.mentor(s).answer("Что такое переменная?", MentorContext(), MentorIntent.EXPLAIN_TOPIC)
                val st = c.mentorClient.lastStats
                val info = c.mentorClient.lastInfo
                val feats = info.substringAfter("Процессор: ", "").lineSequence().first().split(", ").filter { f -> f.isNotEmpty() && f.all { ch -> ch.isUpperCase() || ch.isDigit() || ch == '_' } }
                val warn = if (feats.isNotEmpty() && !CpuTopology.hasFastMatmul(feats))
                    "\nВнимание: быстрые инструкции процессора не используются — ответы будут медленными. Отправьте разработчику эти строки." else ""
                testResult = if (r.source == Source.LLM && st != null) {
                    "Работает. ${timingLine(st.loadMs + st.promptMs + st.genMs, st)}\n$info$warn\n\n${r.text}"
                } else "Нейросеть не ответила, сработал лёгкий режим. ${r.note.orEmpty()}\n$info"
            }
        }, modifier = Modifier.testTag("mentor-test")) { Text("Проверить нейросеть") }
        testResult?.let { Text(it, style = MaterialTheme.typography.bodySmall) }
    }
}

/** Пошаговая установка модели: скачать в браузере → выбрать файл → проверка. */
@Composable
private fun InstallSteps(m: ModelInfo, enabled: Boolean, pick: () -> Unit) {
    val clipboard = LocalClipboardManager.current
    val context = LocalContext.current
    Column(verticalArrangement = Arrangement.spacedBy(6.dp), modifier = Modifier.testTag("mentor-install-steps")) {
        Text("1. Скачайте файл модели в браузере (${m.sizeBytes / 1_000_000} МБ, лучше по Wi-Fi). Ссылка:", style = MaterialTheme.typography.bodyMedium)
        Text(m.url, style = MaterialTheme.typography.bodySmall)
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            OutlinedButton(onClick = { clipboard.setText(AnnotatedString(m.url)) }) { Text("Копировать ссылку") }
            OutlinedButton(onClick = {
                // Скачивает браузер: у самого приложения нет доступа в интернет.
                runCatching { context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(m.url)).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)) }
            }) { Text("Открыть в браузере") }
        }
        Text("2. Дождитесь окончания загрузки. Файл «${m.fileName}» появится в папке «Загрузки» (Download).", style = MaterialTheme.typography.bodyMedium)
        Text("3. Нажмите «Выбрать файл модели» и выберите этот файл.", style = MaterialTheme.typography.bodyMedium)
        Button(enabled = enabled, onClick = pick, modifier = Modifier.testTag("mentor-pick")) { Text("Выбрать файл модели") }
        Text("4. Приложение проверит контрольную сумму (около минуты) и скопирует модель к себе. После этого файл в «Загрузках» можно удалить.",
            style = MaterialTheme.typography.bodyMedium)
        Text("5. Включите «Нейросетевой режим» и нажмите «Проверить нейросеть».", style = MaterialTheme.typography.bodyMedium)
    }
}
