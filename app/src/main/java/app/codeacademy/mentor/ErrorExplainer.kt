package app.codeacademy.mentor

/**
 * Разбор ошибок без нейросети: тип исключения + строка + шаблон → объяснение по-русски,
 * направление исправления и навык (для ссылки на урок). Исправленный код не выдаётся.
 */
object ErrorExplainer {

    data class Analysis(
        val type: String,
        val message: String,
        val line: Int?,
        val lineText: String?,
        val explanation: String,
        val fix: String,
        val skill: String?,
    ) {
        fun render(): String = buildString {
            append("**$type**")
            if (line != null) append(" в строке $line")
            lineText?.takeIf { it.isNotBlank() }?.let { append(":\n```\n").append(it.trim()).append("\n```\n") } ?: append(".\n")
            append(explanation)
            append("\n\n**Что проверить:** ").append(fix)
        }
    }

    private class Rule(
        val type: Regex,
        val message: Regex?,
        val skill: String?,
        val explain: (MatchResult?, Ctx) -> Pair<String, String>,
    )

    /** Данные для шаблонов: код ученика, язык, разобранная строка. */
    class Ctx(val code: String, val language: String, val lineText: String?)

    private fun r(type: String, message: String?, skill: String?, explain: (MatchResult?, Ctx) -> Pair<String, String>) =
        Rule(Regex(type), message?.let { Regex(it, RegexOption.IGNORE_CASE) }, skill, explain)

    private fun t(explanation: String, fix: String): (MatchResult?, Ctx) -> Pair<String, String> = { _, _ -> explanation to fix }

    private val PY_BUILTINS = listOf(
        "print", "input", "int", "str", "float", "len", "range", "list", "dict", "set", "tuple", "sum", "min", "max", "abs",
        "round", "sorted", "enumerate", "zip", "open", "bool", "type", "isinstance", "True", "False", "None", "append",
    )
    private val JS_BUILTINS = listOf("console", "document", "window", "Math", "JSON", "Number", "String", "Array", "parseInt", "parseFloat", "let", "const")

