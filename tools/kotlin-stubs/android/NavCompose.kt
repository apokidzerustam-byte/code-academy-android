package androidx.navigation.compose

import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.navigation.Bundle
import androidx.navigation.NavBackStackEntry
import androidx.navigation.NavGraphBuilder
import androidx.navigation.NavHostController
import stubs.ComposeLog

/** Заглушка: в настоящей библиотеке контроллер запоминается между перерисовками; здесь — каждый вызов новый. */
@Composable
fun rememberNavController(): NavHostController = NavHostController()

fun NavGraphBuilder.composable(route: String, content: @Composable (NavBackStackEntry) -> Unit) {
    routes.add(route to content)
}

private fun match(pattern: String, route: String): Map<String, String>? {
    val p = pattern.split("/")
    val r = route.split("/")
    if (p.size != r.size) return null
    val args = mutableMapOf<String, String>()
    for (i in p.indices) {
        if (p[i].startsWith("{") && p[i].endsWith("}")) args[p[i].substring(1, p[i].length - 1)] = r[i]
        else if (p[i] != r[i]) return null
    }
    return args
}

/** Показывает экран верхней записи стопки; если маршрута нет в графе — ошибка, как в настоящей библиотеке. */
@Composable
fun NavHost(
    navController: NavHostController,
    startDestination: String,
    modifier: Modifier = Modifier,
    builder: NavGraphBuilder.() -> Unit
) {
    val graph = NavGraphBuilder()
    graph.builder()
    if (navController.backStack.isEmpty()) navController.backStack.add(startDestination)
    val current = navController.currentRoute!!
    for ((pattern, content) in graph.routes) {
        val args = match(pattern, current)
        if (args != null) {
            content(NavBackStackEntry(current, Bundle(args)))
            return
        }
    }
    throw IllegalArgumentException("Navigation destination that matches route $current cannot be found in the navigation graph")
}
