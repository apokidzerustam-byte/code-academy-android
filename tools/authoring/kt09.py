"""Урок Kotlin 9: навигация между экранами — маршруты, NavHost, аргументы, стопка экранов.
Код с androidx.navigation проверяется по упрощённой заглушке (tools/kotlin-stubs/android/Navigation*.kt): проверяются синтаксис, типы и логика сопоставления маршрутов.
Настоящая библиотека Navigation Compose в CI не участвует."""
from mk import *


def L(code, text, n=1):
    lines = code.split("\n")
    i = next(k for k, ln in enumerate(lines) if text in ln)
    return list(range(i + 1, i + 1 + n))


IMP = ("import androidx.compose.material3.Text\nimport androidx.compose.runtime.Composable\nimport androidx.navigation.NavHostController\n"
       "import androidx.navigation.compose.NavHost\nimport androidx.navigation.compose.composable\n")
K1 = IMP + ('\n@Composable\nfun AppNav(navController: NavHostController) {\n    NavHost(navController = navController, startDestination = "list") {\n'
            '        composable("list") { Text("Список задач") }\n        composable("detail/{id}") { entry ->\n            val id = entry.arguments?.getString("id")\n'
            '            Text("Задача $id")\n        }\n    }\n}\n\nfun main() {\n    val nav = NavHostController()\n    println(stubs.ComposeLog.render { AppNav(nav) })\n'
            '    nav.navigate("detail/7")\n    println(stubs.ComposeLog.render { AppNav(nav) })\n}\n')
O1 = "Text(Список задач)\nText(Задача 7)\n"
K2 = ('fun detailRoute(id: Int) = "detail/$id"\n\ncomposable(\n    route = "detail/{id}",\n    arguments = listOf(navArgument("id") { type = NavType.IntType })\n) { entry ->\n'
      '    val id = entry.arguments?.getInt("id")\n    // по номеру достаём задачу из базы через ViewModel\n}\n')
K3 = ('class Screens {\n    private val stack = mutableListOf("list")\n\n    fun go(route: String) {\n        stack.add(route)\n    }\n\n    fun back(): Boolean {\n'
      '        if (stack.size == 1) return false\n        stack.removeAt(stack.size - 1)\n        return true\n    }\n\n    fun current(): String = stack.last()\n}\n\n'
      'fun main() {\n    val s = Screens()\n    s.go("detail/1")\n    s.go("settings")\n    println(s.current())\n    s.back()\n    println(s.current())\n'
      '    s.back()\n    println(s.back())\n}\n')
O3 = "settings\ndetail/1\nfalse\n"
KC = ('@Composable\nfun ListScreen(onOpen: (Int) -> Unit) {\n    Button(onClick = { onOpen(7) }) { Text("Открыть задачу 7") }\n}\n\n'
      '// в карте экранов:\ncomposable("list") {\n    ListScreen(onOpen = { id -> navController.navigate(detailRoute(id)) })\n}\n')
K4 = ('navController.navigate("main") {\n    popUpTo("login") { inclusive = true }\n    launchSingleTop = true\n}\n')

