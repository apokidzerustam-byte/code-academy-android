pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.name = "code-academy-android"
include(":app")
// Отдельный модуль-зонд: проверяет, ставится ли FastAPI в Chaquopy.
// Собирается только явно (:probe-fastapi:...), сбой pip не ломает :app.
include(":probe-fastapi")
