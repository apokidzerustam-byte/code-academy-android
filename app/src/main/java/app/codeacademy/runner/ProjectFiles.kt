package app.codeacademy.runner

import java.io.File
import java.io.IOException
import java.nio.file.FileVisitResult
import java.nio.file.Files
import java.nio.file.LinkOption
import java.nio.file.Path
import java.nio.file.SimpleFileVisitor
import java.nio.file.attribute.BasicFileAttributes

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

    /** Ошибка структуры: один и тот же путь дважды или файл, внутри которого «лежит» другой файл. */
    fun conflict(rels: Collection<String>): String? {
        val set = HashSet<String>()
        for (r in rels) if (!set.add(r)) return "Файл $r указан дважды"
        for (r in rels) {
            var i = r.indexOf('/')
            while (i > 0) {
                val dir = r.substring(0, i)
                if (dir in set) return "«$dir» — это файл, внутри него не может быть «$r»"
                i = r.indexOf('/', i + 1)
            }
        }
        return null
    }

    /** Заменяет содержимое папки проекта переданными файлами. Всё проверяется до удаления старых файлов. */
    fun write(root: File, files: Map<String, String>) {
        require(files.size <= MAX_FILES) { "Слишком много файлов в проекте" }
        val prepared = files.map { (path, text) -> safeRel(path) to text.toByteArray(Charsets.UTF_8) }
        var total = 0
        for ((rel, data) in prepared) {
            total += data.size
            require(data.size <= MAX_FILE_BYTES && total <= MAX_PROJECT_BYTES) { "Файл $rel или проект слишком большой" }
        }
        conflict(prepared.map { it.first })?.let { throw IllegalArgumentException(it) }
        wipe(root)
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
        regularFiles(root)
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

    /** Удаляет папку, не переходя по символическим ссылкам (ссылка удаляется сама, а не то, на что она указывает). */
    fun wipe(root: File) {
        val start = root.toPath()
        if (!Files.exists(start, LinkOption.NOFOLLOW_LINKS)) return
        Files.walkFileTree(start, object : SimpleFileVisitor<Path>() {
            override fun visitFile(file: Path, attrs: BasicFileAttributes): FileVisitResult {
                Files.deleteIfExists(file); return FileVisitResult.CONTINUE
            }
            override fun visitFileFailed(file: Path, exc: IOException): FileVisitResult {
                Files.deleteIfExists(file); return FileVisitResult.CONTINUE
            }
            override fun postVisitDirectory(dir: Path, exc: IOException?): FileVisitResult {
                Files.deleteIfExists(dir); return FileVisitResult.CONTINUE
            }
        })
    }

    /** Обычные файлы проекта без __pycache__ и без символических ссылок. */
    private fun regularFiles(root: File): List<File> {
        val out = ArrayList<File>()
        Files.walkFileTree(root.toPath(), object : SimpleFileVisitor<Path>() {
            override fun preVisitDirectory(dir: Path, attrs: BasicFileAttributes): FileVisitResult =
                if (dir.fileName?.toString() == "__pycache__") FileVisitResult.SKIP_SUBTREE else FileVisitResult.CONTINUE
            override fun visitFile(file: Path, attrs: BasicFileAttributes): FileVisitResult {
                if (attrs.isRegularFile) out += file.toFile()
                return if (out.size > MAX_FILES * 5) FileVisitResult.TERMINATE else FileVisitResult.CONTINUE
            }
            override fun visitFileFailed(file: Path, exc: IOException) = FileVisitResult.CONTINUE
        })
        return out
    }

    private fun decodeUtf8(bytes: ByteArray): String? = try {
        Charsets.UTF_8.newDecoder().decode(java.nio.ByteBuffer.wrap(bytes)).toString()
    } catch (e: java.nio.charset.CharacterCodingException) {
        null
    }
}
