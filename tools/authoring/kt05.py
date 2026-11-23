"""Урок Kotlin 5: основы Jetpack Compose — @Composable, Column/Row, Button, LazyColumn.
Код компилируется в CI вместе с упрощёнными заглушками Compose (tools/kotlin-stubs/android): они строят текстовое «дерево интерфейса»
(stubs.ComposeLog) — по нему проверяется, что именно нарисует функция. Настоящий Compose в проверке не участвует."""
from mk import *


def L(code, text, n=1):
    lines = code.split("\n")
    i = next(k for k, ln in enumerate(lines) if text in ln)
    return list(range(i + 1, i + 1 + n))


IMP_TEXT = "import androidx.compose.material3.Text\nimport androidx.compose.runtime.Composable\n\n"
K1 = IMP_TEXT + '@Composable\nfun Greeting(name: String) {\n    Text("Привет, $name!")\n}\n'
IMP_COL = ("import androidx.compose.foundation.layout.Column\nimport androidx.compose.foundation.layout.Row\nimport androidx.compose.foundation.layout.padding\n"
           "import androidx.compose.material3.Text\nimport androidx.compose.runtime.Composable\nimport androidx.compose.ui.Modifier\nimport androidx.compose.ui.unit.dp\n\n")
K2 = IMP_COL + ('@Composable\nfun ProfileCard(name: String, role: String) {\n    Column(modifier = Modifier.padding(16.dp)) {\n        Text(name)\n'
                '        Row {\n            Text("Роль: ")\n            Text(role)\n        }\n    }\n}\n')
IMP_BTN = ("import androidx.compose.foundation.layout.Column\nimport androidx.compose.material3.Button\nimport androidx.compose.material3.Text\n"
           "import androidx.compose.runtime.Composable\nimport androidx.compose.runtime.mutableIntStateOf\nimport androidx.compose.runtime.remember\n"
           "import androidx.compose.runtime.getValue\nimport androidx.compose.runtime.setValue\n\n")
K3 = IMP_BTN + ('@Composable\nfun Counter() {\n    var count by remember { mutableIntStateOf(0) }\n    Column {\n        Text("Нажато: $count")\n'
                '        Button(onClick = { count++ }) {\n            Text("Ещё")\n        }\n    }\n}\n')
IMP_LAZY = ("import androidx.compose.foundation.lazy.LazyColumn\nimport androidx.compose.foundation.lazy.items\nimport androidx.compose.material3.Text\n"
            "import androidx.compose.runtime.Composable\n\n")
K4 = IMP_LAZY + '@Composable\nfun ShoppingList(products: List<String>) {\n    LazyColumn {\n        items(products) { product ->\n            Text(product)\n        }\n    }\n}\n'

K5 = ('// Greeting, ProfileCard и ShoppingList — функции из предыдущих примеров\n@Composable\nfun HomeScreen() {\n    Column {\n        Greeting("Аня")\n'
      '        ProfileCard("Аня", "Android-разработчик")\n        ShoppingList(listOf("Хлеб", "Сыр"))\n    }\n}\n')

