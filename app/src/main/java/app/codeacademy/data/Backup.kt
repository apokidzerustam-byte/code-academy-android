package app.codeacademy.data

import android.database.Cursor
import androidx.sqlite.db.SupportSQLiteDatabase
import java.io.ByteArrayOutputStream
import java.io.IOException
import java.io.InputStream
import java.io.OutputStream
import java.security.MessageDigest
import java.time.Instant
import java.util.Base64
import java.util.zip.ZipEntry
import java.util.zip.ZipInputStream
import java.util.zip.ZipOutputStream
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonNull
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonArray
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.intOrNull
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.longOrNull
import kotlinx.serialization.json.put

/** Ошибка резервной копии: текст для ученика; данные приложения при ней не меняются. */
class BackupException(message: String, cause: Throwable? = null) : IOException(message, cause)

/** Что лежит в копии (для подтверждения и отчёта). */
data class BackupSummary(
    val createdAt: Long,
    val appVersion: String,
    /** Таблица → число строк. */
    val tables: Map<String, Int>,
    val settings: Int,
    val projects: Int,
) {
    val attempts: Int get() = tables["attempt"] ?: 0
    val lessons: Int get() = tables["lesson_progress"] ?: 0
}

/**
 * Формат резервной копии — ZIP, его можно открыть и прочитать на компьютере:
 * - manifest.json — формат, версии приложения и базы, дата, sha256 и размер каждого файла данных;
 * - data/database.json — ВСЕ таблицы базы (кроме служебных Room) строка за строкой с типами SQLite;
 * - data/settings.json — все настройки (DataStore) с типами;
 * - projects/<название>/… — копии файлов проектов для чтения на компьютере (при восстановлении не используются);
 * - README.txt — как восстановить.
 * Копия детерминирована: те же данные дают те же байты файлов data/ — это и проверяют тесты «байт в байт».
 */
object BackupFormat {
    const val FORMAT = "code-academy-backup"
    const val FORMAT_VERSION = 1
    const val MANIFEST = "manifest.json"
    const val DB = "data/database.json"
    const val SETTINGS = "data/settings.json"
    const val README = "README.txt"
    /** Предел распакованного размера одного файла копии (защита от «zip-бомбы»). */
    const val MAX_ENTRY_BYTES = 128L * 1024 * 1024
    const val MAX_ENTRIES = 20_000
    /** При восстановлении читаются только эти файлы; остальные (копии проектов, README) пропускаются без буферизации. */
    val NEEDED = setOf(MANIFEST, DB, SETTINGS)

    val json = Json { prettyPrint = false }

    fun sha256(b: ByteArray): String = MessageDigest.getInstance("SHA-256").digest(b).joinToString("") { "%02x".format(it) }

    // --- Настройки ------------------------------------------------------------------------------------
    fun encodeSettings(values: Map<String, Any>): ByteArray {
        val obj = buildJsonObject {
            for ((k, v) in values.toSortedMap()) {
                put(k, buildJsonObject {
                    when (v) {
                        is Boolean -> { put("type", "boolean"); put("value", v.toString()) }
                        is Int -> { put("type", "int"); put("value", v.toString()) }
                        is Long -> { put("type", "long"); put("value", v.toString()) }
                        is Float -> { put("type", "float"); put("value", v.toString()) }
                        is Double -> { put("type", "double"); put("value", v.toString()) }
                        is String -> { put("type", "string"); put("value", v) }
                        is Set<*> -> { put("type", "stringSet"); put("value", JsonArray(v.map { JsonPrimitive(it as String) }.sortedBy { it.content })) }
                        else -> throw BackupException("Неизвестный тип настройки $k")
                    }
                })
            }
        }
        return json.encodeToString(JsonElement.serializer(), obj).toByteArray(Charsets.UTF_8)
    }

