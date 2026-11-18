package app.codeacademy.lesson

import app.codeacademy.content.Scenario
import app.codeacademy.content.SceneAction
import kotlinx.serialization.Serializable

/** Озвучка урока (audio/narration.json, создаётся content-pipeline/narrate.py). */
@Serializable
data class NarrationMeta(
    val voice: String = "author",
    val engine: String = "",
    val watermark: String = "",
    val scenes: List<SceneAudio> = emptyList(),
)

@Serializable
data class SceneAudio(
    val id: String,
    val file: String,
    val durationMs: Long,
    val hash: String = "",
    val textHash: String = "",
    val cues: List<Cue> = emptyList(),
)

@Serializable
data class Cue(val startMs: Long, val endMs: Long, val text: String)

data class TimedAction(val action: SceneAction, val startMs: Long, val durationMs: Long) {
    val endMs get() = startMs + durationMs
}

data class SceneTiming(
    val index: Int,
    val id: String,
    val title: String,
    /** Начало сцены на общей шкале урока. */
    val startMs: Long,
    val durationMs: Long,
    val actions: List<TimedAction>,
    val cues: List<Cue>,
    /** Файл озвучки сцены или null, если озвучки нет (урок идёт по таймеру с субтитрами). */
    val audioFile: String?,
) {
    val endMs get() = startMs + durationMs
}

/** Что показывает плеер в момент времени t. */
data class PlayerFrame(
    val sceneIndex: Int,
    val sceneTitle: String,
    val file: String,
    val code: String,
    val typing: Boolean,
    val highlight: Set<Int>,
    val running: Boolean,
    val output: String,
    val outputIsError: Boolean,
    val note: String?,
    val caption: String?,
)

/**
 * Шкала времени анимированного урока. Чистая логика без Android: кадр в любой момент
 * вычисляется заново из сценария (перемотка = просто другой t).
 */
class LessonTimeline(scenario: Scenario, narration: NarrationMeta? = null) {
    val scenes: List<SceneTiming>
    val totalMs: Long
    val hasAudio: Boolean

    init {
        val audioById = narration?.scenes?.associateBy { it.id }.orEmpty()
        var t = 0L
        val list = ArrayList<SceneTiming>()
        scenario.scenes.forEachIndexed { i, scene ->
            val audio = audioById[scene.id]
            val cues = audio?.cues?.takeIf { it.isNotEmpty() } ?: estimateCues(scene.narration)
            val duration = audio?.durationMs?.takeIf { it > 0 } ?: (cues.lastOrNull()?.endMs?.plus(GAP_MS) ?: MIN_SCENE_MS)
                .coerceAtLeast(MIN_SCENE_MS)
            list += SceneTiming(
                index = i, id = scene.id, title = scene.title ?: "Сцена ${i + 1}",
                startMs = t, durationMs = duration,
                actions = schedule(scene.actions, cues, duration),
                cues = cues, audioFile = audio?.file,
            )
            t += duration
        }
        scenes = list
        totalMs = t
        hasAudio = scenes.isNotEmpty() && scenes.all { it.audioFile != null }
    }

    fun sceneAt(t: Long): Int {
        if (scenes.isEmpty()) return 0
        val tt = t.coerceIn(0, totalMs)
        return scenes.indexOfLast { it.startMs <= tt }.coerceAtLeast(0).let { i ->
            // Ровно на конце урока остаёмся в последней сцене.
            if (i == scenes.size - 1 || tt < scenes[i].endMs) i else i + 1
        }
    }

    fun frame(t: Long): PlayerFrame {
        val tt = t.coerceIn(0, totalMs)
        val current = sceneAt(tt)
        val files = linkedMapOf("main.py" to "")
        var file = "main.py"
        var highlight = emptySet<Int>()
        var output = ""
        var isError = false
        var running = false
        var typing = false
        var note: String? = null
        for (s in scenes) {
            if (s.index > current) break
            val local = tt - s.startMs
            // Подсветка и заметка относятся к своей сцене.
            highlight = emptySet()
            note = null
            for (ta in s.actions) {
                if (s.index == current && ta.startMs > local) break
                val a = ta.action
                val done = s.index < current || local >= ta.endMs
                val progress = if (done) 1f else ((local - ta.startMs).toFloat() / ta.durationMs.coerceAtLeast(1)).coerceIn(0f, 1f)
                when (a.type) {
                    "clear" -> { files[a.file] = ""; file = a.file; highlight = emptySet(); output = ""; isError = false }
                    "type" -> {
                        val text = a.text.orEmpty()
                        val n = if (done) text.length else (text.length * progress).toInt().coerceIn(0, text.length)
                        files[a.file] = files[a.file].orEmpty() + text.take(n)
                        file = a.file
                        typing = !done
                    }
                    "highlight" -> highlight = a.lines.toSet()
                    "run" -> { output = ""; isError = false; running = !done }
                    "output" -> { output = a.text.orEmpty(); isError = a.stream == "stderr"; running = false }
                    "note" -> note = a.md
                }
            }
        }
        val scene = scenes.getOrNull(current)
        val local = tt - (scene?.startMs ?: 0)
        val caption = scene?.cues?.lastOrNull { it.startMs <= local && local < it.endMs + GAP_MS }?.text
        return PlayerFrame(
            sceneIndex = current, sceneTitle = scene?.title.orEmpty(),
            file = file, code = files[file].orEmpty(), typing = typing, highlight = highlight,
            running = running, output = output, outputIsError = isError, note = note, caption = caption,
        )
    }

