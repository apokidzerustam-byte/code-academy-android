package app.codeacademy

import app.codeacademy.ide.TrainingShell
import app.codeacademy.runner.ProjectFiles
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test
import java.nio.file.Files

class TrainingShellTest {
    private var ran: String? = null
    private fun shell(vararg f: Pair<String, String>) =
        TrainingShell(mutableMapOf(*f)) { path, _ -> ran = path; "запуск $path" }

    private fun TrainingShell.x(line: String) = runBlocking { exec(line).output }

    @Test fun navigationAndListing() {
        val s = shell("main.py" to "print(1)", "utils/greet.py" to "def f(): pass", "docs/.keep" to "")
        assertEquals("docs/  main.py  utils/", s.x("ls"))
        assertEquals("", s.x("cd utils"))
        assertEquals("/utils", s.x("pwd"))
        assertEquals("greet.py", s.x("ls"))
        assertEquals("~/utils $ ", s.prompt)
        s.x("cd ..")
        assertEquals("/", s.x("pwd"))
        assertTrue(s.x("cd nope").contains("нет такой папки"))
    }

    @Test fun cannotEscapeProject() {
        val s = shell("main.py" to "")
        assertTrue(s.x("cd ..").contains("вне проекта"))
        assertTrue(s.x("cat ../../etc/passwd").contains("вне проекта"))
        assertTrue(s.x("rm -r /").contains("корень"))
        assertEquals(setOf("main.py"), s.files.keys)
    }

    @Test fun fileCommands() {
        val s = shell()
        s.x("mkdir src")
        s.x("touch src/a.py")
        s.x("echo \"print('hi')\" > src/a.py")
        assertEquals("print('hi')", s.x("cat src/a.py"))
        s.x("echo second >> src/a.py")
        assertEquals("print('hi')\nsecond", s.x("cat src/a.py"))
        s.x("mv src/a.py b.py")
        assertTrue("b.py" in s.files && "src/a.py" !in s.files)
        assertTrue(s.x("rm src").contains("rm -r"))
        s.x("rm -r src")
        assertFalse(s.files.keys.any { it.startsWith("src/") })
        s.x("rm b.py")
        assertTrue(s.files.isEmpty())
    }

    @Test fun pythonAndHelp() {
        val s = shell("main.py" to "print(1)")
        assertEquals("запуск main.py", s.x("python main.py"))
        assertEquals("main.py", ran)
        assertTrue(s.x("python nope.py").contains("не удаётся открыть"))
        assertTrue(s.x("sudo rm -rf /").contains("команда не найдена"))
        assertTrue(s.x("help").contains("python файл.py"))
        assertTrue(runBlocking { s.exec("clear").clear })
    }

    @Test fun projectFilesRoundTripAndLimits() {
        val root = Files.createTempDirectory("proj").toFile()
        ProjectFiles.write(root, mapOf("main.py" to "print('ж')", "pkg/m.py" to "X=1"))
        assertEquals(mapOf("main.py" to "print('ж')", "pkg/m.py" to "X=1"), ProjectFiles.read(root))
        ProjectFiles.write(root, mapOf("only.py" to ""))
        assertEquals(setOf("only.py"), ProjectFiles.read(root).keys)
        for (bad in listOf("../x", "/etc/passwd", "a/../../b", "")) {
            assertTrue(bad, runCatching { ProjectFiles.write(root, mapOf(bad to "x")) }.isFailure)
        }
        java.io.File(root, "bin.dat").writeBytes(byteArrayOf(-1, -2, 0))
        assertFalse("bin.dat" in ProjectFiles.read(root))
        root.deleteRecursively()
    }

    @Test fun rejectsFileFolderClashes() {
        val s = shell("main.py" to "print(1)", "docs/.keep" to "")
        assertTrue(s.x("touch main.py/x.py").contains("это файл"))
        assertTrue(s.x("mkdir main.py/sub").contains("это файл"))
        assertTrue(s.x("echo hi > main.py/x").contains("это файл"))
        assertTrue(s.x("touch docs").contains("это папка"))
        assertTrue(s.x("touch .project").contains("служебное"))
        assertTrue(s.x("mv main.py docs/.keep").contains("служебное"))
        assertEquals("", s.x("mv main.py docs"))
        assertEquals(setOf("docs/.keep", "docs/main.py"), s.files.keys)
        assertNull(ProjectFiles.conflict(s.files.keys))
        assertEquals("«a» — это файл, внутри него не может быть «a/b»", ProjectFiles.conflict(listOf("a", "a/b")))
        val dir = java.nio.file.Files.createTempDirectory("pf").toFile()
        ProjectFiles.write(dir, mapOf("main.py" to "1"))
        assertThrows(IllegalArgumentException::class.java) { ProjectFiles.write(dir, mapOf("x" to "1", "x/y" to "2")) }
        assertEquals(mapOf("main.py" to "1"), ProjectFiles.read(dir))
        // Ссылка за пределы проекта не читается и не удаляется по ней.
        val outside = java.nio.file.Files.createTempDirectory("out").toFile()
        java.io.File(outside, "secret.txt").writeText("S")
        java.nio.file.Files.createSymbolicLink(java.io.File(dir, "link").toPath(), outside.toPath())
        assertEquals(mapOf("main.py" to "1"), ProjectFiles.read(dir))
        ProjectFiles.write(dir, mapOf("main.py" to "2"))
        assertEquals("S", java.io.File(outside, "secret.txt").readText())
    }
}
