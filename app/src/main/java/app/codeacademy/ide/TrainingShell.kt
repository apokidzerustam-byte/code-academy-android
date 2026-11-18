package app.codeacademy.ide

/**
 * Учебный терминал (TerminalManager, раздел 6 ТЗ): безопасная виртуальная оболочка над файлами
 * проекта. Настоящих системных команд нет — только учебный набор; выйти за пределы проекта нельзя.
 */
class TrainingShell(
    /** Файлы проекта {путь: текст}; изменяются командами. Папка = файл "<папка>/.keep" или общий префикс. */
    val files: MutableMap<String, String>,
    /** Запуск Python-файла проекта; возвращает текст для терминала. */
    private val runPython: suspend (path: String, args: List<String>) -> String,
) {
    data class Result(val output: String, val clear: Boolean = false)

    var cwd: String = ""
        private set

    val prompt: String get() = "~${if (cwd.isEmpty()) "" else "/$cwd"} $ "

    private fun dirs(): Set<String> {
        val out = mutableSetOf("")
        for (p in files.keys) {
            val parts = p.split('/')
            for (i in 1 until parts.size) out += parts.take(i).joinToString("/")
        }
        return out
    }

    private fun isDir(p: String) = p in dirs()

    /** Почему по этому пути нельзя создать файл (null — можно). */
    private fun cannotCreate(p: String, arg: String): String? {
        if (p.isEmpty()) return "$arg: это корень проекта"
        if (p.substringAfterLast('/') == ".keep" || p == app.codeacademy.data.ProjectRepository.META) return "$arg: служебное имя"
        if (isDir(p)) return "$arg: это папка"
        var i = p.indexOf('/')
        while (i > 0) {
            val d = p.substring(0, i)
            if (isFile(d)) return "$arg: «$d» — это файл, а не папка"
            i = p.indexOf('/', i + 1)
        }
        return null
    }
    private fun isFile(p: String) = p in files && !p.endsWith("/.keep")

    /** Нормализует путь относительно cwd; null — попытка выйти за пределы проекта. */
    fun resolve(arg: String): String? {
        val start = if (arg.startsWith("/") || arg.startsWith("~")) mutableListOf() else cwd.split('/').filter { it.isNotEmpty() }.toMutableList()
        for (part in arg.removePrefix("~").split('/')) {
            when (part) {
                "", "." -> {}
                ".." -> if (start.isEmpty()) return null else start.removeAt(start.lastIndex)
                else -> start += part
            }
        }
        return start.joinToString("/")
    }

    private fun children(dir: String): List<String> {
        val prefix = if (dir.isEmpty()) "" else "$dir/"
        return (files.keys + dirs()).asSequence()
            .filter { it.startsWith(prefix) && it != dir }
            .map { it.removePrefix(prefix).substringBefore('/') }
            .filter { it.isNotEmpty() && it != ".keep" }
            .distinct().sorted()
            .map { name -> if (isDir(prefix + name)) "$name/" else name }
            .toList()
    }

    private fun tokenize(line: String): List<String> {
        val out = mutableListOf<String>()
        val cur = StringBuilder()
        var quote: Char? = null
        var hasToken = false
        for (ch in line) {
            when {
                quote != null && ch == quote -> quote = null
                quote != null -> cur.append(ch)
                ch == '"' || ch == '\'' -> { quote = ch; hasToken = true }
                ch.isWhitespace() -> if (cur.isNotEmpty() || hasToken) { out += cur.toString(); cur.clear(); hasToken = false }
                else -> cur.append(ch)
            }
        }
        if (cur.isNotEmpty() || hasToken) out += cur.toString()
        return out
    }

    suspend fun exec(line: String): Result {
        val t = tokenize(line.trim())
        if (t.isEmpty()) return Result("")
        val cmd = t[0]
        val a = t.drop(1)
        fun bad(p: String) = Result("$cmd: $p: путь вне проекта")
        return when (cmd) {
            "help" -> Result(HELP)
            "clear" -> Result("", clear = true)
            "pwd" -> Result("/" + cwd)
            "ls" -> {
                val d = resolve(a.firstOrNull() ?: ".") ?: return bad(a[0])
                when {
                    isFile(d) -> Result(d.substringAfterLast('/'))
                    isDir(d) -> Result(children(d).joinToString("  "))
                    else -> Result("ls: ${a.first()}: нет такого файла или папки")
                }
            }
            "cd" -> {
                val d = resolve(a.firstOrNull() ?: "~") ?: return bad(a[0])
                if (!isDir(d)) Result("cd: ${a.firstOrNull()}: нет такой папки") else { cwd = d; Result("") }
            }
            "cat" -> {
                if (a.isEmpty()) return Result("cat: укажите файл")
                Result(a.joinToString("") { arg ->
                    val p = resolve(arg)
                    when {
                        p == null -> "cat: $arg: путь вне проекта\n"
                        isFile(p) -> files[p]!!.let { if (it.endsWith("\n") || it.isEmpty()) it else "$it\n" }
                        isDir(p) -> "cat: $arg: это папка\n"
                        else -> "cat: $arg: нет такого файла\n"
                    }
                }.trimEnd('\n'))
            }
            "touch" -> {
                if (a.isEmpty()) return Result("touch: укажите файл")
                for (arg in a) {
                    val p = resolve(arg) ?: return bad(arg)
                    if (isFile(p)) continue
                    cannotCreate(p, arg)?.let { return Result("touch: $it") }
                    files[p] = ""
                }
                Result("")
            }
            "mkdir" -> {
                if (a.isEmpty()) return Result("mkdir: укажите имя папки")
                for (arg in a) {
                    val p = resolve(arg) ?: return bad(arg)
                    if (isDir(p) || isFile(p)) return Result("mkdir: $arg: уже существует")
                    cannotCreate(p, arg)?.let { return Result("mkdir: $it") }
                    files["$p/.keep"] = ""
                }
                Result("")
            }
            "rm" -> {
                val recursive = a.any { it == "-r" || it == "-rf" }
                val targets = a.filter { !it.startsWith("-") }
                if (targets.isEmpty()) return Result("rm: укажите файл")
                for (arg in targets) {
                    val p = resolve(arg) ?: return bad(arg)
                    when {
                        p.isEmpty() -> return Result("rm: нельзя удалить корень проекта")
                        isFile(p) -> files.remove(p)
                        isDir(p) && !recursive -> return Result("rm: $arg: это папка (используйте rm -r)")
                        isDir(p) -> files.keys.removeAll { it.startsWith("$p/") }
                        else -> return Result("rm: $arg: нет такого файла")
                    }
                }
                Result("")
            }
            "mv" -> {
                if (a.size != 2) return Result("mv: использование: mv откуда куда")
                val from = resolve(a[0]) ?: return bad(a[0])
                var to = resolve(a[1]) ?: return bad(a[1])
                if (!isFile(from)) return Result("mv: ${a[0]}: нет такого файла")
                if (isDir(to)) to = if (to.isEmpty()) from.substringAfterLast('/') else "$to/${from.substringAfterLast('/')}"
                if (to == from) return Result("")
                if (!isFile(to)) cannotCreate(to, a[1])?.let { return Result("mv: $it") }
                files[to] = files.remove(from)!!
                Result("")
            }
            "echo" -> {
                val i = a.indexOfFirst { it == ">" || it == ">>" }
                val text = (if (i >= 0) a.take(i) else a).joinToString(" ")
                if (i < 0) return Result(text)
                val target = a.getOrNull(i + 1) ?: return Result("echo: укажите файл после ${a[i]}")
                val p = resolve(target) ?: return bad(target)
                if (!isFile(p)) cannotCreate(p, target)?.let { return Result("echo: $it") }
                files[p] = if (a[i] == ">>") (files[p] ?: "") + text + "\n" else text + "\n"
                Result("")
            }
            "python", "python3" -> {
                val script = a.firstOrNull() ?: return Result("python: укажите файл, например: python main.py")
                val p = resolve(script) ?: return bad(script)
                if (!isFile(p)) return Result("python: не удаётся открыть файл '$script'")
                Result(runPython(p, a.drop(1)))
            }
            else -> Result("$cmd: команда не найдена. Введите help — список команд.")
        }
    }

    companion object {
        val HELP = """
            Учебный терминал (работает только внутри проекта):
              ls [папка]          — список файлов
              cd папка | .. | ~   — перейти в папку
              pwd                 — текущая папка
              cat файл            — показать файл
              touch файл          — создать пустой файл
              mkdir папка         — создать папку
              rm файл | rm -r папка — удалить
              mv откуда куда      — переместить/переименовать
              echo текст [> файл] — вывести или записать в файл (>> — дописать)
              python файл.py      — запустить программу
              clear               — очистить экран
        """.trimIndent()
    }
}
