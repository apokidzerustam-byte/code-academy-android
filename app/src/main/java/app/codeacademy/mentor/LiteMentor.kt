package app.codeacademy.mentor

/**
 * Лёгкий наставник: работает всегда, без модели и без сети. Отвечает материалами курса
 * (подсказки задания, конспекты, частые ошибки) и разбором ошибок по правилам.
 * Любой текст перед показом проходит SolutionGuard.
 */
class LiteMentor(private val kb: KnowledgeBase) {

    fun answer(question: String, ctx: MentorContext, intent: Intent = IntentClassifier.classify(question)): MentorReply {
        val guard = ctx.task?.let { SolutionGuard(it, listOf(ctx.code)) }
        val reply = when (intent) {
            Intent.SOLUTION_REQUEST -> solution(ctx, guard)
            Intent.HINT -> hint(ctx, guard, intent)
            Intent.EXPLAIN_ERROR -> error(ctx, guard)
            Intent.EXPLAIN_TOPIC, Intent.OTHER -> topic(question, ctx, guard, intent)
            Intent.REVIEW -> review(ctx, guard)
            Intent.EXERCISE -> exercise(ctx)
            Intent.ARCHITECTURE -> architecture(ctx)
        }
        // Последний рубеж: если что-то всё же похоже на решение — ответ заменяется.
        if (guard != null && guard.check(reply.text).leak) {
            return MentorReply(SAFE_FALLBACK, intent, Source.LITE, replaced = true)
        }
        return reply
    }

    /** Ответ без решения: следующий шаг лестницы подсказок. */
    private fun solution(ctx: MentorContext, guard: SolutionGuard?): MentorReply {
        val task = ctx.task ?: return MentorReply(
            "Готовые решения я не пишу — я помогаю дойти до них самостоятельно. Откройте задание или проект, и я подскажу следующий шаг, разберу ошибку или объясню тему.",
            Intent.SOLUTION_REQUEST, Source.LITE,
        )
        val intro = if (task.isAnswerTask) {
            "Ответ я не называю: в этом задании важно самому проследить, что делает каждая строка. Пройдите код построчно и запишите значения переменных после каждой строки."
        } else {
            "Готовое решение я не даю — так навык не закрепится. Давайте дойдём до него по шагам."
        }
        val next = hint(ctx, guard, Intent.SOLUTION_REQUEST)
        return next.copy(text = intro + "\n\n" + next.text)
    }

    private fun hint(ctx: MentorContext, guard: SolutionGuard?, intent: Intent): MentorReply {
        val task = ctx.task ?: return MentorReply(
            "Сейчас не открыто задание. Напишите, какая тема непонятна, или вставьте текст ошибки — разберу.",
            intent, Source.LITE,
        )
        val shown = ctx.hintsShown.coerceIn(0, task.hints.size)
        if (shown >= task.hints.size) {
            val last = if (ctx.attempts > 0) {
                "Все ${task.hints.size} подсказки уже открыты. Последний шаг лестницы — полное решение: его можно открыть кнопкой «решение» под заданием. Но сначала сравните свой код с подсказкой «${HINT_STEP.last()}» ещё раз."
            } else {
                "Все ${task.hints.size} подсказки уже открыты. Отправьте своё решение на проверку — после попытки можно открыть и полное решение, а я разберу ошибку, если она будет."
            }
            return MentorReply(last, intent, Source.LITE)
        }
        val text = task.hints[shown]
        val level = shown + 1
        if (guard != null && guard.check(text).leak) {
            return MentorReply(
                "Следующая подсказка («${HINT_STEP.getOrElse(shown) { "подсказка" }}») почти раскрывает решение, поэтому я её не пересказываю. " +
                    (if (ctx.attempts > 0) "Откройте её кнопкой «Подсказка $level» под заданием, если готовы."
                    else "Сначала попробуйте написать и отправить своё решение — так вы проверите, что уже получается. Подсказку потом можно открыть кнопкой «Подсказка $level»."),
                intent, Source.LITE,
            )
        }
        return MentorReply("**Подсказка $level из ${task.hints.size + 1} — ${HINT_STEP.getOrElse(shown) { "подсказка" }}.** $text", intent, Source.LITE, revealedHint = level)
    }

