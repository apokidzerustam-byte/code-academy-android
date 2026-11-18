package app.codeacademy.settings

import android.content.Context
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.floatPreferencesKey
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
)

class SettingsRepository(private val context: Context) {
    private val theme = stringPreferencesKey("theme")
    private val scale = floatPreferencesKey("text_scale")
    private val runner = stringPreferencesKey("runner")
    private val plain = booleanPreferencesKey("plain_editor")

    val settings: Flow<Settings> = context.dataStore.data.map { p ->
        Settings(
            theme = p[theme]?.let { runCatching { ThemeMode.valueOf(it) }.getOrNull() } ?: ThemeMode.SYSTEM,
            textScale = (p[scale] ?: 1.0f).coerceIn(0.85f, 1.5f),
            runner = p[runner]?.let { runCatching { RunnerMode.valueOf(it) }.getOrNull() } ?: RunnerMode.AUTO,
            plainEditor = p[plain] ?: false,
        )
    }

    suspend fun setTheme(t: ThemeMode) = context.dataStore.edit { it[theme] = t.name }
    suspend fun setTextScale(v: Float) = context.dataStore.edit { it[scale] = v.coerceIn(0.85f, 1.5f) }
    suspend fun setRunner(r: RunnerMode) = context.dataStore.edit { it[runner] = r.name }
    suspend fun setPlainEditor(v: Boolean) = context.dataStore.edit { it[plain] = v }
}
