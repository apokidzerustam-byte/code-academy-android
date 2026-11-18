package app.codeacademy

import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import app.codeacademy.runner.CodeRunner
import app.codeacademy.runner.PyodideRunner
import app.codeacademy.runner.RunStatus
import app.codeacademy.runner.RunnerClient
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Assume.assumeTrue
import org.junit.Test
import org.junit.runner.RunWith

/** Многофайловый проект: импорт своих модулей, ввод, созданные программой файлы возвращаются. */
@RunWith(AndroidJUnit4::class)
class ProjectRunOnDeviceTest {
    private val ctx = InstrumentationRegistry.getInstrumentation().targetContext
    private val files = mapOf(
        "main.py" to "from tools.calc import add\na = int(input())\nb = int(input())\nprint('Сумма:', add(a, b))\nopen('history.txt', 'a').write(f'{a}+{b}\\n')\n",
        "tools/__init__.py" to "",
        "tools/calc.py" to "def add(x, y):\n    return x + y\n",
    )

    private fun scenario(r: CodeRunner) = runBlocking {
        val res = r.run(files["main.py"]!!, 10_000, "2\n3\n", "devtest", files)
        assertEquals(res.stderr, RunStatus.OK, res.status)
        assertEquals("Сумма: 5\n", res.stdout)
        val back = res.files!!
        assertEquals("2+3\n", back["history.txt"])
        assertEquals(files["tools/calc.py"], back["tools/calc.py"])
        // Второй запуск с обновлёнными файлами: история дописывается, старые файлы заменяются.
        val res2 = r.run(files["main.py"]!!, 10_000, "1\n1\n", "devtest", back)
        assertEquals("2+3\n1+1\n", res2.files!!["history.txt"])
        // Удалённый из проекта файл не должен «воскреснуть».
        val res3 = r.run("import os\nprint(sorted(os.listdir('.')))", 10_000, "", "devtest", mapOf("main.py" to "x"))
        assertTrue(res3.stdout, res3.stdout.trim() == "['main.py']")
    }

    @Test fun levelA() {
        val r = RunnerClient(ctx, isolated = false)
        try { scenario(r) } finally { r.close() }
    }

    @Test fun levelW() {
        val r = PyodideRunner(ctx)
        try {
            assumeTrue(runBlocking { r.prepare() }?.pythonStarted == true)
            scenario(r)
        } finally { r.close() }
    }
}
