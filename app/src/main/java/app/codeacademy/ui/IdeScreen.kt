package app.codeacademy.ui

import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.FilterChip
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Tab
import androidx.compose.material3.TabRow
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.key
import androidx.compose.runtime.mutableStateMapOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import app.codeacademy.data.ProjectRepository
import app.codeacademy.ide.TrainingShell
import app.codeacademy.runner.CodeRunner
import app.codeacademy.runner.ProjectFiles
import app.codeacademy.runner.RunResult
import app.codeacademy.runner.RunStatus
import app.codeacademy.settings.Settings
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

private fun languageOf(path: String) = when (path.substringAfterLast('.', "").lowercase()) {
    "py" -> "python"
    "js" -> "javascript"
    "html", "htm" -> "html"
    "css" -> "css"
    "sql" -> "sql"
    else -> "python"
}

/** Текст результата запуска для консоли/терминала. */
fun formatRun(r: RunResult): String = buildString {
    when (r.status) {
        RunStatus.OK -> {}
        RunStatus.TIMEOUT -> append("[Превышено время выполнения — возможно, бесконечный цикл]\n")
        RunStatus.STOPPED -> append("[Остановлено]\n")
        RunStatus.CRASHED -> append("[Выполнение аварийно завершилось]\n")
        RunStatus.UNAVAILABLE -> append("[Исполнитель недоступен]\n")
        else -> {}
    }
    append(r.stdout)
    if (r.stderr.isNotBlank()) {
        if (isNotEmpty() && !endsWith("\n")) append('\n')
        append(r.stderr)
    }
    if (r.truncated) append("\n(вывод обрезан)")
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun IdeScreen(projectId: String, settings: Settings, onBack: () -> Unit) {
    val c = LocalContainer.current
    val scope = rememberCoroutineScope()
    val projects by c.projects.projects.collectAsStateWithLifecycle(emptyList())
    val title = projects.firstOrNull { it.id == projectId }?.title ?: "Проект"
    val files = remember { mutableStateMapOf<String, String>() }
    var loaded by remember { mutableStateOf(false) }
    var current by rememberSaveable { mutableStateOf("main.py") }
    var tab by rememberSaveable { mutableStateOf(0) }
    var stdin by rememberSaveable { mutableStateOf("") }
    var console by rememberSaveable { mutableStateOf("") }
    var term by rememberSaveable { mutableStateOf("") }
    var termLine by remember { mutableStateOf("") }
    var running by remember { mutableStateOf(false) }
    var runner by remember { mutableStateOf<CodeRunner?>(null) }
    var newFile by remember { mutableStateOf(false) }
    var confirmDelete by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }

    LaunchedEffect(projectId) {
        files.clear()
        files.putAll(c.projects.files(projectId))
        if (current !in files) current = files.keys.firstOrNull { it.endsWith(".py") } ?: files.keys.firstOrNull() ?: "main.py"
        loaded = true
    }
    // Автосохранение файлов проекта.
    val snapshot = files.toMap()
    LaunchedEffect(snapshot) {
        if (!loaded) return@LaunchedEffect
        delay(500)
        c.projects.replaceAll(projectId, snapshot)
    }
    // При уходе с экрана сохраняем то, что не успело попасть в автосохранение.
    // Небольшая пауза — чтобы дошёл последний текст из редактора (flush при закрытии).
    val latestLoaded by rememberUpdatedState(loaded)
    DisposableEffect(projectId) {
        onDispose {
            if (latestLoaded) c.appScope.launch {
                delay(300)
                c.projects.replaceAll(projectId, files.toMap())
            }
        }
    }
    val currentSettings by rememberUpdatedState(settings)

    // Файлы, с которыми работает терминал (копия на время команды).
    val shellFiles = remember(projectId) { mutableMapOf<String, String>() }

    suspend fun runFile(path: String, input: String, target: MutableMap<String, String> = files): String {
        val (_, r) = resolveRunner(c, currentSettings.runner, "W")
        runner = r
        running = true
        val code = target[path] ?: return "Файл $path не найден".also { running = false }
        val res = r.run(code, 10_000, input, projectId, target.toMap())
        res.files?.let { back ->
            // Программа могла создать или изменить файлы — показываем их в проекте.
            val keep = target.filterKeys { it.endsWith("/.keep") }
            target.clear(); target.putAll(keep + back)
        }
        running = false
        return formatRun(res)
    }

    val shell = remember(projectId) {
        TrainingShell(shellFiles) { path, _ -> runFile(path, "", shellFiles) }
    }

    Screen(title, onBack) { padding ->
        Column(Modifier.padding(padding).imePadding().verticalScroll(rememberScrollState()).padding(12.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)) {
            if (!loaded) return@Column
            Row(Modifier.horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                files.keys.filter { !it.endsWith("/.keep") }.sorted().forEach { f ->
                    FilterChip(selected = f == current, enabled = !running, onClick = { current = f }, label = { Text(f) },
                        modifier = Modifier.testTag("file-$f"))
                }
                TextButton(enabled = !running, onClick = { newFile = true }, modifier = Modifier.testTag("new-file")) { Text("+ файл") }
            }
            if (current in files) {
                key(current) {
                    val path = current // текст из этого редактора пишется только в его файл
                    CodeEditor(
                        value = files[path].orEmpty(),
                        onValueChange = { if (path in files) files[path] = it },
                        language = languageOf(path),
                        plain = settings.plainEditor,
                        height = 300.dp,
                        // Пока программа работает, файлы не меняются: результат запуска не затрёт правки.
                        readOnly = running,
                    )
                }
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    TextButton(enabled = !running, onClick = { confirmDelete = true }) { Text("Удалить файл") }
                }
            } else {
                Text("Нет открытого файла. Создайте файл кнопкой «+ файл».")
            }
            TabRow(selectedTabIndex = tab) {
                Tab(tab == 0, { tab = 0 }, text = { Text("Консоль") }, modifier = Modifier.testTag("ide-console-tab"))
                Tab(tab == 1, { tab = 1 }, text = { Text("Терминал") }, modifier = Modifier.testTag("ide-terminal-tab"))
            }
            if (tab == 0) {
                OutlinedTextField(stdin, { stdin = it }, label = { Text("Ввод для программы (каждое значение — с новой строки)") },
                    textStyle = MaterialTheme.typography.bodyMedium.copy(fontFamily = FontFamily.Monospace),
                    modifier = Modifier.fillMaxWidth().testTag("stdin"))
                FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    val target = if ("main.py" in files) "main.py" else current
                    Button(enabled = !running && target in files, onClick = {
                        scope.launch { console = "▶ $target\n" + runFile(target, stdin) }
                    }, modifier = Modifier.testTag("ide-run")) { Text("Запустить $target") }
                    OutlinedButton(enabled = running, onClick = { runner?.stop() }, modifier = Modifier.testTag("ide-stop")) { Text("Стоп") }
                    OutlinedButton(onClick = { console = "" }) { Text("Очистить") }
                    if (running) CircularProgressIndicator(Modifier.padding(4.dp))
                }
                CodeBlock(console.ifEmpty { "Здесь появится вывод программы." }, Modifier.testTag("ide-output"))
            } else {
                CodeBlock(term.ifEmpty { "Учебный терминал. Введите help." }, Modifier.testTag("term-output"))
                OutlinedTextField(
                    termLine, { termLine = it },
                    label = { Text(if (running) "выполняется… (Стоп — на вкладке «Консоль»)" else shell.prompt) }, singleLine = true,
                    enabled = !running,
                    textStyle = MaterialTheme.typography.bodyMedium.copy(fontFamily = FontFamily.Monospace),
                    keyboardOptions = KeyboardOptions(imeAction = ImeAction.Send),
                    keyboardActions = KeyboardActions(onSend = {
                        if (running) return@KeyboardActions
                        val line = termLine
                        termLine = ""
                        scope.launch {
                            shell.files.clear(); shell.files.putAll(files)
                            val prompt = shell.prompt
                            val res = shell.exec(line)
                            files.clear(); files.putAll(shell.files)
                            term = if (res.clear) "" else (term + prompt + line + "\n" + res.output.let { if (it.isEmpty()) "" else it.trimEnd() + "\n" }).takeLast(20_000)
                            if (current !in files) current = files.keys.firstOrNull { !it.endsWith("/.keep") } ?: current
                        }
                    }),
                    modifier = Modifier.fillMaxWidth().testTag("term-input"),
                )
            }
        }
    }

    if (newFile) {
        var name by remember { mutableStateOf("") }
        AlertDialog(
            onDismissRequest = { newFile = false },
            title = { Text("Новый файл") },
            text = {
                Column {
                    OutlinedTextField(name, { name = it }, label = { Text("Имя, например utils.py или data/notes.txt") },
                        singleLine = true, modifier = Modifier.testTag("file-name"))
                    error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
                }
            },
            confirmButton = {
                TextButton(onClick = {
                    val rel = runCatching { ProjectFiles.safeRel(name.trim()) }.getOrNull()
                    error = when {
                        rel == null || rel == ProjectRepository.META -> "Недопустимое имя файла"
                        rel.substringAfterLast('/') == ".keep" -> "Недопустимое имя файла"
                        rel in files || files.keys.any { it.startsWith("$rel/") } -> "Такой файл или папка уже есть"
                        else -> ProjectFiles.conflict(files.keys.filter { !it.endsWith("/.keep") } + rel)
                    }
                    if (error == null && rel != null) { files[rel] = ""; current = rel; newFile = false }
                }, modifier = Modifier.testTag("create-file")) { Text("Создать") }
            },
            dismissButton = { TextButton(onClick = { newFile = false; error = null }) { Text("Отмена") } },
        )
    }
    if (confirmDelete) {
        AlertDialog(
            onDismissRequest = { confirmDelete = false },
            title = { Text("Удалить $current?") },
            confirmButton = {
                TextButton(onClick = {
                    files.remove(current)
                    current = files.keys.firstOrNull { !it.endsWith("/.keep") } ?: "main.py"
                    confirmDelete = false
                }) { Text("Удалить") }
            },
            dismissButton = { TextButton(onClick = { confirmDelete = false }) { Text("Отмена") } },
        )
    }
}
