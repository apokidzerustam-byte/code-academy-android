package stubs

/** Журнал «отрисовки» заглушек: по нему проверяется, какое дерево интерфейса построил код ученика. */
object ComposeLog {
    val lines = mutableListOf<String>()
    var depth = 0
    val clicks = mutableListOf<() -> Unit>()

    fun add(text: String) {
        lines.add("  ".repeat(depth) + text)
    }

    fun nested(block: () -> Unit) {
        depth++
        try {
            block()
        } finally {
            depth--
        }
    }

    fun render(content: () -> Unit): String {
        lines.clear()
        clicks.clear()
        depth = 0
        content()
        return lines.joinToString("\n")
    }

    fun click(index: Int) {
        clicks[index]()
    }
}
