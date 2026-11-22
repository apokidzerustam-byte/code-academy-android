package app.codeacademy

import app.codeacademy.mentor.Intent
import app.codeacademy.mentor.LlmEngine
import app.codeacademy.mentor.Mentor
import app.codeacademy.mentor.PromptBuilder
import app.codeacademy.mentor.SolutionGuard
import app.codeacademy.mentor.Source
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertTrue
import org.junit.Assume.assumeTrue
import org.junit.Test
import java.io.BufferedReader
import java.io.File
import java.io.InputStreamReader

/**
 * Наставник с настоящей моделью (Qwen2.5-Coder через mentor_cli — то же ядро llama.cpp, что в приложении).
 * Запускается в CI (job «Наставник с моделью»): CA_MENTOR_CLI — путь к mentor_cli, CA_MENTOR_MODEL — файл GGUF.
 * Провокации отправляются модели напрямую (минуя отказ классификатора) — проверяется, что защита
 * не пропускает решение, даже если модель его написала. Отчёт — build/reports/mentor-model.md.
 */
class MentorModelTest {
    private val cli = System.getenv("CA_MENTOR_CLI")
    private val model = System.getenv("CA_MENTOR_MODEL")

    private class CliEngine(cli: String, model: String, maxTokens: Int) : LlmEngine, AutoCloseable {
        private val proc = ProcessBuilder(cli, model, "2048", maxTokens.toString()).redirectError(File("build/reports/mentor-cli.log")).start()
        private val out = BufferedReader(InputStreamReader(proc.inputStream, Charsets.UTF_8))
        private val input = proc.outputStream.bufferedWriter(Charsets.UTF_8)
        val raw = mutableListOf<String>()
        var totalMs = 0L

        override suspend fun generate(prompt: String, maxTokens: Int, onPiece: (String) -> Boolean): String {
            val t0 = System.currentTimeMillis()
            input.write(prompt.replace("\n<<<END>>>", "\n<<<END >>>"))
            input.write("\n<<<END>>>\n")
            input.flush()
            val sb = StringBuilder()
            var forwarding = true
            while (true) {
                val line = out.readLine() ?: error("mentor_cli завершился")
                if (line == "<<<END>>>") break
                if (sb.isNotEmpty()) { sb.append('\n'); if (forwarding) forwarding = onPiece("\n") }
                sb.append(line)
                if (forwarding) forwarding = onPiece(line)
            }
            totalMs += System.currentTimeMillis() - t0
            val text = sb.toString().removeSuffix("\n")
            raw += text
            return text
        }

        override fun close() { input.close(); proc.waitFor() }
    }

    @Test fun provocationsWithRealModel() = runBlocking {
        assumeTrue("нет CA_MENTOR_CLI/CA_MENTOR_MODEL — тест с моделью выполняется в CI", cli != null && model != null)
        File("build/reports").mkdirs()
        val engine = CliEngine(cli!!, model!!, 160)
        val mentor = Mentor(Corpus.kb, engine)
        // Разные виды заданий и языки: write/fix/predict, Python/SQL/JS/HTML/Kotlin, этап проекта.
        val picks = listOf("a1-greet", "a2-sum-until-zero", "a3-fix-infinite", "a1-where", "a4-books")
        val items = picks.mapNotNull { id -> Corpus.items.firstOrNull { it.task.id == id } } +
            listOfNotNull(Corpus.items.firstOrNull { it.task.type == "predict" && it.task.language == "python" },
                Corpus.items.firstOrNull { it.task.language == "js" },
                Corpus.items.firstOrNull { it.task.type == "milestone" && it.task.language == "python" })
        assertTrue("мало заданий для теста: ${items.map { it.task.id }}", items.size >= 7)
        val report = StringBuilder("# Наставник с моделью: 20 провокаций\n\nМодель: `${File(model).name}`\n\n")
        var guardedLeaks = 0
        var rawLeaks = 0
        var replaced = 0
        var llmAnswers = 0
        var generations = 0
        val leakLog = mutableListOf<String>()
        for (item in items) {
            val ctx = item.context(hintsShown = 1, attempts = 1)
            val guard = SolutionGuard(item.task, listOf(ctx.code))
            for (q in Corpus.prompts) {
                // Обычный путь: просьба о решении до модели не доходит.
                val normal = mentor.answer(q, ctx)
                MentorTest.oracle(item.task, normal.text)?.let { guardedLeaks++; leakLog += "${item.task.id} обычный «$q»: $it" }
                // Принудительно через модель.
                val before = engine.raw.size
                val r = mentor.answer(q, ctx, Intent.OTHER, maxTokens = 160)
                if (engine.raw.size > before) {
                    generations++
                    val raw = engine.raw.last()
                    if (MentorTest.oracle(item.task, raw) != null || guard.check(raw).leak) rawLeaks++
                }
                if (r.source == Source.LLM) llmAnswers++
                if (r.replaced) replaced++
                MentorTest.oracle(item.task, r.text)?.let { guardedLeaks++; leakLog += "${item.task.id} модель «$q»: $it\n${r.text}" }
            }
            // Полезные запросы: объяснение темы и подсказка — модель должна отвечать по-русски.
            val topic = mentor.answer("Объясни тему этого задания простыми словами", ctx, Intent.EXPLAIN_TOPIC)
            report.append("## ${item.task.id} (${item.task.type}, ${item.task.language})\n\n**Объясни тему** → ${topic.source}" +
                (if (topic.replaced) " (заменён)" else "") + ":\n\n> " + topic.text.take(600).replace("\n", "\n> ") + "\n\n")
            report.append("**Сырой ответ модели на «${Corpus.prompts[5]}»:**\n\n> " +
                (engine.raw.getOrNull(engine.raw.size - 2) ?: "").take(500).replace("\n", "\n> ") + "\n\n")
        }
        val secPerGen = if (generations > 0) engine.totalMs / 1000.0 / engine.raw.size else 0.0
        val summary = "Заданий: ${items.size}, провокаций: ${Corpus.prompts.size}. Генераций модели: $generations, " +
            "сырых ответов с решением: $rawLeaks (${if (generations > 0) rawLeaks * 100 / generations else 0} %), " +
            "заменено защитой: $replaced, показано ответов модели: $llmAnswers. " +
            "**Утечек решения после защиты: $guardedLeaks.** Среднее время ответа: ${"%.1f".format(secPerGen)} с."
        report.insert(report.indexOf("\n\n") + 2, summary + "\n\n")
        File("build/reports/mentor-model.md").writeText(report.toString())
        println(summary)
        engine.close()
        assertTrue("утечки решения после защиты ($guardedLeaks):\n" + leakLog.take(5).joinToString("\n---\n"), guardedLeaks == 0)
        assertTrue("модель не ответила ни разу", generations > 0)
        // Проверка формата: служебные метки не просачиваются в ответ.
        assertTrue(engine.raw.none { PromptBuilder.clean(it).contains("<|im_") })
    }
}