    fun decodeSettings(bytes: ByteArray): Map<String, Any> = try {
        val obj = json.parseToJsonElement(bytes.toString(Charsets.UTF_8)).jsonObject
        obj.mapValues { (k, e) ->
            val o = e.jsonObject
            val type = o.getValue("type").jsonPrimitive.content
            val v = o.getValue("value")
            when (type) {
                "boolean" -> v.jsonPrimitive.content.toBooleanStrict()
                "int" -> v.jsonPrimitive.content.toInt()
                "long" -> v.jsonPrimitive.content.toLong()
                "float" -> v.jsonPrimitive.content.toFloat()
                "double" -> v.jsonPrimitive.content.toDouble()
                "string" -> v.jsonPrimitive.content
                "stringSet" -> v.jsonArray.map { it.jsonPrimitive.content }.toSet()
                else -> throw BackupException("Неизвестный тип настройки $k: $type")
            }
        }
    } catch (e: BackupException) {
        throw e
    } catch (e: Exception) {
        throw BackupException("Файл настроек в копии повреждён", e)
    }

    // --- Значения SQLite ------------------------------------------------------------------------------
    /** INTEGER → число, TEXT → строка, NULL → null, REAL → {"real": "…"}, BLOB → {"blob": base64}. */
    fun cell(c: Cursor, i: Int): JsonElement = when (c.getType(i)) {
        Cursor.FIELD_TYPE_NULL -> JsonNull
        Cursor.FIELD_TYPE_INTEGER -> JsonPrimitive(c.getLong(i))
        Cursor.FIELD_TYPE_FLOAT -> buildJsonObject { put("real", c.getDouble(i).toString()) }
        Cursor.FIELD_TYPE_BLOB -> buildJsonObject { put("blob", Base64.getEncoder().encodeToString(c.getBlob(i))) }
        else -> JsonPrimitive(c.getString(i))
    }

    /** Значение для bind в INSERT: Long, Double, String, ByteArray или null. */
    fun value(e: JsonElement): Any? = when (e) {
        JsonNull -> null
        is JsonPrimitive -> if (e.isString) e.content else e.longOrNull ?: throw BackupException("Неверное число в копии: ${e.content}")
        is JsonObject -> e["real"]?.jsonPrimitive?.content?.toDouble()
            ?: e["blob"]?.jsonPrimitive?.content?.let { Base64.getDecoder().decode(it) }
            ?: throw BackupException("Неизвестное значение в копии")
        else -> throw BackupException("Неизвестное значение в копии")
    }

    // --- ZIP ----------------------------------------------------------------------------------------
    fun writeZip(out: OutputStream, entries: List<Pair<String, ByteArray>>, time: Long) {
        ZipOutputStream(out).use { zip ->
            for ((name, data) in entries) {
                zip.putNextEntry(ZipEntry(name).apply { this.time = time })
                zip.write(data)
                zip.closeEntry()
            }
        }
    }

    /** all = false: только файлы, нужные для восстановления (NEEDED). */
    fun readZip(input: InputStream, all: Boolean = false): Map<String, ByteArray> {
        val out = LinkedHashMap<String, ByteArray>()
        var seen = 0
        try {
            ZipInputStream(input).use { zip ->
                while (true) {
                    val e = zip.nextEntry ?: break
                    if (e.isDirectory) continue
                    if (++seen > MAX_ENTRIES) throw BackupException("В архиве слишком много файлов — это не резервная копия Code Academy")
                    if (!all && e.name !in NEEDED) continue
                    if (out.size >= MAX_ENTRIES) throw BackupException("В архиве слишком много файлов — это не резервная копия Code Academy")
                    val buf = ByteArrayOutputStream()
                    val chunk = ByteArray(64 * 1024)
                    while (true) {
                        val n = zip.read(chunk)
                        if (n < 0) break
                        buf.write(chunk, 0, n)
                        if (buf.size() > MAX_ENTRY_BYTES) throw BackupException("Файл ${e.name} в копии слишком большой")
                    }
                    if (out.put(e.name, buf.toByteArray()) != null) throw BackupException("Файл ${e.name} встречается в копии дважды")
                }
            }
        } catch (e: BackupException) {
            throw e
        } catch (e: Exception) {
            throw BackupException("Файл не похож на ZIP-архив или повреждён", e)
        }
        if (out.isEmpty()) throw BackupException("Файл не похож на резервную копию: это не ZIP-архив или он пуст")
        return out
    }

