package app.codeacademy.ui

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Card
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import app.codeacademy.content.Curriculum
import app.codeacademy.content.Lesson
import app.codeacademy.content.LessonRef
import app.codeacademy.content.PackManifest
import app.codeacademy.data.LessonStatus

@Composable
fun ProgramScreen(onBack: () -> Unit, openLesson: (LessonRef) -> Unit) {
    val c = LocalContainer.current
    var lessons by remember { mutableStateOf<List<Pair<PackManifest, Lesson>>>(emptyList()) }
    LaunchedEffect(Unit) { lessons = c.content.allLessons() }
    val progress by c.progress.lessons.collectAsStateWithLifecycle(emptyList())
    val status = progress.associate { it.lessonKey to it.status }
    val byStage = lessons.groupBy { it.first.stage }

    Screen("Программа", onBack) { padding ->
        LazyColumn(Modifier.padding(padding).testTag("program-list"), contentPadding = androidx.compose.foundation.layout.PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)) {
            items(Curriculum.stages, key = { it.number }) { stage ->
                val stageLessons = byStage[stage.number].orEmpty()
                Card(Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                        Text("Этап ${stage.number}. ${stage.title}", style = MaterialTheme.typography.titleMedium)
                        Text(stage.topics, style = MaterialTheme.typography.bodySmall)
                        if (stageLessons.isEmpty()) {
                            Text("Уроки этого этапа ещё готовятся", style = MaterialTheme.typography.labelMedium,
                                color = MaterialTheme.colorScheme.outline)
                        }
                        stageLessons.forEachIndexed { i, (p, l) ->
                            if (i > 0) HorizontalDivider()
                            val ref = LessonRef(p.id, l.id)
                            val mark = when (status[ref.key]) {
                                LessonStatus.PASSED -> "✓"
                                LessonStatus.TESTED_OUT -> "✓ (диагностика)"
                                LessonStatus.IN_PROGRESS -> "●"
                                else -> "○"
                            }
                            Text(
                                "$mark  ${l.title}",
                                style = MaterialTheme.typography.bodyLarge,
                                modifier = Modifier.fillMaxWidth().clickable { openLesson(ref) }
                                    .padding(vertical = 8.dp).testTag("lesson-${l.id}"),
                            )
                        }
                    }
                }
            }
        }
    }
}
