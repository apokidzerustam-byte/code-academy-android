package app.codeacademy.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Slider
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import app.codeacademy.mentor.PerfMode
import app.codeacademy.settings.RunnerMode
import app.codeacademy.settings.Settings
import app.codeacademy.settings.ThemeMode
import kotlinx.coroutines.launch

@Composable
fun SettingsScreen(onBack: () -> Unit, openLab: () -> Unit) {
    val c = LocalContainer.current
    val scope = rememberCoroutineScope()
    val s by c.settings.settings.collectAsStateWithLifecycle(Settings())

    Screen("Настройки", onBack) { padding ->
        Column(
            Modifier.padding(padding).padding(16.dp).verticalScroll(rememberScrollState()),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Text("Тема", style = MaterialTheme.typography.titleMedium)
            Choice("Как в системе", s.theme == ThemeMode.SYSTEM, "theme-system") { scope.launch { c.settings.setTheme(ThemeMode.SYSTEM) } }
            Choice("Светлая", s.theme == ThemeMode.LIGHT, "theme-light") { scope.launch { c.settings.setTheme(ThemeMode.LIGHT) } }
            Choice("Тёмная", s.theme == ThemeMode.DARK, "theme-dark") { scope.launch { c.settings.setTheme(ThemeMode.DARK) } }
            HorizontalDivider()
            var scale by remember(s.textScale) { mutableFloatStateOf(s.textScale) }
            Text("Размер текста: ${(scale * 100).toInt()} %", style = MaterialTheme.typography.titleMedium)
            Slider(
                value = scale, valueRange = 0.85f..1.5f, steps = 12,
                onValueChange = { scale = it },
                onValueChangeFinished = { scope.launch { c.settings.setTextScale(scale) } },
                modifier = Modifier.testTag("text-scale"),
            )
            HorizontalDivider()
            Text("Выполнение кода", style = MaterialTheme.typography.titleMedium)
            Choice("Автоматически (изолированный W, при недоступности — A)", s.runner == RunnerMode.AUTO, "runner-auto") {
                scope.launch { c.settings.setRunner(RunnerMode.AUTO) }
            }
            Choice("Всегда изолированный (W, Pyodide)", s.runner == RunnerMode.W, "runner-w") { scope.launch { c.settings.setRunner(RunnerMode.W) } }
            Choice("Ограниченный режим (A, Chaquopy)", s.runner == RunnerMode.A, "runner-a") { scope.launch { c.settings.setRunner(RunnerMode.A) } }
            Text(
                "W — код выполняется в изолированном процессе браузерного движка без доступа к сети и файлам. " +
                    "A — нужен для asyncio, потоков и сервера FastAPI; защищает от ошибок, но не является полной изоляцией.",
                style = MaterialTheme.typography.bodySmall,
            )
            HorizontalDivider()
            Text("Редактор кода", style = MaterialTheme.typography.titleMedium)
            Choice("С подсветкой и автоотступами (CodeMirror)", !s.plainEditor, "editor-rich") { scope.launch { c.settings.setPlainEditor(false) } }
            Choice("Простое поле ввода (для слабых устройств)", s.plainEditor, "editor-plain") { scope.launch { c.settings.setPlainEditor(true) } }
            OutlinedButton(onClick = openLab) { Text("Лаборатория выполнения кода") }
            HorizontalDivider()
            Text("Режим производительности", style = MaterialTheme.typography.titleMedium)
            Choice("Экономичный: меньше нагрева и батареи (2 потока, ответы короче, модель выгружается через 2 минуты)", s.perfMode == PerfMode.ECONOMY, "perf-economy") {
                scope.launch { c.settings.setPerfMode(PerfMode.ECONOMY) }
            }
            Choice("Стандартный (4 потока, модель загружается заранее и держится 10 минут)", s.perfMode == PerfMode.STANDARD, "perf-standard") {
                scope.launch { c.settings.setPerfMode(PerfMode.STANDARD) }
            }
            Choice("Расширенный: подробнее ответы, модель держится 30 минут (больше памяти и батареи)", s.perfMode == PerfMode.EXTENDED, "perf-extended") {
                scope.launch { c.settings.setPerfMode(PerfMode.EXTENDED) }
            }
            Text(
                "Режим влияет на нейросетевого наставника — самую тяжёлую часть приложения. Уроки, редактор и запуск кода от него не зависят: " +
                    "для слабых телефонов есть ещё «Простое поле ввода» выше. Лёгкий режим наставника работает во всех режимах.",
                style = MaterialTheme.typography.bodySmall,
            )
            HorizontalDivider()
            MentorSettingsSection()
            HorizontalDivider()
            BackupSection()
            HorizontalDivider()
            CrashLogSection()
            HorizontalDivider()
            Text("О приложении", style = MaterialTheme.typography.titleMedium)
            Text(
                "Code Academy ${app.codeacademy.BuildConfig.VERSION_NAME} · бесплатно и офлайн. Python 3.13: Pyodide 0.29.5 (MPL-2.0), Chaquopy 17 (MIT). " +
                    "Редактор CodeMirror 6 (MIT). Озвучка уроков: Chatterbox (MIT), аудио содержит водяной знак Perth. Наставник: llama.cpp (MIT), модели Qwen (Qwen3, Qwen2.5-Coder; Apache-2.0, скачиваются отдельно).",
                style = MaterialTheme.typography.bodySmall,
            )
        }
    }
}

