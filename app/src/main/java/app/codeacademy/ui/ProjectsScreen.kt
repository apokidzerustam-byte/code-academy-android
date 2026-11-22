package app.codeacademy.ui

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.FilterChip
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import app.codeacademy.data.ProjectInfo
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.text.DateFormat
import java.util.Date

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun ProjectsScreen(onBack: () -> Unit, openProject: (String) -> Unit) {
    val c = LocalContainer.current
    val scope = rememberCoroutineScope()
    val projects by c.projects.projects.collectAsStateWithLifecycle(emptyList())
    var creating by remember { mutableStateOf(false) }
    var deleting by remember { mutableStateOf<ProjectInfo?>(null) }

    Screen("Мои проекты", onBack) { padding ->
        LazyColumn(
            Modifier.padding(padding), contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            item {
                Button(onClick = { creating = true }, modifier = Modifier.testTag("new-project")) { Text("Новый проект") }
            }
            if (projects.isEmpty()) item { Text("Проектов пока нет. Создайте первый — например, «Калькулятор».") }
            items(projects, key = { it.id }) { p ->
                Card(Modifier.fillMaxWidth().clickable { openProject(p.id) }.testTag("project-${p.title}")) {
                    Row(Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
                        Column(Modifier.weight(1f)) {
                            Text(p.title, style = MaterialTheme.typography.titleMedium)
                            Text(
                                "Файлов: ${p.fileCount} · изменён ${DateFormat.getDateTimeInstance(DateFormat.SHORT, DateFormat.SHORT).format(Date(p.updatedAt))}",
                                style = MaterialTheme.typography.bodySmall,
                            )
                        }
                        TextButton(onClick = { deleting = p }) { Text("Удалить") }
                    }
                }
            }
        }
    }

    if (creating) {
        var title by remember { mutableStateOf("") }
        var template by remember { mutableStateOf("python") }
        AlertDialog(
            onDismissRequest = { creating = false },
            title = { Text("Новый проект") },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedTextField(title, { title = it }, label = { Text("Название") }, singleLine = true,
                        modifier = Modifier.testTag("project-title"))
                    Text("Шаблон", style = MaterialTheme.typography.labelLarge)
                    FlowRow(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                        for ((id, name) in listOf("python" to "Python", "web" to "Веб-страница", "sql" to "SQL", "kotlin" to "Kotlin")) {
                            FilterChip(selected = template == id, onClick = { template = id }, label = { Text(name) },
                                modifier = Modifier.testTag("template-$id"))
                        }
                    }
                }
            },
            confirmButton = {
                TextButton(onClick = {
                    creating = false
                    scope.launch {
                        val id = c.projects.create(title, template)
                        // Навигация — строго в главном потоке (после транзакции Room продолжение может прийти из другого).
                        withContext(Dispatchers.Main.immediate) { openProject(id) }
                    }
                }, modifier = Modifier.testTag("create-project")) { Text("Создать") }
            },
            dismissButton = { TextButton(onClick = { creating = false }) { Text("Отмена") } },
        )
    }
    deleting?.let { p ->
        AlertDialog(
            onDismissRequest = { deleting = null },
            title = { Text("Удалить «${p.title}»?") },
            text = { Text("Все файлы проекта будут удалены без возможности восстановления.") },
            confirmButton = {
                TextButton(onClick = { deleting = null; scope.launch { c.projects.delete(p.id) } }) { Text("Удалить") }
            },
            dismissButton = { TextButton(onClick = { deleting = null }) { Text("Отмена") } },
        )
    }
}
