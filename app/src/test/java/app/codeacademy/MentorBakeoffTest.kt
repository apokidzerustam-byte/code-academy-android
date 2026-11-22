package app.codeacademy

import app.codeacademy.mentor.Intent
import app.codeacademy.mentor.Mentor
import app.codeacademy.mentor.PromptBuilder
import app.codeacademy.mentor.Source
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertTrue
import org.junit.Assume.assumeTrue
import org.junit.Test
import java.io.File

/**
 * Сравнение моделей на реальных запросах наставника (workflow «Сравнение моделей наставника»).
 * Для каждой модели — одни и те же задания и вопросы «Объясни тему», «Дай подсказку», «Почему ошибка?»;
 * в журнал и в отчёт попадают ответы целиком, скорость и число токенов запроса. Здесь ничего не «зачитывается как успех»:
 * тест падает только если модель не ответила ни разу; качество оценивается по ответам в отчёте.
 *
 * Переменные: CA_MENTOR_CLI — mentor_cli; CA_BAKEOFF — модели через «;», каждая «имя|путь|суффикс»,
 * суффикс `nothink` добавляет пустой блок размышлений (Qwen3, Qwen3.5), `-` — без суффикса.
 */
class MentorBakeoffTest {
    private val cli = System.getenv("CA_MENTOR_CLI")
    private val spec = System.getenv("CA_BAKEOFF")

    private data class Entry(val name: String, val path: String, val suffix: String)

    private fun entries() = spec.orEmpty().split(";").filter { it.isNotBlank() }.map {
        val (n, p, s) = it.split("|").let { l -> Triple(l[0], l[1], l.getOrElse(2) { "-" }) }
        Entry(n, p, if (s == "nothink") "<think>\n\n</think>\n\n" else "")
    }

    private fun cyrillicShare(t: String): Double {
        val noCode = t.replace(Regex("```[\\s\\S]*?```"), " ").replace(Regex("`[^`]*`"), " ")
        val letters = noCode.filter { it.isLetter() }
        return if (letters.isEmpty()) 0.0 else letters.count { it in 'А'..'я' || it == 'ё' || it == 'Ё' }.toDouble() / letters.length
    }

    /** Модель повторила служебный текст запроса вместо ответа. */
    private fun echoes(t: String) = listOf("Задача наставника", "Код ученика", "Вопрос ученика", "<|im_", "Ты — наставник").any { it in t } ||
        t.trim().length < 15

