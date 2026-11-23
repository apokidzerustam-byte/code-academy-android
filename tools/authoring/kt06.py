"""Урок Kotlin 6: состояние и события в Compose — remember, подъём состояния, неизменяемое состояние (data class + copy).
Код с androidx проверяется по заглушкам (tools/kotlin-stubs/android); блоки на чистом Kotlin (data class, copy) запускаются настоящим kotlinc."""
from mk import *


def L(code, text, n=1):
    lines = code.split("\n")
    i = next(k for k, ln in enumerate(lines) if text in ln)
    return list(range(i + 1, i + 1 + n))


IMP_C = ("import androidx.compose.foundation.layout.Column\nimport androidx.compose.material3.Button\nimport androidx.compose.material3.Text\n"
         "import androidx.compose.runtime.Composable\n")
IMP_S = ("import androidx.compose.runtime.getValue\nimport androidx.compose.runtime.mutableIntStateOf\nimport androidx.compose.runtime.remember\n"
         "import androidx.compose.runtime.setValue\n")
K1 = IMP_C + IMP_S + ('\n@Composable\nfun Counter() {\n    var count by remember { mutableIntStateOf(0) }\n    Column {\n        Text("Счёт: $count")\n'
                      '        Button(onClick = { count++ }) {\n            Text("+1")\n        }\n    }\n}\n')
K2 = IMP_C + ('\n@Composable\nfun CounterView(count: Int, onIncrement: () -> Unit) {\n    Column {\n        Text("Счёт: $count")\n'
              '        Button(onClick = onIncrement) {\n            Text("+1")\n        }\n    }\n}\n')
K3 = IMP_C + IMP_S + ('\n@Composable\nfun CounterScreen() {\n    var count by remember { mutableIntStateOf(0) }\n    CounterView(count = count, onIncrement = { count++ })\n}\n')
K4 = ('data class TaskUi(val title: String, val done: Boolean)\n\nfun main() {\n    val first = TaskUi("Купить хлеб", false)\n    val second = first.copy(done = true)\n'
      '    println(first)\n    println(second)\n    println(first == second)\n}\n')
O4 = "TaskUi(title=Купить хлеб, done=false)\nTaskUi(title=Купить хлеб, done=true)\nfalse\n"

