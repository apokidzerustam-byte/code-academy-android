"""Урок Kotlin 1. На телефоне — синтаксис и структура (tree-sitter); вывод программ в сценах и поведение эталонов
проверяет валидатор в CI настоящим kotlinc."""
from mk import *

K1 = 'fun main() {\n    println("Привет, Kotlin!")\n    val name = "Аня"\n    var age = 20\n    age = age + 1\n    println("$name, $age")\n}\n'
O1 = "Привет, Kotlin!\nАня, 21\n"
K2 = ('fun square(x: Int): Int {\n    return x * x\n}\n\nfun half(x: Double): Double = x / 2\n\n'
      'fun main() {\n    println(square(7))\n    println(half(5.0))\n}\n')
O2 = "49\n2.5\n"
K3 = ('fun describe(n: Int): String = when {\n    n < 0 -> "отрицательное"\n    n == 0 -> "ноль"\n    else -> "положительное"\n}\n\n'
      'fun main() {\n    for (i in -1..1) {\n        println("$i: ${describe(i)}")\n    }\n}\n')
O3 = "-1: отрицательное\n0: ноль\n1: положительное\n"
K4 = ('data class Book(val title: String, val year: Int)\n\n'
      'fun main() {\n    val books = listOf(Book("Онегин", 1833), Book("Мастер", 1967))\n'
      '    val old = books.filter { it.year < 1900 }\n    println(old)\n}\n')
O4 = "[Book(title=Онегин, year=1833)]\n"
KERR = 'fun main() {\n    val name = "Аня"\n    println("Привет, $name"\n}\n'

use_file("Main.kt")
scenes = [
    scene("intro", "Kotlin — язык Андроида", """
      Kotlin — основной язык для приложений на Андроиде, на нём написано и это приложение. Он строгий: у каждого
      значения есть тип, и многие ошибки находятся ещё до запуска. Программа на Котлине сначала компилируется —
      переводится в код для виртуальной машины Java. Такого компилятора в телефоне нет, поэтому здесь приложение
      проверяет синтаксис и структуру кода, а собрать и запустить программу можно бесплатно в GitHub Actions.
      Вывод, который вы увидите в уроке, получен настоящим компилятором.""",
          [NOTE("На телефоне: **проверка синтаксиса и структуры**. Запуск: GitHub Actions или компьютер.", at="поэтому здесь")]),
    scene("main", "main, val и var", """
      Программа начинается с функции main. println печатает строку. Переменные бывают двух видов: val — значение
      нельзя изменить, var — можно. Тип Котлин выводит сам: name — строка, age — целое число. В строке знак
      доллар подставляет значение переменной. Так программа выведет приветствие и возраст двадцать один.""",
          [CLEAR(), T(K1, at="Программа начинается"), HL([1, 7], at="Программа начинается"), HL([3], at="val"), HL([4, 5], at="var — можно"),
           HL([6], at="знак"), RUN(at="Так программа"), OUT(O1, at="Так программа")]),
    scene("funcs", "Функции и типы", """
      Функцию объявляют словом fun. У каждого параметра пишут тип через двоеточие, и тип результата — после скобок.
      Int — целое число, Double — дробное, String — строка. Если функция — одно выражение, можно написать её
      короче, через знак равно. Квадрат семи — сорок девять, половина пяти — две с половиной.""",
          [CLEAR(), T(K2, at="Функцию объявляют"), HL([1, 2, 3], at="У каждого параметра"), HL([5], at="Если функция"),
           RUN(at="Квадрат"), OUT(O2, at="Квадрат")]),
    scene("when", "when и циклы", """
      Вместо длинной цепочки if в Котлине есть when: слева условие, после стрелки — результат, else — для всех
      остальных случаев. Цикл for проходит по диапазону: минус один, две точки, один — это числа от минус
      одного до одного включительно. Внутри строки фигурные скобки после доллара подставляют результат вызова.""",
          [CLEAR(), T(K3, at="Вместо"), HL([1, 2, 3, 4, 5], at="Вместо"), HL([8], at="Цикл for"), HL([9], at="Внутри строки"),
           RUN(at="Внутри строки"), OUT(O3, at="Внутри строки")]),
    scene("data", "data class и списки", """
      data class — класс для хранения данных: перечисляем свойства в скобках, а Котлин сам добавляет печать,
      сравнение и копирование. listOf создаёт список. filter оставляет элементы, для которых условие в фигурных
      скобках истинно; слово ит — текущий элемент. Останется только Онегин.""",
          [CLEAR(), T(K4, at="data class"), HL([1], at="data class"), HL([4], at="listOf"), HL([5], at="filter"),
           RUN(at="Останется"), OUT(O4, at="Останется")]),
    scene("errors", "Синтаксические ошибки", """
      Забудем закрывающую скобку у println и нажмём «Запустить». Приложение разобрало код и показало строку
      с ошибкой: ожидалась скобка. Это та же проверка, что выполняется в заданиях: сначала синтаксис, потом
      структура — есть ли нужные функции, с какими типами параметров и результата, использованы ли нужные конструкции.""",
          [CLEAR(), T(KERR, at="Забудем"), HL([3], at="Забудем"),
           NOTE("Задания по Kotlin на телефоне проверяют: синтаксис → имена и типы функций и классов → нужные конструкции.", at="Это та же")]),
    scene("ci", "Запуск в GitHub Actions", """
      Чтобы запустить программу, создайте в разделе «Проекты» проект Kotlin. В нём уже есть файл сценария сборки
      для GitHub Actions и инструкция по шагам. Вы переносите файлы в свой репозиторий на GitHub, и через минуту
      во вкладке Actions виден вывод программы. Это бесплатно и работает даже с телефона.""",
          [NOTE("Проекты → новый → Kotlin → файл README.md: пошаговая инструкция для GitHub Actions.", at="Чтобы запустить")]),
    scene("summary", "Итоги", """
      Итак: fun main — начало программы, val и var — переменные, у параметров и результата функций есть типы,
      when заменяет цепочки if, for in проходит по диапазону, data class хранит данные, filter отбирает элементы
      списка. Переходите к заданиям.""",
          [NOTE("`val`/`var` · `fun f(x: Int): Int` · `when { … -> … }` · `for (i in 1..n)` · `data class` · `filter { it … }`", at="Итак")]),
]
# Ошибка из сцены — настоящий вывод синтаксической проверки приложения (в CI; локально без tree-sitter не проверить).