use_file("Main.kt")
scenes = [
    scene("intro", "Экраны и маршруты", """
      Приложение редко состоит из одного экрана. Список задач, подробности задачи, настройки: между ними нужно переходить и возвращаться
      назад. В Compose для этого есть библиотека Navigation. Идея простая. Каждому экрану даётся маршрут, строка вроде list или detail.
      Это как адрес страницы на сайте. Участников три. Первый, NavHost, контейнер с картой: какой маршрут какому экрану соответствует.
      Он же показывает текущий экран. Второй, NavController, пульт управления: команда navigate открывает новый экран, а popBackStack
      возвращает назад. Третий, стопка экранов, по-английски back stack. Представьте стопку тарелок: новый экран кладётся сверху, а кнопка
      «Назад» снимает верхний, и под ним снова виден предыдущий. Зачем всё это, если экраны можно просто подменять? Затем, что система
      Андроид сама следит за кнопкой «Назад», жестом и историей. Пользователь ждёт, что назад он попадёт именно туда, откуда пришёл. Navigation
      берёт эту работу на себя: вы описываете только адреса и переходы. Дальше разберём каждого участника и напишем маршруты сами.""",
          [NOTE("**Маршрут** — строка-адрес экрана: `list`, `detail/7`, `settings`", at="Каждому экрану"),
           NOTE("**NavHost** — карта экранов · **NavController** — `navigate` и `popBackStack` · **back stack** — стопка открытых экранов", at="Участников три")]),
    scene("navhost", "NavHost: карта экранов", """
      Вот карта экранов. Функция AppNav принимает контроллер и создаёт NavHost. Параметр startDestination называет стартовый экран: с него
      приложение начинает. Внутри блока для каждого экрана вызывается composable. Первый аргумент это маршрут, дальше в фигурных скобках
      содержимое экрана. Маршрут list показывает надпись со списком задач. Второй маршрут интереснее: в нём есть часть в фигурных скобках.
      Это аргумент. Если перейти по адресу detail слэш семь, то в записи стопки аргумент id будет равен семи. Достать его можно через
      arguments и getString. Контроллер в настоящем приложении создают один раз на самом верху, функцией rememberNavController, и отдают
      вниз. Запустим. Сначала контроллер показывает стартовый экран, потом мы переходим на detail семь, и NavHost рисует второй.
      Обратите внимание: сам код экранов ничего не знает про переходы. Он только описывает, что показать для данного адреса.""",
          [CLEAR(), T(K1, at="Вот карта"), HL(L(K1, "NavHost("), at="Параметр startDestination"), HL(L(K1, 'composable("list")'), at="Внутри блока"),
           HL(L(K1, 'composable("detail/{id}")'), at="Второй маршрут"), HL(L(K1, "getString"), at="Достать его"), RUN(at="Запустим"), OUT(O1, at="Запустим")]),
    scene("args", "Данные между экранами", """
      Как передавать данные между экранами. Главное правило: передавайте маленькие значения, номер или короткую строку, а не целые объекты.
      Экран подробностей получит номер задачи и сам достанет остальное из базы, через ViewModel и Room. Так данные не рассинхронизируются, а
      при повороте экрана или перезапуске приложения номер из маршрута сохранится. Чтобы не ошибиться в написании маршрута, его собирают
      функцией: она принимает номер и возвращает строку. Тогда опечатка может быть только в одном месте. В настоящих проектах аргументу
      ещё задают тип через navArgument, например целое число, и достают его через getInt. Этот код мы только покажем, а в заданиях
      будем работать со строками.""",
          [CLEAR(), T(K2, at="Как передавать"), HL(L(K2, "fun detailRoute"), at="Чтобы не ошибиться"), HL(L(K2, "navArgument"), at="В настоящих проектах"),
           HL(L(K2, "getInt"), at="достают его через getInt")]),
    scene("backstack", "Стопка экранов", """
      Теперь стопка экранов. Её удобно понять на модели без всякого Андроида. Класс хранит список маршрутов, и вначале в нём один стартовый
      экран. Функция go кладёт новый маршрут сверху. Функция back снимает верхний, но только если экранов больше одного. Когда остался
      последний, снимать нечего, и функция возвращает ложь. В настоящем приложении в этот момент система закрывает приложение.
      Запустим. Перейдём на подробности и настройки и посмотрим текущий экран. Вернёмся назад и посмотрим снова. Потом нажмём назад ещё раз,
      до самого низа, и убедимся, что дальше возвращаться некуда. Заметьте, что одинаковые маршруты в стопке могут повторяться: если
      дважды открыть detail один, то в стопке будет две записи, и «Назад» придётся нажать дважды.""",
          [CLEAR(), T(K3, at="Теперь стопка"), HL(L(K3, "private val stack"), at="Класс хранит"), HL(L(K3, "fun go", 3), at="Функция go"),
           HL(L(K3, "fun back", 5), at="Функция back"), RUN(at="Запустим"), OUT(O3, at="Запустим")]),
    scene("callbacks", "Экран и колбэки", """
      Как экран сообщает, что пользователь хочет перейти? Есть соблазн передать в каждый экран весь контроллер, но лучше передавать функцию.
      Экран списка получает параметр onOpen: функцию, которая принимает номер. Когда пользователь нажимает кнопку, экран просто вызывает onOpen
      с номером и больше ничего не знает. А в карте экранов мы решаем, что значит открыть: вызвать navigate с маршрутом, который собрала наша
      функция. Выгода двойная. Экран проще проверять: в проверке подставляется любая функция, и не нужен настоящий контроллер. И экран можно
      переиспользовать: сегодня он ведёт на подробности, а завтра, например, в диалог. Такой приём называют подъёмом событий: события
      поднимаются наверх, к тому, кто управляет навигацией.""",
          [CLEAR(), T(KC, at="Как экран"), HL(L(KC, "fun ListScreen"), at="Экран списка получает"), HL(L(KC, "onOpen(7)"), at="вызывает onOpen"),
           HL(L(KC, "navigate("), at="А в карте экранов")]),
    scene("flow", "Убрать экран из стопки", """
      Иногда экран нужно убрать из стопки. После входа в приложение экран входа не должен оставаться под главным: иначе кнопка «Назад»
      вернёт пользователя на вход. Для этого у navigate есть блок popUpTo. Он снимает из стопки всё до указанного маршрута, а параметр
      inclusive снимает и сам этот маршрут. Если экран уже наверху стопки, повторный переход создал бы его копию, а launchSingleTop
      этого не допускает. И ещё одно. Состояние экрана, например введённый текст, живёт во ViewModel, привязанной к записи в стопке. Пока
      запись в стопке, данные сохранены. Когда её сняли, ViewModel уничтожается.""",
          [CLEAR(), T(K4, at="Иногда экран"), HL(L(K4, "popUpTo"), at="Для этого"), HL(L(K4, "inclusive"), at="inclusive"), HL(L(K4, "launchSingleTop"), at="Если экран уже")]),
    scene("mistakes", "Типичные ошибки", """
      Пять типичных ошибок. Первая: опечатка в маршруте, например details вместо detail. Приложение соберётся, а при переходе упадёт с
      сообщением, что экран не найден. Поэтому маршруты собирают функциями или выносят в константы. Вторая: передавать через маршрут
      большие объекты, превращая их в строку. Берите номер и достаньте данные из базы. Третья: создавать контроллер заново внутри каждого
      экрана. Он один на приложение. А самому экрану лучше передавать не весь контроллер, а функцию, которую он вызовет при нажатии: так экран
      проще проверять. Четвёртая: не убрать экран входа из стопки, и тогда «Назад» возвращает на вход. Пятая, более тонкая: хранить состояние
      экрана в обычных переменных внутри функции экрана. При возврате на экран оно пропадёт, а во ViewModel сохранится.""",
          [NOTE("Ошибка 1: опечатка в маршруте → «экран не найден» при переходе.", at="Первая"),
           NOTE("Ошибка 2: большие объекты в маршруте; передавайте номер.", at="Вторая"),
           NOTE("Ошибка 3: контроллер создан не один раз на приложение.", at="Третья"),
           NOTE("Ошибка 4: экран входа остался в стопке.", at="Четвёртая"),
           NOTE("Ошибка 5: состояние экрана в локальных переменных, а не во ViewModel.", at="Пятая")]),
    scene("summary", "Итог", """
      Подведём итог. Маршрут это строка-адрес экрана, и маршруты с аргументами записывают в фигурных скобках. NavHost хранит карту и
      показывает текущий экран. NavController командой navigate кладёт экран на стопку, а popBackStack снимает верхний. Передавайте номера,
      а не объекты, и собирайте маршруты функцией. В заданиях вы напишете функцию маршрута, разберёте маршрут на части, добавите экран
      в NavHost, исправите опечатку в переходе и предскажете состояние стопки. Критерий прохождения: решить не меньше трёх заданий из пяти.
      Проверка на компьютере идёт по упрощённой заглушке Navigation, а на телефоне код проверяется по структуре.""",
          [NOTE("`navigate(route)` · `popBackStack()` · `popUpTo` · `launchSingleTop` · маршрут `detail/{id}`", at="Подведём итог")]),
]