    /** Проверка манифеста и контрольных сумм. Возвращает манифест. */
    fun verify(entries: Map<String, ByteArray>, dbVersion: Int): JsonObject {
        val m = entries[MANIFEST] ?: throw BackupException("Это не резервная копия Code Academy: нет manifest.json")
        val manifest = runCatching { json.parseToJsonElement(m.toString(Charsets.UTF_8)).jsonObject }.getOrNull()
            ?: throw BackupException("manifest.json повреждён")
        if (manifest["format"]?.jsonPrimitive?.contentOrNull != FORMAT) throw BackupException("Это не резервная копия Code Academy")
        val fv = manifest["formatVersion"]?.jsonPrimitive?.intOrNull ?: throw BackupException("manifest.json повреждён: нет версии формата")
        if (fv > FORMAT_VERSION) throw BackupException("Копия создана более новой версией приложения — обновите приложение")
        val dv = manifest["dbVersion"]?.jsonPrimitive?.intOrNull ?: throw BackupException("manifest.json повреждён: нет версии базы")
        if (dv > dbVersion) throw BackupException("Копия создана более новой версией приложения (база v$dv) — обновите приложение")
        if (dv < dbVersion) throw BackupException("Копия от старой версии базы (v$dv), перенос в v$dbVersion пока не поддерживается")
        val sums = manifest["entries"]?.jsonObject ?: throw BackupException("manifest.json повреждён: нет списка файлов")
        for (name in listOf(DB, SETTINGS)) {
            val data = entries[name] ?: throw BackupException("В копии нет $name")
            val want = sums[name]?.jsonObject ?: throw BackupException("В manifest.json нет $name")
            if (want["size"]?.jsonPrimitive?.longOrNull != data.size.toLong() ||
                want["sha256"]?.jsonPrimitive?.content != sha256(data)) {
                throw BackupException("Копия повреждена: контрольная сумма $name не совпадает")
            }
        }
        return manifest
    }

    fun readme(createdAt: Long, appVersion: String) = """Резервная копия Code Academy
Создана: ${Instant.ofEpochMilli(createdAt)} (приложение $appVersion)

Как восстановить: Code Academy → Настройки → «Восстановить из копии» → выберите этот файл.
Восстановление заменяет весь прогресс, проекты и настройки на устройстве данными из копии.

Что внутри:
  data/database.json — прогресс, попытки, навыки, повторения, черновики, проекты (все таблицы);
  data/settings.json — настройки;
  projects/…        — копии файлов ваших проектов, их можно открыть на компьютере;
  manifest.json     — версии и контрольные суммы (sha256). Изменённая копия не восстановится.
""".toByteArray(Charsets.UTF_8)
}

/**
 * Резервное копирование и восстановление: все таблицы базы + настройки. Восстановление атомарно:
 * копия полностью проверяется до изменений, таблицы заменяются в одной транзакции (при ошибке — откат).
 */
