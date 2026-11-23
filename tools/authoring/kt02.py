"""Урок Kotlin 2: классы и null-безопасность. На телефоне проверяются синтаксис и структура;
вывод в сценах и поведение эталонов (tests.jvm) проверяет в CI настоящий kotlinc."""
from mk import *


def L(code, text, n=1):
    lines = code.split("\n")
    i = next(k for k, ln in enumerate(lines) if text in ln)
    return list(range(i + 1, i + 1 + n))


K1 = ('class Account(val owner: String, var balance: Int) {\n    fun deposit(amount: Int) {\n        balance += amount\n    }\n\n'
      '    fun describe(): String = "$owner: $balance"\n}\n\n'
      'fun main() {\n    val acc = Account("Аня", 100)\n    acc.deposit(50)\n    println(acc.describe())\n}\n')
O1 = "Аня: 150\n"
K2 = ('fun safeLength(text: String?): Int {\n    return text?.length ?: 0\n}\n\n'
      'fun main() {\n    val a: String? = "Привет"\n    val b: String? = null\n    println(safeLength(a))\n    println(safeLength(b))\n    println(b ?: "пусто")\n}\n')
O2 = "6\n0\nпусто\n"
K3 = ('fun label(x: Int?): String {\n    if (x == null) return "пусто"\n    return "значение ${x + 1}"\n}\n\n'
      'fun main() {\n    println(label(4))\n    println(label(null))\n}\n')
O3 = "значение 5\nпусто\n"

use_file("Main.kt")
scenes = [
    scene("intro", "Классы и пустые значения", """
      Программы на Котлине описывают мир через классы. Класс — шаблон: какие у предмета свойства и что он умеет делать. А ещё
      Котлин борется с самой частой ошибкой в программировании — обращением к пустому значению, которое называется нулл.
      Сегодня разберём и то, и другое.""",
          [NOTE("класс = свойства + функции · `String?` = строка, которая может быть `null`", at="Сегодня разберём")]),
    scene("class", "Класс со свойствами и методами", """
      Объявим счёт в банке. После имени класса в скобках идёт главный конструктор: val owner — владелец, его менять нельзя,
      var balance — баланс, он меняется. Внутри фигурных скобок — функции класса, их называют методами. Метод deposit добавляет
      деньги, метод describe собирает строку. Объект создают, вызывая класс как функцию. Внесём пятьдесят и напечатаем описание.""",
          [CLEAR(), T(K1, at="Объявим счёт"), HL(L(K1, "class Account"), at="главный конструктор"), HL(L(K1, "fun deposit", 3), at="Метод deposit"),
           HL(L(K1, "fun describe"), at="метод describe"), HL(L(K1, "Account(\"Аня\""), at="Объект создают"), RUN(at="Внесём"), OUT(O1, at="Внесём")]),
    scene("null", "Тип со знаком вопроса", """
      Теперь нулл. Обычная строка нуллом быть не может — компилятор не позволит. Если значения может не быть, к типу добавляют
      вопросительный знак: String со знаком вопроса. Обратиться к свойству такого значения напрямую нельзя. Запись «вопрос и точка»
      — безопасный вызов: если внутри нулл, то и весь результат нулл. А элвис — вопрос и двоеточие — подставляет запасное значение.
      Длина слова «Привет» — шесть, длина нулла — ноль, а вместо нулла напечатаем «пусто».""",
          [CLEAR(), T(K2, at="Теперь нулл"), HL(L(K2, "fun safeLength"), at="вопросительный знак"), HL(L(K2, "return text"), at="безопасный вызов"),
           HL(L(K2, "return text"), at="А элвис"), RUN(at="Длина слова"), OUT(O2, at="Длина слова")]),
    scene("smart", "Проверка на null", """
      Пустоту можно проверить и обычным if. После проверки компилятор уже знает, что дальше значение не пустое, и разрешает
      работать с ним как с обычным числом. Это называется умным приведением типа. Для четвёрки получим «значение пять», для
      нулла — «пусто».""",
          [CLEAR(), T(K3, at="Пустоту можно"), HL(L(K3, "if (x == null)"), at="После проверки"), HL(L(K3, "return \"значение"), at="работать с ним"),
           RUN(at="Для четвёрки"), OUT(O3, at="Для четвёрки")]),
    scene("summary", "Итог", """
      Итак. Класс — шаблон со свойствами и методами. Свойства объявляют прямо в главном конструкторе: val — неизменяемое, var —
      изменяемое. Тип со знаком вопроса допускает нулл, а безопасный вызов и элвис защищают программу от падения. Двойной
      восклицательный знак обещает, что нулла нет, и роняет программу, если это не так, — лучше им не пользоваться.""",
          [NOTE("`class A(val x: Int)` · `String?` · `a?.b` · `a ?: запас` · `if (a == null) …`", at="Итак")]),
]