@Composable
private fun Choice(label: String, selected: Boolean, tag: String, onClick: () -> Unit) {
    Row(
        Modifier.selectable(selected = selected, onClick = onClick).padding(vertical = 4.dp).testTag(tag),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        RadioButton(selected = selected, onClick = null)
        Text(label, Modifier.padding(start = 8.dp))
    }
}

/** Имя файла копии: code-academy-backup-2026-11-22.zip */
fun backupFileName(now: java.time.LocalDate = java.time.LocalDate.now()) = "code-academy-backup-$now.zip"

/** Резервная копия, восстановление и удаление всех данных (раздел 14 ТЗ). Аккаунт и облако не нужны. */
@Composable
private fun BackupSection() {
    val c = LocalContainer.current
    val scope = rememberCoroutineScope()
    val context = androidx.compose.ui.platform.LocalContext.current
    var status by remember { mutableStateOf<String?>(null) }
    var busy by remember { mutableStateOf(false) }
    var pending by remember { mutableStateOf<Pair<android.net.Uri, app.codeacademy.data.BackupSummary>?>(null) }
    var wipeStep by remember { mutableStateOf(0) }

    fun describe(s: app.codeacademy.data.BackupSummary) =
        "уроков с прогрессом: ${s.lessons}, попыток: ${s.attempts}, проектов: ${s.projects}, настроек: ${s.settings}"

    val save = androidx.activity.compose.rememberLauncherForActivityResult(
        androidx.activity.result.contract.ActivityResultContracts.CreateDocument("application/zip"),
    ) { uri ->
        if (uri != null) scope.launch {
            busy = true
            status = runCatching {
                val out = context.contentResolver.openOutputStream(uri) ?: throw java.io.IOException("не удалось открыть файл")
                out.use { c.backup.export(it) }
            }.fold({ "Копия сохранена: ${describe(it)}." }, { "Не удалось сохранить копию: ${it.message}" })
            busy = false
        }
    }
    val open = androidx.activity.compose.rememberLauncherForActivityResult(
        androidx.activity.result.contract.ActivityResultContracts.OpenDocument(),
    ) { uri ->
        if (uri != null) scope.launch {
            busy = true
            runCatching {
                (context.contentResolver.openInputStream(uri) ?: throw java.io.IOException("не удалось открыть файл")).use { c.backup.inspect(it) }
            }.onSuccess { pending = uri to it }.onFailure { status = "Эту копию нельзя восстановить: ${it.message}" }
            busy = false
        }
    }

    Text("Данные и резервная копия", style = MaterialTheme.typography.titleMedium)
    Text(
        "Всё хранится только на этом устройстве. Копия — один ZIP-файл: прогресс, попытки, повторения, черновики, " +
            "проекты и настройки. Сохраните его, например, в «Загрузки» или на диск, чтобы перенести обучение на другой телефон.",
        style = MaterialTheme.typography.bodySmall,
    )
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        androidx.compose.material3.Button(enabled = !busy, onClick = { save.launch(backupFileName()) },
            modifier = Modifier.testTag("backup-save")) { Text("Сохранить копию") }
        OutlinedButton(enabled = !busy, onClick = { open.launch(arrayOf("application/zip", "application/x-zip-compressed", "application/octet-stream")) },
            modifier = Modifier.testTag("backup-restore")) { Text("Восстановить") }
    }
    OutlinedButton(enabled = !busy, onClick = { wipeStep = 1 }, modifier = Modifier.testTag("wipe-data")) { Text("Удалить все данные") }
    if (busy) androidx.compose.material3.CircularProgressIndicator(Modifier.padding(4.dp))
    status?.let { Text(it, modifier = Modifier.testTag("backup-status")) }

    pending?.let { (uri, sum) ->
        androidx.compose.material3.AlertDialog(
            onDismissRequest = { pending = null },
            title = { Text("Восстановить из копии?") },
            text = {
                Text("Копия от ${java.text.DateFormat.getDateTimeInstance().format(java.util.Date(sum.createdAt))} " +
                    "(версия ${sum.appVersion}): ${describe(sum)}.\n\nВсе текущие данные на устройстве будут заменены. " +
                    "Если они нужны — сначала сохраните отдельную копию.")
            },
            confirmButton = {
                androidx.compose.material3.TextButton(onClick = {
                    pending = null
                    scope.launch {
                        busy = true
                        status = runCatching {
                            (context.contentResolver.openInputStream(uri) ?: throw java.io.IOException("не удалось открыть файл"))
                                .use { c.backup.restore(it) }
                        }.fold({ "Восстановлено: ${describe(it)}." }, { "Восстановление не удалось: ${it.message}" })
                        busy = false
                    }
                }, modifier = Modifier.testTag("backup-restore-confirm")) { Text("Восстановить") }
            },
            dismissButton = { androidx.compose.material3.TextButton(onClick = { pending = null }) { Text("Отмена") } },
        )
    }
    if (wipeStep > 0) {
        androidx.compose.material3.AlertDialog(
            onDismissRequest = { wipeStep = 0 },
            title = { Text(if (wipeStep == 1) "Удалить все данные?" else "Точно удалить?") },
            text = {
                Text(if (wipeStep == 1) "Будут удалены прогресс, попытки, повторения, черновики, все проекты и настройки. " +
                    "Контент курса останется. Сначала можно сохранить копию."
                else "Это нельзя отменить без резервной копии.")
            },
            confirmButton = {
                androidx.compose.material3.TextButton(onClick = {
                    if (wipeStep == 1) { wipeStep = 2; return@TextButton }
                    wipeStep = 0
                    scope.launch {
                        busy = true
                        status = runCatching { c.backup.wipe() }.fold({ "Все данные удалены." }, { "Не удалось удалить: ${it.message}" })
                        busy = false
                    }
                }, modifier = Modifier.testTag("wipe-confirm")) { Text(if (wipeStep == 1) "Далее" else "Удалить") }
            },
            dismissButton = { androidx.compose.material3.TextButton(onClick = { wipeStep = 0 }) { Text("Отмена") } },
        )
    }
}

