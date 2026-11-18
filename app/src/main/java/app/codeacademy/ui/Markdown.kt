package app.codeacademy.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.dp

/** Минимальный Markdown для конспектов: заголовки, абзацы, списки, код, таблицы, **жирный**, `код`. */
@Composable
fun MarkdownText(md: String, modifier: Modifier = Modifier) {
    Column(modifier, verticalArrangement = Arrangement.spacedBy(8.dp)) {
        for (block in parseBlocks(md)) {
            when (block) {
                is MdBlock.Heading -> Text(
                    inline(block.text),
                    style = when (block.level) {
                        1 -> MaterialTheme.typography.headlineSmall
                        2 -> MaterialTheme.typography.titleLarge
                        else -> MaterialTheme.typography.titleMedium
                    },
                )
                is MdBlock.Code -> CodeBlock(block.text)
                is MdBlock.ListItem -> Row {
                    Text(block.marker + " ", style = MaterialTheme.typography.bodyLarge)
                    Text(inline(block.text), style = MaterialTheme.typography.bodyLarge)
                }
                is MdBlock.Table -> TableBlock(block.rows)
                is MdBlock.Paragraph -> Text(inline(block.text), style = MaterialTheme.typography.bodyLarge)
            }
        }
    }
}

/** Таблица: первая строка — заголовок, ячейки переносятся по словам, инлайн-разметка работает. */
@Composable
fun TableBlock(rows: List<List<String>>) {
    val cols = rows.maxOfOrNull { it.size } ?: return
    Column(
        Modifier
            .fillMaxWidth()
            .border(1.dp, MaterialTheme.colorScheme.outlineVariant, RoundedCornerShape(8.dp))
            .padding(4.dp),
    ) {
        rows.forEachIndexed { r, row ->
            if (r > 0) HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)
            Row(Modifier.fillMaxWidth().padding(vertical = 6.dp)) {
                for (c in 0 until cols) {
                    Text(
                        inline(row.getOrElse(c) { "" }),
                        style = if (r == 0) MaterialTheme.typography.labelLarge else MaterialTheme.typography.bodyMedium,
                        fontWeight = if (r == 0) FontWeight.Bold else null,
                        modifier = Modifier.weight(1f).padding(horizontal = 6.dp),
                    )
                }
            }
        }
    }
}

@Composable
fun CodeBlock(code: String, modifier: Modifier = Modifier) {
    Text(
        code.trimEnd(),
        style = MaterialTheme.typography.bodyMedium.copy(fontFamily = FontFamily.Monospace),
        softWrap = false,
        modifier = modifier
            .fillMaxWidth()
            .background(MaterialTheme.colorScheme.surfaceVariant, RoundedCornerShape(8.dp))
            .horizontalScroll(rememberScrollState())
            .padding(12.dp),
    )
}

sealed interface MdBlock {
    data class Heading(val level: Int, val text: String) : MdBlock
    data class Code(val text: String) : MdBlock
    data class ListItem(val marker: String, val text: String) : MdBlock
    data class Table(val rows: List<List<String>>) : MdBlock
    data class Paragraph(val text: String) : MdBlock
}

fun parseBlocks(md: String): List<MdBlock> {
    val out = mutableListOf<MdBlock>()
    val lines = md.replace("\r\n", "\n").lines()
    var i = 0
    val para = StringBuilder()
    fun flush() {
        if (para.isNotBlank()) out += MdBlock.Paragraph(para.toString().trim())
        para.clear()
    }
    while (i < lines.size) {
        val line = lines[i]
        when {
            line.startsWith("```") -> {
                flush()
                val code = StringBuilder()
                i++
                while (i < lines.size && !lines[i].startsWith("```")) { code.appendLine(lines[i]); i++ }
                out += MdBlock.Code(code.toString())
            }
            line.startsWith("#") -> {
                flush()
                val level = line.takeWhile { it == '#' }.length
                out += MdBlock.Heading(level, line.drop(level).trim())
            }
            line.trimStart().startsWith("|") -> {
                flush()
                val rows = mutableListOf<List<String>>()
                while (i < lines.size && lines[i].trimStart().startsWith("|")) {
                    val cells = lines[i].trim().trim('|').split("|").map { it.trim() }
                    if (!cells.all { c -> c.isNotEmpty() && c.all { it == '-' || it == ':' } }) rows += cells
                    i++
                }
                out += MdBlock.Table(rows)
                continue
            }
            Regex("^\\s*([-*]|\\d+\\.)\\s+.*").matches(line) -> {
                flush()
                val m = Regex("^\\s*([-*]|\\d+\\.)\\s+(.*)").find(line)!!
                val marker = m.groupValues[1].let { if (it == "-" || it == "*") "•" else it }
                out += MdBlock.ListItem(marker, m.groupValues[2])
            }
            line.isBlank() -> flush()
            else -> para.append(line).append(' ')
        }
        i++
    }
    flush()
    return out
}

/** Инлайн-разметка: **жирный** и `код`. */
@Composable
fun inline(text: String): AnnotatedString {
    val codeBg = MaterialTheme.colorScheme.surfaceVariant
    return buildAnnotatedString {
        var i = 0
        while (i < text.length) {
            when {
                text.startsWith("**", i) && text.indexOf("**", i + 2) > 0 -> {
                    val end = text.indexOf("**", i + 2)
                    withStyle(SpanStyle(fontWeight = FontWeight.Bold)) { append(text.substring(i + 2, end)) }
                    i = end + 2
                }
                text[i] == '`' && text.indexOf('`', i + 1) > 0 -> {
                    val end = text.indexOf('`', i + 1)
                    withStyle(SpanStyle(fontFamily = FontFamily.Monospace, background = codeBg)) { append(text.substring(i + 1, end)) }
                    i = end + 1
                }
                else -> { append(text[i]); i++ }
            }
        }
    }
}
