package app.codeacademy

import app.codeacademy.ide.TrainingShell
import app.codeacademy.runner.ProjectFiles
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
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
}
