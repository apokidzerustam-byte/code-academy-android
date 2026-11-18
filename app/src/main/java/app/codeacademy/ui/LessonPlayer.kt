package app.codeacademy.ui

import android.content.res.AssetManager
import android.media.AudioAttributes
import android.media.MediaPlayer
import android.media.PlaybackParams
import android.util.Log
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.FilledIconButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Slider
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableLongStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.setValue
import androidx.compose.runtime.withFrameMillis
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.dp
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.lifecycle.compose.LocalLifecycleOwner
import app.codeacademy.lesson.LessonTimeline

/** Скорости воспроизведения по кругу. */
val PLAYER_SPEEDS = listOf(1f, 1.25f, 1.5f, 2f, 0.75f)

/**
 * Озвучка урока: один MediaPlayer на текущую сцену (файлы сцен лежат в assets без сжатия).
 * Время плеера = начало сцены + позиция в её файле, поэтому анимация не уходит от голоса.
 */
class NarrationAudio(private val assets: AssetManager, private val assetPath: (String) -> String) {
    private var player: MediaPlayer? = null
    private var loadedFile: String? = null
    var failed: String? = null
        private set

    fun load(file: String): Boolean {
        if (loadedFile == file && player != null) return true
        release()
        return runCatching {
            val mp = MediaPlayer()
            mp.setAudioAttributes(
                AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_MEDIA)
                    .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH).build(),
            )
            assets.openFd(assetPath(file)).use { fd -> mp.setDataSource(fd.fileDescriptor, fd.startOffset, fd.length) }
            mp.prepare()
            player = mp
            loadedFile = file
            true
        }.getOrElse {
            Log.w("CAPLAYER", "audio $file: $it")
            failed = it.toString()
            release()
            false
        }
    }

    fun positionMs(): Long? = player?.let { runCatching { it.currentPosition.toLong() }.getOrNull() }
    val isPlaying: Boolean get() = player?.let { runCatching { it.isPlaying }.getOrDefault(false) } ?: false

    fun play(fromMs: Long, speed: Float) {
        val mp = player ?: return
        runCatching {
            mp.seekTo(fromMs.toInt())
            mp.playbackParams = PlaybackParams().setSpeed(speed).setPitch(1f)
            if (!mp.isPlaying) mp.start()
        }.onFailure { Log.w("CAPLAYER", "play: $it") }
    }

    fun pause() {
        runCatching { player?.takeIf { it.isPlaying }?.pause() }
    }

    fun release() {
        runCatching { player?.release() }
        player = null
        loadedFile = null
    }
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun LessonPlayer(
    timeline: LessonTimeline,
    audio: NarrationAudio?,
    initialMs: Long,
    onProgress: (sceneIndex: Int, positionMs: Long) -> Unit,
    onFinished: () -> Unit,
    modifier: Modifier = Modifier,
) {
    var t by remember(timeline) { mutableLongStateOf(initialMs.coerceIn(0, timeline.totalMs)) }
    var playing by remember { mutableStateOf(false) }
    var speedIdx by remember { mutableStateOf(0) }
    val speed = PLAYER_SPEEDS[speedIdx]
    var captions by remember { mutableStateOf(!timeline.hasAudio) }
    var seeking by remember { mutableStateOf<Float?>(null) }
    var audioOn by remember { mutableStateOf(false) }
    // Перезапуск часов после перемотки (playing мог остаться тем же значением).
    var epoch by remember { mutableStateOf(0) }
    val latestProgress by rememberUpdatedState(onProgress)
    val latestFinished by rememberUpdatedState(onFinished)
    val useAudio = audio != null && timeline.hasAudio

    // Часы плеера: по позиции аудио текущей сцены, без озвучки — по кадрам с учётом скорости.
    LaunchedEffect(playing, speed, timeline, epoch) {
        if (!playing) {
            audio?.pause(); audioOn = false
            latestProgress(timeline.sceneAt(t), t) // позиция сохраняется при каждой паузе
            return@LaunchedEffect
        }
        var scene = timeline.sceneAt(t)
        fun startAudio() {
            val s = timeline.scenes[scene]
            if (useAudio && s.audioFile != null && audio!!.load(s.audioFile)) {
                audio.play(t - s.startMs, speed)
                audioOn = true
            } else audioOn = false
        }
        startAudio()
        var last = withFrameMillis { it }
        var lastSaved = last
        while (playing) {
            val now = withFrameMillis { it }
            val s = timeline.scenes[scene]
            val pos = if (audioOn) audio!!.positionMs() else null
            val next = if (pos != null && audio!!.isPlaying) s.startMs + pos
            else t + ((now - last) * speed).toLong()
            last = now
            if (next >= s.endMs || (audioOn && !audio!!.isPlaying && (pos ?: 0) >= s.durationMs - 300)) {
                // Конец сцены: следующая сцена (или конец урока).
                if (scene + 1 >= timeline.scenes.size) {
                    t = timeline.totalMs; playing = false
                    latestProgress(scene, t); latestFinished()
                    break
                }
                scene += 1
                t = timeline.scenes[scene].startMs
                latestProgress(scene, t)
                startAudio()
            } else {
                t = maxOf(t, next)
            }
            if (now - lastSaved > 5000) { latestProgress(scene, t); lastSaved = now }
        }
    }
    // Пауза при сворачивании приложения; освобождение плеера при уходе с экрана.
    val lifecycle = LocalLifecycleOwner.current.lifecycle
    DisposableEffect(lifecycle) {
        val obs = LifecycleEventObserver { _, e -> if (e == Lifecycle.Event.ON_PAUSE) playing = false }
        lifecycle.addObserver(obs)
        onDispose {
            lifecycle.removeObserver(obs)
            audio?.release()
            latestProgress(timeline.sceneAt(t), t)
        }
    }

    fun seek(to: Long) {
        Log.i("CAPLAYER", "seek $to (scene ${timeline.sceneAt(to)})")
        t = to.coerceIn(0, timeline.totalMs)
        latestProgress(timeline.sceneAt(t), t)
        epoch++
    }

    val frame = timeline.frame(seeking?.toLong() ?: t)
    val sceneCount = timeline.scenes.size

    Card(modifier.fillMaxWidth().testTag("lesson-player")) {
        Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(
                "Сцена ${frame.sceneIndex + 1} из $sceneCount · ${frame.sceneTitle}",
                style = MaterialTheme.typography.titleSmall, modifier = Modifier.testTag("player-scene"),
            )
            CodePanel(frame.file, frame.code, frame.highlight, frame.typing)
            ConsolePanel(frame.running, frame.output, frame.outputIsError)
            AnimatedVisibility(frame.note != null) {
                Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.secondaryContainer)) {
                    Box(Modifier.padding(10.dp)) { MarkdownText(frame.note.orEmpty()) }
                }
            }
            if (captions) {
                Text(
                    frame.caption ?: " ",
                    style = MaterialTheme.typography.bodyMedium,
                    modifier = Modifier.fillMaxWidth().heightIn(min = 44.dp)
                        .background(MaterialTheme.colorScheme.surfaceVariant, RoundedCornerShape(8.dp))
                        .padding(8.dp).testTag("player-caption"),
                )
            }
            Slider(
                value = seeking ?: t.toFloat(),
                onValueChange = { seeking = it },
                onValueChangeFinished = { seeking?.let { seek(it.toLong()) }; seeking = null },
                valueRange = 0f..timeline.totalMs.coerceAtLeast(1).toFloat(),
                modifier = Modifier.testTag("player-seek"),
            )
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text("${fmt(seeking?.toLong() ?: t)} / ${fmt(timeline.totalMs)}", style = MaterialTheme.typography.labelMedium)
                if (audioOn) Text("  ♪", modifier = Modifier.testTag("player-audio-on").semantics { contentDescription = "Звук идёт" })
            }
            // FlowRow, а не прокрутка вбок: на узком экране кнопки переносятся и всегда видны.
            FlowRow(verticalArrangement = Arrangement.Center, horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                IconButton(onClick = {
                    val i = timeline.sceneAt(t)
                    // Как в плеерах: если сцена идёт дольше 2 с — в её начало, иначе к предыдущей.
                    val target = if (t - timeline.scenes[i].startMs > 2000 || i == 0) i else i - 1
                    seek(timeline.scenes[target].startMs)
                }, modifier = Modifier.testTag("player-prev").semantics { contentDescription = "Предыдущая сцена" }) { Text("⏮") }
                FilledIconButton(onClick = {
                    if (!playing && t >= timeline.totalMs) t = 0 // урок закончился — смотреть сначала
                    playing = !playing
                }, modifier = Modifier.testTag("player-play")) {
                    if (playing) Text("❚❚", modifier = Modifier.semantics { contentDescription = "Пауза" })
                    else Icon(Icons.Filled.PlayArrow, "Воспроизвести")
                }
                IconButton(onClick = {
                    val i = timeline.sceneAt(t)
                    if (i + 1 < sceneCount) seek(timeline.scenes[i + 1].startMs) else seek(timeline.totalMs)
                }, modifier = Modifier.testTag("player-next").semantics { contentDescription = "Следующая сцена" }) { Text("⏭") }
                TextButton(onClick = { speedIdx = (speedIdx + 1) % PLAYER_SPEEDS.size }, modifier = Modifier.testTag("player-speed")) {
                    Text("${speed.toString().removeSuffix(".0")}×")
                }
                TextButton(onClick = { captions = !captions }, modifier = Modifier.testTag("player-cc")) {
                    Text(if (captions) "Субтитры: вкл" else "Субтитры: выкл")
                }
            }
            if (!timeline.hasAudio) {
                Text("Озвучка этого урока ещё готовится — урок идёт с субтитрами.",
                    style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.outline)
            } else if (audio?.failed != null) {
                Text("Не удалось воспроизвести звук — урок идёт с субтитрами.",
                    style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.error)
            }
        }
    }
}

