"""Урок Kotlin 10: разрешения и уведомления Android.
Вызовы Android API (запрос разрешения, канал и уведомление) в уроке показаны как справочный код и не компилируются: Android SDK в CI-проверке контента нет.
Проверяется чистая логика вокруг них: решение по разрешению, версии Android, текст уведомления с падежом числа, список недостающих разрешений."""
from mk import *


def L(code, text, n=1):
    lines = code.split("\n")
    i = next(k for k, ln in enumerate(lines) if text in ln)
    return list(range(i + 1, i + 1 + n))


KM = '<uses-permission android:name="android.permission.POST_NOTIFICATIONS" />\n'
KF = ('val launcher = rememberLauncherForActivityResult(\n    ActivityResultContracts.RequestPermission()\n) { granted ->\n    if (granted) showNotification() else showExplanation()\n}\n\n'
      'val has = ContextCompat.checkSelfPermission(\n    context, Manifest.permission.POST_NOTIFICATIONS\n) == PackageManager.PERMISSION_GRANTED\n\n'
      'Button(onClick = { launcher.launch(Manifest.permission.POST_NOTIFICATIONS) }) {\n    Text("Включить уведомления")\n}\n')
K3 = ('fun nextStep(granted: Boolean, shouldShowRationale: Boolean): String = when {\n    granted -> "использовать"\n    shouldShowRationale -> "объяснить"\n    else -> "спросить"\n}\n\n'
      'fun main() {\n    println(nextStep(true, false))\n    println(nextStep(false, true))\n    println(nextStep(false, false))\n}\n')
O3 = "использовать\nобъяснить\nспросить\n"
K4 = ('fun canNotify(sdk: Int, granted: Boolean): Boolean = sdk < 33 || granted\n\nfun main() {\n    println(canNotify(30, false))\n    println(canNotify(33, false))\n    println(canNotify(34, true))\n}\n')
O4 = "true\nfalse\ntrue\n"
K5 = ('val channel = NotificationChannel("tasks", "Задачи", NotificationManager.IMPORTANCE_DEFAULT)\ncontext.getSystemService(NotificationManager::class.java)\n    .createNotificationChannel(channel)\n\n'
      'val notification = NotificationCompat.Builder(context, "tasks")\n    .setSmallIcon(R.drawable.ic_notification)\n    .setContentTitle("Напоминание")\n    .setContentText("У вас 3 задачи")\n    .build()\n\n'
      'NotificationManagerCompat.from(context).notify(1, notification)\n')
K6 = ('fun tasksText(n: Int): String {\n    val word = when {\n        n % 100 in 11..14 -> "задач"\n        n % 10 == 1 -> "задача"\n        n % 10 in 2..4 -> "задачи"\n        else -> "задач"\n    }\n    return "У вас $n $word"\n}\n\n'
      'fun main() {\n    println(tasksText(1))\n    println(tasksText(3))\n    println(tasksText(5))\n    println(tasksText(11))\n    println(tasksText(21))\n}\n')
O6 = "У вас 1 задача\nУ вас 3 задачи\nУ вас 5 задач\nУ вас 11 задач\nУ вас 21 задача\n"