notes = """
# Kotlin: навигация между экранами

Маршрут — строка-адрес экрана. **NavHost** хранит карту «маршрут → экран» и показывает текущий, **NavController** переходит между экранами, **стопка** (back stack) помнит открытые.

```kotlin
@Composable
fun AppNav(navController: NavHostController) {
    NavHost(navController = navController, startDestination = "list") {
        composable("list") { Text("Список задач") }
        composable("detail/{id}") { entry ->
            val id = entry.arguments?.getString("id")
            Text("Задача $id")
        }
    }
}
```

| Действие | Код |
|---|---|
| открыть экран | `navController.navigate("detail/7")` |
| вернуться | `navController.popBackStack()` |
| убрать экран из стопки | `navigate("main") { popUpTo("login") { inclusive = true } }` |
| не плодить копии экрана | `launchSingleTop = true` |
| собрать маршрут | `fun detailRoute(id: Int) = "detail/$id"` |

- Через маршрут передают **небольшие значения** (номер, короткую строку); данные экрана достают из базы через ViewModel.
- В настоящих проектах аргумент можно типизировать: `navArgument("id") { type = NavType.IntType }` и читать `getInt("id")`.
- Маршруты собирайте функциями или выносите в константы: опечатка приводит к ошибке «экран не найден» при переходе.
- Контроллер один на приложение; экрану удобнее передавать функцию-колбэк, чем весь контроллер.
- ViewModel, созданная на экране навигации, живёт, пока запись экрана есть в стопке.
- **Ограничение проверки:** в CI используется упрощённая заглушка Navigation (сопоставление маршрутов по сегментам, строковые аргументы, перерисовку вызывает проверяющий код). Настоящая библиотека, анимации и системная кнопка «Назад» проверяются только при сборке полного Android-проекта. На телефоне код проверяется по структуре.
"""