notes = """
# Kotlin: первые шаги

```kotlin
fun main() {
    val name = "Аня"     // нельзя изменить
    var age = 20         // можно изменить
    age += 1
    println("$name, $age, ${age * 2}")
}
```

## Функции
```kotlin
fun square(x: Int): Int {
    return x * x
}

fun half(x: Double): Double = x / 2   // функция-выражение

fun main() {
    println(square(3))
    println(half(5.0))
}
```

## when и циклы
```kotlin
fun grade(score: Int): String = when {
    score >= 90 -> "отлично"
    score >= 60 -> "зачёт"
    else -> "незачёт"
}

fun main() {
    for (i in 1..3) println(grade(i * 40))
}
```

## data class и списки
```kotlin
data class Book(val title: String, val year: Int)

fun main() {
    val books = listOf(Book("Онегин", 1833), Book("Мастер", 1967))
    println(books.filter { it.year < 1900 })
}
```

## Типы
`Int` — целое, `Double` — дробное, `String` — строка, `Boolean` — да/нет, `List<Book>` — список книг.

## Как проверяется на телефоне
Компилятора Kotlin в телефоне нет. Задания проверяют синтаксис, имена и типы функций и классов
и нужные конструкции. Запустить программу — проект Kotlin в разделе «Проекты» (файл README.md) и GitHub Actions.
"""