    @Test fun compareModels() = runBlocking<Unit> {
        assumeTrue("нет CA_MENTOR_CLI/CA_BAKEOFF — сравнение выполняется в CI", cli != null && !spec.isNullOrBlank())
        File("build/reports").mkdirs()
        val picks = listOf("a1-greet", "a2-sum-until-zero", "a3-fix-infinite", "a1-where", "a4-books")
        val items = picks.mapNotNull { id -> Corpus.items.firstOrNull { it.task.id == id } } +
            listOfNotNull(Corpus.items.firstOrNull { it.task.type == "predict" && it.task.language == "python" },
                Corpus.items.firstOrNull { it.task.language == "js" })
        val all = StringBuilder("# Сравнение моделей наставника\n\n")
        var answeredAny = false
        for (e in entries()) {
            val log = File("build/reports/mentor-cli-${e.name}.log")
            if (!File(e.path).isFile) {
                all.append("## ${e.name}\n\nфайл модели не скачан — пропуск\n\n")
                println("BAKEOFF|${e.name}|нет файла")
                continue
            }
            val engine = CliEngine(cli!!, e.path, 200, promptSuffix = e.suffix, log = log)
            val mentor = Mentor(Corpus.kb, engine)
            val rows = StringBuilder()
            var n = 0; var shown = 0; var russian = 0; var echo = 0
            val wall = mutableListOf<Double>()
            for (item in items) {
                val ctx = item.context(hintsShown = 1, attempts = 1)
                val err = when (item.task.language) {
                    "js" -> "ReferenceError: nmae is not defined"
                    "sql" -> "Error: no such column: nmae"
                    "kotlin" -> "error: unresolved reference: nmae"
                    else -> "Traceback (most recent call last):\n  File \"main.py\", line 2, in <module>\nNameError: name 'nmae' is not defined"
                }
                val ctxErr = item.context(hintsShown = 1, attempts = 2, error = err)
                val questions = listOf(
                    Triple("Объясни тему", Intent.EXPLAIN_TOPIC, ctx),
                    Triple("Дай подсказку", Intent.HINT, item.context(hintsShown = 0, attempts = 1)),
                    Triple("Почему ошибка?", Intent.EXPLAIN_ERROR, ctxErr),
                )
                for ((label, intent, c) in questions) {
                    val before = engine.raw.size
                    val t0 = System.currentTimeMillis()
                    val r = runCatching { mentor.answer(label, c, intent, maxTokens = 200) }.getOrElse { ex -> rows.append("**ОШИБКА:** ${ex.message}\n\n"); null } ?: continue
                    val sec = (System.currentTimeMillis() - t0) / 1000.0
                    if (engine.raw.size == before) continue // до модели не дошло (подсказка закрыта и т. п.)
                    n++; answeredAny = true
                    val raw = engine.raw.last()
                    val clean = PromptBuilder.clean(raw)
                    val ru = cyrillicShare(clean) >= 0.6
                    val ec = echoes(clean)
                    if (r.source == Source.LLM) shown++
                    if (ru) russian++
                    if (ec) echo++
                    wall += sec
                    val st = engine.stats().getOrNull(n - 1)
                    val meta = "${item.task.id} · $label · ${r.source}${if (r.replaced) " (заменён защитой)" else ""} · по-русски: $ru · эхо запроса: $ec · " +
                        "${"%.1f".format(sec)} с" + (st?.let { " · запрос ${it.promptTokens} ток. (из кэша ${it.cached}) за ${it.promptMs} мс · ответ ${it.generated} ток., ${"%.1f".format(it.tokPerSec)} ток/с" } ?: "")
                    rows.append("**$meta**\n\n> ${clean.take(700).replace("\n", "\n> ")}\n\n")
                    println("BAKEOFF|${e.name}|$meta\nBAKEOFF|${e.name}|ОТВЕТ: ${clean.take(700).replace("\n", "\nBAKEOFF|${e.name}|  ")}")
                }
            }
            val stats = engine.stats()
            val sysInfo = engine.systemInfo()
            engine.close()
            val avgPrompt = if (stats.isNotEmpty()) stats.map { it.promptTokens }.average() else 0.0
            val avgTok = if (stats.isNotEmpty()) stats.map { it.tokPerSec }.average() else 0.0
            val avgPromptMs = if (stats.isNotEmpty()) stats.map { it.promptMs }.average() else 0.0
            val summary = "${e.name}: генераций $n; показано ответов модели $shown; по-русски $russian; эхо запроса/пусто $echo; " +
                "в среднем: ${"%.1f".format(wall.average().takeIf { !it.isNaN() } ?: 0.0)} с на ответ, запрос ${"%.0f".format(avgPrompt)} ток. за ${"%.1f".format(avgPromptMs / 1000)} с, " +
                "${"%.1f".format(avgTok)} ток/с; из кэша в среднем ${"%.0f".format(if (stats.isNotEmpty()) stats.map { it.cached }.average() else 0.0)} ток."
            println("BAKEOFF|$summary")
            println("BAKEOFF|${e.name}|процессор: $sysInfo")
            all.append("## ${e.name}\n\n$summary\n\n`$sysInfo`\n\n$rows")
        }
        File("build/reports/mentor-bakeoff.md").writeText(all.toString())
        assertTrue("ни одна модель не ответила", answeredAny)
    }
}