use_file("Main.kt")
scenes = [
    scene("intro", "Интерфейс как функция от состояния", """
      Начнём с картинки. Представьте табло на вокзале. Диспетчер меняет в таблице время отправления, а табло само показывает новое число. Он не бегает
      и не стирает цифры вручную. Интерфейс в Compose устроен так же. Есть состояние: данные, от которых зависит картинка, например
      счётчик, список задач или введённый текст. А есть функции интерфейса, которые по состоянию рисуют экран. Когда состояние меняется,
      Compose заново вызывает те функции, которые его читают, и экран обновляется. Формула такая: интерфейс равен функции от состояния.
      Всё, что нужно запомнить: данные хранятся в одном понятном месте, а события, например нажатие, их меняют. Сегодня разберём, где хранить
      состояние, как передавать события вверх и как описывать состояние неизменяемым объектом.""",
          [NOTE("**Интерфейс = функция(состояние)**. Меняете состояние — Compose перерисовывает читающие его функции.", at="Формула такая"),
           NOTE("`remember` · подъём состояния · `data class` + `copy()`", at="Сегодня разберём")]),
    scene("remember", "Состояние внутри функции", """
      Начнём с простого счётчика. Состояние создаёт вызов mutableIntStateOf с начальным значением ноль. Но сама функция интерфейса может
      вызываться много раз при перерисовке, и обычная переменная каждый раз обнулялась бы. Чтобы значение пережило перерисовку, его
      оборачивают в remember: он запоминает объект и отдаёт тот же самый при следующем вызове. Слово by позволяет работать с состоянием
      как с обычной переменной: читать count и писать count плюс плюс. Для этого нужны импорты getValue и setValue. Нажатие кнопки
      увеличивает значение, Compose замечает изменение и заново вызывает те части, которые читают count. Остальные не трогаются.""",
          [CLEAR(), T(K1, at="Начнём с простого"), HL(L(K1, "var count"), at="Состояние создаёт"), HL(L(K1, "remember"), at="оборачивают в remember"),
           HL(L(K1, "import androidx.compose.runtime.getValue", 4), at="Для этого нужны импорты"), HL(L(K1, "count++"), at="Нажатие кнопки")]),
    scene("hoist", "Подъём состояния", """
      У такого счётчика есть недостаток: состояние спрятано внутри. Родитель не может узнать, чему равен счёт, а проверить функцию
      в изоляции сложно. Решение называется подъёмом состояния. Мы делаем функцию CounterView без собственного состояния: значение
      приходит параметром count, а о нажатии она сообщает через параметр onIncrement, это функция без аргументов. Сама она ничего не
      меняет и не помнит. Такую функцию называют без состояния, и её очень удобно проверять: передали число, посмотрели, что нарисовано.
      Правило звучит так: состояние течёт вниз, события вверх. Данные идут в функцию через параметры, а действия пользователя поднимаются
      наверх через функции-обратные вызовы. Это похоже на кассу в магазине: касса показывает сумму и принимает деньги, но цены задаёт кто-то другой.""",
          [CLEAR(), T(K2, at="У такого счётчика"), HL(L(K2, "count: Int"), at="приходит параметром"), HL(L(K2, "onIncrement"), at="а о нажатии"),
           HL(L(K2, "Text("), at="Данные идут в функцию")]),
    scene("owner", "Кто владеет состоянием", """
      Кто же тогда хранит число? Родитель. Функция CounterScreen создаёт состояние, а потом вызывает CounterView, передавая ей текущее
      значение и функцию, которая увеличивает счёт. Когда пользователь нажимает кнопку, срабатывает onIncrement, состояние меняется, и
      Compose перерисовывает всё, что зависит от count. Выгода в том, что одну и ту же CounterView можно показать на разных экранах, с
      разным владельцем состояния, и даже без Android: функция видит только число и функцию. Состояние стараются поднимать на тот
      уровень, где оно нужно сразу нескольким функциям, и не выше.""",
          [CLEAR(), T(K3, at="Кто же тогда"), HL(L(K3, "var count"), at="создаёт состояние"), HL(L(K3, "CounterView("), at="вызывает CounterView"),
           HL(L(K3, "count++"), at="увеличивает счёт")]),
    scene("immutable", "Неизменяемое состояние", """
      Когда в состоянии несколько полей, его описывают классом данных. Например, задача: название и отметка о выполнении. Важное правило:
      поля делают неизменяемыми, через val. Чтобы поменять отметку, мы не правим старый объект, а создаём копию методом copy и меняем
      в ней нужное поле. Compose сравнивает старое и новое состояние, и если объекты различаются, перерисовывает экран. Так исключаются
      случайные изменения из разных мест. Запустим пример: исходная задача остаётся невыполненной, а копия получает отметку «готово».
      Сравнение через равенство даёт ложь, потому что поля разные. Заметьте ещё, что строковое представление класса данных печатает все поля: это удобно при отладке, когда нужно быстро увидеть, что лежит в состоянии.""",
          [CLEAR(), T(K4, at="Когда в состоянии"), HL(L(K4, "data class"), at="классом данных"), HL(L(K4, "copy"), at="методом copy"),
           RUN(at="Запустим пример"), OUT(O4, at="Запустим пример")]),
    scene("rotate", "Поворот экрана и ViewModel", """
      Есть тонкость, о которой нельзя промолчать. Когда пользователь поворачивает телефон, Андроид пересоздаёт экран, и значение в обычном
      remember теряется: счётчик снова ноль. Если это неприятно, например теряется введённый текст, берут rememberSaveable: он сохраняет
      значение при повороте. Для данных посерьёзнее, например списка, загруженного из сети, состояние кладут в ViewModel. Это
      отдельный класс, который живёт дольше экрана и переживает поворот. Им мы займёмся в одном из следующих уроков. А пока запомните
      правило: remember переживает перерисовку, rememberSaveable переживает ещё и поворот, ViewModel хранит то, что нельзя терять.""",
          [CLEAR(), NOTE("`remember` — переживает перерисовку", at="remember переживает"), NOTE("`rememberSaveable` — переживает и поворот экрана", at="rememberSaveable переживает"),
           NOTE("`ViewModel` — хранит данные, которые нельзя терять (следующий урок)", at="ViewModel хранит")]),
    scene("mistakes", "Типичные ошибки", """
      Четыре типичные ошибки. Первая: обычная переменная вместо состояния. Экран не обновится, потому что Compose не знает об изменении.
      Вторая: состояние без remember. При каждой перерисовке оно создаётся заново, и счётчик снова ноль. Третья: изменяемые объекты внутри
      состояния. Вы поменяли поле, но ссылка прежняя, и Compose не видит разницы. Создавайте копию через copy. Четвёртая: состояние внутри
      каждой маленькой функции. Тогда значения разъезжаются. Держите его в одном месте и передавайте параметрами.""",
          [NOTE("Ошибка 1: `var count = 0` вместо `remember { mutableIntStateOf(0) }` → экран не обновится.", at="Первая"),
           NOTE("Ошибка 2: `mutableStateOf` без `remember` → при перерисовке значение сбрасывается.", at="Вторая"),
           NOTE("Ошибка 3: меняете поля объекта на месте → используйте `copy()` и неизменяемые поля.", at="Третья"),
           NOTE("Ошибка 4: состояние в каждой функции → поднимите его к родителю.", at="Четвёртая")]),
    scene("summary", "Итог", """
      Подведём итог. Состояние — это данные, от которых зависит экран. Чтобы Compose увидел изменение, его хранят в mutableStateOf, а чтобы оно
      пережило перерисовку, оборачивают в remember. Функции интерфейса лучше делать без состояния: данные приходят параметрами, события уходят
      вверх через функции. Родитель владеет состоянием и передаёт его детям. Сложное состояние описывают классом данных с неизменяемыми
      полями и обновляют через copy. В заданиях вы напишете функцию без состояния с кнопкой, обновите задачу через copy, исправите счётчик
      без remember и предскажете результат. Критерий прохождения: решить не меньше трёх заданий из четырёх. Как и в прошлом уроке, код
      интерфейса проверяется на компьютере по упрощённой модели Compose.""",
          [NOTE("Состояние вниз, события вверх: `CounterView(count, onIncrement)` + владелец с `remember { mutableIntStateOf(0) }`.", at="Подведём итог"),
           NOTE("Сложное состояние: `data class` с `val` и `state.copy(поле = …)`.", at="Сложное состояние")]),
]