notes = """
# Kotlin: классы и null

```kotlin
class Account(val owner: String, var balance: Int) {
    fun deposit(amount: Int) {
        balance += amount
    }

    fun describe(): String = "$owner: $balance"
}

fun safeLength(text: String?): Int {
    return text?.length ?: 0
}

fun label(x: Int?): String {
    if (x == null) return "пусто"
    return "значение ${x + 1}"     // здесь x уже точно не null
}

fun main() {
    val acc = Account("Аня", 100)
    acc.deposit(50)
    println(acc.describe())
    println(safeLength(null))
    println(label(4))
}
```

| Запись | Смысл |
|---|---|
| `class A(val x: Int, var y: Int)` | свойства в главном конструкторе |
| `String?` | строка или `null` |
| `a?.length` | длина, а если `a` равно `null` — `null` |
| `a ?: "запас"` | `a`, а если `null` — запасное значение |
| `a!!` | «точно не null» — роняет программу, если это не так |

Запускается программа в GitHub Actions (проект Kotlin в разделе «Проекты»); на телефоне проверяются синтаксис
и структура кода.
"""

# --- a1: класс Counter ---
S1 = "class Counter {\n    var value = 0\n\n    fun inc() {\n        value++\n    }\n\n    fun reset() {\n        value = 0\n    }\n}\n"
t1 = {"kind": "kotlin", "cases": [
    {"id": "syntax", "type": "syntax"},
    {"id": "cls", "type": "class", "name": "Counter", "kind": "class"},
    {"id": "inc", "type": "function", "name": "inc", "paramTypes": [], "returns": "Unit"},
    {"id": "reset", "type": "function", "name": "reset", "paramTypes": [], "returns": "Unit"},
    {"id": "var", "hidden": True, "type": "contains", "pattern": "\\bvar\\s+value\\b", "message": "value должно быть изменяемым: var"},
    {"id": "plus", "hidden": True, "type": "contains", "pattern": "value\\s*(\\+\\+|\\+=\\s*1|=\\s*value\\s*\\+\\s*1)", "message": "inc увеличивает value на 1"},
    {"id": "zero", "hidden": True, "type": "contains", "pattern": "fun\\s+reset\\s*\\(\\s*\\)\\s*\\{[^}]*value\\s*=\\s*0", "message": "reset присваивает value = 0"},
], "jvm": {"main": "fun main() {\n    val c = Counter()\n    c.inc()\n    c.inc()\n    c.inc()\n    println(c.value)\n    c.reset()\n    println(c.value)\n}", "expected_stdout": "3\n0"}}
a1 = asg("a1-counter", "write", "Счётчик",
         "Напишите класс `Counter` со свойством `value` (целое, сначала 0, **изменяемое**) и двумя методами без параметров: `inc()` увеличивает `value` на 1, `reset()` сбрасывает его в 0.",
         "Описывать класс со свойством и методами.", "—", "Класс Counter.",
         ["Функция main не нужна.", "На телефоне проверяются синтаксис и устройство кода."],
         hints("Класс объявляют словом class: class Counter { … }.", "Свойство внутри класса: var value = 0 — var, потому что значение меняется.", "Метод — обычная fun внутри класса: fun inc() { … }.", "Увеличить: value++ (или value += 1).", "fun reset() { value = 0 }"),
         t1, S1, "Свойство var value хранит число, методы inc и reset меняют его; внутри класса к свойству обращаются по имени.",
         ["Класс Counter с var value.", "Методы inc() и reset()."],
         [("class Counter {\n    val value = 0\n\n    fun inc() {\n        value++\n    }\n\n    fun reset() {\n        value = 0\n    }\n}\n", "val нельзя изменить: нужен var."),
          ("class Counter {\n    var value = 0\n\n    fun reset() {\n        value = 0\n    }\n}\n", "Нет метода inc."),
          ("class Counter {\n    var value = 0\n\n    fun inc() {\n        value++\n    }\n\n    fun reset() {\n        value = 1\n    }\n}\n", "reset должен сбрасывать в 0, а не в 1."),
          ("class Counter {\n    var value = 0\n\n    fun inc(): Int {\n        value++\n        return value\n    }\n\n    fun reset() {\n        value = 0\n    }\n}\n", "inc ничего не возвращает: тип результата Unit."),
          ("fun Counter() {\n    var value = 0\n}\n", "Это функция, а не класс.")],
         starter="// Класс Counter\n")