    private val RULES: List<Rule> = listOf(
        // ---- Python: синтаксис ----
        r("IndentationError", "expected an indented block", "python.errors.indentation",
            t("После строки с двоеточием (`if`, `for`, `while`, `def`, `else`) Python ждёт блок с отступом, а следующая строка начинается без него.",
                "строка после двоеточия должна быть сдвинута вправо на 4 пробела — так Python понимает, что она внутри блока.")),
        r("IndentationError", "unexpected indent", "python.errors.indentation",
            t("Строка сдвинута вправо, хотя блок здесь не начинается.", "уберите лишний отступ: строки одного уровня должны начинаться с одной позиции.")),
        r("IndentationError|TabError", "unindent|inconsistent|tabs", "python.errors.indentation",
            t("Отступы в блоке не совпадают: строки одного блока сдвинуты на разное число пробелов (или смешаны пробелы и табуляция).",
                "выровняйте строки блока одинаково, лучше по 4 пробела, без табуляции.")),
        r("SyntaxError", "expected ':'", "python.errors.syntax",
            t("В конце строки с `if`, `elif`, `else`, `for`, `while`, `def` или `class` нужно двоеточие.", "посмотрите на конец указанной строки — не пропущено ли `:`.")),
        r("SyntaxError", "unterminated string|EOL while scanning|unterminated triple", "python.errors.syntax",
            t("Строка в кавычках не закрыта: Python дошёл до конца строки и не нашёл парную кавычку.", "проверьте, что каждая открывающая кавычка закрыта такой же кавычкой.")),
        r("SyntaxError", "was never closed|unexpected EOF|EOF while parsing", "python.errors.syntax",
            t("Открытая скобка не закрыта: Python дошёл до конца программы, ожидая `)`, `]` или `}`.", "посчитайте скобки в указанной строке и выше — у каждой `(` должна быть пара.")),
        r("SyntaxError", "unmatched|closing parenthesis", "python.errors.syntax",
            t("Лишняя или не та закрывающая скобка.", "проверьте, что скобки идут парами и закрываются в обратном порядке: `( [ ] )`.")),
        r("SyntaxError", "Missing parentheses in call to 'print'", "python.errors.syntax",
            t("В Python 3 `print` — функция: аргументы пишутся в круглых скобках.", "окружите то, что выводите, скобками.")),
        r("SyntaxError", "invalid character|invalid non-printable", "python.errors.syntax",
            t("В коде символ, которого нет в Python: часто это «ёлочки» «», типографские кавычки “ ”, длинное тире или неразрывный пробел, попавшие при копировании.",
                "перепечатайте кавычки и знаки в указанной строке с клавиатуры.")),
        r("SyntaxError", "cannot assign to|can't assign to|Maybe you meant '=='", "python.errors.syntax",
            t("Присваивание там, где нужно сравнение (или слева от `=` стоит не переменная).", "для сравнения нужно `==`; одно `=` кладёт значение в переменную слева.")),
        r("SyntaxError", "invalid decimal literal", "python.errors.syntax",
            t("Число сразу переходит в буквы: например, имя переменной начинается с цифры или между числом и словом нет оператора.",
                "имена не могут начинаться с цифры; между числом и именем нужен оператор (например, `*`).")),
        r("SyntaxError", "f-string", "python.strings.fstring",
            t("Ошибка внутри f-строки: незакрытая `{` или выражение в фигурных скобках записано неверно.", "у каждой `{` должна быть `}`, внутри — имя переменной или выражение.")),
        r("SyntaxError", null, "python.errors.syntax",
            t("Python не смог разобрать строку: нарушены правила записи языка.",
                "частые причины — пропущенное двоеточие, незакрытая скобка или кавычка, `=` вместо `==`. Начните с указанной строки и строки над ней.")),
        // ---- Python: выполнение ----
        r("NameError", "name '([^']+)' is not defined", "python.errors.name") { m, c ->
            val name = m?.groupValues?.get(1).orEmpty()
            val similar = similarName(name, identifiers(c.code) + PY_BUILTINS)
            "Python не знает имени `$name`: переменная ещё не создана, создана ниже по коду или в имени опечатка." to
                (similar?.let { "в коде есть похожее имя `$it` — возможно, опечатка (Python различает большие и маленькие буквы). " }.orEmpty() +
                    "Переменная должна получить значение раньше, чем её используют. Если это текст, а не имя, — возьмите его в кавычки.")
        },
        r("UnboundLocalError", null, null,
            t("Внутри функции переменная используется до того, как ей присвоили значение в этой функции.",
                "передайте значение в функцию параметром или присвойте его внутри функции до использования.")),
        r("TypeError", "can only concatenate str \\(not \"(\\w+)\"\\) to str|unsupported operand type\\(s\\) for \\+: '(int|float)' and 'str'|unsupported operand type\\(s\\) for \\+: 'str' and '(int|float)'", "python.errors.type",
            t("Складываются строка и число. `+` для строк склеивает текст, для чисел — складывает, а смешивать их нельзя. Частая причина — `input()` возвращает строку.",
                "решите, что нужно: число — преобразуйте строку через `int()`/`float()`; текст — преобразуйте число через `str()` или используйте f-строку.")),
        r("TypeError", "unsupported operand type", "python.errors.type",
            t("Операция не подходит для этих типов данных (например, вычитание строк или умножение списка на дробь).", "посмотрите, какие типы у значений в указанной строке; возможно, строку нужно сначала превратить в число.")),
        r("TypeError", "'(\\w+)' not supported between instances of '(\\w+)' and '(\\w+)'", "python.errors.type") { m, _ ->
            "Сравниваются значения разных типов (`${m?.groupValues?.get(2)}` и `${m?.groupValues?.get(3)}`): Python не знает, что больше — текст или число." to
                "приведите значения к одному типу, например число из `input()` — через `int()`."
        },
        r("TypeError", "'(\\w+)' object is not callable", "python.errors.type") { m, _ ->
            "Значение типа `${m?.groupValues?.get(1)}` вызывается как функция (после него стоят скобки). Часто это значит, что имя функции перезаписано переменной, например `print = ...` или `sum = 0`." to
                "не называйте переменные именами встроенных функций; проверьте, нет ли лишних скобок."
        },
        r("TypeError", "'(\\w+)' object is not subscriptable", "python.errors.type") { m, _ ->
            "Квадратные скобки применены к значению типа `${m?.groupValues?.get(1)}`, у которого нет элементов по номеру." to
                (if (m?.groupValues?.get(1) == "NoneType") "значение равно `None` — часто функция ничего не вернула (`return` забыт) или метод изменяет список на месте и возвращает `None`."
                else "проверьте, что в переменной список, строка или словарь, а не число.")
        },
        r("TypeError", "'str' object does not support item assignment", "python.strings.methods",
            t("Строки нельзя менять по одному символу: строка неизменяема.", "соберите новую строку (срезы, `replace`, склеивание) и присвойте её переменной.")),
        r("TypeError", "(\\w+)\\(\\) takes (\\d+) positional arguments? but (\\d+) (were|was) given", null) { m, _ ->
            "Функция `${m?.groupValues?.get(1)}` принимает ${m?.groupValues?.get(2)} аргумент(а), а передано ${m?.groupValues?.get(3)}." to
                "сравните число параметров в `def` с числом значений в вызове."
        },
        r("TypeError", "missing (\\d+) required positional argument", null,
            t("При вызове функции передано меньше значений, чем параметров в её определении.", "сравните параметры в `def` и аргументы в вызове.")),
        r("TypeError", "object of type '(\\w+)' has no len", "python.errors.type",
            t("`len()` считает элементы строки, списка или словаря, а у числа длины нет.", "проверьте тип значения; число можно превратить в строку через `str()`.")),
        r("TypeError", "list indices must be integers|string indices must be integers", "python.errors.type",
            t("Номер элемента в квадратных скобках должен быть целым числом, а передана строка или дробь.", "если номер пришёл из `input()`, преобразуйте его через `int()`.")),
        r("TypeError", null, "python.errors.type",
            t("Операция применена к значению неподходящего типа.", "посмотрите, какого типа значения в указанной строке: `print(type(x))` поможет это выяснить.")),
        r("ValueError", "invalid literal for int\\(\\) with base 10: '([^']*)'", "python.errors.value") { m, _ ->
            "`int()` не может превратить в целое число текст «${m?.groupValues?.get(1)}»." to
                "в строке должно быть только целое число. Если там дробь — используйте `float()`; если пробелы — уберите их через `strip()`; проверьте, что вводятся именно числа."
        },
        r("ValueError", "could not convert string to float", "python.errors.value",
            t("`float()` получил текст, который не похож на число.", "дробная часть отделяется точкой, а не запятой; в строке не должно быть лишних символов.")),
        r("ValueError", "too many values to unpack|not enough values to unpack", "python.errors.value",
            t("Слева от `=` переменных больше или меньше, чем значений справа.", "посчитайте: сколько переменных и сколько значений получается (например, после `split()`).")),
        r("ValueError", "not in list", "python.lists",
            t("Искомого значения нет в списке (`index` или `remove` не нашли его).", "сначала проверьте наличие: `if x in список:`.")),
        r("ValueError", null, "python.errors.value",
            t("Тип значения подходит, но само значение недопустимо для операции.", "посмотрите, какое значение пришло в указанную строку.")),
        r("IndexError", "out of range", "python.errors.index",
            t("Обращение к элементу по номеру, которого нет. Нумерация начинается с 0, последний элемент — `len(...) - 1`.",
                "проверьте границы: цикл или индекс не должны выходить за длину. Пустой список не имеет даже элемента `[0]`.")),
        r("KeyError", null, null,
            t("В словаре нет такого ключа.", "проверьте написание ключа (регистр, пробелы) или используйте `in` / `.get()` перед обращением.")),
        r("AttributeError", "'(\\w+)' object has no attribute '(\\w+)'", null) { m, c ->
            val type = m?.groupValues?.get(1).orEmpty()
            val attr = m?.groupValues?.get(2).orEmpty()
            "У значения типа `$type` нет метода или свойства `$attr`." to
                (if (type == "NoneType") "значение равно `None`: возможно, функция ничего не вернула или метод вроде `sort()` изменил список на месте и вернул `None`."
                else similarName(attr, identifiers(c.code) + listOf("append", "split", "strip", "lower", "upper", "replace", "join", "items", "keys", "values", "get", "sort", "count", "index", "pop", "insert", "remove", "format", "startswith", "endswith"))
                    ?.let { "возможно, имелось в виду `$it`." } ?: "проверьте написание имени и тип значения.")
        },
        r("ZeroDivisionError", null, "python.numbers",
            t("Деление на ноль.", "перед делением проверьте делитель, например `if n != 0:`; подумайте, что программа должна делать в этом случае.")),
        r("EOFError", null, "python.input",
            t("Программа вызывает `input()` больше раз, чем есть строк ввода.", "сравните число вызовов `input()` с описанием входных данных в задании; лишний `input()` в цикле — частая причина.")),
        r("RecursionError", null, null,
            t("Функция вызывает сама себя без остановки.", "у рекурсии должно быть условие выхода, которое обязательно срабатывает.")),
        r("ModuleNotFoundError|ImportError", null, null,
            t("Модуль не найден. Приложение работает без интернета: доступна стандартная библиотека Python и модули, встроенные в курс.",
                "проверьте написание имени модуля; сторонние пакеты установить нельзя.")),
        r("FileNotFoundError", null, null,
            t("Файл с таким именем не найден в папке проекта.", "проверьте имя и расширение файла; путь задаётся относительно папки проекта.")),
        r("AssertionError", null, null,
            t("Не выполнилась проверка `assert` — условие оказалось ложным.", "посмотрите, какое значение проверялось, и сравните с ожидаемым.")),
        r("Timeout|InfiniteLoopError", null, null,
            t("Программа работала дольше лимита — чаще всего это бесконечный цикл: условие `while` никогда не становится ложным.",
                "убедитесь, что внутри цикла меняется переменная из условия и цикл может закончиться.")),
        r("MemoryError|CRASHED", null, null,
            t("Программе не хватило памяти — обычно из-за бесконечного роста списка или строки в цикле.", "проверьте, что цикл заканчивается и не добавляет элементы без конца.")),
        // ---- JavaScript ----
        r("ReferenceError", "([\\w$]+) is not defined", "js.basics") { m, c ->
            val name = m?.groupValues?.get(1).orEmpty()
            val similar = similarName(name, identifiers(c.code) + JS_BUILTINS)
            "JavaScript не знает имени `$name`: переменная не объявлена или в имени опечатка." to
                (similar?.let { "похожее имя в коде — `$it`. " }.orEmpty() + "Объявите переменную через `let` или `const` до использования.")
        },
        r("ReferenceError", "before initialization", "js.basics",
            t("Переменная `let`/`const` используется выше строки, где она объявлена.", "перенесите объявление выше места использования.")),
        r("TypeError", "Assignment to constant variable", "js.basics",
            t("Переменной, объявленной через `const`, нельзя присвоить новое значение.", "если значение меняется, объявите переменную через `let`.")),
        r("TypeError", "Cannot read propert(y|ies) of (null|undefined)", "js.dom") { m, _ ->
            "Обращение к свойству у значения `${m?.groupValues?.get(2)}`: самого объекта нет." to
                (if (m?.groupValues?.get(2) == "null") "часто `document.querySelector`/`getElementById` не нашёл элемент: проверьте селектор, id и что скрипт выполняется после разметки."
                else "проверьте, что переменная получила значение, а у объекта есть такое поле.")
        },
        r("TypeError", "is not a function", null,
            t("Вызывается как функция то, что функцией не является: опечатка в имени метода или переменная перезаписана.", "проверьте написание имени и регистр букв (`getElementById`, а не `getElementByID`).")),
        r("SyntaxError", "Неожиданный|Недопустимый|не закрыт|Unexpected", "web.errors",
            t("JavaScript не смог разобрать код в указанной строке.", "проверьте парность скобок `(){}[]` и кавычек; лишняя или пропущенная скобка — самая частая причина.")),
        // ---- SQL ----
        r("SQLError", "no such table: (\\w+)", "sql.select") { m, _ ->
            "Таблицы `${m?.groupValues?.get(1)}` нет в базе." to "проверьте имя таблицы в задании (единственное/множественное число, опечатки)."
        },
        r("SQLError", "no such column: ([\\w.]+)", "sql.select") { m, _ ->
            "Столбца `${m?.groupValues?.get(1)}` нет в таблице." to "сверьте имя столбца со схемой; текстовые значения пишутся в одинарных кавычках — иначе SQL принимает слово за имя столбца."
        },
        r("SQLError", "ambiguous column", "sql.select",
            t("Столбец с таким именем есть в нескольких таблицах запроса.", "укажите таблицу явно: `таблица.столбец`.")),
        r("SQLError", "UNIQUE constraint", "sql.update",
            t("Вставляется значение, которое уже есть в уникальном столбце.", "проверьте, нет ли уже такой записи.")),
        r("SQLError", "NOT NULL constraint", "sql.update",
            t("Обязательный столбец остался пустым.", "передайте значение для указанного столбца.")),
        r("SQLError", "misuse of aggregate", "sql.select",
            t("Агрегатная функция (`COUNT`, `SUM`, …) использована там, где её нельзя применять, например в `WHERE`.", "условия на результат агрегата пишутся в `HAVING` после `GROUP BY`.")),
        r("SQLError", "syntax error|incomplete input|unrecognized token", "sql.select",
            t("SQL не смог разобрать запрос.", "проверьте порядок частей (`SELECT … FROM … WHERE … ORDER BY …`), запятые между столбцами и закрытые кавычки.")),
        // ---- Kotlin (синтаксическая проверка) ----
        r("Синтаксическая ошибка", null, "kt.syntax",
            t("Kotlin не смог разобрать код в указанной строке.", "проверьте парность фигурных и круглых скобок, кавычки и ключевые слова (`fun`, `val`, `var`).")),
        // ---- Неверный результат ----
        r("WrongResult", null, null,
            t("Программа выполнилась без ошибок, но вывод не совпал с ожидаемым.",
                "сравните «Ожидалось» и «Получено» посимвольно: пробелы, регистр, знаки препинания, лишние подсказки в `input()`.")),
    )

