"""Урок Kotlin 3: коллекции и лямбды (основа для Compose). На телефоне — синтаксис и структура;
вывод и поведение эталонов (tests.jvm) проверяет в CI настоящий kotlinc."""
from mk import *


def L(code, text, n=1):
    lines = code.split("\n")
    i = next(k for k, ln in enumerate(lines) if text in ln)
    return list(range(i + 1, i + 1 + n))


K1 = ('fun main() {\n    val nums = listOf(5, 3, 8, 1)\n    println(nums.sorted())\n    println(nums.map { it * 10 })\n'
      '    println(nums.filter { it > 2 })\n    println(nums.sum())\n    println(nums.maxOrNull())\n}\n')
O1 = "[1, 3, 5, 8]\n[50, 30, 80, 10]\n[5, 3, 8]\n17\n8\n"
K2 = ('fun main() {\n    val cart = mutableListOf("хлеб")\n    cart.add("молоко")\n    cart.add("сыр")\n    cart.remove("хлеб")\n    println(cart)\n'
      '    val ages = mutableMapOf("Аня" to 20)\n    ages["Борис"] = 25\n    println(ages["Борис"])\n    println(ages["Вера"])\n    println(ages.getOrDefault("Вера", 0))\n}\n')
O2 = "[молоко, сыр]\n25\nnull\n0\n"
K3 = ('fun repeatAction(times: Int, action: (Int) -> Unit) {\n    for (i in 1..times) action(i)\n}\n\n'
      'fun main() {\n    val double = { x: Int -> x * 2 }\n    println(double(21))\n    repeatAction(3) { n ->\n        println("Шаг $n")\n    }\n}\n')
O3 = "42\nШаг 1\nШаг 2\nШаг 3\n"

use_file("Main.kt")
scenes = [
    scene("intro", "Списки, множества, словари", """
      Почти любая программа работает с наборами данных. В Котлине их три основных вида. Список хранит элементы по порядку, и
      они могут повторяться. Множество хранит только разные элементы. Словарь связывает ключ со значением. Каждый вид бывает
      неизменяемым — listOf, setOf, mapOf — и изменяемым: mutableListOf, mutableSetOf, mutableMapOf.""",
          [NOTE("`listOf` · `setOf` · `mapOf` — читать · `mutableListOf` · `mutableSetOf` · `mutableMapOf` — менять", at="Каждый вид")]),
    scene("list", "Операции над списком", """
      Создадим список из четырёх чисел. Метод sorted возвращает новый отсортированный список, а исходный не меняется. Метод map
      преобразует каждый элемент: слово «ит» означает текущий элемент, умножаем его на десять. Метод filter оставляет только
      подходящие элементы. Метод sum складывает числа. А maxOrNull возвращает наибольшее, или нулл для пустого списка.""",
          [CLEAR(), T(K1, at="Создадим список"), HL(L(K1, "sorted"), at="Метод sorted"), HL(L(K1, ".map"), at="Метод map"), HL(L(K1, ".filter"), at="Метод filter"),
           HL(L(K1, ".sum"), at="Метод sum"), HL(L(K1, "maxOrNull"), at="А maxOrNull"), RUN(at="А maxOrNull"), OUT(O1, at="А maxOrNull")]),
    scene("mutable", "Изменяемые коллекции и словарь", """
      Изменяемый список умеет добавлять и удалять. Положим в корзину хлеб, добавим молоко и сыр, а хлеб уберём. В словаре
      значение достают по ключу в квадратных скобках, а записывают присваиванием. Если ключа нет, словарь возвращает нулл,
      поэтому тип результата допускает пустоту. Метод getOrDefault подставляет запасное значение. Запустим.""",
          [CLEAR(), T(K2, at="Изменяемый список"), HL(L(K2, "mutableListOf", 4), at="Положим в корзину"), HL(L(K2, "ages[\"Борис\"] ="), at="записывают присваиванием"),
           HL(L(K2, "ages[\"Вера\"]"), at="Если ключа нет"), HL(L(K2, "getOrDefault"), at="Метод getOrDefault"), RUN(at="Запустим"), OUT(O2, at="Запустим")]),
    scene("lambda", "Лямбды и функции-параметры", """
      Лямбда — это маленькая функция без имени, её можно положить в переменную. Параметры пишут слева от стрелки, тело — справа.
      Функцию можно передать в другую функцию: у repeatAction второй параметр — действие с типом «из Int в Unit». Если лямбда
      последняя в списке аргументов, её выносят за круглые скобки. Так repeatAction три раза вызовет действие с номером шага.""",
          [CLEAR(), T(K3, at="Лямбда — это"), HL(L(K3, "val double"), at="Параметры пишут"), HL(L(K3, "fun repeatAction"), at="Функцию можно передать"),
           HL(L(K3, "repeatAction(3)", 3), at="выносят за круглые скобки"), RUN(at="Так repeatAction"), OUT(O3, at="Так repeatAction")]),
    scene("android", "Зачем это Андроиду", """
      Зачем всё это приложению на Андроиде. Экран на Compose собирают из функций, а действие кнопки — это лямбда: кнопке
      передают, что делать при нажатии. Список покупок или задач — это обычный List, а отобразить его на экране помогают
      те же map и filter. Поэтому коллекции и лямбды — основа любого приложения.""",
          [NOTE("Button(onClick = { cart.add(\"сыр\") }) { Text(\"Добавить\") } — лямбда как действие кнопки", at="Экран на Compose"),
           NOTE("tasks.filter { !it.done }.map { it.title } — список для экрана", at="Список покупок")]),
    scene("summary", "Итог", """
      Итак. List хранит по порядку, Set — без повторов, Map — пары ключ и значение. Неизменяемые создают через listOf и mapOf,
      изменяемые — через mutableListOf и mutableMapOf. Методы map, filter, sorted и sum работают с любым списком. Лямбда — функция
      без имени; её передают в другие функции и выносят за скобки, если она последняя.""",
          [NOTE("`map { … }` · `filter { … }` · `sorted()` · `sum()` · `{ x: Int -> x * 2 }` · `(Int) -> Int`", at="Итак")]),
]