use_file("Main.kt")
scenes = [
    scene("intro", "Как рисуется интерфейс в Compose", """
      Раньше экраны Андроида описывали в отдельных файлах разметки, а потом в коде искали нужные элементы по номеру и меняли им
      текст. Jetpack Compose устроен иначе: интерфейс описывается обычными функциями Kotlin. Вы пишете, что должно быть на экране
      при таких-то данных, а система сама перерисовывает его, когда данные меняются. Такой подход называется декларативным. Функция,
      которая рисует кусок экрана, помечается аннотацией Composable. Её имя пишут с большой буквы, как имя класса, потому что она
      изображает объект. Представьте конструктор: из маленьких одинаковых деталей вы строите всё, что угодно. Здесь то же самое: из маленьких функций собирают большие: кнопка, карточка, экран. Сегодня мы напишем первую такую функцию,
      соберём из элементов колонку и строку, добавим кнопку и прокручиваемый список.""",
          [NOTE("**Декларативный интерфейс**: вы описываете, *что* показать для данных, а не *как* менять элементы.", at="Такой подход"),
           NOTE("`@Composable` · `Column` / `Row` · `Modifier` · `Button` · `LazyColumn`", at="Сегодня мы напишем")]),
    scene("composable", "Первая функция Composable", """
      Вот самая простая функция интерфейса. Над ней стоит аннотация Composable. Это метка для компилятора: внутри можно вызывать
      другие функции интерфейса. У функции есть параметр name, то есть данные, от которых зависит картинка. Внутри один вызов Text:
      это готовый элемент, который показывает строку. Мы подставляем в строку имя через шаблон. Обратите внимание: функция ничего не
      возвращает. Она не создаёт объект, а вызывает другие функции интерфейса, и всё, что они нарисуют, становится частью экрана.
      Импортировать нужно и аннотацию, и Text, иначе компилятор не найдёт их. Правила: имя с большой буквы, данные только через
      параметры, никаких долгих вычислений внутри.""",
          [CLEAR(), T(K1, at="Вот самая простая"), HL(L(K1, "@Composable"), at="аннотация Composable"), HL(L(K1, "name: String"), at="параметр name"),
           HL(L(K1, "Text("), at="один вызов Text"), HL(L(K1, "import androidx.compose.runtime.Composable"), at="Импортировать нужно")]),
    scene("layout", "Колонка и строка", """
      Один Text — это ещё не экран. Чтобы разместить элементы, используют контейнеры. Column выкладывает содержимое сверху вниз, Row
      слева направо. Контейнер принимает лямбду, внутри которой вы перечисляете детей. В нашей карточке профиля колонка содержит имя,
      а под ним строку, в которой стоят подпись и должность. Ещё у контейнера есть параметр modifier. Модификатор настраивает
      внешний вид и поведение: например, отступ padding в шестнадцать dp. Здесь dp — это независимая от плотности экрана единица, по ней
      размеры одинаковы на разных телефонах. Модификаторы можно цеплять цепочкой через точку, и порядок важен: отступ, поставленный до
      фона, и отступ после фона дают разную картинку.""",
          [CLEAR(), T(K2, at="Один Text"), HL(L(K2, "Column"), at="Column выкладывает"), HL(L(K2, "Row {"), at="Row"),
           HL(L(K2, "Modifier.padding"), at="параметр modifier"), HL(L(K2, "Text(role)"), at="должность")]),
    scene("state", "Кнопка и состояние", """
      Теперь сделаем экран живым. Кнопка Button принимает onClick: функцию, которую вызовут при нажатии. Внутри кнопки лежит её
      содержимое, обычно Text. Но если просто увеличить обычную переменную, ничего не произойдёт: Compose не узнает, что надо
      перерисовать экран. Поэтому счётчик хранят в состоянии. Вызов mutableIntStateOf создаёт состояние, remember запоминает его между
      перерисовками, а слово by позволяет читать и менять его как обычную переменную. Когда значение меняется, Compose запускает
      перерисовку только тех функций, которые это значение читают. Для этого нужны два импорта: getValue и setValue. Без них
      конструкция by не скомпилируется. Это самая частая ошибка новичка.""",
          [CLEAR(), T(K3, at="Теперь сделаем"), HL(L(K3, "Button("), at="Кнопка Button"), HL(L(K3, "var count"), at="Поэтому счётчик хранят"),
           HL(L(K3, "count++"), at="Когда значение меняется"), HL(L(K3, "import androidx.compose.runtime.getValue", 2), at="Для этого нужны")]),
    scene("lazy", "Длинные списки: LazyColumn", """
      А если элементов сотня? Колонка создаст их все сразу, даже те, что за краем экрана. Для списков есть LazyColumn: он прокручивается
      и создаёт только видимые строки. Внутри него элементы описывают не вызовом Text подряд, а функцией items: ей передают список и
      лямбду, которая рисует одну строку по одному элементу. Здесь каждый продукт превращается в Text. Важная тонкость: лямбда содержимого
      LazyColumn не является функцией интерфейса, поэтому Text напрямую в ней вызвать нельзя, а в лямбде items можно. Если попробуете
      вставить цикл for прямо в LazyColumn, компилятор покажет ошибку.""",
          [CLEAR(), T(K4, at="А если элементов"), HL(L(K4, "LazyColumn {"), at="Для списков есть"), HL(L(K4, "items(products)"), at="функцией items"),
           HL(L(K4, "Text(product)"), at="каждый продукт превращается")]),
    scene("screen", "Из маленьких функций — целый экран", """
      Главная сила Compose в том, что функции интерфейса вызывают друг друга, как обычные функции. Посмотрите на экран HomeScreen. Он
      состоит из трёх готовых кусочков: приветствия, карточки профиля и списка покупок. Каждый кусочек написан и проверен отдельно, а
      экран лишь собирает их в колонку. Это как конструктор: из одинаковых деталей получаются разные модели. Если завтра карточка понадобится
      на другом экране, вы просто вызовете её ещё раз с другими данными. Отдельно скажу про аннотацию Preview. Она позволяет
      посмотреть функцию в Android Studio, не запуская приложение на телефоне. Функция для просмотра не принимает параметров, поэтому
      для неё пишут маленькую обёртку с готовыми данными.""",
          [CLEAR(), T(K5, at="Главная сила"), HL(L(K5, "Greeting("), at="приветствия"), HL(L(K5, "ProfileCard("), at="карточки профиля"),
           HL(L(K5, "ShoppingList("), at="списка покупок")]),
    scene("mistakes", "Типичные ошибки", """
      Разберём четыре типичные ошибки. Первая: забыли аннотацию Composable. Тогда другой код интерфейса не сможет вызвать вашу функцию,
      а внутри неё нельзя вызывать Text. Вторая: обычная переменная вместо состояния. Экран не обновится, потому что Compose не знает об
      изменении. Третья: цикл for прямо внутри LazyColumn. Используйте items. Четвёртая: забыли импорт getValue и setValue при
      использовании by: код с состоянием не соберётся. Сообщения компилятора на английском, но по ключевым словам их легко узнать:
      Composable invocations, Property delegate must have, и так далее.""",
          [NOTE("Ошибка 1: нет `@Composable` → нельзя вызывать `Text` и другие функции интерфейса.", at="Первая"),
           NOTE("Ошибка 2: `var count = 0` вместо `remember { mutableIntStateOf(0) }` → экран не обновится.", at="Вторая"),
           NOTE("Ошибка 3: `for` внутри `LazyColumn` → используйте `items(список) { … }`.", at="Третья"),
           NOTE("Ошибка 4: нет импортов `getValue` / `setValue` → `by` не компилируется.", at="Четвёртая")]),
    scene("summary", "Итог", """
      Подведём итог. Интерфейс в Compose описывают функциями с аннотацией Composable, имя пишут с большой буквы. Элементы собирают в
      Column и Row, внешний вид настраивают через modifier. Кнопке передают onClick, а то, что должно менять картинку, хранят в состоянии
      через remember и mutableStateOf. Длинные списки рисуют LazyColumn с функцией items. Помните: в нашем курсе код интерфейса проверяется
      на компьютере по упрощённой модели, а на телефоне вы его не запустите, потому что для этого нужен полноценный проект. В заданиях вы
      напишете функцию приветствия, соберёте карточку, исправите список с циклом и предскажете результат нажатий. Критерий прохождения:
      решить не меньше трёх заданий из четырёх.""",
          [NOTE("`@Composable` · `Column { }` · `Row { }` · `Modifier.padding(16.dp)` · `Button(onClick = …) { }` · `LazyColumn { items(…) { … } }`", at="Подведём итог"),
           NOTE("Состояние: `var x by remember { mutableIntStateOf(0) }` + импорты `getValue`/`setValue`.", at="Кнопке передают")]),
]