# --- a1: detailRoute ---
t1 = {"kind": "kotlin", "cases": [
    {"id": "syntax", "type": "syntax"},
    {"id": "fn", "type": "function", "name": "detailRoute", "paramTypes": ["Int"], "returns": "String"},
    {"id": "tpl", "raw": True, "type": "contains", "pattern": r'"detail/\$\{?id\}?"|"detail/"\s*\+\s*id\b',
     "message": "Маршрут — «detail/» и номер: \"detail/$id\""},
], "jvm": {"main": "fun main() {\n    println(detailRoute(7))\n    println(detailRoute(42))\n}", "expected_stdout": "detail/7\ndetail/42"}}
S1 = 'fun detailRoute(id: Int): String = "detail/$id"\n'
a1 = asg("a1-route", "write", "Функция маршрута",
         "Напишите функцию `detailRoute(id: Int): String`, которая возвращает маршрут экрана подробностей: `detail/` и номер. Например, `detailRoute(7)` возвращает `detail/7`.",
         "Собирать маршрут в одном месте.", "id: Int", "detailRoute(7) → detail/7.", [],
         hints("Маршрут — обычная строка: слово detail, слэш и номер.", "Функция принимает Int и возвращает String.",
               "Номер можно подставить в строку шаблоном со знаком доллара.", "Шаблон: в кавычках detail, слэш, затем знак доллара и имя параметра.",
               "fun detailRoute(id: Int): String = \"detail/$id\""),
         t1, S1, "Строковый шаблон подставляет номер в строку. Если маршрут собирает одна функция, опечатку можно сделать только в ней.",
         ["Параметр Int, результат String.", "Строка вида detail/номер."],
         [('fun detailRoute(id: Int): String = "detail/id"\n', "Вместо номера подставлено слово id: нужен шаблон со знаком доллара."),
          ('fun detailRoute(id: Int): String = "detail/"\n', "Номер потерялся: маршрут должен заканчиваться номером."),
          ('fun detailRoute(id: Int): String = "details/$id"\n', "В слове detail лишняя буква."),
          ('fun detailRoute(id: String): String = "detail/$id"\n', "Параметр должен быть Int.")],
         starter="// Напишите функцию detailRoute\n")