notes = """
# Kotlin: коллекции и лямбды

```kotlin
fun main() {
    val nums = listOf(5, 3, 8, 1)
    println(nums.sorted())            // [1, 3, 5, 8]
    println(nums.map { it * 10 })     // [50, 30, 80, 10]
    println(nums.filter { it > 2 })   // [5, 3, 8]
    println(nums.sum())               // 17

    val cart = mutableListOf("хлеб")
    cart.add("молоко")
    cart.remove("хлеб")
    println(cart)                     // [молоко]

    val ages = mutableMapOf("Аня" to 20)
    ages["Борис"] = 25
    println(ages["Вера"])             // null — такого ключа нет
}
```

## Лямбды
```kotlin
fun repeatAction(times: Int, action: (Int) -> Unit) {
    for (i in 1..times) action(i)
}

fun main() {
    val double = { x: Int -> x * 2 }
    println(double(21))
    repeatAction(3) { n -> println("Шаг $n") }
}
```

| Вид | Создать | Менять |
|---|---|---|
| список | `listOf(…)` | `mutableListOf(…)` |
| множество | `setOf(…)` | `mutableSetOf(…)` |
| словарь | `mapOf("a" to 1)` | `mutableMapOf("a" to 1)` |

- `it` — имя единственного параметра лямбды.
- `m[ключ]` для словаря возвращает значение или `null`.
- Лямбду, которая стоит последней среди аргументов, выносят за круглые скобки.
- В Compose действие кнопки — лямбда: `Button(onClick = { … })`.
"""

