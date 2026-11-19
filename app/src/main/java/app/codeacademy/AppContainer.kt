package app.codeacademy

import android.app.Application
import android.content.Context
import app.codeacademy.assessment.AssessmentService
import app.codeacademy.content.ContentRepository
import app.codeacademy.data.AppDatabase
import app.codeacademy.data.ProgressRepository
import app.codeacademy.data.ProjectRepository
import app.codeacademy.runner.CodeRunner
import app.codeacademy.runner.PyodideRunner
import app.codeacademy.runner.RunnerClient
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

    /** Область приложения: записи, которые должны завершиться даже после закрытия экрана. */
    val appScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    private var runnerW: PyodideRunner? = null
    private var runnerA: RunnerClient? = null

    /** Исполнитель кода: W по умолчанию; A — если выбран явно или урок требует A, или W недоступен. */
    @Synchronized
    fun runner(mode: RunnerMode, lessonRunner: String = "W", wAvailable: Boolean = true): Pair<String, CodeRunner> =
        if (mode == RunnerMode.A || lessonRunner == "A" || (mode == RunnerMode.AUTO && !wAvailable)) {
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
        container = AppContainer(this)
    }
}
