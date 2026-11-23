package androidx.navigation

import androidx.compose.runtime.Composable

/**
 * Заглушка для проверки учебного кода в CI (не настоящая Navigation Compose).
 * Упрощения: маршруты сопоставляются по сегментам «a/{x}/b»; Bundle хранит строки; перерисовку
 * проверяющий код вызывает сам (render заново); popBackStack не снимает последний экран
 * (в настоящей библиотеке системная «Назад» в этом случае закрывает приложение).
 */
class Bundle(private val map: Map<String, String>) {
    fun getString(key: String): String? = map[key]
    fun getInt(key: String): Int = map[key]?.toIntOrNull() ?: 0
}

class NavBackStackEntry(val route: String, val arguments: Bundle?)

class NavGraphBuilder {
    val routes = mutableListOf<Pair<String, @Composable (NavBackStackEntry) -> Unit>>()
}

class NavHostController {
    val backStack = mutableListOf<String>()
    val currentRoute: String? get() = backStack.lastOrNull()

    fun navigate(route: String) {
        backStack.add(route)
    }

    fun popBackStack(): Boolean {
        if (backStack.size <= 1) return false
        backStack.removeAt(backStack.size - 1)
        return true
    }
}