# --- Задание 1: функция с типами --------------------------------------------------------
S1 = "fun square(x: Int): Int {\n    return x * x\n}\n"
t1 = {"kind": "kotlin", "cases": [
    {"id": "syntax", "type": "syntax"},
    {"id": "fn", "type": "function", "name": "square", "paramTypes": ["Int"], "returns": "Int"},
    {"id": "mul", "hidden": True, "type": "contains", "pattern": "x\\s*\\*\\s*x", "message": "Квадрат — это x * x"},
], "jvm": {"main": "fun main() {\n    println(square(5))\n    println(square(-3))\n    println(square(0))\n}", "expected_stdout": "25\n9\n0"}}
a1 = asg("a1-square", "write", "Квадрат числа",
         "Напишите функцию `square`, которая принимает целое число `x` (тип `Int`) и **возвращает** его квадрат (тип `Int`).",
         "Объявлять функцию с типами параметра и результата.", "Целое x.", "x * x.",
         ["Функция main не нужна.", "На телефоне проверяются синтаксис и заголовок функции."],
         hints("Функцию объявляют словом fun.",
               "Тип параметра пишут через двоеточие: x: Int.",
               "Тип результата — после скобок: ): Int.",
               "Результат возвращают словом return.",
               "fun square(x: Int): Int {\n    return x * x\n}"),
         t1, S1, "fun square(x: Int): Int — имя, параметр с типом и тип результата; return x * x возвращает квадрат.",
         ["Заголовок fun square(x: Int): Int.", "Возвращает x * x."],
         [("fun square(x: Int) {\n    println(x * x)\n}\n", "Нет типа результата: функция печатает, а не возвращает."),
          ("fun square(x: Double): Double {\n    return x * x\n}\n", "Нужен тип Int, а не Double."),
          ("fun sqr(x: Int): Int {\n    return x * x\n}\n", "Функция должна называться square."),
          ("fun square(x: Int): Int {\n    return x * x\n", "Не закрыта фигурная скобка."),
          ("fun square(x: Int): Int {\n    return x + x\n}\n", "x + x — удвоение, а не квадрат.")],
         starter="// Функция square\n")

# --- Задание 2: when --------------------------------------------------------------------------
S2 = 'fun grade(score: Int): String = when {\n    score >= 90 -> "отлично"\n    score >= 60 -> "зачёт"\n    else -> "незачёт"\n}\n'
t2 = {"kind": "kotlin", "cases": [
    {"id": "syntax", "type": "syntax"},
    {"id": "fn", "type": "function", "name": "grade", "paramTypes": ["Int"], "returns": "String"},
    {"id": "when", "type": "contains", "pattern": "\\bwhen\\b", "message": "Используйте when"},
    {"id": "else", "hidden": True, "type": "contains", "pattern": "\\belse\\s*->", "message": "В when нужна ветка else для остальных случаев"},
], "jvm": {"main": 'fun main() {\n    for (s in listOf(95, 90, 75, 60, 59, 0)) println(grade(s))\n}',
           "expected_stdout": "отлично\nотлично\nзачёт\nзачёт\nнезачёт\nнезачёт"}}
a2 = asg("a2-grade", "write", "Оценка через when",
         "Напишите функцию `grade(score: Int): String` с помощью `when`:\n\n"
         "- 90 и больше → `отлично`;\n- от 60 до 89 → `зачёт`;\n- меньше 60 → `незачёт`.",
         "Выбирать результат конструкцией when.", "Целое score от 0 до 100.", "Строка-оценка.",
         ["Используйте when (не цепочку if).", "90 — уже «отлично», 60 — уже «зачёт»."],
         hints("Заголовок: fun grade(score: Int): String.",
               "when без аргумента: when { условие -> результат }.",
               "Ветки проверяются сверху вниз — начните с самого строгого условия.",
               "Последняя ветка — else -> \"незачёт\".",
               "fun grade(score: Int): String = when {\n    score >= 90 -> \"отлично\"\n    score >= 60 -> \"зачёт\"\n    else -> \"незачёт\"\n}"),
         t2, S2, "when проверяет ветки сверху вниз и возвращает результат первой подходящей; else — для остальных.",
         ["Используется when с else.", "Границы 90 и 60 включены."],
         [('fun grade(score: Int): String {\n    if (score >= 90) return "отлично"\n    if (score >= 60) return "зачёт"\n    return "незачёт"\n}\n',
           "Работает, но задание — на when."),
          ('fun grade(score: Int) = when {\n    score >= 90 -> "отлично"\n    score >= 60 -> "зачёт"\n    else -> "незачёт"\n}\n',
           "Не указан тип результата String."),
          ('fun grade(score: Int): String = when {\n    score >= 90 -> "отлично"\n    score >= 60 -> "зачёт"\n}\n',
           "Нет ветки else — Kotlin не скомпилирует when без неё."),
          ('fun grade(score: String): String = when {\n    else -> "незачёт"\n}\n', "Параметр должен быть Int.")],
         starter="// Функция grade через when\n")