    companion object {
        const val GAP_MS = 280L
        const val MIN_SCENE_MS = 2500L
        /** Темп чтения без озвучки (≈ 14 символов в секунду — спокойная речь). */
        const val MS_PER_CHAR = 70L
        private const val LEAD_IN_MS = 300L
        private const val MAX_PHRASE_CHARS = 220

        /** Те же правила деления на фразы, что в content-pipeline/narrate.py (split_phrases). */
        fun splitPhrases(text: String): List<String> {
            val sentences = text.trim().split(Regex("(?<=[.!?…])\\s+")).map { it.trim() }.filter { it.isNotEmpty() }
            val out = ArrayList<String>()
            for (sentence in sentences) {
                var s = sentence
                while (s.length > MAX_PHRASE_CHARS) {
                    // Как str.rfind(sub, 0, MAX) в Python: подстрока целиком в первых MAX символах.
                    fun rfind(sub: String) = s.lastIndexOf(sub, MAX_PHRASE_CHARS - sub.length)
                    var cut = maxOf(rfind(", "), rfind(" — "), rfind(": "))
                    if (cut < 40) cut = rfind(" ")
                    if (cut <= 0) break
                    out += s.substring(0, cut + 1).trim()
                    s = s.substring(cut + 1).trim()
                }
                if (s.isNotEmpty()) out += s
            }
            return out
        }

        fun estimateCues(narration: String): List<Cue> {
            var t = 0L
            return splitPhrases(narration).map { p ->
                val d = (p.length * MS_PER_CHAR).coerceAtLeast(900)
                Cue(t, t + d, p).also { t += d + GAP_MS }
            }
        }

        private fun naturalMs(a: SceneAction): Long = when (a.type) {
            "type" -> (a.text.orEmpty().length * 55L).coerceIn(400, 6000)
            "clear" -> 300
            "highlight" -> 700
            "run" -> 900
            "output" -> 500
            "note" -> 900
            "pause" -> a.ms
            else -> 300
        }

        /**
         * Раскладывает действия по сцене. Действие с cue начинается вместе с этой фразой озвучки,
         * остальные идут друг за другом; каждый отрезок между опорными точками растягивается или
         * сжимается, чтобы анимация шла вместе с речью и заканчивалась до конца сцены.
         */
        fun schedule(actions: List<SceneAction>, cues: List<Cue>, durationMs: Long): List<TimedAction> {
            if (actions.isEmpty()) return emptyList()
            val end = (durationMs * 92 / 100).coerceAtLeast(LEAD_IN_MS + 1)
            // Опорные точки: индекс действия → время начала.
            val anchors = sortedMapOf(0 to LEAD_IN_MS)
            actions.forEachIndexed { i, a ->
                a.cue?.let { c -> cues.getOrNull(c)?.let { anchors[i] = it.startMs.coerceIn(0, end) } }
            }
            val result = ArrayList<TimedAction>(actions.size)
            val keys = anchors.keys.toList()
            for ((k, from) in keys.withIndex()) {
                val to = keys.getOrNull(k + 1) ?: actions.size
                val segStart = maxOf(anchors.getValue(from), result.lastOrNull()?.endMs ?: 0)
                val segEnd = (keys.getOrNull(k + 1)?.let { anchors.getValue(it) } ?: end).coerceAtLeast(segStart + 1)
                val seg = actions.subList(from, to)
                val natural = seg.sumOf { naturalMs(it) }.coerceAtLeast(1)
                val scale = minOf((segEnd - segStart).toDouble() / natural, 2.5)
                var t = segStart
                for (a in seg) {
                    val d = (naturalMs(a) * scale).toLong().coerceAtLeast(if (a.type == "type") 150 else 50)
                    result += TimedAction(a, t, d)
                    t += d
                }
            }
            return result
        }
    }
}
