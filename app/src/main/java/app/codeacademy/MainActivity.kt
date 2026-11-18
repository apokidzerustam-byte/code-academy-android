package app.codeacademy

import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawingPadding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.FilterChip
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
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
import app.codeacademy.runner.RunStatus
import app.codeacademy.runner.RunnerClient
import kotlinx.coroutines.launch

/** Прототип этапа 0: ручная проверка раннера на реальном телефоне. */
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            val scheme = if (isSystemInDarkTheme()) darkColorScheme() else lightColorScheme()
            MaterialTheme(colorScheme = scheme) {
                Surface(Modifier.fillMaxSize()) { RunnerScreen() }
            }
        }
    }
}

private const val SAMPLE = "name = input()\nprint('Привет,', name)\nfor i in range(3):\n    print(i * i)\n"

@Composable
private fun RunnerScreen() {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var isolated by rememberSaveable { mutableStateOf(false) }
    var code by rememberSaveable { mutableStateOf(SAMPLE) }
    var stdin by rememberSaveable { mutableStateOf("Мир") }
    var output by rememberSaveable { mutableStateOf("") }
    var running by remember { mutableStateOf(false) }
    val client = remember(isolated) { RunnerClient(context, isolated) }
    DisposableEffect(client) { onDispose { client.close() } }

    Column(
        Modifier.safeDrawingPadding().padding(12.dp).verticalScroll(rememberScrollState()),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Text("Code Academy · прототип раннера", style = MaterialTheme.typography.titleMedium)
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            FilterChip(selected = !isolated, onClick = { isolated = false }, label = { Text("Уровень A") })
            FilterChip(selected = isolated, onClick = { isolated = true }, label = { Text("Уровень B (isolated)") })
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
                    val r = client.run(code, timeoutMs = 5_000, stdin = stdin)
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
                    val i = client.ping()
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