notes = """
# Kotlin: основы Jetpack Compose

Интерфейс в Compose — обычные функции Kotlin с аннотацией `@Composable`. Вы описываете, что показать для данных; система перерисует экран при изменении данных.

```kotlin
@Composable
fun Greeting(name: String) {
    Text("Привет, $name!")
}

@Composable
fun ProfileCard(name: String, role: String) {
    Column(modifier = Modifier.padding(16.dp)) {
        Text(name)
        Row {
            Text("Роль: ")
            Text(role)
        }
    }
}
```

| Элемент | Назначение |
|---|---|
| `@Composable` | функция описывает кусок интерфейса; имя с большой буквы |
| `Text(строка)` | показывает текст |
| `Column { … }` / `Row { … }` | дети сверху вниз / слева направо |
| `Modifier.padding(16.dp)` | отступ; `dp` — единица, не зависящая от плотности экрана |
| `Button(onClick = { … }) { Text("…") }` | кнопка с содержимым |
| `LazyColumn { items(список) { … } }` | прокручиваемый список; рисует только видимое |

Состояние, которое меняет картинку:

```kotlin
import androidx.compose.runtime.getValue
import androidx.compose.runtime.setValue

var count by remember { mutableIntStateOf(0) }
Button(onClick = { count++ }) { Text("Ещё") }
```

- Обычная переменная вместо `remember { mutableStateOf(…) }` не обновит экран.
- Внутри `LazyColumn` нельзя вызывать `Text` напрямую и писать `for`: используйте `items(список) { элемент -> … }`.
- Для `by` нужны импорты `getValue` и `setValue`.
- **Ограничение проверки:** задания проверяются на компьютере по упрощённым заглушкам Compose (они строят текстовое дерево элементов и не знают про перерисовку). Правила настоящего компилятора Compose (например, «`Text` вне `@Composable`») проверяются структурными правилами. На телефоне в приложении этот код не запускается.
"""

