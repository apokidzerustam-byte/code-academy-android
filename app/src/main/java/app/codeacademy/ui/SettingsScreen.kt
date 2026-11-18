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
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
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
            Text("О приложении", style = MaterialTheme.typography.titleMedium)
            Text(
                "Code Academy · бесплатно и офлайн. Python 3.13: Pyodide 0.29.5 (MPL-2.0), Chaquopy 17 (MIT). " +
                    "Редактор CodeMirror 6 (MIT). Озвучка уроков: Chatterbox (MIT), аудио содержит водяной знак Perth.",
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