notes = """
# Kotlin: состояние и события в Compose

Интерфейс — функция от состояния. Изменили состояние — Compose заново вызывает функции, которые его читают.

```kotlin
@Composable
fun Counter() {
    var count by remember { mutableIntStateOf(0) }   // состояние, переживающее перерисовку
    Column {
        Text("Счёт: $count")
        Button(onClick = { count++ }) { Text("+1") }
    }
}
```

Нужны импорты `getValue`, `setValue`, `remember`, `mutableIntStateOf` из `androidx.compose.runtime`.

## Подъём состояния

```kotlin
@Composable
fun CounterView(count: Int, onIncrement: () -> Unit) {   // без состояния
    Column {
        Text("Счёт: $count")
        Button(onClick = onIncrement) { Text("+1") }
    }
}

@Composable
fun CounterScreen() {                                     // владелец состояния
    var count by remember { mutableIntStateOf(0) }
    CounterView(count = count, onIncrement = { count++ })
}
```

**Состояние течёт вниз, события — вверх.** Функцию без состояния легко повторно использовать и проверять.

## Неизменяемое состояние

```kotlin
data class TaskUi(val title: String, val done: Boolean)
val updated = task.copy(done = true)      // новая копия, старая не меняется
```

- Обычная переменная вместо состояния не обновит экран.
- `mutableStateOf` без `remember` сбрасывается при каждой перерисовке.
- Меняйте объекты копией (`copy`), а не правкой полей на месте.
- **Ограничение проверки:** упрощённая модель Compose в CI не делает перерисовок: проверяется построенное дерево элементов и вызовы `onClick`. Поведение `remember` в проверке не моделируется, его правила закреплены структурными правилами заданий.
"""

PRE = IMP_C + "\n"
# --- a1: CounterView ---
S1 = PRE + '@Composable\nfun CounterView(count: Int, onIncrement: () -> Unit) {\n    Column {\n        Text("Счёт: $count")\n        Button(onClick = onIncrement) {\n            Text("+1")\n        }\n    }\n}\n'
t1 = {"kind": "kotlin", "cases": [
    {"id": "syntax", "type": "syntax"},
    {"id": "fn", "type": "function", "name": "CounterView", "paramTypes": ["Int", "() -> Unit"], "returns": "Unit"},
    {"id": "ann", "type": "contains", "pattern": "@Composable\\s+fun\\s+CounterView\\b", "message": "Нужна аннотация @Composable"},
    {"id": "btn", "type": "contains", "pattern": "\\bButton\\s*\\(\\s*onClick\\s*=\\s*onIncrement\\b(?!\\s*\\()", "message": "Передайте onIncrement кнопке: Button(onClick = onIncrement)",
     "hint": "Функцию-событие не вызывают, а передают дальше"},
    {"id": "nostate", "hidden": True, "type": "not_contains", "pattern": "\\bremember\\b|\\bmutableStateOf\\b|\\bmutableIntStateOf\\b", "message": "Функция без состояния: значение приходит параметром, remember здесь не нужен"},
    {"id": "txt", "hidden": True, "type": "contains", "raw": True, "pattern": "Счёт:\\s*\\$(count|\\{\\s*count\\s*\\})", "message": "Покажите «Счёт: <count>» через шаблон строки"},
], "jvm": {"main": "fun main() {\n    var clicks = 0\n    println(stubs.ComposeLog.render { CounterView(3) { clicks++ } })\n    stubs.ComposeLog.click(0)\n    stubs.ComposeLog.click(0)\n    println(\"Нажатий: $clicks\")\n}",
           "expected_stdout": "Column\n  Text(Счёт: 3)\n  Button\n    Text(+1)\nНажатий: 2"}}