# --- a1: Greeting ---
S1 = IMP_TEXT + '@Composable\nfun Greeting(name: String) {\n    Text("Привет, $name!")\n}\n'
t1 = {"kind": "kotlin", "cases": [
    {"id": "syntax", "type": "syntax"},
    {"id": "fn", "type": "function", "name": "Greeting", "paramTypes": ["String"], "returns": "Unit"},
    {"id": "ann", "type": "contains", "pattern": "@Composable\\s+fun\\s+Greeting\\b", "message": "Над функцией нужна аннотация @Composable", "hint": "Аннотацию пишут прямо перед fun"},
    {"id": "text", "type": "contains", "pattern": "\\bText\\s*\\(", "message": "Покажите приветствие элементом Text(…)"},
    {"id": "tpl", "hidden": True, "type": "contains", "raw": True, "pattern": "Привет,\\s*\\$(name|\\{\\s*name\\s*\\})\\s*!", "message": "Строка должна быть «Привет, имя!» с подстановкой параметра name"},
], "jvm": {"main": "fun main() {\n    println(stubs.ComposeLog.render { Greeting(\"Аня\") })\n}", "expected_stdout": "Text(Привет, Аня!)"}}
a1 = asg("a1-greeting", "write", "Приветствие",
         "Напишите функцию интерфейса `Greeting(name: String)`, которая показывает один элемент `Text` со строкой `Привет, <имя>!` (имя берётся из параметра). "
         "Импорты уже в шаблоне.",
         "Объявить @Composable-функцию с параметром.", "name = «Аня»", "Один элемент Text: «Привет, Аня!».",
         ["Функция ничего не возвращает: она вызывает Text."],
         hints("Заголовок: fun Greeting(name: String), а перед ним нужна аннотация, отмечающая функции интерфейса.", "Эта аннотация — слово Composable с символом @ в начале; её пишут отдельной строкой над fun.", "Внутри вызовите Text(…): это элемент, показывающий строку.",
               "Имя подставьте шаблоном строки: $name.", "Тело: Text(\"Привет, $name!\")."),
         t1, S1, "Функция помечена @Composable, получает name и вызывает Text со строкой-шаблоном. Возвращать ничего не нужно: Text сам становится частью экрана.",
         ["@Composable fun Greeting(name: String).", "Text с шаблоном «Привет, $name!»."],
         [(IMP_TEXT + 'fun Greeting(name: String) {\n    Text("Привет, $name!")\n}\n', "Нет @Composable: в настоящем Compose Text нельзя вызвать вне такой функции."),
          (IMP_TEXT + '@Composable\nfun Greeting(name: String) {\n    Text("Привет, name!")\n}\n', "Имя не подставлено: нужен шаблон $name."),
          (IMP_TEXT + '@Composable\nfun Greeting(name: String): String {\n    return "Привет, $name!"\n}\n', "Функция должна показывать Text, а не возвращать строку.")],
         starter=IMP_TEXT + "// Напишите функцию Greeting\n")

# --- a2: ProfileCard (complete) ---
S2 = IMP_COL + '@Composable\nfun ProfileCard(name: String, role: String) {\n    Column(modifier = Modifier.padding(16.dp)) {\n        Text(name)\n        Row {\n            Text("Роль: ")\n            Text(role)\n        }\n    }\n}\n'
ST2 = IMP_COL + '@Composable\nfun ProfileCard(name: String, role: String) {\n    // Допишите: колонка с именем, под ним строка из подписи «Роль: » и должности\n}\n'
t2 = {"kind": "kotlin", "cases": [
    {"id": "syntax", "type": "syntax"},
    {"id": "fn", "type": "function", "name": "ProfileCard", "paramTypes": ["String", "String"], "returns": "Unit"},
    {"id": "col", "type": "contains", "pattern": "\\bColumn\\s*[({]", "message": "Верхний контейнер — Column"},
    {"id": "row", "type": "contains", "pattern": "\\bRow\\s*[({]", "message": "Подпись и должность поместите в Row"},
    {"id": "texts", "type": "contains", "pattern": "\\bText\\s*\\([\\s\\S]*\\bText\\s*\\([\\s\\S]*\\bText\\s*\\(", "message": "Нужно три элемента Text: имя, подпись и должность"},
    {"id": "order", "type": "contains", "pattern": "\\bColumn\\s*[({][\\s\\S]*\\bText\\s*\\(\\s*name\\s*\\)[\\s\\S]*\\bRow\\s*[({]", "message": "Имя должно стоять в Column выше строки Row с подписью и должностью"},
], "jvm": {"main": "fun main() {\n    println(stubs.ComposeLog.render { ProfileCard(\"Аня\", \"Android-разработчик\") })\n}",
           "expected_stdout": "Column\n  Text(Аня)\n  Row\n    Text(Роль: )\n    Text(Android-разработчик)"}}
