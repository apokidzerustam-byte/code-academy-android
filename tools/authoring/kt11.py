"""Урок Kotlin 11: фоновая работа (WorkManager) и сборка APK.
Вызовы WorkManager и настройки Gradle показаны как справочный код и не компилируются: Android SDK и Gradle в проверке контента нет.
Проверяется чистая логика: выбор инструмента, задержка повтора, период, номер версии."""
from mk import *


def L(code, text, n=1):
    lines = code.split("\n")
    i = next(k for k, ln in enumerate(lines) if text in ln)
    return list(range(i + 1, i + 1 + n))


K2 = ('fun chooseTool(visibleToUser: Boolean, exactTime: Boolean, mustSurviveRestart: Boolean): String = when {\n    visibleToUser -> "служба переднего плана"\n    exactTime -> "будильник"\n'
      '    mustSurviveRestart -> "WorkManager"\n    else -> "корутина"\n}\n\nfun main() {\n    println(chooseTool(true, false, false))\n    println(chooseTool(false, true, false))\n'
      '    println(chooseTool(false, false, true))\n    println(chooseTool(false, false, false))\n}\n')
O2 = "служба переднего плана\nбудильник\nWorkManager\nкорутина\n"
K3 = ('class SyncWorker(context: Context, params: WorkerParameters) : CoroutineWorker(context, params) {\n    override suspend fun doWork(): Result {\n        return try {\n            syncTasks()\n            Result.success()\n'
      '        } catch (e: IOException) {\n            if (runAttemptCount < 3) Result.retry() else Result.failure()\n        }\n    }\n}\n\n'
      'val request = PeriodicWorkRequestBuilder<SyncWorker>(1, TimeUnit.HOURS)\n    .setConstraints(\n        Constraints.Builder()\n            .setRequiredNetworkType(NetworkType.CONNECTED)\n            .setRequiresBatteryNotLow(true)\n            .build()\n    )\n'
      '    .setBackoffCriteria(BackoffPolicy.EXPONENTIAL, 30, TimeUnit.SECONDS)\n    .build()\n\nWorkManager.getInstance(context)\n    .enqueueUniquePeriodicWork("sync", ExistingPeriodicWorkPolicy.KEEP, request)\n')
K4 = ('fun retryDelay(attempt: Int): Int = minOf(30 * (1 shl (attempt - 1)), 18000)\n\nfun periodMinutes(requested: Int): Int = maxOf(requested, 15)\n\nfun main() {\n'
      '    for (a in listOf(1, 2, 3, 6, 12)) println("попытка $a: ${retryDelay(a)} с")\n    println(periodMinutes(5))\n    println(periodMinutes(60))\n}\n')
O4 = "попытка 1: 30 с\nпопытка 2: 60 с\nпопытка 3: 120 с\nпопытка 6: 960 с\nпопытка 12: 18000 с\n15\n60\n"
K5 = ('android {\n    defaultConfig {\n        versionCode = 10203\n        versionName = "1.2.3"\n    }\n    buildTypes {\n        release {\n            isMinifyEnabled = false\n            signingConfig = signingConfigs.getByName("release")\n        }\n    }\n}\n\n'
      '# сборка и проверка\n./gradlew assembleRelease\napksigner verify --print-certs app-release.apk\nadb install -r app-release.apk\n')
K6 = ('fun versionCode(name: String): Int {\n    val p = name.split(".").map { it.toInt() }\n    return p[0] * 10000 + p[1] * 100 + p[2]\n}\n\nfun main() {\n    println(versionCode("1.0.0"))\n    println(versionCode("1.2.3"))\n'
      '    println(versionCode("2.10.5"))\n    println(versionCode("1.2.3") < versionCode("1.10.0"))\n}\n')
O6 = "10000\n10203\n21005\ntrue\n"

