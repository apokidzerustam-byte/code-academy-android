package app.codeacademy.mentor

/**
 * Обёртка JNI над llama.cpp (libmentor.so). Используется только в процессе :mentor.
 * Модель работает на CPU, сеть не используется.
 */
class NativeLlm private constructor(@Volatile private var handle: Long) {
    private val lock = Any()

    fun interface PieceCallback {
        /** false — остановить генерацию. */
        fun onPiece(piece: String): Boolean
    }

    val description: String get() = nativeDescribe(handle)

    /** Возвращает JSON со статистикой: promptTokens, cachedTokens, generatedTokens, promptMs, genMs, stopped, truncated. */
    fun generate(prompt: String, maxTokens: Int, temperature: Float, seed: Int, cb: PieceCallback): String {
        check(handle != 0L) { "модель выгружена" }
        return nativeGenerate(handle, prompt, maxTokens, temperature, seed, cb)
    }

    /** Безопасно вызывать с другого потока: прерывает текущую генерацию. */
    fun stop() = synchronized(lock) { if (handle != 0L) nativeStop(handle) }

    /** Вызывается только из потока генерации (после её завершения); stop() с другого потока не попадёт в освобождённую память. */
    fun close() {
        val h = synchronized(lock) { handle.also { handle = 0 } }
        if (h != 0L) nativeFree(h)
    }

    private external fun nativeDescribe(h: Long): String
    private external fun nativeGenerate(h: Long, prompt: String, maxTokens: Int, temperature: Float, seed: Int, cb: PieceCallback): String
    private external fun nativeStop(h: Long)
    private external fun nativeFree(h: Long)

    companion object {
        @Volatile private var initialized = false

        /** Загружает libmentor и варианты CPU-бэкенда ggml из папки библиотек приложения. */
        @Synchronized fun init(nativeLibDir: String) {
            if (initialized) return
            System.loadLibrary("mentor")
            Init.nativeInit(nativeLibDir)
            initialized = true
        }

        fun load(path: String, nCtx: Int, nThreads: Int, nThreadsBatch: Int): NativeLlm = NativeLlm(Init.nativeLoad(path, nCtx, nThreads, nThreadsBatch))

        /** Возможности процессора, которые использует выбранный вариант бэкенда. */
        fun systemInfo(): String = Init.nativeSystemInfo()
    }

    /** Статические функции JNI без экземпляра. */
    private object Init {
        @JvmStatic external fun nativeInit(libDir: String)
        @JvmStatic external fun nativeLoad(path: String, nCtx: Int, nThreads: Int, nThreadsBatch: Int): Long
        @JvmStatic external fun nativeSystemInfo(): String
    }
}
