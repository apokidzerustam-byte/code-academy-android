package app.codeacademy.mentor

import android.app.ActivityManager
import android.content.Context
import android.net.Uri
import android.os.Build
import android.os.StatFs
import android.provider.OpenableColumns
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.withContext
import java.io.File
import java.security.MessageDigest

/** Модель из каталога. Файл скачивается в браузере, приложение только проверяет и копирует его. */
data class ModelInfo(
    val id: String,
    val title: String,
    val fileName: String,
    val url: String,
    val sizeBytes: Long,
    /** SHA-256 файла: принимается только точная копия модели из каталога. */
    val sha256: String,
    /** Минимальный объём памяти телефона, МБ. */
    val minRamMb: Int,
    val recommendedRamMb: Int,
    val license: String,
    /**
     * Qwen3 по умолчанию «размышляет» перед ответом (долго и лишний текст): к запросу добавляется пустой блок
     * размышлений, и модель сразу отвечает. Для Qwen2.5 и Qwen3-Instruct-2507 не нужно.
     */
    val noThink: Boolean = false,
) {
    /** Что дописывается к запросу после метки роли ассистента. */
    val promptSuffix: String get() = if (noThink) "<think>\n\n</think>\n\n" else ""
}

object ModelCatalog {
    /**
     * Qwen (Apache 2.0), квантование Q4_K_M. Размеры и SHA-256 измерены CI по скачанным файлам
     * (ci/mentor-model-test.sh сверяет их при каждой сборке). Порядок — по качеству ответов в сравнении моделей (TEST_REPORT).
     * Ссылки закреплены на ревизии репозитория: файл в ветке main могут заменить, и контрольная сумма перестала бы совпадать.
     */
    val models = listOf(
        ModelInfo(
            id = "qwen3-4b-instruct-2507-q4km",
            title = "Qwen3 4B Instruct 2507 (лучшие ответы, ~2,5 ГБ)",
            fileName = "Qwen3-4B-Instruct-2507-Q4_K_M.gguf",
            url = "https://huggingface.co/unsloth/Qwen3-4B-Instruct-2507-GGUF/resolve/a06e946bb6b655725eafa393f4a9745d460374c9/Qwen3-4B-Instruct-2507-Q4_K_M.gguf",
            sizeBytes = SIZE_4B,
            sha256 = SHA_4B,
            minRamMb = 7_500, recommendedRamMb = 11_000, license = "Apache-2.0",
        ),
        ModelInfo(
            id = "qwen3-1.7b-q4km",
            title = "Qwen3 1.7B (быстрее, ~1,1 ГБ)",
            fileName = "Qwen3-1.7B-Q4_K_M.gguf",
            url = "https://huggingface.co/unsloth/Qwen3-1.7B-GGUF/resolve/d7f544eead698dbd1f15126ef60b45a1e1933222/Qwen3-1.7B-Q4_K_M.gguf",
            sizeBytes = SIZE_17B,
            sha256 = SHA_17B,
            minRamMb = 5_500, recommendedRamMb = 8_000, license = "Apache-2.0",
            noThink = true,
        ),
        ModelInfo(
            id = "qwen2.5-coder-1.5b-q4km",
            title = "Qwen2.5-Coder 1.5B (~1,1 ГБ)",
            fileName = "qwen2.5-coder-1.5b-instruct-q4_k_m.gguf",
            url = "https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF/resolve/f86cb2c1fa58255f8052cc32aeede1b7482d4361/qwen2.5-coder-1.5b-instruct-q4_k_m.gguf",
            sizeBytes = SIZE_15B,
            sha256 = SHA_15B,
            minRamMb = 6_000, recommendedRamMb = 8_000, license = "Apache-2.0",
        ),
        ModelInfo(
            id = "qwen2.5-coder-0.5b-q4km",
            title = "Qwen2.5-Coder 0.5B (для слабых телефонов, ~0,5 ГБ; ответы простые)",
            fileName = "qwen2.5-coder-0.5b-instruct-q4_k_m.gguf",
            url = "https://huggingface.co/Qwen/Qwen2.5-Coder-0.5B-Instruct-GGUF/resolve/ebb2015119c907b064c512bf053e945850b5875f/qwen2.5-coder-0.5b-instruct-q4_k_m.gguf",
            sizeBytes = SIZE_05B,
            sha256 = SHA_05B,
            minRamMb = 4_000, recommendedRamMb = 6_000, license = "Apache-2.0",
        ),
    )

    fun bySha(sha: String) = models.firstOrNull { it.sha256.equals(sha, ignoreCase = true) }
    fun byId(id: String?) = models.firstOrNull { it.id == id }
}

/** Установка, проверка и удаление модели. Сеть не используется. */
class ModelManager(private val context: Context) {
    val dir: File get() = File(context.filesDir, "models").apply { mkdirs() }