# --- a2: Account ---
S2 = ('class Account(val owner: String, var balance: Int) {\n    fun deposit(amount: Int) {\n        balance += amount\n    }\n\n'
      '    fun describe(): String = "$owner: $balance"\n}\n')
t2 = {"kind": "kotlin", "cases": [
    {"id": "syntax", "type": "syntax"},
    {"id": "cls", "type": "class", "name": "Account", "kind": "class"},
    {"id": "dep", "type": "function", "name": "deposit", "paramTypes": ["Int"], "returns": "Unit"},
    {"id": "desc", "type": "function", "name": "describe", "paramTypes": [], "returns": "String"},
    {"id": "ctor", "hidden": True, "type": "contains", "pattern": "class\\s+Account\\s*\\(\\s*val\\s+owner\\s*:\\s*String\\s*,\\s*var\\s+balance\\s*:\\s*Int\\s*\\)",
     "message": "Конструктор: (val owner: String, var balance: Int)"},
    {"id": "add", "hidden": True, "type": "contains", "pattern": "balance\\s*(\\+=|=\\s*balance\\s*\\+)\\s*amount", "message": "deposit прибавляет amount к balance"},
    {"id": "str", "hidden": True, "type": "contains", "raw": True, "pattern": "\\$\\{?owner\\}?[\\s\\S]*\\$\\{?balance\\}?", "message": "describe собирает строку из owner и balance"},
], "jvm": {"main": 'fun main() {\n    val a = Account("Аня", 100)\n    a.deposit(50)\n    a.deposit(25)\n    println(a.describe())\n    println(Account("Боря", 0).describe())\n}',
           "expected_stdout": "Аня: 175\nБоря: 0"}}
a2 = asg("a2-account", "write", "Счёт в банке",
         "Напишите класс `Account` с главным конструктором `(val owner: String, var balance: Int)`, методом `deposit(amount: Int)` (добавляет к балансу) и методом `describe(): String`, который возвращает строку вида `Аня: 175` (владелец, двоеточие, пробел, баланс).",
         "Описывать свойства в главном конструкторе.", "—", "Класс Account.",
         ["Строка собирается шаблоном: \"$owner: $balance\"."],
         hints("Свойства объявляют в скобках после имени класса: class Account(val owner: String, var balance: Int).", "deposit ничего не возвращает: fun deposit(amount: Int) { … }.", "Прибавить: balance += amount.", "describe возвращает String: fun describe(): String = …", "\"$owner: $balance\" — шаблон подставляет значения."),
         t2, S2, "Свойства, объявленные в главном конструкторе, доступны в методах по имени; шаблон строки подставляет их значения.",
         ["Конструктор с двумя свойствами.", "deposit и describe работают."],
         [(S2.replace("var balance", "val balance"), "balance должен быть изменяемым (var)."),
          (S2.replace("balance += amount", "balance = amount"), "deposit должен прибавлять, а не заменять баланс."),
          (S2.replace('"$owner: $balance"', '"$balance"'), "В строке нет владельца."),
          (S2.replace("fun describe(): String", "fun describe()"), "Нет типа результата String.")],
         starter="// Класс Account\n")