# --- a1: filter ---
S1 = "fun evens(nums: List<Int>): List<Int> = nums.filter { it % 2 == 0 }\n"
t1 = {"kind": "kotlin", "cases": [
    {"id": "syntax", "type": "syntax"},
    {"id": "fn", "type": "function", "name": "evens", "paramTypes": ["List<Int>"], "returns": "List<Int>"},
    {"id": "sel", "hidden": True, "type": "contains", "pattern": "\\bfilter\\b|\\bfor\\b", "message": "Отберите элементы: filter или цикл for"},
    {"id": "even", "hidden": True, "type": "contains", "pattern": "%\\s*2\\s*==\\s*0", "message": "Чётное число: n % 2 == 0"},
], "jvm": {"main": "fun main() {\n    println(evens(listOf(1, 2, 3, 4, 5, 6)))\n    println(evens(listOf(1, 3)))\n    println(evens(listOf()))\n}", "expected_stdout": "[2, 4, 6]\n[]\n[]"}}
a1 = asg("a1-evens", "write", "Только чётные",
         "Напишите функцию `evens(nums: List<Int>): List<Int>`, которая возвращает **только чётные** числа списка в прежнем порядке.",
         "Фильтровать список.", "Список целых.", "Новый список.",
         ["Тип результата укажите явно."],
         hints("Заголовок: fun evens(nums: List<Int>): List<Int>.", "Метод filter оставляет элементы, для которых условие истинно.", "Условие пишут в фигурных скобках; текущий элемент — it.", "Число чётное, если остаток от деления на 2 равен нулю: it % 2 == 0.", "nums.filter { it % 2 == 0 }"),
         t1, S1, "filter { it % 2 == 0 } создаёт новый список из чётных элементов; исходный не меняется.",
         ["Сигнатура evens(List<Int>): List<Int>.", "Условие остатка от деления на 2."],
         [("fun evens(nums: List<Int>): List<Int> = nums.filter { it % 2 == 1 }\n", "Здесь отбираются нечётные, а нужны чётные."),
          ("fun evens(nums: List<Int>): List<Int> = nums\n", "Список не фильтруется."),
          ("fun evens(nums: List<Int>) = nums.filter { it % 2 == 0 }\n", "Не указан тип результата List<Int>."),
          ("fun evens(nums: List<Int>): List<Int> = nums.map { it % 2 == 0 }\n", "map превращает числа в true/false, а не отбирает.")],
         starter="// Функция evens\n")

# --- a2: сумма значений словаря ---
S2 = "fun total(prices: Map<String, Int>): Int = prices.values.sum()\n"
t2 = {"kind": "kotlin", "cases": [
    {"id": "syntax", "type": "syntax"},
    {"id": "fn", "type": "function", "name": "total", "paramTypes": ["Map<String, Int>"], "returns": "Int"},
    {"id": "sum", "hidden": True, "type": "contains", "pattern": "\\.values\\b|\\bsumOf\\b|\\bfor\\b", "message": "Сложите значения словаря: prices.values.sum()"},
], "jvm": {"main": 'fun main() {\n    println(total(mapOf("чай" to 120, "кофе" to 200)))\n    println(total(emptyMap()))\n    println(total(mapOf("сок" to 150)))\n}', "expected_stdout": "320\n0\n150"}}
a2 = asg("a2-total", "write", "Сумма цен",
         "Напишите функцию `total(prices: Map<String, Int>): Int`, которая возвращает **сумму значений** словаря (цен). Для пустого словаря — 0.",
         "Работать со словарём.", "Словарь «товар → цена».", "Сумма цен.",
         ["Тип результата укажите явно."],
         hints("Заголовок: fun total(prices: Map<String, Int>): Int.", "У словаря есть свойство values — все значения без ключей.", "Числа складывает метод sum().", "Для пустого списка sum() вернёт 0.", "prices.values.sum()"),
         t2, S2, "prices.values — коллекция цен; sum() складывает их, а для пустой даёт 0.",
         ["Сигнатура total(Map<String, Int>): Int.", "Складываются значения."],
         [("fun total(prices: List<Int>): Int = prices.sum()\n", "Параметр должен быть словарём Map<String, Int>."),
          ("fun total(prices: Map<String, Int>) = prices.values.sum()\n", "Не указан тип результата Int."),
          ("fun total(prices: Map<String, Int>): Int = prices.size\n", "size — число товаров, а не сумма цен.")],
         starter="// Функция total\n")