use_file("Main.kt")
scenes = [
    scene("intro", "Разрешения: доверие пользователя", """
      Телефон знает о человеке очень много: где он, с кем говорит, что снимает. Поэтому Андроид не даёт приложению доступ к опасным
      возможностям по умолчанию. Камера, микрофон, местоположение, контакты, и с недавних пор даже показ уведомлений: на всё это
      приложение должно получить согласие пользователя. Первое правило разработчика простое: просите только то, без чего функция не
      работает. Каждое лишнее разрешение это повод для пользователя удалить приложение. Хороший пример перед глазами: в манифесте
      самого Code Academy нет ни одной строки с разрешением. Приложению хватает того, что у него есть. Если без разрешения всё же
      не обойтись, действует честная схема: объяснить, зачем оно нужно, попросить в тот момент, когда оно понадобилось, и
      корректно работать, если пользователь отказал.""",
          [NOTE("Просите только необходимое · объясняйте зачем · просите в нужный момент · работайте и при отказе", at="Первое правило"),
           NOTE("У Code Academy в манифесте нет ни одного `uses-permission`", at="Хороший пример")]),
    scene("request", "Как попросить разрешение", """
      Сначала разрешение объявляют в манифесте, файле с описанием приложения. Одной строкой, с названием разрешения. Без неё система даже
      не покажет окно запроса. Дальше, уже в коде, действуем в три шага. Первый: проверить, есть ли уже разрешение. Для этого есть
      вызов checkSelfPermission, и сравнивают его результат с константой «разрешено». Второй: запросить. В Compose для этого создают
      launcher, объект, который открывает системное окно и возвращает ответ пользователя. Нажатие кнопки вызывает launch с названием
      разрешения. Третий: обработать ответ. Если пользователь согласился, показываем уведомление, а если отказал, объясняем, чего он
      лишится, и приложение продолжает работать без этой функции. Этот код только покажем: настоящие вызовы Андроида проверяются
      при сборке полного приложения, а мы сегодня разберём логику вокруг них.""",
          [CLEAR(), T(KM + "\n" + KF, at="Сначала разрешение"), HL([1], at="Одной строкой"), HL(L(KM + "\n" + KF, "val has", 3), at="Первый"),
           HL(L(KM + "\n" + KF, "val launcher", 4), at="Второй"), HL(L(KM + "\n" + KF, "Button(onClick"), at="Нажатие кнопки"), HL(L(KM + "\n" + KF, "if (granted)"), at="Третий")]),
    scene("decide", "Что делать дальше", """
      У разрешения для приложения три ситуации. Первая: оно уже выдано, и функцию можно просто использовать. Вторая: не выдано, но
      пользователь однажды отказал. Тогда система подсказывает, что стоит сперва объяснить, зачем оно нужно, и этот вопрос задаёт
      функция shouldShowRequestPermissionRationale. Третья: не выдано, и объяснять пока нечего, это первый запрос, и можно показать
      системное окно. Обратите внимание на порядок проверок. Сначала смотрим, выдано ли разрешение: если да, остальное не важно. Мы вынесли
      это решение в обычную функцию без всякого Андроида. Её легко проверять. Есть и тонкость: если пользователь в системном окне выбрал
      запрет навсегда, окно больше не появится, и повторный запрос бесполезен. Тогда честно скажите, как включить функцию, и предложите
      открыть настройки приложения. Запустим для трёх ситуаций.""",
          [CLEAR(), T(K3, at="У разрешения"), HL(L(K3, "granted ->"), at="Первая"), HL(L(K3, "shouldShowRationale ->"), at="Вторая"), HL(L(K3, "else ->"), at="Третья"),
           RUN(at="Запустим"), OUT(O3, at="Запустим")]),
    scene("version", "Версии Андроида", """
      Правила зависят от версии системы. До Андроида тринадцатого уведомления показывались без спроса. Начиная с него, это отдельное
      опасное разрешение, которое называется POST_NOTIFICATIONS. Номер версии SDK для Андроида тринадцать равен тридцати трём. Поэтому
      код всегда спрашивает у системы её версию и ведёт себя по-разному. Функция canNotify получает версию и признак «разрешение выдано».
      Если версия меньше тридцати трёх, показывать можно всегда. Иначе всё зависит от разрешения. Запустим: для версии тридцать без
      разрешения ответ положительный, для тридцать третьей без разрешения отрицательный, а для тридцать четвёртой с разрешением
      положительный.""",
          [CLEAR(), T(K4, at="Правила зависят"), HL(L(K4, "fun canNotify"), at="Функция canNotify"), HL(L(K4, "sdk < 33"), at="Если версия меньше"), RUN(at="Запустим"), OUT(O4, at="Запустим")]),
    scene("ux", "Как просить правильно", """
      Разберём, как просить так, чтобы пользователь соглашался. Представьте приложение для напоминаний. Не показывайте системное окно
      сразу при запуске. Дождитесь момента, когда человек сам включает напоминание, и покажите короткий экран на человеческом языке: «Чтобы
      напомнить вовремя, нам нужно разрешение на уведомления». Одна фраза про пользу работает лучше длинного юридического текста. Только после
      этого вызывайте системное окно. Если ответ отрицательный, не настаивайте и не показывайте окно снова при каждом входе. Покажите
      спокойное сообщение и оставьте запасной путь, например напоминания внутри самого приложения. Доверие, которое вы заработали, стоит
      дороже одной функции.""",
          [NOTE("Не при запуске, а когда функция нужна · одна фраза про пользу · потом системное окно", at="Не показывайте"),
           NOTE("Отказ — не повод настаивать: спокойное сообщение и запасной путь", at="Если ответ")]),
    scene("notify", "Канал и уведомление", """
      Теперь само уведомление. Начиная с Андроида восьмого каждое уведомление должно принадлежать каналу. Канал это категория, которую
      пользователь может настроить в системных настройках: например, оставить напоминания, а рекламу выключить. Канал создают один раз,
      с идентификатором, названием и важностью. Затем строят уведомление: нужны маленький значок, заголовок и текст, и обязательно
      идентификатор того же канала. Чтобы нажатие на уведомление открывало приложение, к нему добавляют намерение, PendingIntent.
      Наконец, менеджер уведомлений показывает его по номеру: если показать новое уведомление с тем же номером, оно заменит старое. Не создавайте канал на каждое уведомление и не ставьте высшую важность без причины: звук и
      всплывающие окна раздражают, и пользователь выключит канал целиком.""",
          [CLEAR(), T(K5, at="Теперь само"), HL(L(K5, "val channel", 3), at="Канал создают"), HL(L(K5, "val notification", 5), at="Затем строят"), HL(L(K5, "notify(1"), at="Наконец")]),
    scene("plural", "Текст уведомления", """
      Хорошее уведомление говорит по-человечески. «У вас пять задач» звучит естественно, а «У вас пять задача» режет глаз. В русском языке
      слово зависит от числа: одна задача, две задачи, пять задач. Правило такое. Если число заканчивается на единицу, но не на одиннадцать, то
      «задача». Если на два, три или четыре, и это не числа от одиннадцати до четырнадцати, то «задачи». Иначе «задач». Поэтому сначала
      проверяют остаток от деления на сто: числа от одиннадцати до четырнадцати особые. Затем остаток от деления на десять. Запустим:
      один, три, пять, одиннадцать и двадцать один.""",
          [CLEAR(), T(K6, at="Хорошее уведомление"), HL(L(K6, "n % 100 in 11..14"), at="Поэтому сначала"), HL(L(K6, "n % 10 == 1", 2), at="Затем остаток"),
           RUN(at="Запустим"), OUT(O6, at="Запустим")]),
    scene("mistakes", "Типичные ошибки", """
      Типичные ошибки. Первая: попросить все разрешения при первом запуске. Пользователь не понимает, зачем они, и отказывает. Просите в
      тот момент, когда функция нужна. Вторая: не учесть отказ. Если приложение падает или молчит без разрешения, это плохо. Всегда
      оставляйте запасной путь. Третья: забыть про версии Андроида: код, рассчитанный на тринадцатую версию, на восьмой может упасть.
      Четвёртая: не создать канал или создавать его на каждое уведомление. И пятая, из жизни: ошибка в форме слова. Пользователь
      заметит «одиннадцать задачи» сразу.""",
          [NOTE("Ошибка 1: все разрешения сразу при запуске.", at="Первая"),
           NOTE("Ошибка 2: нет запасного пути при отказе.", at="Вторая"),
           NOTE("Ошибка 3: не учтены версии Андроида (33 для уведомлений).", at="Третья"),
           NOTE("Ошибка 4: нет канала или канал на каждое уведомление.", at="Четвёртая"),
           NOTE("Ошибка 5: неверная форма слова в тексте («11 задачи»).", at="пятая")]),
    scene("summary", "Итог", """
      Подведём итог. Разрешения защищают пользователя, поэтому просите только необходимое и в нужный момент. Схема такая: объявить в
      манифесте, проверить, запросить, обработать ответ. Если разрешения нет, а пользователь уже отказывал, сначала объясните. Для уведомлений
      нужен канал, а начиная с Андроида тринадцать ещё и разрешение. В заданиях вы напишете решение по разрешению, функцию версии, форму слова
      в тексте, исправите поиск недостающих разрешений и предскажете результат. Критерий прохождения: решить не меньше трёх заданий из пяти.
      Вызовы Андроида показаны справочно, проверяется логика вокруг них.""",
          [NOTE("манифест → проверить → запросить → обработать ответ · канал + разрешение (SDK 33+) · `задача` / `задачи` / `задач`", at="Подведём итог")]),
]

