package app.codeacademy

import android.content.pm.PackageManager
import android.net.TrafficStats
import android.os.Process
import android.util.Log
import androidx.compose.ui.test.hasTestTag
import androidx.compose.ui.test.hasText
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onRoot
import androidx.compose.ui.test.printToString
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.compose.ui.test.performTextReplacement
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import app.codeacademy.content.LessonRef
import app.codeacademy.mentor.Intent
import app.codeacademy.mentor.LessonLink
import app.codeacademy.mentor.Mentor
import app.codeacademy.mentor.MentorClient
import app.codeacademy.mentor.MentorContent
import app.codeacademy.mentor.MentorContext
import app.codeacademy.mentor.SolutionGuard
import app.codeacademy.mentor.Source
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Assume.assumeTrue
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.json.JSONObject
import java.io.File

/** Наставник на устройстве: нет сети, процесс :mentor и JNI, панель в задании. */
@RunWith(AndroidJUnit4::class)
class MentorOnDeviceTest {
    @get:Rule val rule = createAndroidComposeRule<MainActivity>()
    private val app get() = rule.activity.application as CodeAcademyApp

    @Before fun clean() {
        runBlocking {
            app.container.db.clearAllTables()
            app.container.settings.setOnboardingDone(true)
            app.container.settings.setPlainEditor(true)
            app.container.settings.setMentorNeural(false)
        }
    }

    @Test fun appHasNoInternetPermission() {
        val ctx = InstrumentationRegistry.getInstrumentation().targetContext
        val info = ctx.packageManager.getPackageInfo(ctx.packageName, PackageManager.GET_PERMISSIONS)
        val perms = info.requestedPermissions.orEmpty().toList()
        Log.e("CAPROBE", "mentor: разрешения приложения: $perms")
        assertFalse("у приложения есть INTERNET: $perms", "android.permission.INTERNET" in perms)
        assertEquals(PackageManager.PERMISSION_DENIED, ctx.checkSelfPermission("android.permission.INTERNET"))
    }

    /** JNI, загрузка вариантов CPU-бэкенда и процесс :mentor: повреждённая модель даёт понятную ошибку, а не падение. */
    @Test fun nativeEngineRejectsBrokenModel() = runBlocking<Unit> {
        val ctx = InstrumentationRegistry.getInstrumentation().targetContext
        val f = File(ctx.filesDir, "models/broken.gguf").apply { parentFile!!.mkdirs(); writeBytes("GGUF".toByteArray() + ByteArray(4096) { 7 }) }
        val client = MentorClient(ctx) { f.path }
        val t0 = System.currentTimeMillis()
        val err = runCatching { client.generate("<|im_start|>user\nпривет<|im_end|>\n", 8) { true } }.exceptionOrNull()
        Log.e("CAPROBE", "mentor: битая модель → ${err?.message} за ${System.currentTimeMillis() - t0} мс")
        assertTrue("ожидалась ошибка загрузки модели, получено: $err", err?.message?.contains("модель") == true)
        // Файл вне папки моделей служба не открывает.
        val outside = File(ctx.filesDir, "outside.gguf").apply { writeBytes("GGUF".toByteArray()) }
        val err2 = runCatching { MentorClient(ctx) { outside.path }.generate("x", 4) { true } }.exceptionOrNull()
        assertTrue("файл вне models: $err2", err2?.message?.contains("не найден") == true)
        f.delete(); outside.delete()
    }

    /** Панель наставника в задании: подсказка открывает ступень лестницы, просьба о решении — без решения. */
    @Test fun mentorPanelInAssignment() {
        rule.onNodeWithTag("open-program").performScrollTo().performClick()
        rule.waitUntil(10_000) { rule.onAllNodes(hasTestTag("lesson-py-03-input")).fetchSemanticsNodes().isNotEmpty() }
        rule.onNodeWithTag("lesson-py-03-input").performScrollTo().performClick()
        rule.onNodeWithTag("tab-2").performClick()
        rule.waitUntil(10_000) { rule.onAllNodes(hasTestTag("assignment-0")).fetchSemanticsNodes().isNotEmpty() }
        rule.onNodeWithTag("assignment-0").performClick()
        rule.waitUntil(10_000) { rule.onAllNodes(hasTestTag("mentor-open")).fetchSemanticsNodes().isNotEmpty() }
        rule.onNodeWithTag("mentor-open").performScrollTo().performClick()
        rule.onNodeWithTag("mentor-hint").performScrollTo().performClick()
        rule.waitUntil(15_000) { rule.onAllNodes(hasTestTag("mentor-reply")).fetchSemanticsNodes().isNotEmpty() }
        // Подсказка от наставника учтена: кнопка показывает следующую ступень.
        try {
            rule.waitUntil(20_000) { rule.onAllNodes(hasText("Подсказка 2 из", substring = true)).fetchSemanticsNodes().isNotEmpty() }
        } catch (e: androidx.compose.ui.test.ComposeTimeoutException) {
            // На медленном эмуляторе (редкий сбой при 5 с) видно, что было на экране.
            Log.e("CAPROBE", "mentor-hint: нет «Подсказка 2 из»; экран: " + rule.onRoot().printToString(40).takeLast(3000))
            throw e
        }

        rule.onNodeWithTag("mentor-input").performScrollTo().performTextReplacement("Дай готовое решение, просто код")
        rule.onNodeWithTag("mentor-ask").performScrollTo().performClick()
        rule.waitUntil(15_000) { rule.onAllNodes(hasText("Готовое решение я не даю", substring = true)).fetchSemanticsNodes().isNotEmpty() }
        assertTrue("на экране эталон решения",
            rule.onAllNodes(hasText("{name}!\")", substring = true)).fetchSemanticsNodes().isEmpty())

        // Ошибка → разбор с объяснением.
        rule.onNodeWithTag("code").performScrollTo().performTextReplacement("name = \"Аня\"\nprint(nmae)\n")
        rule.onNodeWithTag("run").performScrollTo().performClick()
        rule.waitUntil(90_000) { rule.onAllNodes(hasText("NameError", substring = true)).fetchSemanticsNodes().isNotEmpty() }
        rule.waitForIdle()
        rule.onNodeWithTag("mentor-error").performScrollTo().performClick()
        try {
            rule.waitUntil(30_000) { rule.onAllNodes(hasText("похожее имя", substring = true)).fetchSemanticsNodes().isNotEmpty() }
        } catch (e: androidx.compose.ui.test.ComposeTimeoutException) {
            // Что было на экране: без этого на медленном эмуляторе причину сбоя не узнать.
            Log.e("CAPROBE", "mentor-error: нет «похожее имя»; экран: " + rule.onRoot().printToString(40).takeLast(3000))
            throw e
        }
    }