a2 = asg("a2-profile", "complete", "Карточка профиля",
         "Допишите тело функции `ProfileCard(name, role)`: колонка `Column`, в которой сверху `Text` с именем, а под ним `Row` из двух `Text`: подписи `Роль: ` и должности `role`.",
         "Собрать экран из Column и Row.", "name = «Аня», role = «Android-разработчик»", "Дерево: Column → Text(имя), Row → Text(«Роль: »), Text(должность).",
         ["Порядок детей важен: имя, затем строка."],
         hints("Контейнеры принимают лямбду: Column { … }.", "Внутри Column сначала Text(name).", "Следом — Row { … }: дети будут стоять в одну строку.",
               "В Row два Text: подпись и должность.", "Column { Text(name); Row { Text(\"Роль: \"); Text(role) } } — каждый вызов с новой строки. Отступ по желанию: Column(modifier = Modifier.padding(16.dp))."),
         t2, S2, "Column выкладывает детей сверху вниз: имя, затем Row. Row ставит подпись и должность рядом.",
         ["Column с именем.", "Внутри Row с подписью и должностью."],
         [(IMP_COL + '@Composable\nfun ProfileCard(name: String, role: String) {\n    Column {\n        Text(name)\n        Text("Роль: ")\n        Text(role)\n    }\n}\n', "Нет Row: подпись и должность должны стоять в одной строке."),
          (IMP_COL + '@Composable\nfun ProfileCard(name: String, role: String) {\n    Row {\n        Text(name)\n        Column {\n            Text("Роль: ")\n            Text(role)\n        }\n    }\n}\n', "Контейнеры перепутаны: верхний должен быть Column."),
          (IMP_COL + '@Composable\nfun ProfileCard(name: String, role: String) {\n    Column {\n        Row {\n            Text("Роль: ")\n            Text(role)\n        }\n        Text(name)\n    }\n}\n', "Порядок неверный: имя должно быть сверху.")],
         starter=ST2)

# --- a3: fix — for в LazyColumn ---
BAD3 = IMP_LAZY + '@Composable\nfun ShoppingList(products: List<String>) {\n    LazyColumn {\n        for (product in products) {\n            Text(product)\n        }\n    }\n}\n'
S3 = IMP_LAZY + '@Composable\nfun ShoppingList(products: List<String>) {\n    LazyColumn {\n        items(products) { product ->\n            Text(product)\n        }\n    }\n}\n'
t3 = {"kind": "kotlin", "cases": [
    {"id": "syntax", "type": "syntax"},
    {"id": "fn", "type": "function", "name": "ShoppingList", "paramTypes": ["List<String>"], "returns": "Unit"},
    {"id": "items", "type": "contains", "pattern": "\\bitems\\s*\\(\\s*products\\s*\\)", "message": "Строки списка рисуйте функцией items(products) { … }",
     "hint": "Компилятор: «@Composable invocations can only happen from the context of a @Composable function»"},
    {"id": "nofor", "type": "not_contains", "pattern": "\\bfor\\s*\\(", "message": "Цикл for внутри LazyColumn использовать нельзя: Text там вызвать нельзя"},
    {"id": "text", "hidden": True, "type": "contains", "pattern": "\\bText\\s*\\(", "message": "Каждая строка списка — Text"},
], "jvm": {"main": "fun main() {\n    println(stubs.ComposeLog.render { ShoppingList(listOf(\"Хлеб\", \"Сыр\")) })\n}",
           "expected_stdout": "LazyColumn\n  Text(Хлеб)\n  Text(Сыр)"}}