notes = """
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
"""

# --- a1: nextStep ---
S1 = 'fun nextStep(granted: Boolean, shouldShowRationale: Boolean): String = when {\n    granted -> "использовать"\n    shouldShowRationale -> "объяснить"\n    else -> "спросить"\n}\n'
START1 = 'fun nextStep(granted: Boolean, shouldShowRationale: Boolean): String = when {\n    // допишите три ветки\n}\n'
t1 = {"kind": "kotlin", "cases": [
    {"id": "syntax", "type": "syntax"},
    {"id": "fn", "type": "function", "name": "nextStep", "paramTypes": ["Boolean", "Boolean"], "returns": "String"},
    {"id": "g", "raw": True, "type": "contains", "pattern": r'\bgranted\s*->\s*"использовать"', "message": "Если разрешение выдано — «использовать»: granted -> \"использовать\""},
    {"id": "r", "raw": True, "type": "contains", "pattern": r'\bshouldShowRationale\s*->\s*"объяснить"', "message": "Если пользователь уже отказывал — «объяснить»"},
    {"id": "e", "raw": True, "type": "contains", "pattern": r'\belse\s*->\s*"спросить"', "message": "Во всех остальных случаях — «спросить»"},
    {"id": "order", "hidden": True, "type": "contains", "pattern": r"\bgranted\s*->[\s\S]*\bshouldShowRationale\s*->",
     "message": "Сначала проверьте granted: если разрешение выдано, остальное не важно"},
], "jvm": {"main": 'fun main() {\n    println(nextStep(true, true))\n    println(nextStep(true, false))\n    println(nextStep(false, true))\n    println(nextStep(false, false))\n}',
           "expected_stdout": "использовать\nиспользовать\nобъяснить\nспросить"}}