# --- a2: parseId ---
S2 = ('fun parseId(route: String): Int? {\n    val parts = route.split("/")\n    if (parts.size != 2 || parts[0] != "detail") return null\n    return parts[1].toIntOrNull()\n}\n')
START2 = ('fun parseId(route: String): Int? {\n    val parts = route.split("/")\n    // Допишите: вернуть номер, если маршрут вида detail/<число>, иначе null\n}\n')
t2 = {"kind": "kotlin", "cases": [
    {"id": "syntax", "type": "syntax"},
    {"id": "fn", "type": "function", "name": "parseId", "paramTypes": ["String"], "returns": "Int?"},
    {"id": "safe", "type": "contains", "pattern": r"toIntOrNull\s*\(\s*\)", "message": "Число из строки безопасно достаёт toIntOrNull()",
     "hint": "toInt() упадёт на строке «abc», а toIntOrNull() вернёт null"},
    {"id": "nothrow", "type": "not_contains", "pattern": r"\.toInt\s*\(\s*\)", "message": "toInt() падает на нечисловой строке: используйте toIntOrNull()"},
    {"id": "prefix", "raw": True, "type": "contains", "pattern": r'"detail/?"', "message": "Нужно проверить, что первая часть маршрута — detail"},
    {"id": "size", "hidden": True, "type": "contains", "pattern": r"size\s*(!=|==|<|>|<=|>=)\s*\d|removePrefix|substringAfter|Regex|matches",
     "message": "Проверьте, что в маршруте ровно две части: detail/1/2 не подходит"},
], "jvm": {"main": ('fun main() {\n    println(parseId("detail/7"))\n    println(parseId("detail/abc"))\n    println(parseId("list"))\n    println(parseId("detail/1/2"))\n'
                    '    println(parseId("settings/5"))\n}'), "expected_stdout": "7\nnull\nnull\nnull\nnull"}}
a2 = asg("a2-parse", "complete", "Номер из маршрута",
         "Допишите функцию `parseId(route: String): Int?`: если маршрут имеет вид `detail/<число>`, верните число, иначе `null`. Например, `detail/7` → 7; `detail/abc`, `list`, `detail/1/2`, `settings/5` → `null`. "
         "Маршрут уже разбит на части по `/`.",
         "Безопасно разбирать маршрут.", "route: String", "Int? — число или null.",
         ["Не используйте toInt(): он падает на нечисловой строке."],
         hints("Маршрут разбит на части: parts[0] — первое слово, parts[1] — второе.", "Сначала проверьте, что частей две и первая из них — detail; иначе вернуть null.",
               "Из текста число достаёт toIntOrNull(): для «abc» он вернёт null, а не упадёт.", "Условие отказа: parts.size != 2 или parts[0] != \"detail\".",
               "if (parts.size != 2 || parts[0] != \"detail\") return null; return parts[1].toIntOrNull()"),
         t2, S2, "Проверка формы маршрута отсекает чужие адреса, а toIntOrNull() превращает нечисловую часть в null вместо исключения.",
         ["Сигнатура Int?.", "Проверка префикса detail.", "Безопасный разбор числа."],
         [('fun parseId(route: String): Int? {\n    val parts = route.split("/")\n    if (parts.size != 2 || parts[0] != "detail") return null\n    return parts[1].toInt()\n}\n', "toInt() падает на «detail/abc»: нужно toIntOrNull()."),
          ('fun parseId(route: String): Int? {\n    val parts = route.split("/")\n    if (parts.size != 2) return null\n    return parts[1].toIntOrNull()\n}\n', "Не проверено слово detail: settings/5 вернёт число."),
          ('fun parseId(route: String): Int? {\n    val parts = route.split("/")\n    if (parts[0] != "detail") return null\n    return parts[1].toIntOrNull()\n}\n', "Не проверено число частей: detail/1/2 вернёт 1, а при маршруте «detail» программа упадёт.")],
         starter=START2)