    fun file(m: ModelInfo) = File(dir, m.fileName)
    fun installed(): List<ModelInfo> = ModelCatalog.models.filter { file(it).let { f -> f.isFile && f.length() == it.sizeBytes } }

    val totalRamMb: Long get() {
        val mi = ActivityManager.MemoryInfo()
        (context.getSystemService(Context.ACTIVITY_SERVICE) as ActivityManager).getMemoryInfo(mi)
        return mi.totalMem / (1024 * 1024)
    }

    val freeSpaceBytes: Long get() = StatFs(context.filesDir.path).availableBytes

    /** Нейросеть собрана для arm64 (телефоны) и x86_64 (эмулятор). */
    val abiSupported: Boolean get() = Build.SUPPORTED_ABIS.any { it == "arm64-v8a" || it == "x86_64" }

    /** Почему модель нельзя поставить на этот телефон; null — можно. */
    fun blocker(m: ModelInfo): String? = when {
        !abiSupported -> "Процессор телефона не поддерживается (нужен 64-битный ARM)."
        totalRamMb < m.minRamMb * 0.9 -> "Мало памяти: у телефона ${"%.1f".format(totalRamMb / 1024.0)} ГБ, нужно от ${m.minRamMb / 1000} ГБ. Лёгкий режим наставника работает без модели."
        else -> null
    }

    sealed interface ImportResult {
        data class Ok(val model: ModelInfo) : ImportResult
        data class Failed(val message: String) : ImportResult
    }

    /**
     * Копирует выбранный файл в filesDir/models, считая SHA-256 на лету. Принимается только файл
     * из каталога (совпадение контрольной суммы) — это защищает от подменённых и повреждённых файлов.
     */
    suspend fun import(uri: Uri, onProgress: (Float) -> Unit): ImportResult = withContext(Dispatchers.IO) {
        val cr = context.contentResolver
        val size = cr.query(uri, arrayOf(OpenableColumns.SIZE), null, null, null)?.use { c ->
            if (c.moveToFirst() && !c.isNull(0)) c.getLong(0) else -1L
        } ?: uri.path?.takeIf { uri.scheme == "file" }?.let { File(it).length() } ?: -1L
        val candidates = ModelCatalog.models.filter { size < 0 || it.sizeBytes == size }
        if (candidates.isEmpty()) {
            return@withContext ImportResult.Failed("Размер файла (${size / 1_000_000} МБ) не совпадает ни с одной моделью каталога. Скачайте файл по ссылке из инструкции.")
        }
        val expected = candidates.maxOf { it.sizeBytes }
        // Если модель уже стоит, временная копия занимает место рядом со старой.
        if (freeSpaceBytes < expected + 50_000_000) {
            return@withContext ImportResult.Failed("Не хватает места: нужно ${expected / 1_000_000 + 50} МБ свободных.")
        }
        val tmp = File(dir, "import.tmp")
        tmp.delete()
        try {
            val md = MessageDigest.getInstance("SHA-256")
            var copied = 0L
            val input = cr.openInputStream(uri) ?: return@withContext ImportResult.Failed("Файл не открывается.")
            input.use { ins ->
                tmp.outputStream().buffered(1 shl 20).use { out ->
                    val buf = ByteArray(1 shl 20)
                    var first = true
                    while (true) {
                        ensureActive()
                        val n = ins.read(buf)
                        if (n < 0) break
                        if (first) {
                            // GGUF начинается с «GGUF»: другие файлы отбрасываются сразу.
                            if (n < 4 || buf[0] != 'G'.code.toByte() || buf[1] != 'G'.code.toByte() || buf[2] != 'U'.code.toByte() || buf[3] != 'F'.code.toByte()) {
                                return@withContext ImportResult.Failed("Это не файл модели GGUF.")
                            }
                            first = false
                        }
                        md.update(buf, 0, n)
                        out.write(buf, 0, n)
                        copied += n
                        if (copied > expected) return@withContext ImportResult.Failed("Файл больше ожидаемого — это не модель из каталога.")
                        onProgress((copied.toDouble() / expected).toFloat().coerceAtMost(1f))
                    }
                }
            }
            val sha = md.digest().joinToString("") { "%02x".format(it) }
            val m = ModelCatalog.bySha(sha)
                ?: return@withContext ImportResult.Failed("Контрольная сумма не совпала: файл повреждён или это другая модель. Скачайте его заново по ссылке из инструкции.")
            val dst = file(m)
            dst.delete()
            if (!tmp.renameTo(dst)) return@withContext ImportResult.Failed("Не удалось сохранить модель.")
            ImportResult.Ok(m)
        } catch (e: kotlinx.coroutines.CancellationException) {
            throw e
        } catch (e: Exception) {
            // Нет места, нет доступа к файлу, ошибка чтения — сообщение, а не падение приложения.
            ImportResult.Failed("Не удалось скопировать файл: ${e.message ?: e.javaClass.simpleName}")
        } finally {
            tmp.delete()
        }
    }

    fun delete(m: ModelInfo) { file(m).delete() }
}