a1 = asg("a1-step", "complete", "Что делать с разрешением",
         "Допишите ветки `when` в функции `nextStep(granted, shouldShowRationale)`: если разрешение выдано (`granted`) — вернуть «использовать»; если не выдано, но пользователь отказывал (`shouldShowRationale`) — «объяснить»; иначе — «спросить». Порядок проверок важен.",
         "Выбрать действие по состоянию разрешения.", "granted, shouldShowRationale: Boolean", "Одна из трёх строк.",
         ["Порядок веток when: сначала granted."],
         hints("Ветка when записывается как условие, стрелка и результат.", "Первой проверяйте granted: если разрешение есть, остальное не важно.",
               "Вторая ветка — shouldShowRationale: сначала объясняем, зачем нужно разрешение.", "Последняя ветка — else.",
               "granted -> \"использовать\"; shouldShowRationale -> \"объяснить\"; else -> \"спросить\""),
         t1, S1, "when проверяет ветки сверху вниз и берёт первую подходящую, поэтому порядок задаёт приоритет: выданное разрешение важнее подсказки, а подсказка важнее первого запроса.",
         ["Три ветки.", "Порядок: granted, затем shouldShowRationale."],
         [('fun nextStep(granted: Boolean, shouldShowRationale: Boolean): String = when {\n    shouldShowRationale -> "объяснить"\n    granted -> "использовать"\n    else -> "спросить"\n}\n', "Порядок веток: при выданном разрешении объяснять ничего не нужно, granted проверяется первым."),
          ('fun nextStep(granted: Boolean, shouldShowRationale: Boolean): String = when {\n    granted -> "использовать"\n    else -> "спросить"\n}\n', "Нет ветки «объяснить»."),
          ('fun nextStep(granted: Boolean, shouldShowRationale: Boolean): String = when {\n    granted -> "спросить"\n    shouldShowRationale -> "объяснить"\n    else -> "использовать"\n}\n', "Результаты перепутаны: выданное разрешение — «использовать»."),],
         starter=START1)