a1 = asg("a1-counter-view", "write", "Счётчик без состояния",
         "Напишите функцию интерфейса `CounterView(count: Int, onIncrement: () -> Unit)`: в `Column` элемент `Text` со строкой `Счёт: <count>` и кнопка `Button`, "
         "в которой лежит `Text(\"+1\")`. Кнопка должна вызывать `onIncrement` при нажатии. Собственного состояния у функции быть не должно.",
         "Написать функцию без состояния: данные вниз, события вверх.", "count = 3", "Column → Text(«Счёт: 3»), Button → Text(«+1»); два нажатия вызывают onIncrement дважды.",
         ["Импорты уже в шаблоне."],
         hints("Состояние здесь не хранится: count приходит параметром.", "Кнопка принимает onClick — функцию, которую вызовут при нажатии.",
               "У вас уже есть такая функция: параметр onIncrement.", "Передайте её кнопке как есть, не вызывая: onClick = onIncrement.",
               "Column { Text(\"Счёт: $count\"); Button(onClick = onIncrement) { Text(\"+1\") } } — каждый вызов с новой строки."),
         t1, S1, "Функция только показывает переданный count и отдаёт нажатие наверх через onIncrement. Состояния внутри нет.",
         ["@Composable fun CounterView(count, onIncrement).", "Button(onClick = onIncrement).", "Без remember."],
         [(PRE + '@Composable\nfun CounterView(count: Int, onIncrement: () -> Unit) {\n    Column {\n        Text("Счёт: $count")\n        Button(onClick = { }) {\n            Text("+1")\n        }\n    }\n}\n', "Кнопка ничего не делает: onIncrement не подключён."),
          (PRE + '@Composable\nfun CounterView(count: Int, onIncrement: () -> Unit) {\n    Column {\n        Text("Счёт: $count")\n        Button(onClick = onIncrement()) {\n            Text("+1")\n        }\n    }\n}\n', "onIncrement() вызывает функцию сразу, а кнопке нужно передать саму функцию."),
          (PRE + '@Composable\nfun CounterView(count: Int, onIncrement: () -> Unit) {\n    Column {\n        Button(onClick = onIncrement) {\n            Text("+1")\n        }\n    }\n}\n', "Нет Text со счётом.")],
         starter=PRE + "// Напишите функцию CounterView\n")

# --- a2: toggle via copy ---
PRE2 = "data class TaskUi(val title: String, val done: Boolean)\n\n"
S2 = PRE2 + "fun toggle(task: TaskUi): TaskUi = task.copy(done = !task.done)\n"
t2 = {"kind": "kotlin", "cases": [
    {"id": "syntax", "type": "syntax"},
    {"id": "fn", "type": "function", "name": "toggle", "paramTypes": ["TaskUi"], "returns": "TaskUi"},
    {"id": "copy", "type": "contains", "pattern": "\\.copy\\s*\\(", "message": "Создайте новую задачу методом copy: task.copy(…)", "hint": "Неизменяемое состояние обновляют копией"},
    {"id": "not", "hidden": True, "type": "contains", "pattern": "!\\s*task\\.done", "message": "Отметка должна поменяться на противоположную: !task.done"},
], "jvm": {"main": "fun main() {\n    val a = TaskUi(\"хлеб\", false)\n    val b = toggle(a)\n    println(\"$a $b ${toggle(b)}\")\n}",
           "expected_stdout": "TaskUi(title=хлеб, done=false) TaskUi(title=хлеб, done=true) TaskUi(title=хлеб, done=false)"}}
