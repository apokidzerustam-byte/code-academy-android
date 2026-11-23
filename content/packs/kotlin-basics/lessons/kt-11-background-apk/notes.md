# Kotlin: фоновая работа и сборка APK

## Какой инструмент выбрать

| Задача | Инструмент |
|---|---|
| работа, пока приложение или экран живы | корутина |
| пользователь видит и ждёт (музыка, запись) | служба переднего плана с уведомлением |
| точное время (будильник) | AlarmManager |
| отложенная, но гарантированная работа (синхронизация) | WorkManager |

```kotlin
fun chooseTool(visibleToUser: Boolean, exactTime: Boolean, mustSurviveRestart: Boolean): String = when {
    visibleToUser -> "служба переднего плана"
    exactTime -> "будильник"
    mustSurviveRestart -> "WorkManager"
    else -> "корутина"
}
```

## WorkManager (справочный код)

```kotlin
class SyncWorker(context: Context, params: WorkerParameters) : CoroutineWorker(context, params) {
    override suspend fun doWork(): Result = try {
        syncTasks()
        Result.success()
    } catch (e: IOException) {
        if (runAttemptCount < 3) Result.retry() else Result.failure()
    }
}

val request = PeriodicWorkRequestBuilder<SyncWorker>(1, TimeUnit.HOURS)
    .setConstraints(Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).setRequiresBatteryNotLow(true).build())
    .setBackoffCriteria(BackoffPolicy.EXPONENTIAL, 30, TimeUnit.SECONDS)
    .build()
WorkManager.getInstance(context).enqueueUniquePeriodicWork("sync", ExistingPeriodicWorkPolicy.KEEP, request)
```

- Результаты: `success` · `retry` (повторить позже) · `failure` (окончательный провал).
- Периодическая работа — не чаще чем раз в **15 минут**; точное время — не задача WorkManager.
- Пауза между повторами при экспоненциальной политике растёт вдвое (30 с, 60 с, 120 с…), потолок — 5 часов.

```kotlin
fun retryDelay(attempt: Int): Int = minOf(30 * (1 shl (attempt - 1)), 18000)
fun periodMinutes(requested: Int): Int = maxOf(requested, 15)
```

## Сборка и подпись APK

```
./gradlew assembleRelease
apksigner verify --print-certs app-release.apk
adb install -r app-release.apk
```

- Обновление ставится поверх, только если **подпись та же**: потерянный ключ означает, что обновить приложение у пользователей нельзя.
- Ключ и пароли не кладут в репозиторий. В проекте Code Academy релизный ключ берётся из переменных окружения CI (`CA_RELEASE_KEYSTORE` и др.); ключ в репозитории — только прототипный, для проверок, не для магазина.
- `versionCode` должен только расти; связь с версией для людей: `старшая * 10000 + средняя * 100 + младшая`.
- Сжатие R8 (`isMinifyEnabled`) в проекте выключено сознательно: Chaquopy, нативный код и сериализация требуют особых правил.

```kotlin
fun versionCode(name: String): Int {
    val p = name.split(".").map { it.toInt() }
    return p[0] * 10000 + p[1] * 100 + p[2]
}
```

- **Ограничение проверки:** вызовы WorkManager и настройки Gradle в уроке справочные и не компилируются и не запускаются ни в CI-проверке контента, ни на телефоне: Android SDK и Gradle там нет. Проверяется чистая логика вокруг них.