# --- a3: безопасный вызов ---
S3 = "fun lengthOrZero(text: String?): Int {\n    return text?.length ?: 0\n}\n"
t3 = {"kind": "kotlin", "cases": [
    {"id": "syntax", "type": "syntax"},
    {"id": "fn", "type": "function", "name": "lengthOrZero", "paramTypes": ["String?"], "returns": "Int"},
    {"id": "safe", "hidden": True, "type": "contains", "pattern": "\\?\\.", "message": "Безопасный вызов: text?.length"},
    {"id": "elvis", "hidden": True, "type": "contains", "pattern": "\\?:", "message": "Запасное значение через ?: (элвис)"},
    {"id": "nobang", "hidden": True, "type": "not_contains", "pattern": "!!", "message": "Не используйте !!"},
], "jvm": {"main": 'fun main() {\n    println(lengthOrZero("Привет"))\n    println(lengthOrZero(null))\n    println(lengthOrZero(""))\n}', "expected_stdout": "6\n0\n0"}}
a3 = asg("a3-safe", "write", "Длина или ноль",
         "Напишите функцию `lengthOrZero(text: String?): Int`: длина строки, а для `null` — **0**. Используйте безопасный вызов `?.` и элвис `?:`; `!!` не применяйте.",
         "Работать с типом, допускающим null.", "Строка или null.", "Целое число.",
         ["!! запрещён."],
         hints("Тип параметра со знаком вопроса: String?.", "Обратиться к длине безопасно: text?.length.", "Если text равен null, результат тоже null — это Int?, а нужен Int.", "Запасное значение подставляет элвис: … ?: 0.", "return text?.length ?: 0"),
         t3, S3, "text?.length даёт длину или null; ?: 0 заменяет null нулём, и результат становится обычным Int.",
         ["Параметр String?.", "Используются ?. и ?:."],
         [("fun lengthOrZero(text: String): Int {\n    return text.length\n}\n", "Тип параметра должен допускать null: String?."),
          ("fun lengthOrZero(text: String?): Int {\n    return text!!.length\n}\n", "!! роняет программу на null."),
          ("fun lengthOrZero(text: String?): Int? {\n    return text?.length\n}\n", "Результат должен быть Int (для null — 0)."),
          ("fun lengthOrZero(text: String?): Int {\n    return 0\n}\n", "Длина не считается.")],
         starter="// Функция lengthOrZero\n")

