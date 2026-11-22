package app.codeacademy

import app.codeacademy.mentor.LlmEngine
import java.io.BufferedReader
import java.io.File
import java.io.InputStreamReader
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit

/**
 * Модель через mentor_cli — то же ядро llama.cpp, что в приложении. Один процесс на всё время теста.
 * [promptSuffix] дописывается к промпту после метки роли ассистента (например, пустой блок размышлений для Qwen3).
 * Статистика каждой генерации (токены запроса, из кэша, скорость) читается из журнала CLI — см. [stats].
 */
class CliEngine(
    cli: String,
    model: String,
    maxTokens: Int,
    private val promptSuffix: String = "",
    private val log: File = File("build/reports/mentor-cli.log"),
) : LlmEngine, AutoCloseable {
    /** Строка статистики CLI: `#3 prompt=412 cached=380 gen=57 prompt_ms=900 gen_ms=2100 tok/s=27.1`. */
    data class Stat(val promptTokens: Int, val cached: Int, val generated: Int, val promptMs: Long, val genMs: Long) {
        val tokPerSec: Double get() = if (genMs > 0) generated * 1000.0 / genMs else 0.0
    }

    private val proc = ProcessBuilder(cli, model, "4096", maxTokens.toString()).redirectError(log.also { it.parentFile?.mkdirs() }).start()
    private val out = BufferedReader(InputStreamReader(proc.inputStream, Charsets.UTF_8))
    private val input = proc.outputStream.bufferedWriter(Charsets.UTF_8)
    val raw = mutableListOf<String>()
    var totalMs = 0L

    /** Если одна генерация зависла, процесс убивается (иначе readLine блокирует CI до таймаута всего job). */
    private val watchdog = Executors.newSingleThreadScheduledExecutor { r -> Thread(r, "mentor-watchdog").apply { isDaemon = true } }

    override suspend fun generate(prompt: String, maxTokens: Int, onPiece: (String) -> Boolean): String {
        val t0 = System.currentTimeMillis()
        input.write((prompt + promptSuffix).replace("\n<<<END>>>", "\n<<<END >>>"))
        input.write("\n<<<END>>>\n")
        input.flush()
        val sb = StringBuilder()
        var forwarding = true
        val killer = watchdog.schedule({ proc.destroyForcibly() }, GENERATION_TIMEOUT_S, TimeUnit.SECONDS)
        try {
            while (true) {
                val line = out.readLine() ?: error("mentor_cli завершился или завис дольше $GENERATION_TIMEOUT_S с")
                if (line == "<<<END>>>") break
                if (sb.isNotEmpty()) { sb.append('\n'); if (forwarding) forwarding = onPiece("\n") }
                sb.append(line)
                if (forwarding) forwarding = onPiece(line)
            }
        } finally {
            killer.cancel(false)
        }
        totalMs += System.currentTimeMillis() - t0
        val text = sb.toString().removeSuffix("\n")
        raw += text
        return text
    }

    /** Статистика всех генераций по порядку; журнал пишется процессом, поэтому читается заново. */
    fun stats(): List<Stat> = runCatching {
        val re = Regex("""#\d+ prompt=(\d+) cached=(\d+) gen=(\d+) prompt_ms=(\d+) gen_ms=(\d+)""")
        log.readLines().mapNotNull { re.find(it) }.map { m ->
            val (p, c, g, pm, gm) = m.destructured
            Stat(p.toInt(), c.toInt(), g.toInt(), pm.toLong(), gm.toLong())
        }
    }.getOrDefault(emptyList())

    /** Строка «system_info» из журнала: какие инструкции процессора использует бэкенд. */
    fun systemInfo(): String = runCatching { log.readLines().firstOrNull { "NEON" in it || "AVX" in it || "SSE" in it }.orEmpty() }.getOrDefault("")

    override fun close() { input.close(); proc.waitFor(); watchdog.shutdownNow() }

    companion object {
        const val GENERATION_TIMEOUT_S = 600L

        /** `nothink` — пустой блок размышлений для Qwen3 (как ModelInfo.promptSuffix в приложении). */
        fun suffix(name: String?) = if (name == "nothink") "<think>\n\n</think>\n\n" else ""
    }
}