    private fun error(ctx: MentorContext, guard: SolutionGuard?): MentorReply {
        val language = ctx.task?.language ?: "python"
        val err = ctx.error?.takeIf { it.isNotBlank() }
        if (err == null) {
            val lint = StaticChecks.run(ctx.code, language)
            val text = if (lint.isNotEmpty()) {
                "Ошибки выполнения пока нет, но в коде есть подозрительные места:\n" + lint.joinToString("\n") { "• $it" }
            } else {
                "Я пока не вижу ошибки. Нажмите «Запустить» или «Проверить» — после этого спросите снова, и я разберу сообщение. Можно и просто вставить текст ошибки в вопрос."
            }
            return MentorReply(text, Intent.EXPLAIN_ERROR, Source.LITE)
        }
        val a = ErrorExplainer.analyze(err, ctx.code, language)
            ?: return MentorReply(
                "Это сообщение я не распознал как ошибку Python, JavaScript или SQL. Посмотрите на последнюю строку сообщения — там обычно тип ошибки и причина.",
                Intent.EXPLAIN_ERROR, Source.LITE,
            )
        val links = mutableListOf<LessonLink>()
        val sb = StringBuilder(a.render())
        val mistake = ctx.commonMistakes.firstOrNull { it.errorType == a.type }
            ?: a.skill?.let { kb.lessonOfSkill(it) }?.commonMistakes?.firstOrNull { it.errorType == a.type }
        mistake?.let { sb.append("\n\n**Частая причина в этом уроке:** ${it.mistake}. ${it.fix}") }
        a.skill?.let { kb.lessonOfSkill(it) }?.let { l ->
            if (l.link.key != ctx.lesson?.key) {
                links += l.link
                sb.append("\n\nЭта ошибка разбирается в уроке «${l.link.title}».")
            }
        }
        val text = sb.toString()
        // Строка с ошибкой — код ученика; объяснение — шаблон. Утечки быть не должно, но проверяем.
        if (guard != null && guard.check(text).leak) {
            return MentorReply("**${a.type}**" + (a.line?.let { " в строке $it" } ?: "") + ". " + a.explanation + "\n\n**Что проверить:** " + a.fix,
                Intent.EXPLAIN_ERROR, Source.LITE, links = links)
        }
        return MentorReply(text, Intent.EXPLAIN_ERROR, Source.LITE, links = links)
    }

    private fun topic(question: String, ctx: MentorContext, guard: SolutionGuard?, intent: Intent): MentorReply {
        val query = question.ifBlank { ctx.task?.title.orEmpty() + " " + ctx.lesson?.title.orEmpty() }
        val found = kb.search(query, k = 4, preferLesson = ctx.lesson?.key)
            .filter { p -> guard == null || !guard.check(p.text).leak }
        if (found.isEmpty()) {
            val base = if (intent == Intent.OTHER) "Я наставник курса: объясняю темы, разбираю ошибки, даю подсказки по шагам и предлагаю упражнения. "
            else ""
            return MentorReply(
                base + "В материалах курса не нашлось ответа на этот вопрос. Переформулируйте его коротко, например «что такое f-строка» или «чем while отличается от for».",
                intent, Source.LITE,
            )
        }
        val best = found.first()
        val second = found.drop(1).firstOrNull { it.lesson.key != best.lesson.key || it.heading != best.heading }
        val sb = StringBuilder()
        sb.append("**${best.heading}** (урок «${best.lesson.title}»)\n\n").append(trimPassage(best.text))
        if (second != null && second.score > best.score * 0.6) {
            sb.append("\n\n**См. также:** ${second.heading} — урок «${second.lesson.title}».")
        }
        val links = listOf(best.lesson) + listOfNotNull(second?.lesson?.takeIf { it.key != best.lesson.key })
        return MentorReply(sb.toString(), intent, Source.LITE, links = links.filter { it.key != ctx.lesson?.key }.distinctBy { it.key })
    }

