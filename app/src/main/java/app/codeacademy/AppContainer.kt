package app.codeacademy

import android.app.Application
import android.content.Context
import app.codeacademy.assessment.AssessmentService
import app.codeacademy.content.ContentRepository
import app.codeacademy.data.AppDatabase
import app.codeacademy.data.BackupManager
import app.codeacademy.data.ProgressRepository
import app.codeacademy.content.LessonRef
import app.codeacademy.data.ProjectRepository
import app.codeacademy.settings.Settings
import app.codeacademy.mentor.KnowledgeBase
import app.codeacademy.mentor.Mentor
import app.codeacademy.mentor.MentorClient
import app.codeacademy.mentor.MentorContent
import app.codeacademy.mentor.ModelCatalog
import app.codeacademy.mentor.ModelInfo
import app.codeacademy.mentor.ModelManager
import app.codeacademy.mentor.PerfMode
import app.codeacademy.mentor.PerfPolicy
import app.codeacademy.runner.CodeRunner
import app.codeacademy.runner.ProjectFiles
import app.codeacademy.runner.PyodideRunner
import app.codeacademy.runner.RunnerClient
import app.codeacademy.runner.WebRunner
import app.codeacademy.runner.WebRunnerHost
import app.codeacademy.settings.RunnerMode
import app.codeacademy.settings.SettingsRepository
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob

/** Ручной контейнер зависимостей (без Hilt — меньше генерации кода, проще сборка на этапе каркаса). */
class AppContainer(context: Context) {
    private val app = context.applicationContext
    val assets: android.content.res.AssetManager get() = app.assets
    val content = ContentRepository(app.assets)
    /** Курс для адаптивных экранов (загружается один раз). */
    @Volatile var courseCache: app.codeacademy.ui.CourseData? = null
    val db: AppDatabase by lazy { AppDatabase.create(app) }
    val progress by lazy { ProgressRepository(db) }
    val projects by lazy { ProjectRepository(db) }
    val settings = SettingsRepository(app)
    val assessment = AssessmentService()

    /** Резервная копия: все таблицы базы + настройки; при восстановлении папки запуска проектов пересоздаются. */
    val backup: BackupManager by lazy {
        BackupManager(
            db,
            object : BackupManager.SettingsStore {
                override suspend fun snapshot() = settings.snapshot()
                override suspend fun replaceAll(values: Map<String, Any>) = settings.replaceAll(values)
                override suspend fun clearAll() = settings.clearAll()
            },
            appVersion = BuildConfig.VERSION_NAME,
            wipeFiles = { java.io.File(app.filesDir, "projects").let { if (it.exists()) ProjectFiles.wipe(it) } },
        )
    }

    /** Модели нейросетевого наставника (файлы в filesDir/models). */
    val models by lazy { ModelManager(app) }
    /** Путь к выбранной модели для процесса :mentor. */
    @Volatile var mentorModelPath: String? = null
    @Volatile var mentorPromptSuffix: String = ""
    @Volatile var perfMode: PerfMode = PerfMode.STANDARD
    val mentorClient by lazy { MentorClient(app, promptSuffix = { mentorPromptSuffix }, perfMode = { perfMode }) { mentorModelPath } }
    @Volatile private var kb: KnowledgeBase? = null

    /** База знаний наставника: конспекты и частые ошибки всех уроков (строится один раз). */
    suspend fun knowledgeBase(): KnowledgeBase = kb ?: run {
        val docs = content.allLessons().map { (pack, lesson) ->
            val ref = LessonRef(pack.id, lesson.id)
            MentorContent.lessonDoc(pack.id, lesson, content.notes(ref), content.assignments(ref))
        }
        KnowledgeBase(docs).also { kb = it }
    }

    /** Модель, которой сейчас отвечает наставник, или null (лёгкий режим). */
    fun activeModel(s: Settings): ModelInfo? {
        if (!s.mentorNeural) return null
        val m = ModelCatalog.byId(s.mentorModel) ?: models.installed().firstOrNull() ?: return null
        return m.takeIf { it in models.installed() && models.blocker(it) == null }
    }

    /** Наставник с учётом настроек: нейросеть, если включена и модель установлена. */
    suspend fun mentor(s: Settings): Mentor {
        val m = activeModel(s)
        mentorModelPath = m?.let { models.file(it).path }
        mentorPromptSuffix = m?.promptSuffix.orEmpty()
        perfMode = s.perfMode
        return Mentor(knowledgeBase(), if (m != null) mentorClient else null, PerfPolicy.of(s.perfMode))
    }

    /** Область приложения: записи, которые должны завершиться даже после закрытия экрана. */
    val appScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    private var runnerW: PyodideRunner? = null
    private var runnerA: RunnerClient? = null

    private val webHost by lazy { WebRunnerHost(app) }
    private val webRunners = mutableMapOf<String, WebRunner>()

    /**
     * Исполнитель кода. Python: W по умолчанию; A — если выбран явно, урок требует A (например, FastAPI)
     * или W недоступен. HTML/JS, SQL и Kotlin — всегда песочница браузера (имя совпадает с языком).
     */
    @Synchronized
    fun runner(mode: RunnerMode, lessonRunner: String = "W", wAvailable: Boolean = true): Pair<String, CodeRunner> =
        if (lessonRunner in WebRunner.LANGS) {
            lessonRunner to webRunners.getOrPut(lessonRunner) { WebRunner(webHost, lessonRunner) }
        } else if (mode == RunnerMode.A || lessonRunner == "A" || (mode == RunnerMode.AUTO && !wAvailable)) {
            "A" to (runnerA ?: RunnerClient(app, isolated = false).also { runnerA = it })
        } else {
            "W" to (runnerW ?: PyodideRunner(app).also { runnerW = it })
        }
}

class CodeAcademyApp : Application() {
    lateinit var container: AppContainer
        private set

    override fun onCreate() {
        super.onCreate()
        installCrashLog()
        container = AppContainer(this)
    }

    /** Файл журнала сбоев (виден только этому приложению). */
    val crashLogFile: java.io.File get() = java.io.File(filesDir, "logs/${CrashLog.FILE_NAME}")

    /** Необработанное исключение любого процесса приложения попадает в журнал, затем обрабатывается как обычно. */
    private fun installCrashLog() {
        Thread.setDefaultUncaughtExceptionHandler(crashHandler(Thread.getDefaultUncaughtExceptionHandler()))
    }

    /** Обработчик сбоев: пишет в журнал и передаёт исключение [previous] (в тестах — null, чтобы процесс не завершался). */
    fun crashHandler(previous: Thread.UncaughtExceptionHandler?): Thread.UncaughtExceptionHandler {
        val process = processNameCompat()
        return Thread.UncaughtExceptionHandler { thread, error ->
            runCatching {
                CrashLog.append(crashLogFile, CrashLog.entry(process, thread.name, error, BuildConfig.VERSION_NAME, deviceInfo(), System.currentTimeMillis()))
            }
            previous?.uncaughtException(thread, error)
        }
    }

    private fun processNameCompat(): String = runCatching {
        if (android.os.Build.VERSION.SDK_INT >= 28) getProcessName() else java.io.File("/proc/self/cmdline").readText().trim('\u0000')
    }.getOrDefault("?")

    companion object {
        fun deviceInfo() = "${android.os.Build.MANUFACTURER} ${android.os.Build.MODEL}, Android ${android.os.Build.VERSION.RELEASE} (API ${android.os.Build.VERSION.SDK_INT})"
    }
}