a2 = asg("a2-toggle", "write", "Переключить задачу",
         "Класс `TaskUi(title, done)` неизменяемый. Напишите функцию `toggle(task: TaskUi): TaskUi`, которая возвращает **новую** задачу с тем же названием и **противоположной** отметкой `done`. "
         "Исходный объект менять нельзя.",
         "Обновлять неизменяемое состояние через copy.", "TaskUi(\"хлеб\", false)", "TaskUi(title=хлеб, done=true).",
         ["Поля data class объявлены как val: присвоить новое значение нельзя."],
         hints("Поля заданы через val, их не изменить.", "Для data class есть метод copy: он делает новый объект.", "В copy указывают только то поле, которое меняется.",
               "Противоположное значение Boolean получают оператором !.", "fun toggle(task: TaskUi): TaskUi = task.copy(done = !task.done)."),
         t2, S2, "copy создаёт новый объект с теми же полями, кроме done. Исходная задача не меняется, и Compose увидит разницу между старым и новым состоянием.",
         ["Возвращается новая задача.", "done инвертировано."],
         [(PRE2 + "fun toggle(task: TaskUi): TaskUi = task.copy(done = true)\n", "done всегда true: отметка должна меняться на противоположную."),
          (PRE2 + "fun toggle(task: TaskUi): TaskUi = task\n", "Задача не изменилась: нужна копия с инвертированной отметкой."),
          (PRE2 + "fun toggle(task: TaskUi): TaskUi = TaskUi(\"хлеб\", !task.done)\n", "Название зашито в код вместо task.title.")],
         starter=PRE2 + "// Напишите функцию toggle\n")

# --- a3: fix remember ---
BAD3 = IMP_C + "\n" + '@Composable\nfun Counter() {\n    var count = 0\n    Column {\n        Text("Счёт: $count")\n        Button(onClick = { count++ }) {\n            Text("+1")\n        }\n    }\n}\n'
S3 = IMP_C + IMP_S + '\n@Composable\nfun Counter() {\n    var count by remember { mutableIntStateOf(0) }\n    Column {\n        Text("Счёт: $count")\n        Button(onClick = { count++ }) {\n            Text("+1")\n        }\n    }\n}\n'
t3 = {"kind": "kotlin", "cases": [
    {"id": "syntax", "type": "syntax"},
    {"id": "fn", "type": "function", "name": "Counter", "paramTypes": [], "returns": "Unit"},
    {"id": "rem", "type": "contains", "pattern": "\\bremember\\s*\\{\\s*(mutableIntStateOf|mutableStateOf)\\s*\\(\\s*0\\s*\\)\\s*\\}", "message": "Храните счётчик в состоянии: remember { mutableIntStateOf(0) }",
     "hint": "Обычная переменная не заставит Compose перерисовать экран"},
    {"id": "by", "hidden": True, "type": "contains", "pattern": "\\bvar\\s+count\\s+by\\b", "message": "Объявите var count by remember { … }, чтобы работать со значением как с обычной переменной"},
    {"id": "imp1", "hidden": True, "type": "contains", "pattern": "import\\s+androidx\\.compose\\.runtime\\.getValue\\b", "message": "Для by нужен импорт androidx.compose.runtime.getValue"},
    {"id": "imp2", "hidden": True, "type": "contains", "pattern": "import\\s+androidx\\.compose\\.runtime\\.setValue\\b", "message": "Для by нужен импорт androidx.compose.runtime.setValue"},
], "jvm": {"main": "fun main() {\n    println(stubs.ComposeLog.render { Counter() })\n}", "expected_stdout": "Column\n  Text(Счёт: 0)\n  Button\n    Text(+1)"}}
a3 = asg("a3-remember", "fix", "Счётчик не обновляется",
         "Счётчик не обновляет экран: `count` — обычная переменная, Compose о её изменении не узнаёт. Исправьте функцию `Counter`: храните счёт в состоянии "
         "`var count by remember { mutableIntStateOf(0) }` и добавьте нужные импорты (`mutableIntStateOf`, `remember`, `getValue`, `setValue` из `androidx.compose.runtime`).",
         "Хранить меняющееся значение в состоянии.", "—", "Первый показ: «Счёт: 0».",
         ["Остальной код функции менять не нужно."],
         hints("Compose перерисовывает экран, только когда меняется состояние.", "Обычная переменная — не состояние.",
               "Состояние создаёт mutableIntStateOf, а чтобы оно пережило перерисовку, его оборачивают в remember.",
               "Слово by позволяет читать и менять состояние как обычную переменную, но требует импортов getValue и setValue.",
               "var count by remember { mutableIntStateOf(0) } — и четыре импорта из androidx.compose.runtime."),
         t3, S3, "remember сохраняет состояние между перерисовками, mutableIntStateOf делает его наблюдаемым, а by с импортами getValue и setValue даёт синтаксис обычной переменной.",
         ["Состояние в remember.", "Импорты для by.", "Остальной код сохранён."],
         [(BAD3, "Ошибка осталась: обычная переменная вместо состояния."),
          (IMP_C + IMP_S + '\n@Composable\nfun Counter() {\n    var count by mutableIntStateOf(0)\n    Column {\n        Text("Счёт: $count")\n        Button(onClick = { count++ }) {\n            Text("+1")\n        }\n    }\n}\n', "Состояние без remember: при перерисовке оно сбросится в ноль."),
          (IMP_C + "import androidx.compose.runtime.mutableIntStateOf\nimport androidx.compose.runtime.remember\n\n" + '@Composable\nfun Counter() {\n    var count by remember { mutableIntStateOf(0) }\n    Column {\n        Text("Счёт: $count")\n        Button(onClick = { count++ }) {\n            Text("+1")\n        }\n    }\n}\n', "Нет импортов getValue и setValue: by не скомпилируется.")],
         starter=BAD3)