private fun fmt(ms: Long): String {
    val s = ms / 1000
    return "%d:%02d".format(s / 60, s % 60)
}

private val CODE_BG = Color(0xFF282C34)
private val CODE_FG = Color(0xFFDCDFE4)
private val LINE_NO = Color(0xFF7D8799)
private val HL_BG = Color(0xFF3E4451)

@Composable
private fun CodePanel(file: String, code: String, highlight: Set<Int>, typing: Boolean) {
    val lines = code.removeSuffix("\n").split("\n").let { if (code.isEmpty()) listOf("") else it }
    Column(
        Modifier.fillMaxWidth().background(CODE_BG, RoundedCornerShape(8.dp)).padding(vertical = 8.dp)
            .heightIn(min = 96.dp).testTag("player-code")
            .semantics { contentDescription = "Код: $code" },
    ) {
        Text(file, color = LINE_NO, style = MaterialTheme.typography.labelSmall, modifier = Modifier.padding(start = 12.dp, bottom = 4.dp))
        lines.forEachIndexed { i, line ->
            val n = i + 1
            Row(Modifier.fillMaxWidth().background(if (n in highlight) HL_BG else Color.Transparent).padding(horizontal = 8.dp)) {
                Text("$n", color = LINE_NO, fontFamily = FontFamily.Monospace, modifier = Modifier.width(28.dp),
                    style = MaterialTheme.typography.bodyMedium)
                Text(
                    buildAnnotatedString {
                        append(line)
                        // Курсор набора на последней строке.
                        if (typing && i == lines.lastIndex) withStyle(SpanStyle(color = Color(0xFF528BFF))) { append("▍") }
                    },
                    color = CODE_FG, fontFamily = FontFamily.Monospace, style = MaterialTheme.typography.bodyMedium,
                )
            }
        }
    }
}

@Composable
private fun ConsolePanel(running: Boolean, output: String, isError: Boolean) {
    Column(
        Modifier.fillMaxWidth().background(Color(0xFF1E1E1E), RoundedCornerShape(8.dp)).padding(10.dp)
            .heightIn(min = 56.dp).testTag("player-output"),
    ) {
        Text("Консоль", color = LINE_NO, style = MaterialTheme.typography.labelSmall)
        Text(
            when {
                running -> "▶ Выполняется…"
                output.isEmpty() -> ""
                else -> output.trimEnd()
            },
            color = if (isError) Color(0xFFFF7B72) else Color(0xFFE6EDF3),
            fontFamily = FontFamily.Monospace, style = MaterialTheme.typography.bodyMedium,
        )
    }
}
