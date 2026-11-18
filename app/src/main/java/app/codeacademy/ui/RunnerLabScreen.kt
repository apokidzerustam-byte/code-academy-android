package app.codeacademy.ui

import android.content.Intent
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.FilterChip
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.unit.dp
import app.codeacademy.editor.EditorActivity
import app.codeacademy.runner.CodeRunner
import app.codeacademy.runner.PyodideRunner
import app.codeacademy.runner.RunStatus
import app.codeacademy.runner.RunnerClient
import kotlinx.coroutines.launch

private const val SAMPLE = "name = input()\nprint('Привет,', name)\nfor i in range(3):\n    print(i * i)\n"

@Composable
fun RunnerLabScreen(onBack: () -> Unit) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var mode by rememberSaveable { mutableStateOf("W") }
    var code by rememberSaveable { mutableStateOf(SAMPLE) }
    var stdin by rememberSaveable { mutableStateOf("Мир") }
    var output by rememberSaveable { mutableStateOf("") }
    var running by remember { mutableStateOf(false) }
    val client: CodeRunner = remember(mode) {
        when (mode) {
            "A" -> RunnerClient(context, isolated = false)
            else -> PyodideRunner(context)
        }
    }
    DisposableEffect(client) { onDispose { client.close() } }

    Screen("Лаборатория выполнения кода", onBack) { padding ->
    Column(
        Modifier.padding(padding).padding(12.dp).verticalScroll(rememberScrollState()),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            FilterChip(selected = mode == "W", onClick = { mode = "W" }, label = { Text("W · Pyodide (изоляция)") })
            FilterChip(selected = mode == "A", onClick = { mode = "A" }, label = { Text("A · Chaquopy") })
        }
        OutlinedTextField(
            value = code, onValueChange = { code = it },
            label = { Text("Код Python") },
            textStyle = MaterialTheme.typography.bodyMedium.copy(fontFamily = FontFamily.Monospace),
            modifier = Modifier.fillMaxWidth().heightIn(min = 160.dp),
        )
        OutlinedTextField(
            value = stdin, onValueChange = { stdin = it },
            label = { Text("Ввод (stdin)") }, modifier = Modifier.fillMaxWidth(),
        )
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(enabled = !running, onClick = {
                running = true
                output = "Выполняется…"
                scope.launch {
                    val r = client.run(code, timeoutMs = 5_000, stdin = stdin)  // первый запуск W ждёт загрузки Pyodide
                    output = buildString {
                        append("[${r.status}] ${r.durationMs} мс\n")
                        append(r.stdout)
                        if (r.stderr.isNotEmpty()) append("\n--- stderr ---\n").append(r.stderr)
                        if (r.truncated) append("\n(вывод обрезан)")
                    }
                    running = false
                }
            }) { Text("Запустить") }
            OutlinedButton(enabled = running, onClick = { client.stop() }) { Text("Стоп") }
            OutlinedButton(onClick = {
                scope.launch {
                    val i = client.prepare()
                    output = if (i == null) "Раннер не ответил" else
                        "Python: ${i.pythonStarted}, старт ${i.startMs} мс\npid=${i.pid} uid=${i.uid} isolated=${i.isolated}\n${i.pyInfo ?: ""}\n${i.startError ?: ""}"
                }
            }) { Text("Инфо") }
        }
        OutlinedButton(onClick = { context.startActivity(Intent(context, EditorActivity::class.java)) }) {
            Text("Прототип редактора (CodeMirror)")
        }
        Text(
            output,
            style = MaterialTheme.typography.bodySmall.copy(fontFamily = FontFamily.Monospace),
            color = if (output.startsWith("[${RunStatus.OK}]")) MaterialTheme.colorScheme.onSurface else MaterialTheme.colorScheme.error,
        )
    }
}
}
