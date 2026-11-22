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
import app.codeacademy.runner.WebRunner
import app.codeacademy.settings.Settings
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

private fun languageOf(path: String) = when (path.substringAfterLast('.', "").lowercase()) {
    "py" -> "python"
    "js" -> "javascript"
    "html", "htm" -> "html"
    "css" -> "css"
    "sql" -> "sql"
    "kt", "kts" -> "kotlin"
    else -> "python"
}

private fun ext(path: String) = path.substringAfterLast('.', "").lowercase()

/**
 * Какой файл запускать кнопкой «Запустить». Python — main.py, если он есть (модули импортируются из него);
 * HTML, SQL, Kotlin — открытый файл; CSS и JS веб-проекта — его HTML-страница.
 */
fun runTarget(files: Set<String>, current: String): String? {
    val html = files.firstOrNull { it == "index.html" } ?: files.firstOrNull { ext(it) in setOf("html", "htm") }
    return when (ext(current)) {
        "py" -> if ("main.py" in files) "main.py" else current
        "html", "htm", "sql", "kt", "kts" -> current
        "js" -> html ?: current
        "css" -> html
        else -> when {
            "main.py" in files -> "main.py"
            html != null -> html
            "Main.kt" in files -> "Main.kt"
            else -> files.firstOrNull { ext(it) == "kt" } ?: files.firstOrNull { ext(it) == "sql" && it != "schema.sql" }
        }
    }.takeIf { it != null && it in files }
}

/** Строки ввода терминала: каждая непустая строка — отдельная команда. */
fun terminalCommands(input: String): List<String> =
    input.split('\n', '\r').map { it.trim() }.filter { it.isNotEmpty() }

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

/** Имя архива из названия проекта: буквы, цифры и дефисы. */
fun zipName(title: String): String {
    val base = title.trim().lowercase().replace(Regex("[^\\p{L}\\p{N}]+"), "-").trim('-').ifBlank { "project" }
    return "$base.zip"
}

/** Файлы проекта в ZIP (UTF-8); служебные записи (.project, …/.keep) не попадают в архив. */
fun writeProjectZip(files: Map<String, String>, out: java.io.OutputStream) {
    java.util.zip.ZipOutputStream(out).use { zip ->
        for ((path, text) in files.toSortedMap()) {
            if (path == ProjectRepository.META || path.endsWith("/.keep")) continue
            zip.putNextEntry(java.util.zip.ZipEntry(path))
            zip.write(text.toByteArray(Charsets.UTF_8))
            zip.closeEntry()
        }
    }
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
    val preview = remember { WebPreviewController() }
    var showPreview by rememberSaveable { mutableStateOf(false) }
    var newFile by remember { mutableStateOf(false) }
    var confirmDelete by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    val context = androidx.compose.ui.platform.LocalContext.current
    // Экспорт проекта архивом: например, чтобы загрузить проект Kotlin на GitHub и собрать его в Actions.
    val exportZip = androidx.activity.compose.rememberLauncherForActivityResult(
        androidx.activity.result.contract.ActivityResultContracts.CreateDocument("application/zip"),
    ) { uri ->
        if (uri != null) scope.launch {
            val snapshotFiles = files.toMap()
            val ok = kotlinx.coroutines.withContext(kotlinx.coroutines.Dispatchers.IO) {
                runCatching {
                    context.contentResolver.openOutputStream(uri)?.use { out -> writeProjectZip(snapshotFiles, out) }
                        ?: throw java.io.IOException("не удалось открыть файл")
                }
            }
            console = ok.fold({ "Проект сохранён в ZIP (${snapshotFiles.size} файлов).\n" }, { "Экспорт не удался: ${it.message}\n" }) + console
            tab = 0
        }
    }

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
        val code = target[path] ?: return "Файл $path не найден"
        val webLang = when (ext(path)) {
            "html", "htm" -> "html"
            "js" -> "js"
            "sql" -> "sql"
            "kt", "kts" -> "kotlin"
            else -> null
        }
        if (webLang != null) {
            running = true
            try {
                val res = if (webLang == "html") {
                    showPreview = true
                    preview.onOutput = { _, text -> console = (console + text).takeLast(20_000) }
                    preview.run("html", code, target.toMap(), entry = path, stdin = input)
                } else {
                    val (_, r) = resolveRunner(c, currentSettings.runner, webLang)
                    runner = r
                    // SQL: schema.sql (таблицы и данные) выполняется перед запускаемым файлом.
                    val setup = if (webLang == "sql" && path != "schema.sql") target["schema.sql"].orEmpty() else ""
                    (r as WebRunner).runWith(code, 10_000, input, target.toMap(), setup, entry = path)
                }
                return formatRun(res)
            } finally {
                running = false
            }
        }
        // FastAPI есть только в режиме A (Chaquopy): в Pyodide его нет.
        val needsA = Regex("^\\s*(from|import)\\s+(fastapi|starlette|pydantic)\\b", RegexOption.MULTILINE).containsMatchIn(code)
        val (_, r) = resolveRunner(c, currentSettings.runner, if (needsA) "A" else "W")
        runner = r
        running = true
        val res = r.run(code, if (needsA) 25_000 else 10_000, input, projectId, target.toMap())
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
            if (loaded) {
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
                    TextButton(enabled = !running, onClick = { exportZip.launch(zipName(title)) },
                        modifier = Modifier.testTag("export-zip")) { Text("Экспорт ZIP") }
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
                    val target = runTarget(files.keys, current)
                    Button(enabled = !running && target != null, onClick = {
                        val t = target ?: return@Button
                        scope.launch {
                            console = "▶ $t\n"
                            val out = runFile(t, stdin)
                            console = "▶ $t\n" + out
                        }
                    }, modifier = Modifier.testTag("ide-run")) { Text(if (target != null) "Запустить $target" else "Нечего запускать") }
                    OutlinedButton(enabled = running || showPreview, onClick = { runner?.stop(); preview.stop() },
                        modifier = Modifier.testTag("ide-stop")) { Text("Стоп") }
                    OutlinedButton(onClick = { console = "" }) { Text("Очистить") }
                    if (running) CircularProgressIndicator(Modifier.padding(4.dp))
                }
                if (showPreview) {
                    Text("Страница", style = MaterialTheme.typography.titleSmall)
                    WebPreview(preview, height = 320.dp)
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
                            // Вставка нескольких строк (например, скопированных из инструкции):
                            // каждая строка выполняется отдельной командой, по порядку.
                            for (cmd in terminalCommands(line)) {
                                shell.files.clear(); shell.files.putAll(files)
                                val prompt = shell.prompt
                                val res = shell.exec(cmd)
                                files.clear(); files.putAll(shell.files)
                                term = if (res.clear) "" else (term + prompt + cmd + "\n" + res.output.let { if (it.isEmpty()) "" else it.trimEnd() + "\n" }).takeLast(20_000)
                            }
                            if (current !in files) current = files.keys.firstOrNull { !it.endsWith("/.keep") } ?: current
                        }
                    }),
                    modifier = Modifier.fillMaxWidth().testTag("term-input"),
                )
            }
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