# --- a3: add second screen to NavHost ---
S3_BODY = ('@Composable\nfun AppNav(navController: NavHostController) {\n    NavHost(navController = navController, startDestination = "list") {\n'
           '        composable("list") { Text("Список задач") }\n        composable("detail/{id}") { entry ->\n            val id = entry.arguments?.getString("id")\n'
           '            Text("Задача $id")\n        }\n    }\n}\n')
START3 = IMP + ('\n@Composable\nfun AppNav(navController: NavHostController) {\n    NavHost(navController = navController, startDestination = "list") {\n'
                '        composable("list") { Text("Список задач") }\n        // Добавьте экран подробностей: маршрут detail/{id}, текст «Задача <номер>»\n    }\n}\n')
S3 = IMP + "\n" + S3_BODY
t3 = {"kind": "kotlin", "cases": [
    {"id": "syntax", "type": "syntax"},
    {"id": "fn", "type": "function", "name": "AppNav", "paramTypes": ["NavHostController"]},
    {"id": "list", "raw": True, "type": "contains", "pattern": r'composable\s*\(\s*"list"\s*\)', "message": "Экран списка менять не нужно"},
    {"id": "route", "raw": True, "type": "contains", "pattern": r'composable\s*\(\s*"detail/\{id\}"\s*\)', "message": "Добавьте composable(\"detail/{id}\") { … }"},
    {"id": "arg", "raw": True, "type": "contains", "pattern": r'getString\s*\(\s*"id"\s*\)', "message": "Номер берётся из аргумента: entry.arguments?.getString(\"id\")"},
    {"id": "text", "raw": True, "type": "contains", "pattern": r'Text\s*\(\s*"Задача\s*(\$|"\s*\+)', "message": "Текст экрана — «Задача» и номер из аргумента, например \"Задача $id\""},
], "jvm": {"main": ('fun main() {\n    val nav = NavHostController()\n    println(stubs.ComposeLog.render { AppNav(nav) })\n    nav.navigate("detail/7")\n'
                    '    println(stubs.ComposeLog.render { AppNav(nav) })\n    nav.navigate("detail/12")\n    println(stubs.ComposeLog.render { AppNav(nav) })\n}'),
           "expected_stdout": "Text(Список задач)\nText(Задача 7)\nText(Задача 12)"}}
