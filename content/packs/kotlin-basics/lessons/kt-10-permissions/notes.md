# Kotlin: разрешения и уведомления Android

Опасные возможности (камера, микрофон, местоположение, контакты, показ уведомлений с Android 13) требуют согласия пользователя.

**Правила:** просите только необходимое · объясняйте зачем · просите, когда функция понадобилась · приложение должно работать и при отказе.

## Схема запроса (справочный код)

```kotlin
// манифест: <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />
val launcher = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
    if (granted) showNotification() else showExplanation()
}
val has = ContextCompat.checkSelfPermission(context, Manifest.permission.POST_NOTIFICATIONS) == PackageManager.PERMISSION_GRANTED
Button(onClick = { launcher.launch(Manifest.permission.POST_NOTIFICATIONS) }) { Text("Включить уведомления") }
```

## Логика, которую можно проверять без Android

```kotlin
fun nextStep(granted: Boolean, shouldShowRationale: Boolean): String = when {
    granted -> "использовать"
    shouldShowRationale -> "объяснить"
    else -> "спросить"
}

fun canNotify(sdk: Int, granted: Boolean): Boolean = sdk < 33 || granted
```

| Версия Android | Что важно |
|---|---|
| 6 (API 23) | опасные разрешения запрашиваются во время работы |
| 8 (API 26) | уведомление должно принадлежать каналу |
| 13 (API 33) | показ уведомлений — отдельное разрешение `POST_NOTIFICATIONS` |

## Канал и уведомление (справочный код)

```kotlin
val channel = NotificationChannel("tasks", "Задачи", NotificationManager.IMPORTANCE_DEFAULT)
context.getSystemService(NotificationManager::class.java).createNotificationChannel(channel)

val notification = NotificationCompat.Builder(context, "tasks")
    .setSmallIcon(R.drawable.ic_notification)
    .setContentTitle("Напоминание")
    .setContentText("У вас 3 задачи")
    .build()
NotificationManagerCompat.from(context).notify(1, notification)
```

Канал создают один раз; важность выше обычной нужна редко. Новое уведомление с тем же номером заменяет прежнее.

## Форма слова после числа

```kotlin
val word = when {
    n % 100 in 11..14 -> "задач"
    n % 10 == 1 -> "задача"
    n % 10 in 2..4 -> "задачи"
    else -> "задач"
}
```

- В манифесте Code Academy нет ни одной строки `uses-permission`: приложению хватает собственных возможностей.
- **Ограничение проверки:** вызовы Android API (launcher, checkSelfPermission, каналы, уведомления) в уроке показаны как справочный код и не компилируются и не запускаются ни в CI, ни на телефоне: Android SDK в проверке контента нет. Проверяется только чистая логика вокруг них.
