package app.codeacademy.runner

import java.io.File

/** Файлы учебного проекта на диске (уровень A). Правила совпадают с ca_runner.write_files/read_files. */
object ProjectFiles {
    const val MAX_FILE_BYTES = 256 * 1024
    const val MAX_PROJECT_BYTES = 2 * 1024 * 1024
    const val MAX_FILES = 200

    fun safeRel(path: String): String {
        val p = path.replace('\\', '/')
        require(!p.startsWith("/") && !(p.length > 1 && p[1] == ':')) { "Абсолютный путь запрещён: $path" }
        val parts = p.split('/').filter { it.isNotEmpty() && it != "." }
        require(parts.isNotEmpty() && parts.none { it == ".." }) { "Недопустимый путь: $path" }
        return parts.joinToString("/")
    }

    /** Заменяет содержимое папки проекта переданными файлами. */
    fun write(root: File, files: Map<String, String>) {
        require(files.size <= MAX_FILES) { "Слишком много файлов в проекте" }
        val prepared = files.map { (path, text) -> safeRel(path) to text.toByteArray(Charsets.UTF_8) }
        var total = 0
        for ((rel, data) in prepared) {
            total += data.size
            require(data.size <= MAX_FILE_BYTES && total <= MAX_PROJECT_BYTES) { "Файл $rel или проект слишком большой" }
        }
        root.deleteRecursively()
        root.mkdirs()
        for ((rel, data) in prepared) {
            val f = File(root, rel)
            f.parentFile?.mkdirs()
            f.writeBytes(data)
        }
    }

    /** Текстовые файлы проекта; двоичные, слишком большие и __pycache__ пропускаются. */
    fun read(root: File): Map<String, String> {
        val out = sortedMapOf<String, String>()
        if (!root.isDirectory) return out
        var total = 0L
        root.walkTopDown()
            .onEnter { it.name != "__pycache__" }
            .filter { it.isFile }
            .sortedBy { it.relativeTo(root).invariantSeparatorsPath }
            .forEach { f ->
                val size = f.length()
                if (size > MAX_FILE_BYTES || total + size > MAX_PROJECT_BYTES || out.size >= MAX_FILES) return@forEach
                val bytes = f.readBytes()
                val text = decodeUtf8(bytes) ?: return@forEach
                total += size
                out[f.relativeTo(root).invariantSeparatorsPath] = text
            }
        return out
    }

    private fun decodeUtf8(bytes: ByteArray): String? = try {
        Charsets.UTF_8.newDecoder().decode(java.nio.ByteBuffer.wrap(bytes)).toString()
    } catch (e: java.nio.charset.CharacterCodingException) {
        null
    }
}