/** Журнал сбоев: причина, если приложение закрылось само. Хранится только на телефоне и никуда не отправляется. */
@Composable
private fun CrashLogSection() {
    val context = androidx.compose.ui.platform.LocalContext.current
    val file = remember { (context.applicationContext as app.codeacademy.CodeAcademyApp).crashLogFile }
    var text by remember { mutableStateOf(app.codeacademy.CrashLog.read(file)) }
    var shown by remember { mutableStateOf(false) }
    val clipboard = androidx.compose.ui.platform.LocalClipboardManager.current
    val count = app.codeacademy.CrashLog.count(text)

    Text("Журнал сбоев", style = MaterialTheme.typography.titleMedium)
    Text(
        if (count == 0) "Сбоев не было. Если приложение закроется само, причина сохранится здесь: только на этом телефоне, никуда не отправляется."
        else "Записей: $count. Журнал хранится только на этом телефоне; показать его разработчику или нет — решаете вы.",
        style = MaterialTheme.typography.bodySmall, modifier = Modifier.testTag("crash-status"),
    )
    if (count > 0) {
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            OutlinedButton(onClick = { shown = !shown }, modifier = Modifier.testTag("crash-show")) { Text(if (shown) "Скрыть" else "Показать") }
            OutlinedButton(onClick = { clipboard.setText(androidx.compose.ui.text.AnnotatedString(text)) }, modifier = Modifier.testTag("crash-copy")) { Text("Копировать") }
            OutlinedButton(onClick = {
                val send = android.content.Intent(android.content.Intent.ACTION_SEND).apply {
                    type = "text/plain"
                    putExtra(android.content.Intent.EXTRA_SUBJECT, "Code Academy: журнал сбоев")
                    putExtra(android.content.Intent.EXTRA_TEXT, text)
                }
                runCatching { context.startActivity(android.content.Intent.createChooser(send, "Отправить журнал").addFlags(android.content.Intent.FLAG_ACTIVITY_NEW_TASK)) }
            }, modifier = Modifier.testTag("crash-share")) { Text("Поделиться") }
        }
        OutlinedButton(onClick = { app.codeacademy.CrashLog.clear(file); text = ""; shown = false }, modifier = Modifier.testTag("crash-clear")) { Text("Очистить журнал") }
        if (shown) {
            Text(text.takeLast(6_000), style = MaterialTheme.typography.bodySmall.copy(fontFamily = androidx.compose.ui.text.font.FontFamily.Monospace),
                modifier = Modifier.testTag("crash-text"))
        }
    }
}
