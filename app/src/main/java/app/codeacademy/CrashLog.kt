package app.codeacademy

import java.io.File
import java.io.PrintWriter
import java.io.StringWriter
import java.time.Instant

/**
 * Локальный журнал сбоев: если приложение закрылось само, причина остаётся в файле на телефоне.
 * Никуда не отправляется (в приложении нет доступа к сети); ученик сам решает, показать ли журнал разработчику
 * (в настройках: «Копировать» или «Поделиться»). Хранятся последние [MAX_CHARS] символов.
 */
object CrashLog {
    const val FILE_NAME = "crash.log"
    const val MAX_CHARS = 60_000
    private const val MAX_TRACE = 8_000
    private const val SEP = "\n=====\n"
    private val lock = Any()

    /** Запись о необработанном исключении: время, версия, устройство, процесс, поток и стек. */
    fun entry(process: String, thread: String, t: Throwable, version: String, device: String, nowMs: Long): String {
        val trace = StringWriter().also { t.printStackTrace(PrintWriter(it)) }.toString().trim()
        return header(version, device, nowMs) + "процесс: $process, поток: $thread\n" + trace.take(MAX_TRACE)
    }

    /** Запись о событии без исключения (например, «процесс нейросети завершился»). */
    fun note(process: String, text: String, version: String, device: String, nowMs: Long): String =
        header(version, device, nowMs) + "процесс: $process\n" + text

    private fun header(version: String, device: String, nowMs: Long) = "${Instant.ofEpochMilli(nowMs)} · $version · $device\n"

    /** Дописывает запись; при превышении размера отбрасываются самые старые записи целиком. Ошибки записи не пробрасываются. */
    fun append(file: File, entry: String) {
        synchronized(lock) {
            runCatching {
                file.parentFile?.mkdirs()
                val old = if (file.isFile) file.readText() else ""
                var all = if (old.isEmpty()) entry else old + SEP + entry
                if (all.length > MAX_CHARS) {
                    all = all.takeLast(MAX_CHARS)
                    val cut = all.indexOf(SEP)
                    all = if (cut >= 0) all.substring(cut + SEP.length) else all
                }
                file.writeText(all)
            }
        }
    }

    fun read(file: File): String = synchronized(lock) { runCatching { if (file.isFile) file.readText() else "" }.getOrDefault("") }

    fun clear(file: File) {
        synchronized(lock) { runCatching { file.delete() } }
    }

    /** Число записей в журнале. */
    fun count(text: String): Int = if (text.isBlank()) 0 else text.split(SEP).size
}