# --- a2: tasksText ---
S2 = ('fun tasksText(n: Int): String {\n    val word = when {\n        n % 100 in 11..14 -> "задач"\n        n % 10 == 1 -> "задача"\n        n % 10 in 2..4 -> "задачи"\n        else -> "задач"\n    }\n    return "У вас $n $word"\n}\n')
t2 = {"kind": "kotlin", "cases": [
    {"id": "syntax", "type": "syntax"},
    {"id": "fn", "type": "function", "name": "tasksText", "paramTypes": ["Int"], "returns": "String"},
    {"id": "m10", "type": "contains", "pattern": r"%\s*10\b", "message": "Форма зависит от последней цифры: n % 10"},
    {"id": "m100", "type": "contains", "pattern": r"%\s*100\b", "message": "Числа 11–14 особые: нужен остаток n % 100"},
    {"id": "teen", "hidden": True, "type": "contains", "pattern": r"\b11\b", "message": "Числа от 11 до 14 всегда «задач»: 11 задач, а не «11 задача»"},
    {"id": "w1", "raw": True, "type": "contains", "pattern": r'"задача"', "message": "Нужна форма «задача» (1, 21, 101…)"},
    {"id": "w2", "raw": True, "type": "contains", "pattern": r'"задачи"', "message": "Нужна форма «задачи» (2–4, 22–24…)"},
    {"id": "w3", "raw": True, "type": "contains", "pattern": r'"задач"', "message": "Нужна форма «задач» (0, 5–20, 25…)"},
    {"id": "fmt", "raw": True, "type": "contains", "pattern": r'"У вас\s*\$\{?n\}?\s*\$\{?\w+\}?"|"У вас\s*\$\{?n\}?\s*"\s*\+|"У вас "\s*\+\s*n', "message": "Результат: «У вас <число> <слово>», например «У вас 5 задач»"},
], "jvm": {"main": ('fun main() {\n    for (n in listOf(0, 1, 2, 4, 5, 11, 12, 14, 21, 22, 25, 100, 101, 111)) println(tasksText(n))\n}'),
           "expected_stdout": "\n".join(f"У вас {n} {w}" for n, w in [(0, "задач"), (1, "задача"), (2, "задачи"), (4, "задачи"), (5, "задач"), (11, "задач"), (12, "задач"), (14, "задач"), (21, "задача"), (22, "задачи"), (25, "задач"), (100, "задач"), (101, "задача"), (111, "задач")])}}