    private fun review(ctx: MentorContext, guard: SolutionGuard?): MentorReply {
        if (ctx.code.isBlank()) return MentorReply("Пока нечего проверять: напишите код или ответ, и я посмотрю.", Intent.REVIEW, Source.LITE)
        val language = ctx.task?.language ?: "python"
        val lint = StaticChecks.run(ctx.code, language)
        val sb = StringBuilder()
        if (lint.isEmpty()) sb.append("Явных ошибок оформления я не вижу.")
        else sb.append("Что стоит поправить:\n").append(lint.joinToString("\n") { "• $it" })
        sb.append("\n\nПравильность решения проверяют тесты — нажмите «Проверить». ")
        if (ctx.error != null) sb.append("Последний запуск завершился ошибкой — спросите «почему ошибка?», и я её разберу.")
        else sb.append("Подробный разбор стиля и логики делает нейросетевой режим наставника (его можно включить в настройках).")
        return MentorReply(sb.toString(), Intent.REVIEW, Source.LITE)
    }

    private fun exercise(ctx: MentorContext): MentorReply {
        val lang = ctx.task?.language
        val err = ctx.error?.let { ErrorExplainer.analyze(it, ctx.code, lang ?: "python") }
        val target = err?.skill?.let { kb.lessonOfSkill(it) } ?: ctx.lesson?.let { kb.lesson(it.key) }
        if (target == null) {
            return MentorReply("Откройте урок — я предложу упражнения из него. Повторение по навыкам есть на главном экране («Повторение»).",
                Intent.EXERCISE, Source.LITE)
        }
        val list = target.assignments.filter { it.first != ctx.task?.id }
            .sortedBy { if (err != null && it.second == "fix") 0 else 1 }.take(3)
        if (list.isEmpty()) return MentorReply("В уроке «${target.link.title}» других упражнений нет. Загляните в «Повторение» на главном экране.", Intent.EXERCISE, Source.LITE)
        val sb = StringBuilder(if (err != null) "Чтобы закрепить работу с ошибкой ${err.type}, попробуйте:\n" else "Для тренировки по теме «${target.link.title}»:\n")
        list.forEach { (_, type, title) -> sb.append("• «$title» — ${TYPE_NAMES[type] ?: type}\n") }
        sb.append("Упражнения — в уроке «${target.link.title}».")
        return MentorReply(sb.toString().trim(), Intent.EXERCISE, Source.LITE, links = listOf(target.link))
    }

    private fun architecture(ctx: MentorContext): MentorReply {
        val text = when (ctx.task?.language) {
            "html", "js" -> "Для веб-страницы удобно разделить три слоя: разметка (HTML) — что есть на странице, стили (CSS) — как это выглядит, " +
                "поведение (JS) — что происходит при действиях. Держите их в отдельных файлах, давайте элементам понятные id и классы, " +
                "а в JS сначала находите элементы, потом вешайте обработчики, а вычисления выносите в отдельные функции."
            "sql" -> "Запрос удобно строить по шагам: сначала `FROM` — откуда данные, затем `WHERE` — какие строки, потом `SELECT` — какие столбцы, " +
                "в конце `ORDER BY`/`LIMIT`. Проверяйте результат после каждого шага."
            "kotlin" -> "В Kotlin разделяйте данные и действия: данные — в `data class`, вычисления — в функции без ввода-вывода, " +
                "а `main` только читает данные, вызывает функции и печатает результат."
            else -> "Небольшую программу удобно разбить на три части: ввод данных, вычисление, вывод результата. " +
                "Вычисления выносите в функции с понятными именами — их легко проверить отдельно. В проекте каждый файл отвечает за одно: " +
                "например, функции расчёта в одном модуле, а `main.py` только связывает части. Избегайте повторов кода: если строка повторяется — это кандидат в функцию или цикл."
        }
        return MentorReply(text, Intent.ARCHITECTURE, Source.LITE)
    }

    private fun trimPassage(text: String, max: Int = 900): String {
        if (text.length <= max) return text
        val cut = text.take(max)
        // Не обрываем блок кода посередине.
        val fences = Regex("```").findAll(cut).count()
        val safe = if (fences % 2 == 1) cut.substring(0, cut.lastIndexOf("```")) else cut
        return safe.trimEnd() + "\n…"
    }

