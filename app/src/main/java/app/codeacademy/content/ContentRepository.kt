package app.codeacademy.content

import android.content.res.AssetManager
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import app.codeacademy.lesson.NarrationMeta
import kotlinx.serialization.json.Json

/**
 * Чтение контент-пакетов из assets/packs (встроенные). Позже — также из загруженных/импортированных
 * пакетов в файлах приложения (ContentManager, этап 9).
 */
class ContentRepository(private val assets: AssetManager) {

    private val json = Json { ignoreUnknownKeys = true }
    private val cache = HashMap<String, Any>()

    private fun read(path: String): String =
        assets.open(path).bufferedReader(Charsets.UTF_8).use { it.readText() }

    @Suppress("UNCHECKED_CAST")
    private fun <T> cached(key: String, load: () -> T): T = synchronized(cache) {
        cache.getOrPut(key) { load() as Any } as T
    }

    suspend fun packs(): List<PackManifest> = withContext(Dispatchers.IO) {
        cached("packs") {
            (assets.list(ROOT) ?: emptyArray())
                .filter { runCatching { assets.open("$ROOT/$it/pack.json").close() }.isSuccess }
                .map { json.decodeFromString(PackManifest.serializer(), read("$ROOT/$it/pack.json")) }
                .sortedBy { it.stage }
        }
    }

    private fun lessonDir(ref: LessonRef) = "$ROOT/${ref.packId}/lessons/${ref.lessonId}"

    suspend fun lesson(ref: LessonRef): Lesson = withContext(Dispatchers.IO) {
        cached("lesson:${ref.key}") { json.decodeFromString(Lesson.serializer(), read("${lessonDir(ref)}/lesson.json")) }
    }

    suspend fun scenario(ref: LessonRef): Scenario = withContext(Dispatchers.IO) {
        val l = lesson(ref)
        cached("scenario:${ref.key}") { json.decodeFromString(Scenario.serializer(), read("${lessonDir(ref)}/${l.scenario}")) }
    }

    /** Озвучка урока или null, если её ещё нет (урок показывается с субтитрами по таймеру). */
    suspend fun narration(ref: LessonRef): NarrationMeta? = withContext(Dispatchers.IO) {
        val meta = runCatching {
            cached("narration:${ref.key}") {
                json.decodeFromString(NarrationMeta.serializer(), read("${lessonDir(ref)}/audio/narration.json"))
            }
        }.getOrNull() ?: return@withContext null
        // Сцены, для которых нет файла, считаются неозвученными.
        val present = runCatching { assets.list("${lessonDir(ref)}/audio")?.toSet() }.getOrNull().orEmpty()
        meta.copy(scenes = meta.scenes.filter { it.file in present })
    }

    /** Путь к файлу озвучки внутри assets (для AssetManager.openFd). */
    fun audioAsset(ref: LessonRef, file: String) = "${lessonDir(ref)}/audio/$file"

    suspend fun notes(ref: LessonRef): String = withContext(Dispatchers.IO) {
        val l = lesson(ref)
        cached("notes:${ref.key}") { read("${lessonDir(ref)}/${l.notes}") }
    }

    suspend fun assignments(ref: LessonRef): List<Assignment> = withContext(Dispatchers.IO) {
        val l = lesson(ref)
        cached("assign:${ref.key}") {
            l.assignments.map { json.decodeFromString(Assignment.serializer(), read("${lessonDir(ref)}/$it")) }
        }
    }

    /** Все уроки всех пакетов по порядку программы. */
    suspend fun allLessons(): List<Pair<PackManifest, Lesson>> =
        packs().flatMap { p -> p.lessons.map { p to lesson(LessonRef(p.id, it)) } }

    companion object {
        const val ROOT = "packs"
    }
}
