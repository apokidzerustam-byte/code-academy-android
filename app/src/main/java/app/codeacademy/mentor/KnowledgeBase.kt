package app.codeacademy.mentor

import app.codeacademy.content.CommonMistake
import kotlin.math.ln

/** Урок для базы знаний: конспект, навыки, частые ошибки. */
data class LessonDoc(
    val link: LessonLink,
    val skills: List<String>,
    val notes: String,
    val commonMistakes: List<CommonMistake>,
    /** Задания урока: id, тип и название (для «дай упражнение»). */
    val assignments: List<Triple<String, String, String>> = emptyList(),
)

/**
 * Поиск по конспектам и частым ошибкам курса (BM25 по основам слов). Работает в памяти:
 * конспекты небольшие, индекс строится за миллисекунды.
 */
class KnowledgeBase(val lessons: List<LessonDoc>) {

    data class Passage(val lesson: LessonLink, val heading: String, val text: String, val score: Double)

    private class Doc(val lesson: LessonLink, val heading: String, val text: String, val terms: Map<String, Int>, val len: Int)

    private val docs: List<Doc> = lessons.flatMap { l -> sections(l) }
    private val df: Map<String, Int> = HashMap<String, Int>().also { m -> docs.forEach { d -> d.terms.keys.forEach { m[it] = (m[it] ?: 0) + 1 } } }
    private val avgLen = docs.map { it.len }.average().takeIf { !it.isNaN() && it > 0 } ?: 1.0
    private val bySkill: Map<String, LessonDoc> = HashMap<String, LessonDoc>().also { m ->
        lessons.forEach { l -> l.skills.forEach { s -> m.putIfAbsent(s, l) } }
    }

    fun lessonOfSkill(skill: String): LessonDoc? = bySkill[skill]
    fun lesson(key: String): LessonDoc? = lessons.firstOrNull { it.link.key == key }

    fun search(query: String, k: Int = 3, preferLesson: String? = null): List<Passage> {
        val q = terms(query).keys
        if (q.isEmpty()) return emptyList()
        val n = docs.size.toDouble()
        return docs.map { d ->
            var s = 0.0
            for (t in q) {
                val f = d.terms[t] ?: continue
                val idf = ln(1 + (n - (df[t] ?: 0) + 0.5) / ((df[t] ?: 0) + 0.5))
                s += idf * f * (K1 + 1) / (f + K1 * (1 - B + B * d.len / avgLen))
            }
            if (preferLesson != null && d.lesson.key == preferLesson && s > 0) s *= 1.3
            // Объяснение темы — из конспекта; частые ошибки ниже по приоритету.
            if (d.heading.startsWith(MISTAKE)) s *= 0.6
            Passage(d.lesson, d.heading, d.text, s)
        }.filter { it.score > 0 }.sortedByDescending { it.score }.take(k)
    }

    private fun sections(l: LessonDoc): List<Doc> {
        val out = mutableListOf<Doc>()
        var heading = l.link.title
        val buf = StringBuilder()
        fun flush() {
            val text = buf.toString().trim()
            if (text.isNotEmpty()) out += doc(l.link, heading, text)
            buf.clear()
        }
        for (line in l.notes.lines()) {
            if (line.startsWith("#")) {
                flush()
                heading = line.trimStart('#', ' ').ifBlank { l.link.title }
            } else buf.append(line).append('\n')
        }
        flush()
        l.commonMistakes.forEach { m ->
            out += doc(l.link, "$MISTAKE${m.mistake}", "${m.mistake}. ${m.fix}" + (m.errorType?.let { " ($it)" } ?: ""))
        }
        return out
    }

    private fun doc(link: LessonLink, heading: String, text: String): Doc {
        val t = terms("$heading $heading $text")
        return Doc(link, heading, text, t, t.values.sum())
    }

    companion object {
        private const val MISTAKE = "Частая ошибка: "
        private const val K1 = 1.4
        private const val B = 0.75

        private val STOP = setOf(
            "и", "в", "во", "не", "что", "он", "на", "я", "с", "со", "как", "а", "то", "все", "она", "так", "его", "но", "да", "ты",
            "к", "у", "же", "вы", "за", "бы", "по", "только", "ее", "мне", "было", "вот", "от", "меня", "еще", "нет", "о", "из",
            "ему", "теперь", "когда", "даже", "ну", "ли", "если", "уже", "или", "ни", "быть", "был", "него", "до", "вас", "нибудь",
            "это", "этот", "эта", "эти", "мой", "моя", "мое", "мои", "можно", "нужно", "надо", "почему", "зачем", "такое", "объясни",
            "расскажи", "пожалуйста", "the", "a", "an", "is", "of", "to", "in", "and", "what", "how",
        )
        private val ENDINGS = listOf(
            "иями", "ями", "ами", "ого", "его", "ому", "ему", "ыми", "ими", "ешь", "ете", "ите", "ует", "уют", "ают", "яют",
            "ать", "ять", "еть", "ить", "ах", "ях", "ов", "ев", "ей", "ой", "ий", "ый", "ая", "яя", "ое", "ее", "ые", "ие", "ую", "юю",
            "ом", "ем", "ам", "ям", "ть", "ет", "ют", "ит", "ат", "ят", "ия", "ие", "а", "я", "о", "е", "ы", "и", "у", "ю", "ь",
        )

        /** Простая основа русского слова: срезается самое длинное окончание, основа не короче 3 букв. */
        fun stem(word: String): String {
            val w = word.lowercase().replace('ё', 'е')
            if (w.length <= 3 || w.any { it in 'a'..'z' }) return w
            for (e in ENDINGS) if (w.endsWith(e) && w.length - e.length >= 3) return w.dropLast(e.length)
            return w
        }

        fun terms(text: String): Map<String, Int> {
            val m = HashMap<String, Int>()
            Regex("[\\p{L}_][\\p{L}\\d_]*(?:-[\\p{L}\\d_]+)*").findAll(text).forEach {
                val w = it.value.lowercase().replace('ё', 'е')
                // «f-строка» — отдельный термин (и его части тоже).
                val parts = if ('-' in w) w.split('-').filter { p -> p.length >= 2 } + w else listOf(w)
                for (part in parts) {
                    if (part in STOP || part.length < 2) continue
                    val s = if ('-' in part) part.split('-').joinToString("-") { stem(it) } else stem(part)
                    m[s] = (m[s] ?: 0) + 1
                }
            }
            return m
        }
    }
}