a3 = asg("a3-navhost", "complete", "Второй экран",
         "В `AppNav` уже есть экран `list`. Добавьте экран подробностей: маршрут `detail/{id}`, в нём `Text` с надписью «Задача » и номером из аргумента `id` (`entry.arguments?.getString(\"id\")`). "
         "Например, по адресу `detail/7` экран показывает «Задача 7».",
         "Добавить экран с аргументом в NavHost.", "—", "Для detail/7 — Text(Задача 7).",
         ["Экран list не менять."],
         hints("Каждый экран описывается вызовом composable внутри блока NavHost.", "Первый аргумент composable — маршрут; часть в фигурных скобках — аргумент: detail/{id}.",
               "Лямбда экрана получает запись стопки: composable(\"…\") { entry -> … }.", "Номер лежит в entry.arguments?.getString(\"id\").",
               "composable(\"detail/{id}\") { entry -> val id = entry.arguments?.getString(\"id\"); Text(\"Задача $id\") }"),
         t3, S3, "Маршрут detail/{id} подходит к любому адресу detail/<что угодно>, а значение в скобках попадает в аргументы записи стопки.",
         ["Маршрут detail/{id}.", "Аргумент из записи.", "Текст «Задача <номер>»."],
         [(START3, "Экран подробностей не добавлен."),
          (S3.replace('composable("detail/{id}")', 'composable("detail")'), "У маршрута нет части с аргументом: detail/7 не подойдёт."),
          (S3.replace('Text("Задача $id")', 'Text("Задача 7")'), "Номер зашит в текст: он должен браться из аргумента."),
          (S3.replace('composable("detail/{id}")', 'composable("details/{id}")'), "В слове detail лишняя буква.")],
         starter=START3)

# --- a4: fix route typo ---
BAD4 = IMP.replace("import androidx.compose.material3.Text\n", "import androidx.compose.material3.Button\nimport androidx.compose.material3.Text\n") + (
    '\n@Composable\nfun ListScreen(navController: NavHostController) {\n    Button(onClick = { navController.navigate("details/7") }) { Text("Открыть") }\n}\n\n'
    '@Composable\nfun AppNav(navController: NavHostController) {\n    NavHost(navController = navController, startDestination = "list") {\n        composable("list") { ListScreen(navController) }\n'
    '        composable("detail/{id}") { entry ->\n            val id = entry.arguments?.getString("id")\n            Text("Задача $id")\n        }\n    }\n}\n')
S4 = BAD4.replace('navigate("details/7")', 'navigate("detail/7")')
t4 = {"kind": "kotlin", "cases": [
    {"id": "syntax", "type": "syntax"},
    {"id": "go", "raw": True, "type": "contains", "pattern": r'navigate\s*\(\s*"detail/7"\s*\)', "message": "Переход должен вести на маршрут из графа: navigate(\"detail/7\")",
     "hint": "Приложение упадёт: «Navigation destination … cannot be found»"},
    {"id": "typo", "raw": True, "type": "not_contains", "pattern": r'"details', "message": "Осталась опечатка details"},
    {"id": "graph", "raw": True, "type": "contains", "pattern": r'composable\s*\(\s*"detail/\{id\}"\s*\)', "message": "Маршрут в графе менять не нужно: исправьте переход"},
    {"id": "btn", "hidden": True, "type": "contains", "pattern": r"\bButton\s*\(", "message": "Кнопку убирать не нужно"},
], "jvm": {"main": ('fun main() {\n    val nav = NavHostController()\n    println(stubs.ComposeLog.render { AppNav(nav) })\n    stubs.ComposeLog.click(0)\n'
                    '    println(stubs.ComposeLog.render { AppNav(nav) })\n}'), "expected_stdout": "Button\n  Text(Открыть)\nText(Задача 7)"}}
a4 = asg("a4-typo", "fix", "Опечатка в маршруте",
         "По нажатию кнопки приложение падает: переход ведёт на маршрут `details/7`, а в графе есть только `detail/{id}`. Исправьте переход. Карту экранов (`NavHost`) менять не нужно.",
         "Находить опечатки в маршрутах.", "—", "После нажатия показывается «Задача 7».",
         ["Граф NavHost не менять."],
         hints("Сообщение об ошибке: экран с таким маршрутом не найден.", "Сравните маршрут в navigate с маршрутом в composable.",
               "В графе слово detail, а в переходе — details.", "Маршрут перехода должен подходить под шаблон detail/{id}.",
               "Замените navigate(\"details/7\") на navigate(\"detail/7\")."),
         t4, S4, "NavHost ищет в графе маршрут, подходящий под адрес. Для «details/7» подходящего нет, поэтому приложение падает; после исправления адрес detail/7 совпадает с шаблоном detail/{id}.",
         ["Переход на detail/7.", "Граф не изменён."],
         [(BAD4, "Опечатка осталась: details вместо detail."),
          (BAD4.replace('composable("detail/{id}")', 'composable("details/{id}")'), "Изменён граф, а нужно исправить переход."),
          (BAD4.replace('navigate("details/7")', 'navigate("detail/{id}")'), "В переходе нужен конкретный адрес detail/7, а не шаблон.")],
         starter=BAD4)