use_file("Main.kt")
scenes = [
    scene("intro", "Работа без экрана", """
      Пока приложение на экране, всё просто. А что делать, если нужно синхронизировать данные, когда оно закрыто? Система Андроид
      бережёт батарею и сама останавливает всё, что работает без нужды. Поэтому для разной фоновой работы есть разные инструменты, и главное
      выбрать подходящий. Корутины работают, пока живёт приложение или экран: подойдёт для загрузки списка при открытии. Служба переднего
      плана нужна, когда пользователь видит и ждёт результат: играет музыка, идёт запись, показывается постоянное уведомление. Будильник
      срабатывает в точное время, как в приложении-будильнике. А WorkManager нужен для отложенной работы, которая обязана выполниться
      даже после перезапуска телефона: отправка черновика, синхронизация, очистка кэша. Система сама выберет удобный момент, когда
      есть сеть и достаточно заряда. Есть и ещё одна причина так делать: ночью и в кармане телефон переходит в экономный режим Doze, где
      обычные задачи откладываются. WorkManager умеет работать вместе с ним, а самодельные таймеры нет.""",
          [NOTE("**Корутина** — пока приложение живо · **служба переднего плана** — пользователь видит · **будильник** — точное время · **WorkManager** — отложено, но гарантированно", at="Корутины работают")]),
    scene("choose", "Как выбрать инструмент", """
      Выбор можно записать в виде обычной функции. Три вопроса. Видит ли пользователь работу: если да, нужна служба переднего плана.
      Нужно ли точное время: тогда будильник. Должна ли работа пережить перезапуск и выполниться позже: тогда WorkManager. Если ни одно
      условие не подошло, хватит корутины. Порядок вопросов важен: ветки проверяются сверху вниз. И ещё предупреждение: начиная с Андроида
      двенадцатого службу переднего плана почти нельзя запускать из фона, поэтому её запускают, пока пользователь работает с приложением.
      Запустим для четырёх ситуаций.""",
          [CLEAR(), T(K2, at="Выбор можно"), HL(L(K2, "visibleToUser ->"), at="Видит ли"), HL(L(K2, "exactTime ->"), at="Нужно ли точное"), HL(L(K2, "mustSurviveRestart ->"), at="Должна ли"),
           HL(L(K2, "else ->"), at="Если ни одно"), RUN(at="Запустим"), OUT(O2, at="Запустим")]),
    scene("worker", "WorkManager: работа и условия", """
      Вот типичная работа. Класс SyncWorker наследует CoroutineWorker, а вся работа происходит в функции doWork. Она возвращает один из
      трёх результатов. Success значит, что всё сделано. Retry просит систему повторить позже. Failure означает окончательный провал. В
      примере при ошибке сети мы просим повторить, но не больше трёх раз, число попыток даёт runAttemptCount. Ниже описан запрос на
      работу. Она периодическая, раз в час. Условия: сеть и достаточный заряд, пока их нет, работа ждёт. Политика повтора
      экспоненциальная: каждая следующая пауза вдвое больше. Наконец, уникальное имя sync с политикой KEEP не даёт запустить
      вторую копию, если первая уже стоит в очереди. Работы можно соединять в цепочки: сначала скачать данные, потом обработать, и вторая
      начнётся только после успеха первой. Этот код только покажем.""",
          [CLEAR(), T(K3, at="Вот типичная"), HL(L(K3, "override suspend fun doWork"), at="вся работа"), HL(L(K3, "Result.retry"), at="В примере"),
           HL(L(K3, "PeriodicWorkRequestBuilder"), at="Она периодическая"), HL(L(K3, "setRequiredNetworkType", 2), at="Условия"), HL(L(K3, "setBackoffCriteria"), at="Политика повтора"),
           HL(L(K3, "enqueueUniquePeriodicWork"), at="уникальное имя")]),
    scene("retry", "Задержка повтора и период", """
      Посмотрим на цифры. Задержка между повторами растёт по степеням двойки: первая попытка через тридцать секунд, вторая через шестьдесят,
      третья через сто двадцать. Но растёт она не бесконечно: у системы есть потолок в пять часов, то есть восемнадцать тысяч секунд.
      Обратите внимание на единицу: степень двойки берём от номера попытки минус один, иначе первая пауза окажется вдвое длиннее.
      Второе ограничение: период у периодической работы не может быть меньше пятнадцати минут. Если попросить пять, система поднимет до
      пятнадцати. Запустим.""",
          [CLEAR(), T(K4, at="Посмотрим на цифры"), HL(L(K4, "fun retryDelay"), at="Задержка между"), HL(L(K4, "fun periodMinutes"), at="Второе ограничение"),
           RUN(at="Запустим"), OUT(O4, at="Запустим")]),
    scene("apk", "Сборка и подпись APK", """
      Теперь о том, как приложение попадает на телефон. Установочный файл называется APK. Отладочная сборка подписывается временным ключом и
      нужна разработчику. Релизная подписывается настоящим ключом. Запомните три правила. Первое: обновление ставится поверх старой
      версии только если подпись та же, поэтому потеряв ключ, вы уже не сможете обновить приложение у пользователей. Второе: ключ и его
      пароли никогда не попадают в репозиторий: в нашем проекте релизный ключ берётся из переменных окружения CI, а ключ в репозитории
      только прототипный, для проверок, и в магазин с ним выходить нельзя. Третье: номер versionCode должен только расти, иначе система
      откажется ставить новую версию поверх. Сборка одной командой Gradle. Проверить подпись можно инструментом apksigner, а поставить файл на
      телефон командой adb install. Сжатие кода R8 в нашем проекте выключено сознательно: библиотекам Python и нативному коду нужны
      отдельные правила, а выигрыш в размере небольшой. Для магазина Google Play обычно собирают не APK, а пакет AAB: из него магазин сам
      делает файл под конкретный телефон, и скачивание получается меньше.""",
          [CLEAR(), T(K5, at="Теперь о том"), HL(L(K5, "signingConfig"), at="Второе"), HL(L(K5, "versionCode"), at="Третье"), HL(L(K5, "./gradlew"), at="Сборка одной"),
           HL(L(K5, "apksigner"), at="Проверить подпись"), HL(L(K5, "adb install"), at="adb install"), HL(L(K5, "isMinifyEnabled"), at="Сжатие кода")]),
    scene("version", "Номер версии", """
      Для людей версия выглядит как один, два, три, через точки. А системе нужно целое число versionCode, которое только растёт. Их
      легко связать: старшая часть умножается на десять тысяч, средняя на сто, и прибавляется младшая. Версия один точка два точка
      три превращается в десять тысяч двести три. Важно, чтобы средняя часть была меньше ста, иначе числа перекроются. Запустим: нулевая
      версия один даёт десять тысяч, потом наш пример, потом версия два точка десять точка пять. А в последней строке проверим, что версия
      один точка десять больше версии один точка два: при сравнении строк она оказалась бы меньше, ведь единица идёт раньше двойки. Для людей остаётся versionName: её пишут в настройках, и именно её пользователь видит
      в магазине, а versionCode нужен только системе.""",
          [CLEAR(), T(K6, at="Для людей"), HL(L(K6, "p[0] * 10000", 1), at="Их легко"), RUN(at="Запустим"), OUT(O6, at="Запустим")]),
    scene("mistakes", "Типичные ошибки", """
      Типичные ошибки. Первая: запускать долгую работу в корутине экрана и надеяться, что она доживёт. Закроют экран, и работа оборвётся.
      Вторая: выбирать службу переднего плана для всего подряд: пользователь увидит постоянное уведомление и расстроится. Третья: просить
      WorkManager о периоде короче пятнадцати минут или ждать точности до секунды: он не для этого. Четвёртая: потерять ключ подписи или
      положить его в репозиторий. Пятая: забыть поднять versionCode, и телефон не примет обновление.""",
          [NOTE("Ошибка 1: долгая работа в корутине экрана.", at="Первая"),
           NOTE("Ошибка 2: служба переднего плана «на всякий случай».", at="Вторая"),
           NOTE("Ошибка 3: период короче 15 минут и ожидание точности от WorkManager.", at="Третья"),
           NOTE("Ошибка 4: ключ потерян или лежит в репозитории.", at="Четвёртая"),
           NOTE("Ошибка 5: versionCode не вырос.", at="Пятая")]),
    scene("summary", "Итог", """
      Подведём итог. Для фоновой работы выбирают инструмент по задаче: корутина, служба переднего плана, будильник или WorkManager.
      WorkManager принимает условия, повторяет работу с растущей паузой и гарантирует выполнение. Приложение собирают командой Gradle и
      подписывают постоянным ключом, который хранят отдельно от кода. А номер версии должен только расти. В заданиях вы напишете выбор
      инструмента, задержку повтора, номер версии, исправите период и предскажете результат. Критерий прохождения: решить не меньше трёх
      заданий из пяти. Вызовы WorkManager и настройки Gradle показаны справочно, проверяется логика вокруг них.""",
          [NOTE("корутина · служба переднего плана · будильник · WorkManager — `retry` с паузой ×2, период ≥ 15 мин · ключ вне репозитория · `versionCode` только растёт", at="Подведём итог")]),
]