    private val TYPE_RE = Regex("((?:[A-Z][A-Za-z]*)?(?:Error|Exception))(?::\\s*(.*))?")
    private val PY_LINE = Regex("File \"([^\"]+)\", line (\\d+)")
    private val GENERIC_LINE = Regex("(?:line|строка|строке)\\s+(\\d+)", RegexOption.IGNORE_CASE)

    /** Разбор текста ошибки. null — текст не похож на ошибку. */
    fun analyze(error: String, code: String, language: String): Analysis? {
        val text = error.trim()
        if (text.isEmpty()) return null
        val lines = text.lines()
        // Последняя строка вида «Тип: сообщение» (Python печатает её внизу traceback).
        var type: String? = null
        var message = ""
        for (l in lines.asReversed()) {
            val m = TYPE_RE.find(l.trim()) ?: continue
            if (m.range.first > 0 && l.trim()[m.range.first - 1].isLetterOrDigit()) continue
            type = m.groupValues[1]
            message = m.groupValues[2].trim()
            break
        }
        if (type == null) {
            type = when {
                text.startsWith("Синтаксическая ошибка") -> "Синтаксическая ошибка"
                text == "Timeout" || text.contains("Превышено время") -> "Timeout"
                text == "WrongResult" -> "WrongResult"
                text == "CRASHED" -> "CRASHED"
                else -> return null
            }
            message = text.lines().first()
        }
        // Номер строки: последняя ссылка на файл ученика (не на внутренности песочницы).
        val lineNo = PY_LINE.findAll(text).lastOrNull { m -> !m.groupValues[1].startsWith("<") && "ca_runner" !in m.groupValues[1] }
            ?.groupValues?.get(2)?.toIntOrNull()
            ?: GENERIC_LINE.findAll(text).lastOrNull()?.groupValues?.get(1)?.toIntOrNull()
        val codeLines = code.lines()
        val lineText = lineNo?.let { codeLines.getOrNull(it - 1) }
        val ctx = Ctx(code, language, lineText)
        val full = "$type: $message"
        val rule = RULES.firstOrNull { rl ->
            rl.type.matches(type) && (rl.message == null || rl.message.containsMatchIn(full)) && langOk(rl, language)
        } ?: return Analysis(type, message, lineNo, lineText,
            "Программа остановилась с ошибкой `$type`." + (if (message.isNotBlank()) " Сообщение: «$message»." else ""),
            "прочитайте сообщение и посмотрите на указанную строку: что в ней за значения и какого они типа.", null)
        val match = rule.message?.find(full)
        val (explanation, fix) = rule.explain(match, ctx)
        return Analysis(type, message, lineNo, lineText, explanation, fix, rule.skill)
    }

