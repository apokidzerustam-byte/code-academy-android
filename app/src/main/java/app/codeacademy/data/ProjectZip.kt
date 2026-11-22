package app.codeacademy.data

import app.codeacademy.runner.ProjectFiles
import java.io.IOException
import java.io.InputStream
import java.nio.ByteBuffer
import java.nio.charset.CharacterCodingException
import java.nio.charset.CodingErrorAction
import java.util.zip.ZipInputStream

/** Ошибка импорта проекта: текст для ученика. */
class ProjectZipException(message: String) : IOException(message)

/**
 * Чтение проекта из ZIP (импорт). Те же ограничения, что у проектов в приложении:
 * не больше 200 текстовых файлов, файл ≤ 256 КБ, проект ≤ 2 МБ; пути — только внутри проекта.
 * Общая верхняя папка (как в архивах GitHub «repo-main/…») убирается. Служебные файлы macOS, .git
 * и не текстовые файлы (картинки и т. п.) пропускаются — о них сообщается.
 */
object ProjectZip {
    /** files — текстовые файлы проекта; skipped — что не импортировано (картинки и другие не текстовые файлы, .git). */
    data class Result(val files: Map<String, String>, val skipped: List<String>)

    fun read(input: InputStream): Map<String, String> = readWithReport(input).files

    fun readWithReport(input: InputStream): Result {
        val raw = LinkedHashMap<String, ByteArray>()
        var total = 0L
        ZipInputStream(input).use { zip ->
            while (true) {
                val e = zip.nextEntry ?: break
                if (e.isDirectory) continue
                val name = e.name.replace('\\', '/')
                if (name.startsWith("__MACOSX/") || name.substringAfterLast('/') == ".DS_Store") continue
                if (raw.size >= ProjectFiles.MAX_FILES) throw ProjectZipException("В архиве больше ${ProjectFiles.MAX_FILES} файлов")
                val bytes = readLimited(zip, ProjectFiles.MAX_FILE_BYTES)
                    ?: throw ProjectZipException("Файл $name больше ${ProjectFiles.MAX_FILE_BYTES / 1024} КБ")
                total += bytes.size
                if (total > ProjectFiles.MAX_PROJECT_BYTES) throw ProjectZipException("Проект больше ${ProjectFiles.MAX_PROJECT_BYTES / 1024 / 1024} МБ")
                if (raw.put(name, bytes) != null) throw ProjectZipException("Файл $name встречается в архиве дважды")
            }
        }
        if (raw.isEmpty()) throw ProjectZipException("В архиве нет файлов")
        val strip = commonTopFolder(raw.keys)
        val out = sortedMapOf<String, String>()
        val skipped = mutableListOf<String>()
        for ((name, bytes) in raw) {
            val rel = runCatching { ProjectFiles.safeRel(name.removePrefix(strip)) }.getOrNull()
                ?: throw ProjectZipException("Недопустимый путь в архиве: $name")
            if (rel in ProjectRepository.META_FILES || rel.substringAfterLast('/') == ".keep") continue
            if (rel == ".git" || rel.startsWith(".git/")) { skipped += rel; continue }
            val text = utf8(bytes)
            if (text == null) { skipped += rel; continue } // в проектах хранятся только тексты
            if (out.put(rel, text) != null) throw ProjectZipException("Файл $rel встречается в архиве дважды")
        }
        ProjectFiles.conflict(out.keys)?.let { throw ProjectZipException(it) }
        if (out.isEmpty()) throw ProjectZipException(if (skipped.isEmpty()) "В архиве нет файлов проекта" else "В архиве нет текстовых файлов")
        return Result(out, skipped)
    }

    /** "folder/" если все файлы лежат в одной верхней папке, иначе "". */
    fun commonTopFolder(names: Collection<String>): String {
        val tops = names.map { it.trimStart('/').substringBefore('/', missingDelimiterValue = "") }
        val first = tops.firstOrNull() ?: return ""
        return if (first.isNotEmpty() && tops.all { it == first } && names.all { it.trimStart('/').contains('/') }) "$first/" else ""
    }

    private fun readLimited(input: InputStream, limit: Int): ByteArray? {
        val buf = java.io.ByteArrayOutputStream()
        val chunk = ByteArray(8192)
        while (true) {
            val n = input.read(chunk)
            if (n < 0) break
            buf.write(chunk, 0, n)
            if (buf.size() > limit) return null
        }
        return buf.toByteArray()
    }

    private fun utf8(bytes: ByteArray): String? = try {
        Charsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT).onUnmappableCharacter(CodingErrorAction.REPORT)
            .decode(ByteBuffer.wrap(bytes)).toString().removePrefix("\uFEFF")
    } catch (_: CharacterCodingException) {
        null
    }
}