a3 = asg("a3-lazy", "fix", "Список покупок",
         "Код не соберётся в настоящем Compose: внутри `LazyColumn` стоит цикл `for`, а вызывать `Text` в его лямбде нельзя. Исправьте функцию `ShoppingList(products)`, "
         "чтобы каждая покупка рисовалась через `items(products) { … }`.",
         "Рисовать списки через items.", "products = [Хлеб, Сыр]", "LazyColumn с двумя Text.",
         ["Импорт items уже есть."],
         hints("Лямбда LazyColumn не является функцией интерфейса, поэтому Text вызывать там нельзя.", "Для каждой строки списка у LazyColumn есть функция items.",
               "Ей передают список и лямбду для одного элемента.", "Цикл for нужно заменить вызовом items.",
               "items(products) { product -> Text(product) }."),
         t3, S3, "Лямбда items — это функция интерфейса, в ней можно вызывать Text. LazyColumn создаст только видимые строки.",
         ["Вместо for используется items.", "Строка рисуется элементом Text."],
         [(BAD3, "Ошибка осталась: цикл for внутри LazyColumn."),
          (IMP_LAZY + '@Composable\nfun ShoppingList(products: List<String>) {\n    LazyColumn {\n        items(products) { product ->\n            product\n        }\n    }\n}\n', "Элемент не показан: нужен вызов Text(product)."),
          (IMP_LAZY + '@Composable\nfun ShoppingList(products: List<String>) {\n    LazyColumn {\n        Text("Хлеб")\n    }\n}\n', "Список зашит в код вместо параметра products.")],
         starter=BAD3)

# --- a4: predict (обычный Kotlin: событие → состояние → текст) ---
CODE4 = ('fun main() {\n    var count = 0\n    val onClick = { count += 2 }\n    onClick()\n    onClick()\n    onClick()\n'
         '    val label = if (count > 5) "Много: $count" else "Мало: $count"\n    println(label)\n    println("Нажатий: ${count / 2}")\n}\n')
ans4 = "Много: 6\nНажатий: 3"
a4 = asg("a4-predict", "predict", "Событие и состояние",
         "Кнопка в Compose вызывает функцию `onClick`, а та меняет состояние. Что выведет программа? Каждая строка — с новой строки.",
         "Проследить изменение состояния по событиям.", "—", "Две строки.", [],
         hints("onClick — лямбда: при вызове она прибавляет два к count.", "Лямбда вызывается три раза: считайте, чему равен count после каждого вызова.",
               "После трёх вызовов count = 6.", "label зависит от условия count > 5.", "Вторая строка делит count на два."),
         {"kind": "answer", "expected_answer": ans4}, ans4,
         "Лямбда трижды прибавляет 2: count = 6. Условие 6 > 5 верно, поэтому первая строка «Много: 6». Вторая: 6 / 2 = 3 нажатия.",
         ["Обе строки верны."],
         [("Много: 6\nНажатий: 6", "Деление: 6 / 2 = 3, а не 6."),
          ("Мало: 6\nНажатий: 3", "Условие count > 5 верно для 6, значит выбирается первая ветка."),
          ("Много: 4\nНажатий: 2", "onClick вызывается три раза, а не два.")],
         code=CODE4)

skills = {"kt.compose": "Основы Compose: @Composable", "kt.compose.layout": "Column, Row и Modifier", "kt.compose.lists": "Списки и кнопки в Compose"}
write_lesson("kt-05-compose-basics", "Kotlin: основы Jetpack Compose",
             "Описывать интерфейс функциями @Composable, собирать из Column и Row, добавлять кнопку и список LazyColumn.",
             list(skills), ["kt-04-coroutines"], scenes, notes, [a1, a2, a3, a4],
             [{"mistake": "Нет аннотации @Composable", "fix": "Поставьте @Composable над функцией интерфейса, иначе в ней нельзя вызывать Text и другие функции Compose."},
              {"mistake": "Обычная переменная вместо состояния", "fix": "Храните меняющееся значение в remember { mutableStateOf(…) }, иначе экран не обновится."},
              {"mistake": "for внутри LazyColumn", "fix": "Рисуйте строки через items(список) { элемент -> … }."},
              {"mistake": "Нет импорта getValue/setValue при by", "fix": "Добавьте import androidx.compose.runtime.getValue и setValue."}],
             min_pass=3, pack="kotlin-basics", runner="kotlin")
f = ROOT / "content/packs/kotlin-basics/pack.json"
data = json.loads(f.read_text("utf-8"))
if "kt-05-compose-basics" not in data["lessons"]:
    data["lessons"].append("kt-05-compose-basics")
data["skills"].update(skills)
f.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", "utf-8")