class BackupManager(
    private val db: AppDatabase,
    private val settings: SettingsStore,
    private val appVersion: String,
    private val clock: () -> Long = System::currentTimeMillis,
    /** Удаление производных файлов (папки проектов для запуска кода) при восстановлении и очистке. */
    private val wipeFiles: () -> Unit = {},
) {
    /** Доступ к настройкам (реальный DataStore или тестовый). */
    interface SettingsStore {
        suspend fun snapshot(): Map<String, Any>
        suspend fun replaceAll(values: Map<String, Any>)
        suspend fun clearAll()
    }

    private val dbVersion: Int get() = db.openHelper.readableDatabase.version

    private fun tables(sdb: SupportSQLiteDatabase): List<String> =
        sdb.query("SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name").use { c ->
            buildList { while (c.moveToNext()) add(c.getString(0)) }
        }.filter { it !in SKIP && !it.startsWith("sqlite_stat") }

    private fun columns(sdb: SupportSQLiteDatabase, table: String): List<String> =
        sdb.query("PRAGMA table_info(${q(table)})").use { c ->
            val idx = c.getColumnIndexOrThrow("name")
            buildList { while (c.moveToNext()) add(c.getString(idx)) }
        }

    private fun identity(sdb: SupportSQLiteDatabase): String? = runCatching {
        sdb.query("SELECT identity_hash FROM room_master_table LIMIT 1").use { if (it.moveToFirst()) it.getString(0) else null }
    }.getOrNull()

    /** Все таблицы базы в каноническом JSON (одинаковые данные → одинаковые байты). */
    suspend fun dumpDatabase(): ByteArray = withContext(Dispatchers.IO) {
        db.runInTransaction(java.util.concurrent.Callable {
            val sdb = db.openHelper.writableDatabase
            val obj = buildJsonObject {
                put("dbVersion", sdb.version)
                identity(sdb)?.let { put("identity", it) }
                put("tables", buildJsonArray {
                    for (t in tables(sdb)) {
                        val cols = columns(sdb, t)
                        add(buildJsonObject {
                            put("name", t)
                            put("columns", JsonArray(cols.map { JsonPrimitive(it) }))
                            // Порядок строк: по первичному ключу/rowid; для sqlite_sequence — по имени таблицы.
                            val order = if (t == "sqlite_sequence") "name" else "rowid"
                            put("rows", buildJsonArray {
                                sdb.query("SELECT ${cols.joinToString { q(it) }} FROM ${q(t)} ORDER BY $order").use { c ->
                                    while (c.moveToNext()) add(JsonArray(cols.indices.map { BackupFormat.cell(c, it) }))
                                }
                            })
                        })
                    }
                })
            }
            BackupFormat.json.encodeToString(JsonElement.serializer(), obj).toByteArray(Charsets.UTF_8)
        })
    }

    suspend fun dumpSettings(): ByteArray = BackupFormat.encodeSettings(settings.snapshot())

    suspend fun export(out: OutputStream): BackupSummary {
        val dbBytes = dumpDatabase()
        val setBytes = dumpSettings()
        if (dbBytes.size > BackupFormat.MAX_ENTRY_BYTES) throw BackupException("Данных больше ${BackupFormat.MAX_ENTRY_BYTES / 1024 / 1024} МБ — такую копию нельзя будет восстановить")
        val now = clock()
        val summary = summarize(dbBytes, setBytes, now, appVersion)
        val manifest = buildJsonObject {
            put("format", BackupFormat.FORMAT)
            put("formatVersion", BackupFormat.FORMAT_VERSION)
            put("appVersion", appVersion)
            put("dbVersion", dbVersion)
            put("createdAt", now)
            put("createdAtIso", Instant.ofEpochMilli(now).toString())
            put("counts", buildJsonObject { summary.tables.toSortedMap().forEach { (k, v) -> put(k, v) } })
            put("entries", buildJsonObject {
                for ((n, b) in listOf(BackupFormat.DB to dbBytes, BackupFormat.SETTINGS to setBytes)) {
                    put(n, buildJsonObject { put("sha256", BackupFormat.sha256(b)); put("size", b.size) })
                }
            })
        }
        val entries = mutableListOf(
            BackupFormat.MANIFEST to BackupFormat.json.encodeToString(JsonElement.serializer(), manifest).toByteArray(Charsets.UTF_8),
            BackupFormat.DB to dbBytes,
            BackupFormat.SETTINGS to setBytes,
            BackupFormat.README to BackupFormat.readme(now, appVersion),
        )
        entries += readableProjects(dbBytes)
        withContext(Dispatchers.IO) { BackupFormat.writeZip(out, entries, now) }
        return summary
    }

    /** Проверяет копию, ничего не меняя: для подтверждения «что будет восстановлено». */
    suspend fun inspect(input: InputStream): BackupSummary = withContext(Dispatchers.IO) {
        val (dbBytes, setBytes, manifest) = load(input)
        summarize(dbBytes, setBytes, manifest["createdAt"]?.jsonPrimitive?.longOrNull ?: 0,
            manifest["appVersion"]?.jsonPrimitive?.contentOrNull ?: "?")
    }

    /** Заменяет все данные приложения данными копии. При любой ошибке данные не меняются. */
    suspend fun restore(input: InputStream): BackupSummary = withContext(Dispatchers.IO) {
        val (dbBytes, setBytes, manifest) = load(input)
        val tablesJson = parseDb(dbBytes)
        val prefs = BackupFormat.decodeSettings(setBytes)
        // Настройки — первыми, со снимком прежних: если база не восстановится, настройки вернутся как были.
        val oldPrefs = settings.snapshot()
        try {
            settings.replaceAll(prefs)
        } catch (e: Exception) {
            runCatching { settings.replaceAll(oldPrefs) }
            throw BackupException("Не удалось восстановить настройки (ничего не изменено): ${e.message}", e)
        }
        try {
            db.runInTransaction(Runnable {
                val sdb = db.openHelper.writableDatabase
                val current = tables(sdb)
                val byName = tablesJson.associateBy { it.jsonObject.getValue("name").jsonPrimitive.content }
                for (name in byName.keys) if (name !in current) throw BackupException("В копии есть таблица $name, которой нет в этой версии")
                // Сначала проверяем все столбцы, потом пишем.
                for ((name, t) in byName) {
                    val cols = t.jsonObject.getValue("columns").jsonArray.map { it.jsonPrimitive.content }
                    if (cols != columns(sdb, name)) throw BackupException("Столбцы таблицы $name в копии не совпадают с базой")
                }
                val ordered = current.filter { it != SEQ } + current.filter { it == SEQ }
                for (name in ordered) {
                    sdb.execSQL("DELETE FROM ${q(name)}")
                    val t = byName[name]?.jsonObject ?: continue
                    val cols = t.getValue("columns").jsonArray.map { it.jsonPrimitive.content }
                    val stmt = sdb.compileStatement(
                        "INSERT INTO ${q(name)} (${cols.joinToString { q(it) }}) VALUES (${cols.joinToString { "?" }})")
                    for (row in t.getValue("rows").jsonArray) {
                        val cells = row.jsonArray
                        if (cells.size != cols.size) throw BackupException("Строка таблицы $name повреждена")
                        stmt.clearBindings()
                        cells.forEachIndexed { i, e ->
                            when (val v = BackupFormat.value(e)) {
                                null -> stmt.bindNull(i + 1)
                                is Long -> stmt.bindLong(i + 1, v)
                                is Double -> stmt.bindDouble(i + 1, v)
                                is String -> stmt.bindString(i + 1, v)
                                is ByteArray -> stmt.bindBlob(i + 1, v)
                            }
                        }
                        stmt.executeInsert()
                    }
                    stmt.close()
                }
            })
        } catch (e: Exception) {
            runCatching { settings.replaceAll(oldPrefs) }
            if (e is BackupException) throw e
            throw BackupException("Не удалось восстановить данные (ничего не изменено): ${e.message}", e)
        }
        runCatching(wipeFiles)
        summarize(dbBytes, setBytes, manifest["createdAt"]?.jsonPrimitive?.longOrNull ?: 0,
            manifest["appVersion"]?.jsonPrimitive?.contentOrNull ?: "?")
    }

    /** Удаляет весь прогресс, проекты и настройки (как «Очистить данные» в Android). */
    suspend fun wipe() = withContext(Dispatchers.IO) {
        // Конец транзакции Room сам сообщает наблюдателям (Flow) об изменении таблиц.
        db.runInTransaction(Runnable {
            val sdb = db.openHelper.writableDatabase
            for (t in tables(sdb)) sdb.execSQL("DELETE FROM ${q(t)}")
        })
        settings.clearAll()
        runCatching(wipeFiles)
    }

    private data class Loaded(val db: ByteArray, val settings: ByteArray, val manifest: JsonObject)

    private fun load(input: InputStream): Loaded {
        val entries = BackupFormat.readZip(input)
        val manifest = BackupFormat.verify(entries, dbVersion)
        val dbBytes = entries.getValue(BackupFormat.DB)
        val sdb = db.openHelper.readableDatabase
        val have = identity(sdb)
        val obj = runCatching { BackupFormat.json.parseToJsonElement(dbBytes.toString(Charsets.UTF_8)).jsonObject }.getOrNull()
            ?: throw BackupException("Данные в копии повреждены")
        val theirs = obj["identity"]?.jsonPrimitive?.contentOrNull
        if (have != null && theirs != null && have != theirs) throw BackupException("Схема базы в копии отличается от этой версии приложения")
        return Loaded(dbBytes, entries.getValue(BackupFormat.SETTINGS), manifest)
    }

    private fun parseDb(bytes: ByteArray): JsonArray = runCatching {
        BackupFormat.json.parseToJsonElement(bytes.toString(Charsets.UTF_8)).jsonObject.getValue("tables").jsonArray
    }.getOrElse { throw BackupException("Данные в копии повреждены", it) }

    private fun summarize(dbBytes: ByteArray, setBytes: ByteArray, createdAt: Long, version: String): BackupSummary {
        val tables = parseDb(dbBytes).associate {
            val o = it.jsonObject
            o.getValue("name").jsonPrimitive.content to o.getValue("rows").jsonArray.size
        }.filterKeys { it != SEQ }
        val projects = projectRows(dbBytes).map { it.first }.distinct().size
        return BackupSummary(createdAt, version, tables, BackupFormat.decodeSettings(setBytes).size, projects)
    }

    /** Строки project_file: (projectId, path, content). */
    private fun projectRows(dbBytes: ByteArray): List<Triple<String, String, String>> {
        val t = parseDb(dbBytes).firstOrNull { it.jsonObject.getValue("name").jsonPrimitive.content == "project_file" }?.jsonObject
            ?: return emptyList()
        val cols = t.getValue("columns").jsonArray.map { it.jsonPrimitive.content }
        val (pi, pa, co) = listOf("projectId", "path", "content").map { cols.indexOf(it) }
        if (pi < 0 || pa < 0 || co < 0) return emptyList()
        return t.getValue("rows").jsonArray.map { r ->
            val a = r.jsonArray
            Triple(a[pi].jsonPrimitive.content, a[pa].jsonPrimitive.content, a[co].jsonPrimitive.content)
        }
    }

    /** Копии проектов «для глаз»: projects/<название>/<путь>. */
    private fun readableProjects(dbBytes: ByteArray): List<Pair<String, ByteArray>> {
        val rows = projectRows(dbBytes)
        val titles = rows.filter { it.second == ProjectRepository.META }.associate { it.first to it.third }
        val used = HashSet<String>()
        val folder = rows.map { it.first }.distinct().associateWith { id ->
            // Только буквы, цифры, пробел, «_», «-», «.»; без точек и пробелов по краям — никаких «..» и «.».
            val base = (titles[id] ?: id).replace(Regex("[^\\p{L}\\p{N}._ -]+"), "_").take(60)
                .trim(' ', '.').ifBlank { id.trim(' ', '.').ifBlank { "project" } }
            var name = base
            var n = 2
            while (!used.add(name.lowercase())) name = "$base (${n++})" // без различия регистра (Windows, macOS)
            name
        }
        return rows.filter { it.second !in ProjectRepository.META_FILES }
            .sortedWith(compareBy({ folder.getValue(it.first) }, { it.second }))
            .map { (id, path, text) -> "projects/${folder.getValue(id)}/$path" to text.toByteArray(Charsets.UTF_8) }
    }

    companion object {
        private const val SEQ = "sqlite_sequence"
        private val SKIP = setOf("android_metadata", "room_master_table")
        private fun q(name: String) = "\"" + name.replace("\"", "\"\"") + "\""
    }
}