a2 = asg("a2-plural", "write", "Форма слова «задача»",
         "Напишите функцию `tasksText(n: Int): String`, которая возвращает текст уведомления: «У вас N задача/задачи/задач». Форма: оканчивается на 1 (кроме 11) — «задача»; на 2, 3, 4 (кроме 12–14) — «задачи»; во всех остальных случаях, включая 0 и 11–14, — «задач». "
         "Например: 1 → «У вас 1 задача», 22 → «У вас 22 задачи», 11 → «У вас 11 задач».",
         "Склонять слово после числа.", "n: Int", "Строка вида «У вас 5 задач».", [],
         hints("Форма зависит от последней цифры числа: её даёт остаток от деления на 10.", "Числа от 11 до 14 — исключение: проверьте их первыми, остатком от деления на 100.",
               "Остаток от деления на 100 между 11 и 14 включительно — «задач».", "Дальше: остаток на 10 равен 1 — «задача»; от 2 до 4 — «задачи»; иначе «задач».",
               "when { n % 100 in 11..14 -> \"задач\"; n % 10 == 1 -> \"задача\"; n % 10 in 2..4 -> \"задачи\"; else -> \"задач\" }, затем \"У вас $n $word\""),
         t2, S2, "Исключение 11–14 проверяется первым, иначе 11 дало бы «задача» (последняя цифра 1). Остальное определяет последняя цифра.",
         ["Три формы слова.", "Исключение 11–14.", "Формат «У вас N …»."],
         [('fun tasksText(n: Int): String {\n    val word = if (n == 1) "задача" else "задач"\n    return "У вас $n $word"\n}\n', "Только две формы: для 2, 3, 4 нужно «задачи»; для 21 — «задача»."),
          ('fun tasksText(n: Int): String {\n    val word = when {\n        n % 10 == 1 -> "задача"\n        n % 10 in 2..4 -> "задачи"\n        else -> "задач"\n    }\n    return "У вас $n $word"\n}\n', "Не учтено исключение 11–14: «11 задача» неверно."),
          ('fun tasksText(n: Int): String {\n    val word = when {\n        n % 100 in 11..14 -> "задач"\n        n % 10 == 1 -> "задача"\n        n % 10 in 2..4 -> "задачи"\n        else -> "задач"\n    }\n    return "$n $word"\n}\n', "Нет начала «У вас»: формат «У вас N слово».")],
         starter="// Напишите функцию tasksText\n")

# --- a3: canNotify ---
S3 = 'fun canNotify(sdk: Int, granted: Boolean): Boolean {\n    if (sdk < 33) return true\n    return granted\n}\n'
START3 = 'fun canNotify(sdk: Int, granted: Boolean): Boolean {\n    // до Android 13 (SDK 33) разрешение не требуется\n}\n'
t3 = {"kind": "kotlin", "cases": [
    {"id": "syntax", "type": "syntax"},
    {"id": "fn", "type": "function", "name": "canNotify", "paramTypes": ["Int", "Boolean"], "returns": "Boolean"},
    {"id": "v33", "type": "contains", "pattern": r"\b33\b|\b32\b", "message": "Граница — SDK 33 (Android 13)"},
    {"id": "g", "type": "contains", "pattern": r"(\breturn|\|\||&&|\belse|->)\s*\(?\s*granted\b|\)\s+granted\b", "message": "Начиная с SDK 33 всё зависит от granted"},
    {"id": "w1", "hidden": True, "type": "not_contains", "pattern": r">=\s*33\s*\|\|", "message": "Перепутано направление: для SDK ниже 33 уведомления можно показывать без разрешения"},
    {"id": "w2", "hidden": True, "type": "not_contains", "pattern": r"<\s*33\s*&&", "message": "Для SDK ниже 33 разрешение не нужно: не требуйте granted"},
    {"id": "w3", "hidden": True, "type": "not_contains", "pattern": r">=\s*33\s*\)\s*(\{\s*)?(return\s+)?true", "message": "Для SDK 33 и выше нужно разрешение"},
], "jvm": {"main": 'fun main() {\n    println(canNotify(26, false))\n    println(canNotify(32, false))\n    println(canNotify(33, false))\n    println(canNotify(33, true))\n    println(canNotify(35, false))\n}',
           "expected_stdout": "true\ntrue\nfalse\ntrue\nfalse"}}
