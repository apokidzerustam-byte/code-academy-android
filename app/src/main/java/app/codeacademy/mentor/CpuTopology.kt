package app.codeacademy.mentor

import java.io.File

/**
 * Выбор числа потоков для модели. На телефонах ядра разные: 1–2 «больших», несколько «средних» и несколько слабых.
 * Если часть потоков попадёт на слабые ядра, остальные ждут их на каждом шаге, и ответ замедляется в разы.
 * Поэтому потоков берётся не больше, чем быстрых ядер (частота не ниже 70 % от максимальной).
 */
object CpuTopology {
    data class Threads(val generation: Int, val prompt: Int, val fastCores: Int, val cores: Int)

    /** Максимальные частоты ядер, кГц. Пусто, если система не даёт их прочитать. */
    fun readMaxFreqs(root: File = File("/sys/devices/system/cpu")): List<Long> {
        val dirs = root.listFiles { f -> f.isDirectory && Regex("cpu\\d+").matches(f.name) } ?: return emptyList()
        return dirs.sortedBy { it.name.removePrefix("cpu").toInt() }.mapNotNull { d ->
            runCatching { File(d, "cpufreq/cpuinfo_max_freq").readText().trim().toLong() }.getOrNull()
        }
    }

    fun fastCores(freqs: List<Long>): Int {
        val top = freqs.maxOrNull() ?: return 0
        if (top <= 0) return 0
        return freqs.count { it * 10 >= top * 7 }
    }

    /**
     * Потоков генерации (упирается в память — больше четырёх не помогает) и разбора запроса (упирается в вычисления).
     * [freqs] пусты — берётся половина ядер.
     */
    fun threads(cores: Int, freqs: List<Long>): Threads {
        val fast = fastCores(freqs).takeIf { freqs.size >= 2 && it > 0 }
        val base = fast ?: (cores / 2)
        return Threads(
            generation = base.coerceIn(2, 4),
            prompt = base.coerceIn(2, 6),
            fastCores = fast ?: 0,
            cores = cores,
        )
    }

    fun detect(): Threads = threads(Runtime.getRuntime().availableProcessors(), readMaxFreqs())

    /** Возможности процессора, которые использует вычислительный бэкенд: `NEON = 1 | DOTPROD = 1 …` → список названий. */
    fun features(systemInfo: String): List<String> {
        val interesting = listOf("NEON", "DOTPROD", "MATMUL_INT8", "SVE", "SME", "FP16_VA", "BF16", "AVX2", "AVX512")
        val on = Regex("([A-Z0-9_]+)\\s*=\\s*1").findAll(systemInfo).map { it.groupValues[1] }.toSet()
        return interesting.filter { it in on }
    }

    /** Быстрые целочисленные инструкции, ради которых нужен «правильный» вариант бэкенда на arm64. */
    fun hasFastMatmul(features: List<String>): Boolean = "DOTPROD" in features || "MATMUL_INT8" in features || "AVX2" in features
}
