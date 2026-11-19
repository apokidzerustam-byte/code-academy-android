package app.codeacademy.settings

import android.content.Context
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.floatPreferencesKey
import androidx.datastore.preferences.core.intPreferencesKey
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

private val Context.dataStore by preferencesDataStore(name = "settings")

enum class ThemeMode { SYSTEM, LIGHT, DARK }

/** Где выполнять код: AUTO — W, а если WebView не поддерживает — A. */
enum class RunnerMode { AUTO, W, A }

data class Settings(
    val theme: ThemeMode = ThemeMode.SYSTEM,
    val textScale: Float = 1.0f,
    val runner: RunnerMode = RunnerMode.AUTO,
    /** Простое поле ввода вместо CodeMirror (слабые устройства, доступность). */
    val plainEditor: Boolean = false,
    /** Выбран старт («с нуля» или диагностика) — карточка выбора на главной больше не показывается. */
    val onboardingDone: Boolean = false,
    /** Длительность занятия, мин: 30, 60 (рекомендуется) или 90. */
    val sessionMinutes: Int = 60,
    val daysPerWeek: Int = 5,
)

class SettingsRepository(private val context: Context) {
    private val theme = stringPreferencesKey("theme")
    private val scale = floatPreferencesKey("text_scale")
    private val runner = stringPreferencesKey("runner")
    private val plain = booleanPreferencesKey("plain_editor")
    private val onboarding = booleanPreferencesKey("onboarding_done")
    private val session = intPreferencesKey("session_minutes")
    private val days = intPreferencesKey("days_per_week")

    val settings: Flow<Settings> = context.dataStore.data.map { p ->
        Settings(
            theme = p[theme]?.let { runCatching { ThemeMode.valueOf(it) }.getOrNull() } ?: ThemeMode.SYSTEM,
            textScale = (p[scale] ?: 1.0f).coerceIn(0.85f, 1.5f),
            runner = p[runner]?.let { runCatching { RunnerMode.valueOf(it) }.getOrNull() } ?: RunnerMode.AUTO,
            plainEditor = p[plain] ?: false,
            onboardingDone = p[onboarding] ?: false,
            sessionMinutes = (p[session] ?: 60).let { if (it in listOf(30, 60, 90)) it else 60 },
            daysPerWeek = (p[days] ?: 5).coerceIn(1, 7),
        )
    }

    suspend fun setTheme(t: ThemeMode) = context.dataStore.edit { it[theme] = t.name }
    suspend fun setTextScale(v: Float) = context.dataStore.edit { it[scale] = v.coerceIn(0.85f, 1.5f) }
    suspend fun setRunner(r: RunnerMode) = context.dataStore.edit { it[runner] = r.name }
    suspend fun setPlainEditor(v: Boolean) = context.dataStore.edit { it[plain] = v }

    suspend fun setOnboardingDone(v: Boolean) = context.dataStore.edit { it[onboarding] = v }
    suspend fun setSessionMinutes(v: Int) = context.dataStore.edit { it[session] = v }
    suspend fun setDaysPerWeek(v: Int) = context.dataStore.edit { it[days] = v.coerceIn(1, 7) }
}
