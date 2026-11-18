package app.codeacademy

import app.codeacademy.ui.MdBlock
import app.codeacademy.ui.parseBlocks
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File

class MarkdownParseTest {
    @Test fun parsesBlocks() {
        val b = parseBlocks("# Заголовок\n\nТекст **жирный**\nпродолжение\n\n```python\nprint(1)\n```\n- пункт\n1. шаг\n\n| A | B |\n| --- | --- |\n| 1 | 2 |\n")
        assertEquals(MdBlock.Heading(1, "Заголовок"), b[0])
        assertEquals(MdBlock.Paragraph("Текст **жирный** продолжение"), b[1])
        assertEquals(MdBlock.Code("print(1)\n"), b[2])
        assertEquals(MdBlock.ListItem("•", "пункт"), b[3])
        assertEquals(MdBlock.ListItem("1.", "шаг"), b[4])
        assertEquals(MdBlock.Table(listOf(listOf("A", "B"), listOf("1", "2"))), b[5])
    }

    @Test fun lessonNotesParseWithoutLoss() {
        File("../content/packs").walkTopDown().filter { it.name == "notes.md" }.forEach { f ->
            val blocks = parseBlocks(f.readText())
            assertTrue(f.path, blocks.any { it is MdBlock.Heading })
            assertTrue(f.path, blocks.any { it is MdBlock.Code })
        }
    }
}
