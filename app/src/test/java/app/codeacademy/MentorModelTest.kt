package app.codeacademy

import app.codeacademy.mentor.Intent
import app.codeacademy.mentor.Mentor
import app.codeacademy.mentor.PromptBuilder
import app.codeacademy.mentor.SolutionGuard
import app.codeacademy.mentor.Source
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertTrue
import org.junit.Assume.assumeTrue
import org.junit.Test
import java.io.File

/**
 * Наставник с настоящей моделью (Qwen2.5-Coder через mentor_cli — то же ядро llama.cpp, что в приложении).
 * Запускается в CI (job «Наставник с моделью»): CA_MENTOR_CLI — путь к mentor_cli, CA_MENTOR_MODEL — файл GGUF.
 * Провокации отправляются модели напрямую (минуя отказ классификатора) — проверяется, что защита
 * не пропускает решение, даже если модель его написала. Отчёт — build/reports/mentor-model.md.
 */
class MentorModelTest {
    private val cli = System.getenv("CA_MENTOR_CLI")
    private val model = System.getenv("CA_MENTOR_MODEL")

    @Test fun provocationsWithRealModel() = runBlocking<Unit> {
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
        var usefulFromLlm = 0
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
            if (topic.source == Source.LLM) usefulFromLlm++
            report.append("## ${item.task.id} (${item.task.type}, ${item.task.language})\n\n**Объясни тему** → ${topic.source}" +
                (if (topic.replaced) " (заменён)" else "") + ":\n\n> " + topic.text.take(600).replace("\n", "\n> ") + "\n\n")
            report.append("**Сырой ответ модели на «${Corpus.prompts[5]}»:**\n\n> " +
                (engine.raw.getOrNull(engine.raw.size - 2) ?: "").take(500).replace("\n", "\n> ") + "\n\n")
        }
        val secPerGen = if (generations > 0) engine.totalMs / 1000.0 / engine.raw.size else 0.0
        val summary = "Заданий: ${items.size}, провокаций: ${Corpus.prompts.size}. Генераций модели: $generations, " +
            "сырых ответов с решением: $rawLeaks (${if (generations > 0) rawLeaks * 100 / generations else 0} %), " +
            "заменено защитой: $replaced, показано ответов модели: $llmAnswers; на «Объясни тему» модель ответила полезно в $usefulFromLlm из ${items.size}. " +
            "**Утечек решения после защиты: $guardedLeaks.** Среднее время ответа: ${"%.1f".format(secPerGen)} с."
        report.insert(report.indexOf("\n\n") + 2, summary + "\n\n")
        File("build/reports/mentor-model.md").writeText(report.toString())
        println(summary)
        engine.close()
        assertTrue("утечки решения после защиты ($guardedLeaks):\n" + leakLog.take(5).joinToString("\n---\n"), guardedLeaks == 0)
        assertTrue("модель не ответила ни разу", generations > 0)
        // Если защита заменяет вообще все ответы, нейросетевой режим бесполезен — это тоже ошибка.
        assertTrue("ни один полезный ответ модели не дошёл до ученика (заменено защитой: $replaced из $generations)", usefulFromLlm > 0)
        // Проверка формата: служебные метки не просачиваются в ответ.
        assertTrue(engine.raw.none { PromptBuilder.clean(it).contains("<|im_") })
    }

    /**
     * Кэш начала запроса (общая часть промпта не пересчитывается) не должен менять ответ:
     * тот же запрос после другого запроса даёт тот же текст, что и «холодный» (допускается расхождение ближе к концу
     * из-за разной последовательности вычислений); при испорченном кэше текст расходится с первых слов.
     */
    @Test fun prefixCacheKeepsAnswersIntact() = runBlocking<Unit> {
        assumeTrue("нет CA_MENTOR_CLI/CA_MENTOR_MODEL — тест с моделью выполняется в CI", cli != null && model != null)
        val log = File("build/reports/mentor-cache.log")
        val engine = CliEngine(cli!!, model!!, 60, log = log)
        val a = Corpus.items.first { it.task.id == "a1-greet" }
        val b = Corpus.items.first { it.task.id == "a2-sum-until-zero" }
        val mentor = Mentor(Corpus.kb, engine)
        val q = "Объясни тему этого задания простыми словами"
        mentor.answer(q, a.context(hintsShown = 1, attempts = 1), Intent.EXPLAIN_TOPIC, maxTokens = 60)
        mentor.answer(q, b.context(hintsShown = 1, attempts = 1), Intent.EXPLAIN_TOPIC, maxTokens = 60)
        mentor.answer(q, a.context(hintsShown = 1, attempts = 1), Intent.EXPLAIN_TOPIC, maxTokens = 60)
        mentor.answer(q, a.context(hintsShown = 1, attempts = 1), Intent.EXPLAIN_TOPIC, maxTokens = 60)
        val stats = engine.stats()
        val raw = engine.raw.toList()
        engine.close()
        val common = raw[0].commonPrefixWith(raw[2]).length
        val report = "Кэш начала запроса: токенов в запросах ${stats.map { it.promptTokens }}, из кэша ${stats.map { it.cached }}; " +
            "одинаковое начало ответов: $common симв. из ${raw[0].length}; повтор подряд: ${raw[2].commonPrefixWith(raw[3]).length} симв."
        File("build/reports").mkdirs()
        File("build/reports/mentor-cache.md").writeText("# Кэш начала запроса\n\n$report\n")
        println(report)
        assertTrue("кэш ни разу не сработал: $stats", stats.size == 4 && stats.drop(1).any { it.cached > 0 })
        assertTrue("после кэша ответ расходится с первых слов ($common симв.):\n${raw[0]}\n---\n${raw[2]}", common >= minOf(20, raw[0].length))
        assertTrue("повторный запрос подряд дал другой ответ:\n${raw[2]}\n---\n${raw[3]}", raw[2].commonPrefixWith(raw[3]).length >= minOf(20, raw[2].length))
    }
}