notes = """
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
"""

# --- a1: chooseTool ---
S1 = K2.split("\nfun main()")[0] + ""
S1 = S1.rstrip() + "\n"
START1 = 'fun chooseTool(visibleToUser: Boolean, exactTime: Boolean, mustSurviveRestart: Boolean): String = when {\n    // допишите четыре ветки\n}\n'
t1 = {"kind": "kotlin", "cases": [
    {"id": "syntax", "type": "syntax"},
    {"id": "fn", "type": "function", "name": "chooseTool", "paramTypes": ["Boolean", "Boolean", "Boolean"], "returns": "String"},
    {"id": "v", "raw": True, "type": "contains", "pattern": r'\bvisibleToUser\s*->\s*"служба переднего плана"', "message": "Пользователь видит работу — «служба переднего плана»"},
    {"id": "x", "raw": True, "type": "contains", "pattern": r'\bexactTime\s*->\s*"будильник"', "message": "Нужно точное время — «будильник»"},
    {"id": "m", "raw": True, "type": "contains", "pattern": r'\bmustSurviveRestart\s*->\s*"WorkManager"', "message": "Должна пережить перезапуск — «WorkManager»"},
    {"id": "e", "raw": True, "type": "contains", "pattern": r'\belse\s*->\s*"корутина"', "message": "Иначе — «корутина»"},
    {"id": "order", "hidden": True, "type": "contains", "pattern": r"\bvisibleToUser\s*->[\s\S]*\bexactTime\s*->[\s\S]*\bmustSurviveRestart\s*->",
     "message": "Порядок: видит ли пользователь, затем точное время, затем перезапуск"},
], "jvm": {"main": ('fun main() {\n    println(chooseTool(true, true, true))\n    println(chooseTool(false, true, true))\n    println(chooseTool(false, false, true))\n    println(chooseTool(false, false, false))\n}'),
           "expected_stdout": "служба переднего плана\nбудильник\nWorkManager\nкорутина"}}