# --- a5: predict back stack ---
CODE5 = ('fun main() {\n    val stack = mutableListOf("list")\n    fun go(route: String) { stack.add(route) }\n'
         '    fun back(): Boolean {\n        if (stack.size == 1) return false\n        stack.removeAt(stack.size - 1)\n        return true\n    }\n'
         '    go("detail/1")\n    go("detail/2")\n    back()\n    go("settings")\n    println(stack)\n    println(back())\n    println(back())\n    println(back())\n    println(stack.last())\n}\n')
ans5 = "[list, detail/1, settings]\ntrue\ntrue\nfalse\nlist"
a5 = asg("a5-predict", "predict", "Стопка экранов",
         "Стопка моделируется списком: `go` кладёт маршрут сверху, `back` снимает верхний, если экранов больше одного. Что выведет программа?",
         "Проследить состояние стопки.", "—", "Пять строк.", [],
         hints("Следите за списком по шагам: сначала один экран list.", "После двух go и одного back в стопке list и detail/1.",
               "Затем go(\"settings\") кладёт настройки сверху: [list, detail/1, settings].", "Каждый back снимает верхний экран и возвращает true, пока экранов больше одного.",
               "Три вызова back: true, true, затем false (остался один list). Последняя строка — верхний экран, то есть list."),
         {"kind": "answer", "expected_answer": ans5}, ans5,
         "После go, go, back и go в стопке [list, detail/1, settings]. Два back снимают settings и detail/1 (true, true), третий не может снять последний экран (false), поэтому наверху остаётся list.",
         ["Все пять строк верны."],
         [("[list, detail/1, detail/2, settings]\ntrue\ntrue\ntrue\nlist", "Вызов back между двумя go снимает detail/2."),
          ("[list, detail/1, settings]\ntrue\ntrue\ntrue\nlist", "Последний экран снять нельзя: третий back возвращает false."),
          ("[list, detail/1, settings]\ntrue\ntrue\nfalse\nsettings", "Верхний экран после трёх back — list: остальные сняты.")],
         code=CODE5)

skills = {"kt.nav.routes": "Навигация: маршруты и NavHost", "kt.nav.args": "Навигация: аргументы маршрутов", "kt.nav.backstack": "Навигация: стопка экранов"}
write_lesson("kt-09-navigation", "Kotlin: навигация между экранами",
             "Описывать экраны маршрутами, собирать NavHost с аргументами, переходить между экранами и понимать стопку экранов.",
             list(skills), ["kt-08-room"], scenes, notes, [a1, a2, a3, a4, a5],
             [{"mistake": "Опечатка в маршруте", "fix": "Собирайте маршруты функциями или выносите в константы; при падении «экран не найден» сравните navigate и composable."},
              {"mistake": "Большие объекты в маршруте", "fix": "Передавайте номер и достаньте данные из базы через ViewModel."},
              {"mistake": "Контроллер создан заново на каждом экране", "fix": "Контроллер один на приложение; экрану передавайте функцию-колбэк."},
              {"mistake": "Экран входа остался в стопке", "fix": "Используйте popUpTo с inclusive = true."}],
             min_pass=3, pack="kotlin-basics", runner="kotlin")
f = ROOT / "content/packs/kotlin-basics/pack.json"
data = json.loads(f.read_text("utf-8"))
if "kt-09-navigation" not in data["lessons"]:
    data["lessons"].append("kt-09-navigation")
data["skills"].update(skills)
f.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", "utf-8")