a3 = asg("a3-version", "complete", "Нужно ли разрешение",
         "Допишите `canNotify(sdk: Int, granted: Boolean): Boolean`: можно ли показывать уведомления. До Android 13 (SDK **меньше 33**) разрешение не требуется — всегда `true`. Начиная с SDK 33 — только если `granted`.",
         "Учесть версию Android в проверке разрешения.", "sdk: Int, granted: Boolean", "Boolean.", [],
         hints("Сначала разберите случай старой системы: версия ниже 33.", "На старых версиях уведомления разрешены всегда.",
               "На версии 33 и выше результат совпадает со значением granted.", "Условие для старой системы: sdk < 33.",
               "if (sdk < 33) return true; return granted"),
         t3, S3, "Разрешение POST_NOTIFICATIONS появилось в Android 13 (SDK 33). На старых версиях его нет, поэтому уведомления показываются всегда; на новых — только после согласия.",
         ["SDK < 33 → true.", "SDK ≥ 33 → granted."],
         [('fun canNotify(sdk: Int, granted: Boolean): Boolean {\n    return granted\n}\n', "Не учтена версия: на SDK ниже 33 уведомления разрешены без запроса."),
          ('fun canNotify(sdk: Int, granted: Boolean): Boolean {\n    return sdk >= 33 || granted\n}\n', "Направление перепутано: на SDK 33 без разрешения уведомления показывать нельзя."),
          ('fun canNotify(sdk: Int, granted: Boolean): Boolean {\n    return sdk < 33 && granted\n}\n', "На старых версиях разрешение не требуется: granted проверяется только с SDK 33."),
          ('fun canNotify(sdk: Int, granted: Boolean): Boolean {\n    if (sdk >= 33) return true\n    return granted\n}\n', "Для SDK 33 и выше нужно разрешение, а не безусловное true.")],
         starter=START3)

# --- a4: fix inverted filter ---
BAD4 = ('fun permissionsToRequest(required: List<String>, granted: Set<String>): List<String> {\n    return required.filter { it in granted }\n}\n')
S4 = ('fun permissionsToRequest(required: List<String>, granted: Set<String>): List<String> {\n    return required.filter { it !in granted }\n}\n')
t4 = {"kind": "kotlin", "cases": [
    {"id": "syntax", "type": "syntax"},
    {"id": "fn", "type": "function", "name": "permissionsToRequest", "paramTypes": ["List<String>", "Set<String>"], "returns": "List<String>"},
    {"id": "not", "type": "contains", "pattern": r"filterNot\s*\{\s*it\s+in\s+granted\s*\}|\bit\s+!in\s+granted\b|!\s*granted\.contains\s*\(\s*it\s*\)|!\s*\(\s*it\s+in\s+granted\s*\)|granted\.contains\s*\(\s*it\s*\)\s*\.not\s*\(\s*\)|filter\s*\{\s*it\s*!in",
     "message": "Нужны разрешения, которых ещё нет: отфильтруйте те, что НЕ входят в granted",
     "hint": "Сейчас функция возвращает уже выданные разрешения"},
], "jvm": {"main": ('fun main() {\n    println(permissionsToRequest(listOf("camera", "mic", "notifications"), setOf("camera")))\n    println(permissionsToRequest(listOf("camera"), setOf("camera")))\n'
                    '    println(permissionsToRequest(listOf("mic"), emptySet()))\n}'), "expected_stdout": "[mic, notifications]\n[]\n[mic]"}}