    private fun langOk(rule: Rule, language: String): Boolean {
        val s = rule.skill ?: return true
        val lang = s.substringBefore('.')
        return when (language) {
            "python" -> lang == "python"
            "js", "html" -> lang == "js" || lang == "web"
            "sql" -> lang == "sql"
            "kotlin" -> lang == "kt"
            else -> true
        }
    }

    fun identifiers(code: String): List<String> =
        Regex("[A-Za-z_][A-Za-z0-9_]*").findAll(code).map { it.value }.distinct().toList()

    /** Похожее имя (опечатка): расстояние Левенштейна ≤ 2, без учёта регистра — 0. */
    fun similarName(name: String, candidates: List<String>): String? {
        if (name.length < 2) return null
        return candidates.asSequence().filter { it != name }
            .map { it to levenshtein(name.lowercase(), it.lowercase()) }
            .filter { (c, d) -> d <= (if (name.length <= 4) 1 else 2) && kotlin.math.abs(c.length - name.length) <= 2 }
            .minByOrNull { it.second }?.first
    }

    /** Расстояние редактирования с перестановкой соседних букв («nmae» → «name» = 1). */
    fun levenshtein(a: String, b: String): Int {
        val d = Array(a.length + 1) { i -> IntArray(b.length + 1) { j -> if (i == 0) j else if (j == 0) i else 0 } }
        for (i in 1..a.length) for (j in 1..b.length) {
            val cost = if (a[i - 1] == b[j - 1]) 0 else 1
            d[i][j] = minOf(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + cost)
            if (i > 1 && j > 1 && a[i - 1] == b[j - 2] && a[i - 2] == b[j - 1]) d[i][j] = minOf(d[i][j], d[i - 2][j - 2] + 1)
        }
        return d[a.length][b.length]
    }
}