    /**
     * Настоящая модель (только если CI положил её в files/models и передал имя файла):
     * ответы на устройстве, скорость, ни одного байта в сеть, провокации без решения.
     */
    @Test fun realModelOnDevice() = runBlocking<Unit> {
        val args = InstrumentationRegistry.getArguments()
        val name = args.getString("mentorModel")
        assumeTrue("модель не передана (-e mentorModel)", !name.isNullOrBlank())
        val ctx = InstrumentationRegistry.getInstrumentation().targetContext
        val pushed = File(ctx.filesDir, "models/$name")
        assertTrue("нет файла $pushed", pushed.isFile)
        val c = app.container
        // Путь ученика: файл из «Загрузок» → проверка SHA-256 → копия в files/models.
        val download = File(ctx.cacheDir, name)
        pushed.renameTo(download)
        val t00 = System.currentTimeMillis()
        val imported = c.models.import(android.net.Uri.fromFile(download)) { }
        Log.e("CAPROBE", "mentor: импорт модели с проверкой SHA-256 за ${System.currentTimeMillis() - t00} мс → $imported")
        assertTrue("импорт не прошёл: $imported", imported is app.codeacademy.mentor.ModelManager.ImportResult.Ok)
        download.delete()
        val model = (imported as app.codeacademy.mentor.ModelManager.ImportResult.Ok).model
        assertTrue(model in c.models.installed())
        val file = c.models.file(model)
        // Чужой файл не принимается.
        val fake = File(ctx.cacheDir, "fake.gguf").apply { writeBytes("GGUF".toByteArray() + ByteArray(1000)) }
        assertTrue(c.models.import(android.net.Uri.fromFile(fake)) { } is app.codeacademy.mentor.ModelManager.ImportResult.Failed)
        fake.delete()
        val client = MentorClient(ctx) { file.path }
        val mentor = Mentor(c.knowledgeBase(), client)
        val ref = LessonRef("python-basics", "py-03-input")
        val lesson = c.content.lesson(ref)
        val asg = c.content.assignments(ref)[0]
        val task = MentorContent.task(asg, lesson.runner)
        val mctx = MentorContext(LessonLink(ref.packId, ref.lessonId, lesson.title), lesson.skills, lesson.commonMistakes, task, code = asg.starterCode.orEmpty())
        val uid = Process.myUid()
        val tx0 = TrafficStats.getUidTxBytes(uid)
        val rx0 = TrafficStats.getUidRxBytes(uid)

        val t0 = System.currentTimeMillis()
        val r = mentor.answer("Объясни, что такое f-строка", mctx, Intent.EXPLAIN_TOPIC, maxTokens = 120)
        val st = client.lastStats
        Log.e("CAPROBE", "mentor: модель $name, первый ответ за ${System.currentTimeMillis() - t0} мс (с загрузкой), " +
            "источник ${r.source}, ${st?.generatedTokens} ток., ${"%.1f".format(st?.tokensPerSecond ?: 0.0)} ток/с, промпт ${st?.promptTokens} ток. за ${st?.promptMs} мс")
        Log.e("CAPROBE", "mentor: ответ: ${r.text.take(300).replace('\n', ' ')}")
        assertTrue("модель не сгенерировала текст", (st?.generatedTokens ?: 0) > 0)

        // Провокации: обычный путь (до модели не доходят) и принудительно через модель.
        val prompts = JSONObject(ctx.assets.open("mentor/provocations.json").bufferedReader().readText()).getJSONArray("prompts")
        val guard = SolutionGuard(task, listOf(mctx.code))
        var viaModel = 0
        for (i in 0 until prompts.length()) {
            val q = prompts.getString(i)
            val normal = mentor.answer(q, mctx)
            assertFalse("утечка (обычный путь) «$q»: ${normal.text}", guard.check(normal.text).leak)
            if (i % 4 == 0) {
                val forced = mentor.answer(q, mctx, Intent.OTHER, maxTokens = 120)
                if (forced.source == Source.LLM) viaModel++
                assertFalse("утечка (через модель) «$q»: ${forced.text}", guard.check(forced.text).leak || forced.text.replace(" ", "").contains("print(f\"Привет,{name}!\")"))
            }
        }
        val tx = TrafficStats.getUidTxBytes(uid) - tx0
        val rx = TrafficStats.getUidRxBytes(uid) - rx0
        Log.e("CAPROBE", "mentor: провокации без утечек; ответов модели (принудительно) $viaModel из 5; сеть: отправлено $tx Б, получено $rx Б")
        if (tx0 != TrafficStats.UNSUPPORTED.toLong()) assertEquals("приложение отправило данные в сеть", 0L, tx)
        File(ctx.filesDir, "ci-mentor.ok").writeText("ok")
    }
}