a4 = asg("a4-missing", "fix", "Какие разрешения запросить",
         "Функция должна вернуть список разрешений из `required`, которых **ещё нет** в `granted`, но возвращает как раз выданные. Исправьте её. Например: требуются camera, mic, notifications, выдано camera → [mic, notifications].",
         "Найти недостающие разрешения.", "required: List<String>, granted: Set<String>", "List<String> недостающих.", ["Сигнатуру не менять."],
         hints("Функция возвращает не то, что нужно: проверьте условие внутри filter.", "Сейчас в результат попадают элементы, которые уже есть в granted.",
               "Нужны элементы, которых в granted нет.", "Оператор «не входит» записывается как !in.",
               "required.filter { it !in granted }"),
         t4, S4, "filter оставляет элементы, для которых условие истинно. Нам нужны те, что не входят в granted, поэтому условие — it !in granted (или filterNot { it in granted }).",
         ["Возвращаются только недостающие разрешения."],
         [(BAD4, "Ошибка осталась: возвращаются уже выданные разрешения."),
          ('fun permissionsToRequest(required: List<String>, granted: Set<String>): List<String> {\n    return required\n}\n', "Запрашиваются все разрешения подряд, включая уже выданные."),
          ('fun permissionsToRequest(required: List<String>, granted: Set<String>): List<String> {\n    return granted.toList()\n}\n', "Возвращается granted: нужно отфильтровать required.")],
         starter=BAD4)

# --- a5: predict ---
CODE5 = ('fun main() {\n    val granted = mutableSetOf("camera")\n    val required = listOf("camera", "mic", "notifications")\n    println(required.filter { it !in granted })\n    granted.add("mic")\n'
         '    println(required.filter { it !in granted }.size)\n    println(required.all { it in granted })\n    granted.addAll(required)\n    println(required.all { it in granted })\n}\n')
ans5 = "[mic, notifications]\n1\nfalse\ntrue"
a5 = asg("a5-predict", "predict", "Выданные и недостающие",
         "Что выведет программа? Множество `granted` меняется по ходу работы.",
         "Проследить изменение множества разрешений.", "—", "Четыре строки.", [],
         hints("В начале выдано только camera.", "Первая строка: из трёх требуемых не выдано два — mic и notifications, в порядке списка required.",
               "После add(\"mic\") не хватает только notifications: размер результата 1.", "all проверяет, что условие верно для каждого элемента: notifications всё ещё нет — false.",
               "addAll добавляет все три разрешения: тогда all даст true."),
         {"kind": "answer", "expected_answer": ans5}, ans5,
         "Сначала недостают mic и notifications. После выдачи mic остаётся одно (notifications), и all ещё false. После addAll выданы все три — true.",
         ["Все четыре строки верны."],
         [("[camera]\n1\nfalse\ntrue", "Первая строка — недостающие, а не выданные разрешения."),
          ("[mic, notifications]\n2\nfalse\ntrue", "После выдачи mic недостающее одно: notifications."),
          ("[mic, notifications]\n1\ntrue\ntrue", "notifications ещё не выдано, поэтому all даёт false.")],
         code=CODE5)

skills = {"kt.perm.flow": "Разрешения Android: схема запроса", "kt.perm.version": "Разрешения и версии Android", "kt.notify": "Уведомления: канал и текст"}
write_lesson("kt-10-permissions", "Kotlin: разрешения и уведомления Android",
             "Понимать схему запроса разрешений, учитывать версии Android, создавать канал уведомлений и формулировать текст уведомления.",
             list(skills), ["kt-09-navigation"], scenes, notes, [a1, a2, a3, a4, a5],
             [{"mistake": "Все разрешения при первом запуске", "fix": "Просите разрешение, когда функция понадобилась, и объясняйте зачем."},
              {"mistake": "Нет запасного пути при отказе", "fix": "Приложение должно работать без разрешения: покажите объяснение и продолжайте."},
              {"mistake": "Не учтены версии Android", "fix": "Проверяйте SDK_INT: уведомления требуют разрешения с SDK 33, каналы — с SDK 26."},
              {"mistake": "Неверная форма слова после числа", "fix": "Проверяйте сначала остаток от деления на 100 (11–14), затем на 10."}],
             min_pass=3, pack="kotlin-basics", runner="kotlin")
f = ROOT / "content/packs/kotlin-basics/pack.json"
data = json.loads(f.read_text("utf-8"))
if "kt-10-permissions" not in data["lessons"]:
    data["lessons"].append("kt-10-permissions")
data["skills"].update(skills)
f.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", "utf-8")