    companion object {
        val HINT_STEP = listOf("намёк", "направление", "концепция", "где искать", "алгоритм", "решение")
        const val SAFE_FALLBACK = "Этот ответ слишком близко подходил к готовому решению, поэтому я его не показываю. " +
            "Попросите подсказку — я дам следующий шаг, или спросите про конкретную строку или ошибку."
        private val TYPE_NAMES = mapOf("write" to "написать код", "fix" to "найти и исправить ошибку", "predict" to "предсказать результат", "review" to "разбор кода")
    }
}

/** Простые проверки кода без запуска: находят место проблемы, но не исправляют его. */
object StaticChecks {
    fun run(code: String, language: String): List<String> {
        if (code.isBlank()) return emptyList()
        val out = mutableListOf<String>()
        val lines = code.lines()
        when (language) {
            "python" -> {
                val block = Regex("^\\s*(if|elif|else|for|while|def|class|try|except|finally|with)\\b")
                lines.forEachIndexed { i, raw ->
                    val l = raw.substringBefore(" #").trimEnd()
                    if (block.containsMatchIn(l) && !l.endsWith(":") && !l.endsWith("\\") && !l.endsWith("(") && !l.endsWith(",")) {
                        out += "строка ${i + 1}: строка с `${block.find(l)!!.groupValues[1]}` должна заканчиваться двоеточием"
                    }
                    if (Regex("^\\s*(if|elif|while)\\b[^=!<>]*[^=!<>]=[^=]").containsMatchIn(l)) {
                        out += "строка ${i + 1}: в условии одно `=` — для сравнения нужно `==`"
                    }
                    if (Regex("[«»“”„]").containsMatchIn(l)) out += "строка ${i + 1}: типографские кавычки — в коде нужны обычные \" или '"
                    if ('\t' in raw && lines.any { it.startsWith("    ") }) out += "строка ${i + 1}: табуляция вместе с пробелами — отступы лучше делать только пробелами"
                }
                if (Regex("input\\(\\s*[\"']").containsMatchIn(code)) {
                    out += "`input()` с текстом в скобках: если задание проверяет вывод, этот текст попадёт в ответ"
                }
            }
            "js", "html" -> {
                lines.forEachIndexed { i, l ->
                    if (Regex("\\bif\\s*\\([^)]*[^=!<>]=[^=>][^)]*\\)").containsMatchIn(l)) out += "строка ${i + 1}: в условии одно `=` — для сравнения нужно `===`"
                    if (Regex("getElementByID|innerHtml|addEventlistener|queryselector").containsMatchIn(l)) out += "строка ${i + 1}: проверьте регистр букв в имени метода"
                }
            }
            "sql" -> {
                if (Regex("\"[^\"]*\"").containsMatchIn(code)) out += "текстовые значения в SQL пишутся в одинарных кавычках: 'текст'"
                if (Regex("(?i)\\bwhere\\b.*\\b(count|sum|avg|max|min)\\s*\\(").containsMatchIn(code)) out += "агрегатные функции в WHERE не работают — условие на них пишется в HAVING"
            }
        }
        // Скобки и кавычки — для всех языков.
        if (language != "html") balance(code, language)?.let { out += it }
        return out.distinct().take(6)
    }

    private fun balance(code: String, language: String): String? {
        val pairs = mapOf(')' to '(', ']' to '[', '}' to '{')
        val stack = ArrayDeque<Pair<Char, Int>>()
        var line = 1
        var quote: Char? = null
        var prev = ' '
        var comment = false
        for (ch in code) {
            if (ch == '\n') { line++; comment = false; if (quote == '"' || quote == '\'') quote = null }
            if (comment) continue
            if (quote == null && ((language == "python" && ch == '#') || (language == "sql" && ch == '-' && prev == '-'))) { comment = true; continue }
            if (quote != null) { if (ch == quote && prev != '\\') quote = null; prev = ch; continue }
            when (ch) {
                '"', '\'', '`' -> quote = ch
                '(', '[', '{' -> stack.addLast(ch to line)
                ')', ']', '}' -> {
                    if (stack.isEmpty() || stack.last().first != pairs[ch]) return "строка $line: лишняя или не та закрывающая скобка `$ch`"
                    stack.removeLast()
                }
            }
            prev = ch
        }
        return stack.lastOrNull()?.let { "строка ${it.second}: скобка `${it.first}` не закрыта" }
    }
}