# --- a4: predict ---
CODE4 = ('fun counterLabel(count: Int, onIncrement: () -> Unit): String {\n    onIncrement()\n    return "Счёт: $count"\n}\n\nfun main() {\n    var count = 0\n'
         '    val first = counterLabel(count) { count += 1 }\n    val second = counterLabel(count) { count += 1 }\n    println(first)\n    println(second)\n    println(count)\n}\n')
ans4 = "Счёт: 0\nСчёт: 1\n2"
a4 = asg("a4-predict", "predict", "Значение вниз, событие вверх",
         "Функция получает значение и функцию-событие, как `CounterView`. Что выведет программа? Каждая строка — с новой строки.",
         "Понять, что параметр хранит значение на момент вызова.", "—", "Три строки.", [],
         hints("Параметр count — копия числа на момент вызова.", "onIncrement меняет переменную в main, а не параметр функции.", "В первый вызов передаётся 0, внутри count в main становится 1.",
               "Во второй вызов уже передаётся 1: после него count в main равен 2.", "Строки возвращают значение параметра, а третья печатает итоговое значение переменной main."),
         {"kind": "answer", "expected_answer": ans4}, ans4,
         "Первый вызов получает 0 и возвращает «Счёт: 0», а событие поднимает count в main до 1. Второй получает 1 и возвращает «Счёт: 1»; после него count равен 2. Параметр хранит значение на момент вызова.",
         ["Все три строки верны."],
         [("Счёт: 1\nСчёт: 2\n2", "Параметр — это значение на момент вызова: первый вызов получил 0."),
          ("Счёт: 0\nСчёт: 0\n2", "Второй вызов получает уже обновлённый count = 1."),
          ("Счёт: 0\nСчёт: 1\n1", "Событие вызывается дважды: итоговое значение 2.")],
         code=CODE4)

skills = {"kt.state": "Состояние и remember", "kt.hoisting": "Подъём состояния", "kt.immutable": "Неизменяемое состояние (copy)"}
write_lesson("kt-06-state", "Kotlin: состояние и события в Compose",
             "Хранить состояние через remember, поднимать его к родителю и обновлять неизменяемые данные через copy.",
             list(skills), ["kt-05-compose-basics"], scenes, notes, [a1, a2, a3, a4],
             [{"mistake": "Обычная переменная вместо состояния", "fix": "Используйте var x by remember { mutableStateOf(…) }."},
              {"mistake": "Состояние без remember", "fix": "Оберните его в remember, иначе оно сбрасывается при перерисовке."},
              {"mistake": "Изменение полей объекта на месте", "fix": "Делайте поля val и обновляйте объект через copy."},
              {"mistake": "onClick = onIncrement()", "fix": "Передайте функцию, а не её результат: onClick = onIncrement."}],
             min_pass=3, pack="kotlin-basics", runner="kotlin")
f = ROOT / "content/packs/kotlin-basics/pack.json"
data = json.loads(f.read_text("utf-8"))
if "kt-06-state" not in data["lessons"]:
    data["lessons"].append("kt-06-state")
data["skills"].update(skills)
f.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", "utf-8")