a1 = asg("a1-tool", "complete", "Какой инструмент выбрать",
         "Допишите ветки `when` в `chooseTool`. Порядок вопросов: пользователь видит работу → «служба переднего плана»; нужно точное время → «будильник»; работа должна пережить перезапуск → «WorkManager»; иначе → «корутина».",
         "Выбрать инструмент фоновой работы.", "три признака Boolean", "Название инструмента.", ["Порядок веток важен."],
         hints("Каждая ветка when — условие, стрелка и результат.", "Ветки проверяются сверху вниз; первая подходящая побеждает.",
               "Сначала visibleToUser, затем exactTime, затем mustSurviveRestart.", "Последняя ветка else возвращает «корутина».",
               "visibleToUser -> \"служба переднего плана\"; exactTime -> \"будильник\"; mustSurviveRestart -> \"WorkManager\"; else -> \"корутина\""),
         t1, S1, "when выбирает первую подходящую ветку, поэтому порядок задаёт приоритет: если пользователь видит работу, остальные признаки уже неважны.",
         ["Четыре ветки.", "Порядок как в условии."],
         [('fun chooseTool(visibleToUser: Boolean, exactTime: Boolean, mustSurviveRestart: Boolean): String = when {\n    mustSurviveRestart -> "WorkManager"\n    exactTime -> "будильник"\n    visibleToUser -> "служба переднего плана"\n    else -> "корутина"\n}\n', "Порядок веток неверен: сначала проверяется, видит ли пользователь работу."),
          ('fun chooseTool(visibleToUser: Boolean, exactTime: Boolean, mustSurviveRestart: Boolean): String = when {\n    visibleToUser -> "служба переднего плана"\n    exactTime -> "будильник"\n    else -> "корутина"\n}\n', "Нет ветки «WorkManager»."),
          ('fun chooseTool(visibleToUser: Boolean, exactTime: Boolean, mustSurviveRestart: Boolean): String = when {\n    visibleToUser -> "будильник"\n    exactTime -> "служба переднего плана"\n    mustSurviveRestart -> "WorkManager"\n    else -> "корутина"\n}\n', "Результаты веток перепутаны.")],
         starter=START1)