# --- a4: fix — «Привет, null» ---
BAD4 = 'fun greet(name: String?): String = "Привет, " + name\n\nfun main() {\n    println(greet("Аня"))\n    println(greet(null))\n}\n'
S4 = 'fun greet(name: String?): String = "Привет, " + (name ?: "гость")\n\nfun main() {\n    println(greet("Аня"))\n    println(greet(null))\n}\n'
t4 = {"kind": "kotlin", "cases": [
    {"id": "syntax", "type": "syntax"},
    {"id": "fn", "type": "function", "name": "greet", "paramTypes": ["String?"], "returns": "String"},
    {"id": "null", "type": "contains", "pattern": "\\?:|[=!]=\\s*null", "message": "Проверьте name на null: ?: или if (name == null)", "hint": "Для null нужна своя ветка"},
    {"id": "guest", "hidden": True, "type": "contains", "raw": True, "pattern": "гость", "message": "Для null выводите «гость»"},
    {"id": "nobang", "hidden": True, "type": "not_contains", "pattern": "!!", "message": "Не используйте !!"},
], "jvm": {"main": "", "expected_stdout": "Привет, Аня\nПривет, гость"}}
a4 = asg("a4-greet", "fix", "«Привет, null»",
         "Для `greet(null)` программа печатает `Привет, null`, а нужно **`Привет, гость`**. Для обычного имени вывод тот же: `Привет, Аня`. Исправьте функцию `greet`; `!!` не применяйте.",
         "Не выводить null пользователю.", "—", "Привет, гость.",
         ["Заголовок функции менять не нужно."],
         hints("Запустите программу в GitHub Actions или прочитайте код: что склеивается со строкой, если name равен null?", "Строка + null даёт слово null — компилятор это разрешает.", "Нужен запасной вариант для null.", "Элвис: name ?: \"гость\".", "\"Привет, \" + (name ?: \"гость\")"),
         t4, S4, "Склейка строки с null не падает, а печатает «null». Элвис подставляет «гость», когда имени нет.",
         ["greet(null) даёт «Привет, гость».", "greet(\"Аня\") не изменилось."],
         [(BAD4, "Ошибка осталась: для null по-прежнему «null»."),
          ('fun greet(name: String?): String = "Привет, " + name!!\n\nfun main() {\n    println(greet("Аня"))\n}\n', "!! роняет программу на null."),
          ('fun greet(name: String?): String = "Привет, гость"\n\nfun main() {\n    println(greet("Аня"))\n}\n', "Для имени всегда «гость»: проверки на null нет.")],
         starter=BAD4)

# --- a5: predict ---
CODE5 = ('class Box(var items: Int) {\n    fun add(n: Int) {\n        items += n\n    }\n}\n\n'
         'fun label(x: Int?): String {\n    if (x == null) return "пусто"\n    return "значение $x"\n}\n\n'
         'fun main() {\n    val b = Box(2)\n    b.add(3)\n    println(b.items)\n    println(label(b.items))\n    println(label(null))\n}\n')
ans5 = "5\nзначение 5\nпусто"
a5 = asg("a5-predict", "predict", "Что напечатает программа?",
         "Что выведет программа? Каждая строка вывода — с новой строки.",
         "Читать класс и проверку на null.", "—", "Три строки.", [],
         hints("Сначала создаётся Box с двумя предметами.", "b.add(3) прибавляет три к items — получается пять.", "Первая строка — просто 5.", "label(5): число не null, значит «значение 5».", "label(null) возвращает «пусто»."),
         {"kind": "answer", "expected_answer": ans5}, ans5,
         "add меняет items с 2 до 5. label для числа возвращает «значение 5», а для null — «пусто».",
         ["Все три строки верны."],
         [("2\nзначение 2\nпусто", "b.add(3) увеличивает items: теперь их 5."),
          ("5\nзначение 5\nnull", "Для null функция возвращает строку «пусто»."),
          ("5\n5\nпусто", "label добавляет слово «значение».")],
         code=CODE5)

skills = {"kt.class": "Классы: свойства и методы", "kt.ctor": "Главный конструктор", "kt.null": "Типы с null и безопасный вызов", "kt.smartcast": "Проверка на null"}
write_lesson("kt-02-classes", "Kotlin: классы и null",
             "Описывать классы со свойствами и методами и безопасно работать со значениями, которые могут быть пустыми.",
             list(skills), ["kt-01-basics"], scenes, notes, [a1, a2, a3, a4, a5],
             [{"mistake": "Обращение к String? напрямую", "fix": "Используйте text?.length и запасное значение ?: …"},
              {"mistake": "!! вместо проверки", "fix": "!! роняет программу, если значение пустое."},
              {"mistake": "val вместо var в свойстве, которое меняется", "fix": "val присваивают один раз, var — можно менять."},
              {"mistake": "Склейка строки с null", "fix": "Получится слово «null»: подставьте запасное значение элвисом."}],
             min_pass=3, pack="kotlin-basics", runner="kotlin")
f = ROOT / "content/packs/kotlin-basics/pack.json"
data = json.loads(f.read_text("utf-8"))
if "kt-02-classes" not in data["lessons"]:
    data["lessons"].append("kt-02-classes")
data["skills"].update(skills)
data["stage"] = 13
f.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", "utf-8")
