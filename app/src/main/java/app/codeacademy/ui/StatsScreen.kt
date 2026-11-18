package app.codeacademy.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import app.codeacademy.data.SkillStatus

private val SKILL_STATUS = mapOf(
    SkillStatus.NOT_STUDIED to "не изучено", SkillStatus.LEARNING to "изучается",
    SkillStatus.NEEDS_REVIEW to "требует повторения", SkillStatus.MASTERED to "освоено",
    SkillStatus.CONFIRMED to "подтверждено",
)

@Composable
fun StatsScreen(onBack: () -> Unit) {
    val c = LocalContainer.current
    val attempts by c.progress.attemptsCount.collectAsStateWithLifecycle(0)
    val passed by c.progress.passedCount.collectAsStateWithLifecycle(0)
    val hints by c.progress.hintsTotal.collectAsStateWithLifecycle(0)
    val errors by c.progress.topErrors.collectAsStateWithLifecycle(emptyList())
    val skills by c.progress.skills.collectAsStateWithLifecycle(emptyList())
    val week by c.progress.activitySince(6).collectAsStateWithLifecycle(emptyList())
    val lessons by c.progress.lessons.collectAsStateWithLifecycle(emptyList())

    Screen("Статистика", onBack) { padding ->
        Column(
            Modifier.padding(padding).padding(16.dp).verticalScroll(rememberScrollState()),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Card(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Text("Попытки и точность", style = MaterialTheme.typography.titleMedium)
                    Text("Проверок решений: $attempts")
                    Text("Успешных: $passed" + if (attempts > 0) " (${passed * 100 / attempts} %)" else "")
                    Text("Открыто подсказок: $hints")
                    val minutes = week.sumOf { it.activeMs } / 60_000
                    Text("Время занятий за 7 дней: $minutes мин, решено задач: ${week.sumOf { it.tasksSolved }}")
                    Text("Время в уроках всего: ${lessons.sumOf { it.timeSpentMs } / 60_000} мин")
                }
            }
            Card(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Text("Частые ошибки", style = MaterialTheme.typography.titleMedium)
                    if (errors.isEmpty()) Text("Пока нет")
                    errors.forEach { Text("${it.type}: ${it.n}") }
                }
            }
            Card(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Text("Карта навыков", style = MaterialTheme.typography.titleMedium)
                    if (skills.isEmpty()) Text("Навыки появятся после первых заданий")
                    skills.sortedBy { it.skillId }.forEach {
                        Text("${it.skillId} — ${SKILL_STATUS[it.status] ?: it.status}, точность ${(it.accuracy * 100).toInt()} %")
                    }
                }
            }
        }
    }
}
