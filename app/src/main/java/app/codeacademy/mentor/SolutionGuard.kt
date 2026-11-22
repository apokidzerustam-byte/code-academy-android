package app.codeacademy.mentor

/**
 * Защита от выдачи готового решения. Проверяет любой текст наставника (правила, материалы курса,
 * ответ модели) по эталону задания. Эталон известен только защите: в запрос модели он не передаётся,
 * поэтому, кроме совпадения с эталоном, ловится и «своё» решение модели (много нового кода
 * или почти все имена и значения эталона).
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
    private val baseGrams = ngrams(tokens(baseText))

    /** Новые (не из заготовки/условия) 6-граммы эталона. */
    private val novelGrams: Set<String> = ngrams(tokens(solutionText)) - baseGrams

    /** Строки эталона, которых нет в заготовке: показать любую из них — значит раскрыть решение. */
    private val novelLines: List<String> = codeLines(solutionText).filter { it !in baseLines && it.split(' ').size >= 3 }

    /** Имена и значения эталона, которых нет в заготовке и условии. */
    private val novelNames: Set<String> = run {
        val base = tokens(baseText).toSet()
        tokens(solutionText).filter { isName(it) && it !in base && it.lowercase() !in KEYWORDS }.toSet()
    }

    /** Исправление только отступа (fix-задания): строка эталона с отступом, которого нет в заготовке. */
    private val reindented: List<String> = run {
        val starterRaw = task.starterFiles.values.flatMap { it.lines() }.map { it.trimEnd() }.toSet()
        val starterTrim = starterRaw.map { it.trim() }.toSet()
        solutionText.lines().map { it.trimEnd() }
            .filter { it.isNotBlank() && it !in starterRaw && it.trim() in starterTrim && it.first().isWhitespace() }
    }

    private val answerLines: List<String> =
        task.expectedAnswer?.trim()?.lines()?.map { it.trim() }?.filter { it.isNotEmpty() }.orEmpty()

    fun check(text: String): Verdict {
        if (text.isBlank()) return Verdict.OK
        if (task.isAnswerTask && answerLines.isNotEmpty()) answerLeak(text)?.let { return Verdict(true, it) }
        if (solutionText.isBlank()) return Verdict.OK
        if (reindented.isNotEmpty()) {
            val raw = text.lines().map { it.trimEnd() }.toSet()
            reindented.firstOrNull { it in raw }?.let { return Verdict(true, "исправленный отступ: ${it.trim()}") }
        }
        val replyTokens = tokens(text)
        val joined = " " + replyTokens.joinToString(" ") + " "
        novelLines.firstOrNull { joined.contains(" $it ") }?.let { return Verdict(true, "строка решения: $it") }
        if (novelGrams.isNotEmpty()) {
            val common = ngrams(replyTokens).count { it in novelGrams }
            val share = common.toDouble() / novelGrams.size
            if ((novelGrams.size >= 3 && share >= 0.35) || common >= 8) {
                return Verdict(true, "совпадение с решением ${(share * 100).toInt()}%")
            }
        }
        val newCode = codeLines(codeOnly(text)).filter { it !in baseLines && it.split(' ').size >= 3 }
        if (newCode.size >= MAX_NEW_CODE_LINES) return Verdict(true, "слишком много готового кода: ${newCode.size} строк")
        if (novelNames.size >= 3 && newCode.isNotEmpty()) {
            val names = newCode.flatMap { it.split(' ') }.toSet()
            val covered = novelNames.count { it in names }
            if (covered.toDouble() / novelNames.size >= 0.8) return Verdict(true, "код повторяет имена и значения решения")
        }
        return Verdict.OK
    }

    /** «Предскажи результат»: нельзя называть ожидаемый вывод. */
    private fun answerLeak(text: String): String? {
        val lines = text.lines().map { stripDecor(it) }.filter { it.isNotEmpty() }
        if (answerLines.size >= 2) {
            for (i in 0..lines.size - answerLines.size) {
                if ((answerLines.indices).all { lines[i + it] == answerLines[it] }) return "ожидаемый вывод целиком"
            }
            val flat = squash(text)
            if (flat.contains(squash(answerLines.joinToString(" ")))) return "ожидаемый вывод в строку"
            if (flat.contains(squash(answerLines.joinToString(", ")))) return "ожидаемый вывод через запятую"
        }
        val single = answerLines.singleOrNull() ?: answerLines.joinToString(" ")
        if (lines.any { it == single }) return "ожидаемый вывод отдельной строкой"
        val q = Regex.escape(single)
        val quoted = Regex("[«\"'`]\\s*$q\\s*[»\"'`]|(ответ|вывод\\S*|выведет|напечатает|получится|будет)\\s*(—|-|:|=)?\\s*$q(?![\\p{L}\\d])",
            RegexOption.IGNORE_CASE)
        if (quoted.containsMatchIn(text)) return "ожидаемый вывод назван"
        return null
    }

    companion object {
        const val MAX_NEW_CODE_LINES = 5
        private val SPACES = Regex("\\s+")

        private val TOKEN = Regex(
            "[\\p{L}_][\\p{L}\\d_]*|\\d+(?:\\.\\d+)?|\"[^\"\\n]*\"|'[^'\\n]*'|`[^`\\n]*`|==|!=|<=|>=|\\*\\*|//|->|=>|&&|\\|\\||\\+=|-=|[^\\s\\p{L}\\d_]"
        )
        private val KEYWORDS = setOf(
            "def", "return", "if", "else", "elif", "for", "while", "in", "and", "or", "not", "is", "none", "true", "false",
            "print", "input", "int", "str", "float", "len", "range", "list", "dict", "set", "import", "from", "class", "self",
            "function", "const", "let", "var", "console", "log", "fun", "val", "println", "select", "where", "order", "by",
            "group", "having", "limit", "insert", "into", "values", "update", "delete", "join", "on", "as", "asc", "desc",
            "count", "sum", "avg", "min", "max", "null", "document", "html", "head", "body", "div", "p", "main", "string",
            "break", "continue", "pass", "try", "except", "with", "lambda", "new", "this", "async", "await",
        )

        /** Токены кода; строки в кавычках — один токен с единым видом кавычек. */
        fun tokens(text: String): List<String> = TOKEN.findAll(text).map {
            val v = it.value
            if (v.length >= 2 && v[0] in "\"'`" && v.last() == v[0]) "\"" + v.substring(1, v.length - 1).replace(SPACES, "") + "\"" else v
        }.toList()

        fun ngrams(t: List<String>, n: Int = 6): Set<String> =
            if (t.size < n) emptySet() else (0..t.size - n).mapTo(HashSet()) { t.subList(it, it + n).joinToString(" ") }

        /** Строки кода в нормализованном виде (токены через пробел), без пустых и комментариев. */
        fun codeLines(text: String): List<String> = text.lines().mapNotNull { raw ->
            val l = raw.trim()
            if (l.isEmpty() || l.startsWith("#") || l.startsWith("//") || l.startsWith("--") || l.startsWith("```")) null
            else tokens(l).joinToString(" ").takeIf { it.isNotEmpty() }
        }

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

        private fun isName(t: String) = t.length >= 2 && (t[0].isLetter() || t[0] == '_' || t[0] == '"' || t[0].isDigit())
        private fun stripDecor(s: String) = s.trim().trim('`', '«', '»', '"', '\'', '*', '-', '•', '>', ' ')
        private fun squash(s: String) = s.lowercase().replace(Regex("[\\s`«»\"'*]+"), " ").trim()
    }
}