# --- a2: retryDelay ---
S2 = 'fun retryDelay(attempt: Int): Int = minOf(30 * (1 shl (attempt - 1)), 18000)\n'
t2 = {"kind": "kotlin", "cases": [
    {"id": "syntax", "type": "syntax"},
    {"id": "fn", "type": "function", "name": "retryDelay", "paramTypes": ["Int"], "returns": "Int"},
    {"id": "base", "type": "contains", "pattern": r"\b30\b", "message": "Первая пауза — 30 секунд"},
    {"id": "exp", "type": "contains", "pattern": r"\bshl\b|\bpow\s*\(|\*=\s*2\b|\*\s*2\b|\b2\s*\*", "message": "Пауза растёт вдвое с каждой попыткой: степень двойки"},
    {"id": "cap", "type": "contains", "pattern": r"\b18000\b", "message": "Потолок — 18000 секунд (5 часов)"},
    {"id": "first", "hidden": True, "type": "contains", "pattern": r"-\s*1\b|\bfor\b|\brepeat\b|\bwhile\b", "message": "Первая попытка — 30 с (степень двойки от номера попытки минус один)"},
], "jvm": {"main": 'fun main() {\n    for (a in listOf(1, 2, 3, 4, 6, 10, 11, 12, 15)) println(retryDelay(a))\n}',
           "expected_stdout": "\n".join(str(min(30 * 2 ** (a - 1), 18000)) for a in [1, 2, 3, 4, 6, 10, 11, 12, 15])}}
a2 = asg("a2-backoff", "write", "Пауза перед повтором",
         "Напишите функцию `retryDelay(attempt: Int): Int`: пауза в секундах перед повтором номер `attempt` (1, 2, 3…). Первая — 30 секунд, каждая следующая вдвое больше (30, 60, 120…), но не больше 18000 секунд (5 часов). "
         "Попытки считайте не больше 15.",
         "Рассчитать экспоненциальную паузу.", "attempt: Int", "Секунды.", [],
         hints("Пауза удваивается: 30, 60, 120, 240…", "Это 30, умноженное на степень двойки: 30·2⁰, 30·2¹, 30·2²…",
               "Показатель степени равен номеру попытки минус один: для первой попытки он нулевой.", "Двойку в степени n получают сдвигом: 1 shl n.",
               "minOf(30 * (1 shl (attempt - 1)), 18000)"),
         t2, S2, "Показатель степени на единицу меньше номера попытки, иначе первая пауза окажется 60 секунд. minOf ограничивает рост потолком в 5 часов.",
         ["Рост вдвое.", "Первая пауза 30 с.", "Потолок 18000 с."],
         [('fun retryDelay(attempt: Int): Int = 30 * attempt\n', "Рост линейный: нужен рост вдвое (степень двойки)."),
          ('fun retryDelay(attempt: Int): Int = 30 * (1 shl (attempt - 1))\n', "Нет потолка: пауза не должна превышать 18000 секунд."),
          ('fun retryDelay(attempt: Int): Int = minOf(10 * (1 shl (attempt - 1)), 18000)\n', "Первая пауза должна быть 30 секунд."),
          ('fun retryDelay(attempt: Int): Int = minOf(30 * (1 shl attempt), 18000)\n', "Сдвиг на attempt даёт первую паузу в 60 секунд: нужен attempt - 1.")],
         starter="// Напишите функцию retryDelay\n")

# --- a3: versionCode ---
S3 = 'fun versionCode(name: String): Int {\n    val p = name.split(".").map { it.toInt() }\n    return p[0] * 10000 + p[1] * 100 + p[2]\n}\n'
t3 = {"kind": "kotlin", "cases": [
    {"id": "syntax", "type": "syntax"},
    {"id": "fn", "type": "function", "name": "versionCode", "paramTypes": ["String"], "returns": "Int"},
    {"id": "split", "raw": True, "type": "contains", "pattern": r'split\s*\(\s*"\."\s*\)', "message": "Версия разбивается по точкам: split(\".\")"},
    {"id": "w", "type": "contains", "pattern": r"\b10000\b", "message": "Старшая часть умножается на 10000"},
    {"id": "w2", "type": "contains", "pattern": r"\*\s*100\b|\b100\s*\*", "message": "Средняя часть умножается на 100"},
    {"id": "num", "hidden": True, "type": "contains", "pattern": r"toInt\s*\(\s*\)|toIntOrNull", "message": "Части версии — строки: превратите их в числа"},
], "jvm": {"main": 'fun main() {\n    println(versionCode("1.0.0"))\n    println(versionCode("1.2.3"))\n    println(versionCode("2.10.5"))\n    println(versionCode("0.9.12"))\n}',
           "expected_stdout": "10000\n10203\n21005\n912"}}