# --- Задание 3: исправить синтаксис -----------------------------------------------------------
STARTER3 = 'fun add(a: Int, b: Int): Int {\n    return a + b\n\nfun main() {\n    val total = add(2, 3)\n    println("Сумма: $total"\n}\n'
S3 = 'fun add(a: Int, b: Int): Int {\n    return a + b\n}\n\nfun main() {\n    val total = add(2, 3)\n    println("Сумма: $total")\n}\n'
t3 = {"kind": "kotlin", "cases": [
    {"id": "syntax", "type": "syntax"},
    {"id": "add", "type": "function", "name": "add", "paramTypes": ["Int", "Int"], "returns": "Int"},
    {"id": "main", "type": "function", "name": "main", "paramTypes": []},
    {"id": "call", "hidden": True, "type": "contains", "pattern": "add\\s*\\(\\s*2\\s*,\\s*3\\s*\\)", "message": "main должна вызывать add(2, 3)"},
], "jvm": {"main": "", "expected_stdout": "Сумма: 5"}}
a3 = asg("a3-fix", "fix", "Две потерянные скобки",
         "Программа должна напечатать `Сумма: 5`, но не компилируется. Найдите и исправьте **две** синтаксические ошибки.",
         "Читать сообщения о синтаксических ошибках.", "—", "Программа без синтаксических ошибок.",
         ["Не меняйте логику — только скобки."],
         hints("Нажмите «Запустить»: приложение покажет первую ошибку и её строку.",
               "У каждой { должна быть своя }.",
               "Где заканчивается функция add?",
               "У println тоже должна закрыться круглая скобка.",
               "Добавьте } после return a + b и ) в конце println(\"Сумма: $total\")."),
         t3, S3, "Функция add не была закрыта фигурной скобкой, а вызов println — круглой.",
         ["Код компилируется.", "Функции add и main на месте."],
         [('fun add(a: Int, b: Int): Int {\n    return a + b\n}\n\nfun main() {\n    val total = add(2, 3)\n    println("Сумма: $total"\n}\n',
           "Исправлена только фигурная скобка."),
          ('fun add(a: Int, b: Int): Int {\n    return a + b\n\nfun main() {\n    val total = add(2, 3)\n    println("Сумма: $total")\n}\n',
           "Исправлена только круглая скобка."),
          ('fun main() {\n    println("Сумма: 5")\n}\n', "Функцию add удалили — задача была исправить ошибки.")],
         starter=STARTER3)

# --- Задание 4: data class и filter --------------------------------------------------------------
S4 = ("data class Book(val title: String, val year: Int)\n\n"
      "fun oldBooks(books: List<Book>): List<Book> = books.filter { it.year < 1900 }\n")
t4 = {"kind": "kotlin", "cases": [
    {"id": "syntax", "type": "syntax"},
    {"id": "cls", "type": "class", "name": "Book", "kind": "data class"},
    {"id": "fn", "type": "function", "name": "oldBooks", "paramTypes": ["List<Book>"], "returns": "List<Book>"},
    {"id": "props", "hidden": True, "type": "contains", "pattern": "data\\s+class\\s+Book\\s*\\(\\s*val\\s+title\\s*:\\s*String\\s*,\\s*val\\s+year\\s*:\\s*Int\\s*\\)",
     "message": "У Book два свойства: val title: String и val year: Int"},
    {"id": "loop", "hidden": True, "type": "contains", "pattern": "\\bfilter\\b|\\bfor\\b", "message": "Отберите книги: filter или цикл for"},
], "jvm": {"main": 'fun main() {\n    val b = listOf(Book("Онегин", 1833), Book("Мастер", 1967), Book("Анна", 1878), Book("Ровно", 1900))\n'
                   '    println(oldBooks(b).map { it.title })\n    println(oldBooks(listOf()).size)\n}',
           "expected_stdout": "[Онегин, Анна]\n0"}}
