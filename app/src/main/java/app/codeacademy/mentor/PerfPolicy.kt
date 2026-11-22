package app.codeacademy.mentor

/** Режим производительности (ТЗ, раздел 15): экономичный, стандартный, расширенный. */
enum class PerfMode { ECONOMY, STANDARD, EXTENDED }

/**
 * Что меняет режим. Меняется нейросетевой наставник — самая тяжёлая часть приложения по памяти, батарее и нагреву;
 * остальные части (редактор, запуск кода, уроки) от режима не зависят и настраиваются отдельно (редактор — в настройках).
 */
data class PerfPolicy(
    /** Верхний предел потоков генерации ответа (больше четырёх на телефоне не помогает — упирается в память). */
    val maxGenerationThreads: Int,
    /** Верхний предел потоков разбора запроса. */
    val maxPromptThreads: Int,
    /** Через сколько миллисекунд простоя модель выгружается из памяти. */
    val idleUnloadMs: Long,
    /** Загружать ли модель заранее, когда ученик открыл панель наставника. */
    val preload: Boolean,
    /** Длина ответа в процентах от обычной: короткие ответы — меньше времени, нагрева и расхода батареи. */
    val answerLengthPercent: Int,
) {
    /** Число потоков с учётом режима: не больше, чем подобрано по быстрым ядрам. */
    fun threads(t: CpuTopology.Threads): CpuTopology.Threads =
        t.copy(generation = minOf(t.generation, maxGenerationThreads), prompt = minOf(t.prompt, maxPromptThreads))

    /** Лимит токенов ответа с учётом режима (не меньше 40: иначе ответ обрывается на первом предложении). */
    fun maxTokens(base: Int): Int = (base * answerLengthPercent / 100).coerceAtLeast(40)

    companion object {
        fun of(mode: PerfMode): PerfPolicy = when (mode) {
            PerfMode.ECONOMY -> PerfPolicy(2, 3, 120_000L, false, 70)
            PerfMode.STANDARD -> PerfPolicy(4, 6, 600_000L, true, 100)
            PerfMode.EXTENDED -> PerfPolicy(4, 6, 1_800_000L, true, 130)
        }

        /** Неизвестное или пустое имя (например, из резервной копии другой версии) — стандартный режим. */
        fun parse(name: String?): PerfMode = PerfMode.values().firstOrNull { it.name == name } ?: PerfMode.STANDARD
    }
}
