package app.codeacademy.ui

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.getValue
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.Modifier
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.unit.Density
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import app.codeacademy.AppContainer
import app.codeacademy.content.LessonRef
import app.codeacademy.settings.Settings
import app.codeacademy.settings.ThemeMode

val LocalContainer = staticCompositionLocalOf<AppContainer> { error("AppContainer не задан") }

object Routes {
    const val HOME = "home"
    const val PROGRAM = "program"
    const val LESSON = "lesson/{pack}/{lesson}"
    const val ASSIGNMENT = "assignment/{pack}/{lesson}/{index}"
    const val STATS = "stats"
    const val SETTINGS = "settings"
    const val LAB = "lab"
    const val PROJECTS = "projects"
    const val DIAGNOSTIC = "diagnostic"
    const val MAP = "map"
    const val REVIEW = "review"
    const val PLAN = "plan"
    const val IDE = "ide/{id}"
    fun ide(id: String) = "ide/$id"
    fun lesson(r: LessonRef) = "lesson/${r.packId}/${r.lessonId}"
    fun assignment(r: LessonRef, index: Int) = "assignment/${r.packId}/${r.lessonId}/$index"
}

@Composable
fun AppRoot(container: AppContainer) {
    val settings by container.settings.settings.collectAsStateWithLifecycle(Settings())
    val dark = when (settings.theme) {
        ThemeMode.SYSTEM -> isSystemInDarkTheme()
        ThemeMode.DARK -> true
        ThemeMode.LIGHT -> false
    }
    val density = LocalDensity.current
    CompositionLocalProvider(
        LocalContainer provides container,
        LocalDensity provides Density(density.density, density.fontScale * settings.textScale),
    ) {
        MaterialTheme(colorScheme = if (dark) darkColorScheme() else lightColorScheme()) {
            Surface(Modifier.fillMaxSize()) { AppNav(settings) }
        }
    }
}

@Composable
private fun AppNav(settings: Settings) {
    val nav = rememberNavController()
    val back: () -> Unit = { nav.popBackStack() }
    NavHost(nav, startDestination = Routes.HOME) {
        composable(Routes.HOME) {
            HomeScreen(
                openProgram = { nav.navigate(Routes.PROGRAM) },
                openLesson = { nav.navigate(Routes.lesson(it)) },
                openStats = { nav.navigate(Routes.STATS) },
                openSettings = { nav.navigate(Routes.SETTINGS) },
                openProjects = { nav.navigate(Routes.PROJECTS) },
                openDiagnostic = { nav.navigate(Routes.DIAGNOSTIC) },
                openReview = { nav.navigate(Routes.REVIEW) },
                openMap = { nav.navigate(Routes.MAP) },
                openPlan = { nav.navigate(Routes.PLAN) },
            )
        }
        composable(Routes.PROGRAM) { ProgramScreen(back) { nav.navigate(Routes.lesson(it)) } }
        composable(
            Routes.LESSON,
            listOf(navArgument("pack") { type = NavType.StringType }, navArgument("lesson") { type = NavType.StringType }),
        ) { e ->
            val ref = LessonRef(e.arguments!!.getString("pack")!!, e.arguments!!.getString("lesson")!!)
            LessonScreen(ref, back) { i -> nav.navigate(Routes.assignment(ref, i)) }
        }
        composable(
            Routes.ASSIGNMENT,
            listOf(
                navArgument("pack") { type = NavType.StringType },
                navArgument("lesson") { type = NavType.StringType },
                navArgument("index") { type = NavType.IntType },
            ),
        ) { e ->
            val ref = LessonRef(e.arguments!!.getString("pack")!!, e.arguments!!.getString("lesson")!!)
            AssignmentScreen(ref, e.arguments!!.getInt("index"), settings, back) { r, i -> nav.navigate(Routes.assignment(r, i)) }
        }
        composable(Routes.STATS) { StatsScreen(back) }
        composable(Routes.DIAGNOSTIC) { DiagnosticScreen(back) { nav.popBackStack(Routes.HOME, inclusive = false) } }
        composable(Routes.MAP) { KnowledgeMapScreen(back) { nav.navigate(Routes.lesson(it)) } }
        composable(Routes.REVIEW) { ReviewScreen(back) { r, i -> nav.navigate(Routes.assignment(r, i)) } }
        composable(Routes.PLAN) { PlanScreen(back, { nav.navigate(Routes.lesson(it)) }, { nav.navigate(Routes.REVIEW) }) }
        composable(Routes.SETTINGS) { SettingsScreen(back) { nav.navigate(Routes.LAB) } }
        composable(Routes.LAB) { RunnerLabScreen(back) }
        composable(Routes.PROJECTS) { ProjectsScreen(back) { id -> nav.navigate(Routes.ide(id)) } }
        composable(Routes.IDE, listOf(navArgument("id") { type = NavType.StringType })) { e ->
            IdeScreen(e.arguments!!.getString("id")!!, settings, back)
        }
    }
}