a3 = asg("a3-version", "write", "Номер версии",
         "Напишите функцию `versionCode(name: String): Int`: из версии вида `1.2.3` получите число `старшая * 10000 + средняя * 100 + младшая`. "
         "Например, `1.2.3` → 10203, `2.10.5` → 21005. Считайте, что вход всегда корректен и содержит три числа.",
         "Связать версию для людей с versionCode.", "name: String", "Int.", [],
         hints("Версию нужно разбить на три части по точке.", "Строку делит метод split(\".\"); части — тоже строки.",
               "Каждую часть превращают в число методом toInt(); для списка — map { it.toInt() }.", "Старшая часть весит 10000, средняя — 100, младшая — 1.",
               "val p = name.split(\".\").map { it.toInt() }; return p[0] * 10000 + p[1] * 100 + p[2]"),
         t3, S3, "Разряды с запасом (по два десятичных знака на среднюю и младшую части) делают числа монотонными: большая версия всегда даёт большее число.",
         ["Разбор по точкам.", "Веса 10000, 100 и 1."],
         [('fun versionCode(name: String): Int {\n    val p = name.split(".").map { it.toInt() }\n    return p[0] * 1000 + p[1] * 100 + p[2]\n}\n', "Вес старшей части должен быть 10000."),
          ('fun versionCode(name: String): Int {\n    return name.replace(".", "").toInt()\n}\n', "Склейка цифр ломает порядок: 1.10.0 станет меньше 1.2.3. Нужны веса разрядов."),
          ('fun versionCode(name: String): Int {\n    val p = name.split(".").map { it.toInt() }\n    return p[0] + p[1] + p[2]\n}\n', "Сумма частей не различает версии: нужны веса 10000, 100 и 1.")],
         starter="// Напишите функцию versionCode\n")

# --- a4: fix minOf -> maxOf ---
BAD4 = 'fun periodMinutes(requested: Int): Int = minOf(requested, 15)\n'
S4 = 'fun periodMinutes(requested: Int): Int = maxOf(requested, 15)\n'
t4 = {"kind": "kotlin", "cases": [
    {"id": "syntax", "type": "syntax"},
    {"id": "fn", "type": "function", "name": "periodMinutes", "paramTypes": ["Int"], "returns": "Int"},
    {"id": "fix", "type": "contains", "pattern": r"maxOf\s*\(\s*requested\s*,\s*15\s*\)|maxOf\s*\(\s*15\s*,\s*requested\s*\)|requested\s*\.coerceAtLeast\s*\(\s*15\s*\)|if\s*\(\s*requested\s*<\s*15\s*\)\s*15\s*else\s*requested|if\s*\(\s*requested\s*>=\s*15\s*\)\s*requested\s*else\s*15",
     "message": "Период не может быть меньше 15: берите большее из двух (maxOf или coerceAtLeast)", "hint": "Сейчас функция режет период сверху: 60 минут превращаются в 15"},
], "jvm": {"main": 'fun main() {\n    println(periodMinutes(5))\n    println(periodMinutes(15))\n    println(periodMinutes(60))\n}', "expected_stdout": "15\n15\n60"}}
a4 = asg("a4-period", "fix", "Минимальный период",
         "Периодическая работа WorkManager не бывает чаще, чем раз в **15 минут**: если просят меньше — берётся 15, а если больше — остаётся как есть. Функция `periodMinutes` ведёт себя наоборот (60 превращает в 15). Исправьте её.",
         "Применять нижнюю границу значения.", "requested: Int", "Минуты.", ["Сигнатуру не менять."],
         hints("Проверьте на примере: 60 должно остаться 60, а сейчас получается 15.", "minOf берёт меньшее из двух чисел, и это ограничивает значение сверху.",
               "Нам нужна нижняя граница: результат не меньше 15.", "Для нижней границы нужно большее из двух чисел.",
               "maxOf(requested, 15)"),
         t4, S4, "minOf ограничивает значение сверху, maxOf — снизу. Минимальный период 15 минут — это ограничение снизу, поэтому нужен maxOf.",
         ["5 → 15.", "60 → 60."],
         [(BAD4, "Ошибка осталась: minOf режет период сверху."),
          ('fun periodMinutes(requested: Int): Int = 15\n', "Период всегда 15: значения больше 15 должны сохраняться."),
          ('fun periodMinutes(requested: Int): Int = requested.coerceAtMost(15)\n', "coerceAtMost — верхняя граница; нужна нижняя (coerceAtLeast).")],
         starter=BAD4)

