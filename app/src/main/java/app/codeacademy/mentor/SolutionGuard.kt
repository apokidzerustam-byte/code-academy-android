package app.codeacademy.mentor

/**
 * Защита от выдачи готового решения. Проверяет любой текст наставника (правила, материалы курса,
 * ответ модели) по эталону задания. Эталон известен только защите: в запрос модели он не передаётся,
 * поэтому, кроме совпадения с эталоном, ловится и «своё» решение модели (новый код, почти все имена
 * и значения эталона).
 *
 * Сравнение устойчиво к оформлению: код в `обратных кавычках` внутри текста, регистр букв (SQL, HTML),
 * пробелы и вид кавычек, переименованные переменные (для длинных строк), отступы fix-заданий.
 */
class SolutionGuard(
    private val task: TaskContext,
    /** Текст, который ученик уже видит или написал сам: его повтор не считается подсказкой решения. */
    visible: List<String>,
) {
    data class Verdict(val leak: Boolean, val reason: String = "") {
        companion object { val OK = Verdict(false) }
    }

    private val solutionText = task.solutionFiles.values.joinToString("\n")
    private val baseText = (task.starterFiles.values + task.statement + visible).joinToString("\n")
    private val baseLines = codeLines(baseText).toSet()
    private val baseAnon = codeLines(baseText).map(::anon).toSet()
    private val baseGrams = ngrams(tokens(baseText))
    private val baseAnonGrams = ngrams(tokens(baseText).map(::anonToken), 8)

    private val solutionLines = codeLines(solutionText)

    /** Новые (не из заготовки/условия) 6-граммы эталона и 8-граммы с обезличенными именами. */
    private val novelGrams: Set<String> = ngrams(tokens(solutionText)) - baseGrams
    private val novelAnonGrams: Set<String> = ngrams(tokens(solutionText).map(::anonToken), 8) - baseAnonGrams

    /** Строки эталона, которых нет в заготовке: показать любую из них — значит раскрыть решение. */
    private val novelLines: List<String> = solutionLines.filter { it !in baseLines && it.split(' ').size >= 3 && meaningful(it) }

    /**
     * Слова строк эталона без знаков препинания и вида кавычек: ловит ту же строку, записанную иначе
     * (`return "Привет, " + name + "!"` вместо шаблона в обратных кавычках). Только строки из трёх и более разных слов.
     */
    private val novelBags: List<Set<String>> =
        solutionLines.filter { it !in baseLines && meaningful(it) }.map(::words).filter { it.size >= 3 }.distinct()

    /** Длинные строки эталона с обезличенными именами: ловят переименование переменных. */
    private val novelAnonLines: List<String> = solutionLines.map(::anon).filter { it !in baseAnon && it.split(' ').size >= 6 }

    /** Исправление только отступа (fix-задания): строка эталона с отступом, которого нет в заготовке. */
    private val reindented: List<String> = run {
        val starterRaw = task.starterFiles.values.flatMap { it.lines() }.map { it.trimEnd() }.toSet()
        val starterTrim = starterRaw.map { it.trim() }.toSet()
        solutionText.lines().map { it.trimEnd() }
            .filter { it.isNotBlank() && it !in starterRaw && it.trim() in starterTrim && it.first().isWhitespace() }
    }

    /**
     * Исправление только регистра (`Planet` → `planet`): при сравнении без учёта регистра строка совпадает
     * с заготовкой, поэтому такие строки эталона проверяются отдельно, с учётом регистра.
     */
    private val recased: List<String> = run {
        val baseCs = codeLines(baseText, lower = false).toSet()
        codeLines(solutionText, lower = false).filter { it !in baseCs && it.lowercase() in baseLines && it.split(' ').size >= 3 }
    }

    /** Имена и значения эталона, которых нет в заготовке и условии. */
    private val novelNames: Set<String> = run {
        val base = tokens(baseText).toSet()
        tokens(solutionText).filter { isName(it) && it.length >= 2 && it !in base && it !in KEYWORDS }.toSet()
    }

    private val answerLines: List<String> =
        task.expectedAnswer?.trim()?.lines()?.map { it.trim() }?.filter { it.isNotEmpty() }.orEmpty()

    /** Значимые части ожидаемого вывода (числа, слова, элементы списков) — по порядку. */
    private val answerAtoms: List<String> = ATOM.findAll(answerLines.joinToString("\n").lowercase()).map { it.value }.toList()

    fun check(text: String): Verdict {
        if (text.isBlank()) return Verdict.OK
        if (task.isAnswerTask && answerLines.isNotEmpty()) answerLeak(text)?.let { return Verdict(true, it) }
        if (solutionText.isBlank()) return Verdict.OK
        if (reindented.isNotEmpty()) {
            val raw = text.lines().map { it.trimEnd() }.toSet()
            reindented.firstOrNull { it in raw }?.let { return Verdict(true, "исправленный отступ: ${it.trim()}") }
        }
        if (recased.isNotEmpty()) {
            val cs = " " + tokens(text, lower = false).joinToString(" ") + " "
            recased.firstOrNull { cs.contains(" $it ") }?.let { return Verdict(true, "исправленная строка: $it") }
        }
        val replyTokens = tokens(text)
        val joined = " " + replyTokens.joinToString(" ") + " "
        novelLines.firstOrNull { joined.contains(" $it ") }?.let { return Verdict(true, "строка решения: $it") }
        if (novelBags.isNotEmpty()) {
            for (span in codeSpans(text)) {
                val w = words(span)
                novelBags.firstOrNull { w.containsAll(it) }?.let { return Verdict(true, "строка решения, записанная иначе: ${it.joinToString(" ")}") }
            }
        }
        val anonTokens = replyTokens.map(::anonToken)
        val anonJoined = " " + anonTokens.joinToString(" ") + " "
        novelAnonLines.firstOrNull { anonJoined.contains(" $it ") }?.let { return Verdict(true, "строка решения с другими именами: $it") }
        if (novelGrams.isNotEmpty()) {
            val common = ngrams(replyTokens).count { it in novelGrams }
            val share = common.toDouble() / novelGrams.size
            if ((novelGrams.size >= 3 && share >= 0.35) || common >= 8) {
                return Verdict(true, "совпадение с решением ${(share * 100).toInt()}%")
            }
        }
        if (novelAnonGrams.size >= 3) {
            val share = ngrams(anonTokens, 8).count { it in novelAnonGrams }.toDouble() / novelAnonGrams.size
            if (share >= 0.5) return Verdict(true, "структура решения с другими именами ${(share * 100).toInt()}%")
        }
        val newCode = codeLines(codeOnly(text)).filter { it !in baseLines && it.split(' ').size >= 3 && meaningful(it) }
        if (newCode.size >= MAX_NEW_CODE_LINES || (newCode.size >= 2 && solutionLines.size <= 3)) {
            return Verdict(true, "слишком много готового кода: ${newCode.size} строк")
        }
        if (novelNames.size >= 3 && newCode.isNotEmpty()) {
            val names = newCode.flatMap { it.split(' ') }.toSet()
            val covered = novelNames.count { it in names }
            if (covered.toDouble() / novelNames.size >= 0.8) return Verdict(true, "код повторяет имена и значения решения")
        }
        return Verdict.OK
    }

    /** «Предскажи результат»: нельзя называть ожидаемый вывод ни строками, ни в тексте. */
    private fun answerLeak(text: String): String? {
        val lines = text.lines().map { stripDecor(it) }.filter { it.isNotEmpty() }
        if (answerLines.size >= 2) {
            for (i in 0..lines.size - answerLines.size) {
                if ((answerLines.indices).all { lines[i + it].equals(answerLines[it], ignoreCase = true) }) return "ожидаемый вывод целиком"
            }
        }
        val single = answerLines.singleOrNull() ?: answerLines.joinToString(" ")
        if (lines.any { it.equals(single, ignoreCase = true) }) return "ожидаемый вывод отдельной строкой"
        // Все значимые части ответа по порядку, близко друг к другу («сначала 8, потом 10»).
        if (answerAtoms.size >= 2) {
            val words = ATOM.findAll(text.lowercase()).map { it.value }.toList()
            var pos = -1
            var ok = true
            for ((k, atom) in answerAtoms.withIndex()) {
                val from = pos + 1
                val limit = if (k == 0) words.size else minOf(words.size, from + MAX_ATOM_GAP)
                val idx = (from until limit).firstOrNull { words[it] == atom }
                if (idx == null) { ok = false; break }
                pos = idx
            }
            if (ok) return "все части ожидаемого вывода по порядку"
        }
        val q = Regex.escape(single)
        val quoted = Regex(
            "[«\"'`]\\s*$q\\s*[»\"'`]|(ответ|вывод\\S*|выведет|выводит\\S*|напечата\\S*|печата\\S*|получится|получим|будет|равн\\S*)\\s*(—|-|:|=)?\\s*$q(?![\\p{L}\\d])",
            RegexOption.IGNORE_CASE,
        )
        if (quoted.containsMatchIn(text)) return "ожидаемый вывод назван"
        return null
    }

    companion object {
        const val MAX_NEW_CODE_LINES = 3
        private const val MAX_ATOM_GAP = 8
        private val SPACES = Regex("\\s+")
        private val ATOM = Regex("[\\p{L}\\d_]+(?:\\.[\\p{L}\\d_]+)*")

        private val TOKEN = Regex(
            "[\\p{L}_][\\p{L}\\d_]*|\\d+(?:\\.\\d+)?|\"[^\"\\n]*\"|'[^'\\n]*'|==|!=|<=|>=|\\*\\*|//|->|=>|&&|\\|\\||\\+=|-=|[^\\s\\p{L}\\d_]"
        )
        val KEYWORDS = setOf(
            "def", "return", "if", "else", "elif", "for", "while", "in", "and", "or", "not", "is", "none", "true", "false",
            "print", "input", "int", "str", "float", "len", "range", "list", "dict", "set", "import", "from", "class", "self",
            "function", "const", "let", "var", "console", "log", "fun", "val", "println", "select", "where", "order", "by",
            "group", "having", "limit", "insert", "into", "values", "update", "delete", "join", "on", "as", "asc", "desc",
            "count", "sum", "avg", "min", "max", "null", "document", "html", "head", "body", "div", "p", "main", "string",
            "break", "continue", "pass", "try", "except", "with", "lambda", "new", "this", "async", "await", "append",
            "when", "data", "style", "script", "title", "ul", "li", "h1", "h2", "span", "button",
        )

        /**
         * Токены кода в нижнем регистре; `обратные кавычки` (код в тексте) снимаются;
         * строка в кавычках — один токен с единым видом кавычек и без пробелов внутри.
         */
        fun tokens(text: String, lower: Boolean = true): List<String> = TOKEN.findAll(text.replace('`', ' ')).map {
            val v = if (lower) it.value.lowercase() else it.value
            if (v.length >= 2 && v[0] in "\"'" && v.last() == v[0]) "\"" + v.substring(1, v.length - 1).replace(SPACES, "") + "\"" else v
        }.toList()

        /** Имя переменной/функции (не ключевое слово) → «_»: ловит решение с переименованными переменными. */
        fun anonToken(t: String): String =
            if (t.isNotEmpty() && (t[0].isLetter() || t[0] == '_') && t !in KEYWORDS) "_" else t

        private fun anon(line: String): String = line.split(' ').joinToString(" ") { anonToken(it) }

        fun ngrams(t: List<String>, n: Int = 6): Set<String> =
            if (t.size < n) emptySet() else (0..t.size - n).mapTo(HashSet()) { t.subList(it, it + n).joinToString(" ") }

        /** Строки кода в нормализованном виде (токены через пробел), без пустых и комментариев. */
        fun codeLines(text: String, lower: Boolean = true): List<String> = text.lines().mapNotNull { raw ->
            val l = raw.trim()
            if (l.isEmpty() || l.startsWith("#") || l.startsWith("//") || l.startsWith("--") || l.startsWith("```")) null
            else tokens(l, lower).joinToString(" ").takeIf { it.isNotEmpty() }
        }

        /** Строка несёт смысл: есть имя или значение (не только скобки, `});` или закрывающий тег). */
        private fun meaningful(line: String): Boolean {
            if (line.startsWith("< /")) return false
            return line.split(' ').any { isName(it) }
        }

        private val WORD = Regex("[\\p{L}\\d_]+")

        /** Слова строки в нижнем регистре (имена, ключевые слова, числа и слова внутри строковых литералов). */
        fun words(line: String): Set<String> = WORD.findAll(line.lowercase()).map { it.value }.toSet()

        /** Фрагменты кода в ответе: `код` в тексте и строки кода (блоки ``` и строки, похожие на код). */
        fun codeSpans(text: String): List<String> =
            Regex("`([^`\\n]+)`").findAll(text).map { it.groupValues[1] }.toList() + codeOnly(text).lines().filter { it.isNotBlank() }

        /** Код ответа: блоки ``` и строки, похожие на код. */
        fun codeOnly(text: String): String {
            val out = StringBuilder()
            var inFence = false
            for (line in text.lines()) {
                val t = line.trim()
                if (t.startsWith("```")) { inFence = !inFence; continue }
                if (inFence || looksLikeCode(t)) out.append(line).append('\n')
            }
            return out.toString()
        }

        private val CODE_START = Regex(
            "^(def|for|while|if|elif|else|return|print|import|from|class|try|except|with|fun|val|var|let|const|function|" +
                "select|insert|update|delete|create|console\\.|document\\.|<[a-z!/])", RegexOption.IGNORE_CASE
        )

        fun looksLikeCode(line: String): Boolean {
            if (line.isEmpty()) return false
            if (CODE_START.containsMatchIn(line)) return true
            val cyr = line.count { it in 'а'..'я' || it in 'А'..'Я' }
            if (cyr > line.length / 3) return false
            return Regex("[=;{}]|\\w\\(.*\\)|:\\s*$").containsMatchIn(line)
        }

        private fun isName(t: String) = t.isNotEmpty() && (t[0].isLetter() || t[0] == '_' || t[0] == '"' || t[0].isDigit())
        private fun stripDecor(s: String) = s.trim().trim('`', '«', '»', '"', '\'', '*', '-', '•', '>', ' ', '.')
    }
}