a4 = asg("a4-books", "write", "Старые книги",
         "1. Объявите `data class Book` со свойствами `title: String` и `year: Int` (оба `val`).\n"
         "2. Напишите функцию `oldBooks(books: List<Book>): List<Book>`, которая возвращает только книги, "
         "написанные **раньше 1900 года**.",
         "Описывать данные классом data class и фильтровать список.", "Список книг.", "Список книг до 1900 года.",
         ["1900 год уже не подходит."],
         hints("data class Book(val title: String, val year: Int).",
               "Тип списка книг — List<Book>.",
               "filter оставляет элементы, для которых условие в фигурных скобках истинно.",
               "Внутри filter текущая книга — it, год — it.year.",
               "fun oldBooks(books: List<Book>): List<Book> = books.filter { it.year < 1900 }"),
         t4, S4, "data class хранит данные; filter { it.year < 1900 } возвращает новый список подходящих книг.",
         ["Book — data class с двумя свойствами.", "oldBooks возвращает List<Book>."],
         [("class Book(val title: String, val year: Int)\n\nfun oldBooks(books: List<Book>): List<Book> = books.filter { it.year < 1900 }\n",
           "Нужен именно data class."),
          ("data class Book(val title: String, val year: Int)\n\nfun oldBooks(books: List<Book>): List<String> = books.filter { it.year < 1900 }.map { it.title }\n",
           "Функция должна возвращать книги, а не названия."),
          ("data class Book(val title: String, val year: String)\n\nfun oldBooks(books: List<Book>): List<Book> = books\n",
           "year должен быть Int, и книги нужно отобрать."),
          ("data class Book(val title: String, val year: Int)\n", "Нет функции oldBooks.")],
         starter="// data class Book и функция oldBooks\n")

# --- Задание 5: предсказать вывод ----------------------------------------------------------------
CODE5 = 'fun main() {\n    val nums = listOf(3, 8, 1)\n    var sum = 0\n    for (n in nums) {\n        if (n > 2) sum += n\n    }\n    println("Сумма: $sum")\n}\n'
a5 = asg("a5-predict", "predict", "Что напечатает программа?",
         "Что выведет программа? Напишите строку вывода целиком.",
         "Читать цикл и условие на Kotlin.", "—", "Одна строка.", [],
         hints("Цикл проходит по 3, 8 и 1.",
               "В сумму попадают только числа больше 2.",
               "1 не больше 2.",
               "3 + 8 = 11.",
               "Ответ: Сумма: 11"),
         {"kind": "answer", "expected_answer": "Сумма: 11"}, "Сумма: 11",
         "Условие n > 2 пропускает 3 и 8; единица отбрасывается. $sum подставляет 11.",
         ["Строка целиком, как выведет программа."],
         [("Сумма: 12", "Единица не больше 2 — она не прибавляется."),
          ("11", "Программа печатает строку целиком: «Сумма: 11»."),
          ("Сумма: $sum", "Знак $ в строке подставляет значение переменной.")],
         code=CODE5)

skills = {"kt.basics": "Kotlin: main, val и var", "kt.functions": "Функции и типы", "kt.when": "when и циклы",
          "kt.data": "data class и списки", "kt.syntax": "Синтаксические ошибки"}
write_pack("kotlin-basics", 12, "Kotlin для Андроида",
           "Язык Андроида: типы, функции, when, data class. На телефоне — проверка синтаксиса и структуры, запуск — в GitHub Actions. Пилот этапа 12.",
           "kotlin", ["kt-01-basics"], skills)
write_lesson("kt-01-basics", "Kotlin: первые шаги",
             "Писать функции с типами, использовать when, циклы и data class; исправлять синтаксические ошибки.",
             list(skills), [], scenes, notes, [a1, a2, a3, a4, a5],
             [{"mistake": "Нет типа результата функции", "fix": "Пишите тип после скобок: fun f(x: Int): Int."},
              {"mistake": "Изменение val", "fix": "val нельзя переназначить — используйте var."},
              {"mistake": "when без else", "fix": "Если ветки не покрывают все случаи, добавьте else ->."},
              {"mistake": "Незакрытая скобка", "fix": "Приложение показывает строку синтаксической ошибки: проверьте пары скобок."},
              {"mistake": "Тип Double вместо Int", "fix": "Int — целое, Double — дробное: они не взаимозаменяемы."}],
             min_pass=3, pack="kotlin-basics", runner="kotlin")
