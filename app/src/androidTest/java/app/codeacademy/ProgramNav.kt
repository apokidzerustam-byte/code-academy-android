package app.codeacademy

import androidx.compose.ui.semantics.SemanticsProperties
import androidx.compose.ui.semantics.getOrNull
import androidx.compose.ui.test.SemanticsMatcher
import androidx.compose.ui.test.hasTestTag
import androidx.compose.ui.test.junit4.ComposeTestRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollToNode

/**
 * Открывает урок на экране «Программа». Список ленивый, а в курсе много уроков: урок далеко от начала
 * не создан, пока список не прокручен к нему, — поэтому прокручиваем к нужному пункту, а не ищем его сразу.
 */
fun ComposeTestRule.openLessonInProgram(lessonId: String, timeoutMs: Long = 15_000) {
    // Сначала ждём загрузки уроков: пока их нет, на карточках этапов написано «ещё готовятся».
    waitUntil(timeoutMs) {
        onAllNodes(SemanticsMatcher("пункт урока") { it.config.getOrNull(SemanticsProperties.TestTag)?.startsWith("lesson-") == true })
            .fetchSemanticsNodes().isNotEmpty()
    }
    onNodeWithTag("program-list").performScrollToNode(hasTestTag("lesson-$lessonId"))
    onNodeWithTag("lesson-$lessonId").performClick()
}