# --- a3: функция как параметр ---
S3 = "fun applyTwice(x: Int, op: (Int) -> Int): Int {\n    return op(op(x))\n}\n"
t3 = {"kind": "kotlin", "cases": [
    {"id": "syntax", "type": "syntax"},
    {"id": "fn", "type": "function", "name": "applyTwice", "paramTypes": ["Int", "(Int) -> Int"], "returns": "Int"},
    {"id": "twice", "hidden": True, "type": "contains", "pattern": "op\\s*\\(\\s*op\\s*\\(", "message": "Примените op два раза: op(op(x))"},
], "jvm": {"main": "fun main() {\n    println(applyTwice(3) { it * 2 })\n    println(applyTwice(5) { it + 10 })\n    println(applyTwice(2) { it * it })\n}", "expected_stdout": "12\n25\n16"}}
a3 = asg("a3-twice", "write", "Дважды",
         "Напишите функцию `applyTwice(x: Int, op: (Int) -> Int): Int`, которая применяет функцию `op` к `x` **два раза** подряд и возвращает результат: `op(op(x))`.",
         "Принимать функцию в параметре.", "Число и функция.", "Результат двойного применения.",
         ["Тип параметра op — (Int) -> Int."],
         hints("Заголовок: fun applyTwice(x: Int, op: (Int) -> Int): Int.", "Параметр op — это функция; её вызывают как обычную: op(…).", "Первое применение: op(x).", "Второе применяется к результату первого.", "return op(op(x))"),
         t3, S3, "op — параметр-функция. Результат первого вызова op(x) подаётся в op ещё раз.",
         ["Сигнатура с параметром (Int) -> Int.", "op вызывается дважды."],
         [("fun applyTwice(x: Int, op: (Int) -> Int): Int {\n    return op(x)\n}\n", "op применяется один раз."),
          ("fun applyTwice(x: Int, op: (Int) -> Unit): Int {\n    return x\n}\n", "Тип op — (Int) -> Int, а не (Int) -> Unit."),
          ("fun applyTwice(x: Int, op: (Int) -> Int): Int {\n    return x\n}\n", "Функция op не вызывается.")],
         starter="// Функция applyTwice\n")

# --- a4: fix — топ-3 ---
BAD4 = "fun top3(scores: List<Int>): List<Int> = scores.sorted().take(3)\n"
S4 = "fun top3(scores: List<Int>): List<Int> = scores.sortedDescending().take(3)\n"
t4 = {"kind": "kotlin", "cases": [
    {"id": "syntax", "type": "syntax"},
    {"id": "fn", "type": "function", "name": "top3", "paramTypes": ["List<Int>"], "returns": "List<Int>"},
    {"id": "desc", "type": "contains", "pattern": "sortedDescending|sortedByDescending|reversed", "message": "Нужен порядок от большего к меньшему", "hint": "sorted() сортирует по возрастанию"},
    {"id": "take", "hidden": True, "type": "contains", "pattern": "\\btake\\s*\\(\\s*3\\s*\\)", "message": "Возьмите три первых: take(3)"},
], "jvm": {"main": "fun main() {\n    println(top3(listOf(5, 1, 9, 7, 3)))\n    println(top3(listOf(4, 2)))\n}", "expected_stdout": "[9, 7, 5]\n[4, 2]"}}
a4 = asg("a4-top3", "fix", "Три лучших результата",
         "Функция `top3` должна вернуть **три наибольших** результата от большего к меньшему, а возвращает три наименьших. Для `[5, 1, 9, 7, 3]` ожидается `[9, 7, 5]`. Исправьте.",
         "Различать порядок сортировки.", "—", "Три наибольших.",
         ["Тип результата не меняйте."],
         hints("Для [5, 1, 9, 7, 3] функция вернёт [1, 3, 5]. Что это за числа?", "sorted() сортирует по возрастанию — сначала самые маленькие.", "take(3) берёт первые три из отсортированного.", "Нужен обратный порядок.", "sortedDescending() вместо sorted()"),
         t4, S4, "sorted() ставит наименьшие первыми, и take(3) берёт именно их. sortedDescending() расставляет от большего к меньшему.",
         ["Сортировка по убыванию.", "Берутся три элемента."],
         [(BAD4, "Ошибка осталась: возвращаются три наименьших."),
          ("fun top3(scores: List<Int>): List<Int> = scores.sorted().takeLast(3)\n", "Это три наибольших, но по возрастанию: [5, 7, 9], а нужно [9, 7, 5]."),
          ("fun top3(scores: List<Int>): List<Int> = scores.sortedDescending().take(2)\n", "Берутся два элемента вместо трёх.")],
         starter=BAD4)