# --- a5: predict ---
CODE5 = ('fun resultFor(ok: Boolean, attempt: Int, max: Int): String = when {\n    ok -> "success"\n    attempt < max -> "retry"\n    else -> "failure"\n}\n\n'
         'fun main() {\n    var attempt = 0\n    val outcomes = listOf(false, false, true)\n    val log = mutableListOf<String>()\n    for (ok in outcomes) {\n        attempt++\n        log.add(resultFor(ok, attempt, 3))\n    }\n'
         '    println(log)\n    println(resultFor(false, 3, 3))\n    println(resultFor(false, 1, 1))\n}\n')
ans5 = "[retry, retry, success]\nfailure\nfailure"
a5 = asg("a5-predict", "predict", "Повторы работы",
         "Функция `resultFor` возвращает результат работы, как `doWork`: успех, повтор или окончательный провал. Что выведет программа?",
         "Проследить логику повторов.", "—", "Три строки.", [],
         hints("Сначала разберите resultFor: при успехе — success; иначе, если попыток меньше максимума, — retry; иначе failure.", "В цикле попытки нумеруются 1, 2, 3.",
               "Первая и вторая попытки неудачны, но 1 < 3 и 2 < 3: оба раза retry.", "Третья попытка успешна: success.",
               "resultFor(false, 3, 3): 3 < 3 ложно — failure; resultFor(false, 1, 1): 1 < 1 ложно — failure."),
         {"kind": "answer", "expected_answer": ans5}, ans5,
         "Две неудачи при попытках 1 и 2 (меньше трёх) дают retry, третья попытка успешна. Когда попытка достигла максимума, а работа не удалась, повторять уже нельзя — failure.",
         ["Все три строки верны."],
         [("[retry, retry, retry]\nretry\nretry", "Когда попытка равна максимуму, повтора уже нет: failure."),
          ("[retry, retry, failure]\nfailure\nfailure", "Третья попытка в списке успешна — success."),
          ("[retry, retry, success]\nretry\nfailure", "При attempt = 3 и max = 3 условие attempt < max ложно: failure.")],
         code=CODE5)

skills = {"kt.work.tool": "Фоновая работа: выбор инструмента", "kt.work.manager": "WorkManager: повторы и условия", "kt.apk.sign": "Сборка APK: подпись и versionCode"}
write_lesson("kt-11-background-apk", "Kotlin: фоновая работа и сборка APK",
             "Выбирать инструмент фоновой работы, понимать повторы и условия WorkManager, подписывать и версионировать APK.",
             list(skills), ["kt-10-permissions"], scenes, notes, [a1, a2, a3, a4, a5],
             [{"mistake": "Долгая работа в корутине экрана", "fix": "Для работы, которая должна пережить закрытие экрана, используйте WorkManager."},
              {"mistake": "Служба переднего плана для всего подряд", "fix": "Она нужна только когда пользователь видит и ждёт результат."},
              {"mistake": "Потерян ключ подписи или он лежит в репозитории", "fix": "Храните ключ отдельно и делайте его резервную копию; пароли — в секретах."},
              {"mistake": "versionCode не вырос", "fix": "Номер должен только расти: сопоставьте версию для людей с числом."}],
             min_pass=3, pack="kotlin-basics", runner="kotlin")
f = ROOT / "content/packs/kotlin-basics/pack.json"
data = json.loads(f.read_text("utf-8"))
if "kt-11-background-apk" not in data["lessons"]:
    data["lessons"].append("kt-11-background-apk")
data["skills"].update(skills)
f.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", "utf-8")