# --- a5: predict ---
CODE5 = ('fun main() {\n    val words = listOf("кот", "слон", "ёж", "жираф")\n    val long = words.filter { it.length > 3 }\n'
         '    println(long)\n    println(words.map { it.length })\n    println(words.size - long.size)\n}\n')
ans5 = "[слон, жираф]\n[3, 4, 2, 5]\n2"
a5 = asg("a5-predict", "predict", "Что напечатает программа?",
         "Что выведет программа? Каждая строка вывода — с новой строки.",
         "Читать цепочки filter и map.", "—", "Три строки.", [],
         hints("Сначала filter: оставляем слова длиннее трёх букв.", "«кот» — три буквы, не длиннее трёх; «ёж» — две.", "Остаются «слон» и «жираф».", "map даёт длины всех четырёх слов по порядку: 3, 4, 2, 5.", "В списке четыре слова, в long — два: 4 − 2 = 2."),
         {"kind": "answer", "expected_answer": ans5}, ans5,
         "Длиннее трёх букв — «слон» и «жираф». map возвращает длины всех слов, а разность размеров — 4 − 2 = 2.",
         ["Все три строки верны."],
         [("[кот, слон, жираф]\n[3, 4, 2, 5]\n2", "«кот» из трёх букв — условие строгое: длиннее трёх."),
          ("[слон, жираф]\n[4, 5]\n2", "map применяется к исходному списку words, а не к отфильтрованному."),
          ("[слон, жираф]\n[3, 4, 2, 5]\n4", "Разность размеров: 4 − 2 = 2.")],
         code=CODE5)

skills = {"kt.collections": "Списки, множества, словари", "kt.lambdas": "Лямбды и функции-параметры", "kt.hof": "map, filter, sorted и sum"}
write_lesson("kt-03-collections", "Kotlin: коллекции и лямбды",
             "Работать со списками и словарями, преобразовывать их методами map и filter и передавать функции в параметрах.",
             list(skills), ["kt-02-classes"], scenes, notes, [a1, a2, a3, a4, a5],
             [{"mistake": "listOf нельзя менять", "fix": "Чтобы добавлять и удалять, создайте mutableListOf."},
              {"mistake": "Забыли, что m[ключ] может вернуть null", "fix": "Результат допускает null: используйте ?: или getOrDefault."},
              {"mistake": "sorted() вместо sortedDescending()", "fix": "sorted() — по возрастанию, наибольшие в конце."},
              {"mistake": "map вместо filter", "fix": "map преобразует каждый элемент, filter отбирает подходящие."}],
             min_pass=3, pack="kotlin-basics", runner="kotlin")
f = ROOT / "content/packs/kotlin-basics/pack.json"
data = json.loads(f.read_text("utf-8"))
if "kt-03-collections" not in data["lessons"]:
    data["lessons"].append("kt-03-collections")
data["skills"].update(skills)
data["description"] = "Язык Андроида: типы, функции, when, классы, null-безопасность, коллекции и лямбды. На телефоне — проверка синтаксиса и структуры, запуск — в GitHub Actions."
f.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", "utf-8")
