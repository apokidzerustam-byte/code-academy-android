"""Озвучка уроков голосом автора (Chatterbox Multilingual, MIT) + субтитры WebVTT.

Для каждого урока со сценарием (content/packs/*/lessons/*/scenario.json):
  audio/<scene-id>.m4a   — озвучка сцены (AAC, моно, нормализованная громкость);
  audio/narration.json   — длительности сцен и тайминги фраз (для синхронизации анимации и субтитров);
  audio/subtitles.vtt    — субтитры всего урока.

Сцена пересинтезируется только если изменился её текст (хэш), опорный голос или настройки.
Каждая фраза проверяется распознаванием речи (faster-whisper): если распознанный текст слишком
отличается от сценария (CER > порога), фраза синтезируется заново с другим seed.
Во всех файлах Chatterbox есть неслышимый водяной знак Perth (признак синтеза).

Запуск: python content-pipeline/narrate.py ref.wav [content/packs] [--voice author] [--report out.json]
"""
import argparse
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import time

SETTINGS_VERSION = "1"  # меняется при изменении параметров синтеза → полная пересборка
SAMPLE_GAP_MS = 280  # пауза между фразами
CER_LIMIT = 0.22
MAX_ATTEMPTS = 3
MAX_PHRASE_CHARS = 220


def split_phrases(text: str) -> list[str]:
    """Фразы по концам предложений; слишком длинные — по запятым/тире (модель стабильнее на коротких фразах)."""
    sentences = [s.strip() for s in re.split(r"(?<=[.!?…])\s+", text.strip()) if s.strip()]
    out = []
    for s in sentences:
        while len(s) > MAX_PHRASE_CHARS:
            cut = max(s.rfind(", ", 0, MAX_PHRASE_CHARS), s.rfind(" — ", 0, MAX_PHRASE_CHARS), s.rfind(": ", 0, MAX_PHRASE_CHARS))
            if cut < 40:
                cut = s.rfind(" ", 0, MAX_PHRASE_CHARS)
            if cut <= 0:
                break
            out.append(s[: cut + 1].strip())
            s = s[cut + 1 :].strip()
        if s:
            out.append(s)
    return out


def apply_stress(text: str, stress: dict) -> str:
    for word, repl in stress.items():
        text = re.sub(rf"\b{re.escape(word)}\b", repl, text)
    return text


_TRANSLIT = dict(zip("абвгдеёжзийклмнопрстуфхцчшщъыьэюя",
                     ["a", "b", "v", "g", "d", "e", "e", "zh", "z", "i", "i", "k", "l", "m", "n", "o", "p", "r", "s",
                      "t", "u", "f", "h", "ts", "ch", "sh", "sch", "", "y", "", "e", "yu", "ya"]))


def normalize_for_cer(text: str) -> str:
    """Сравнение в общей латинской записи: распознавание пишет «принт» вместо print — это не ошибка озвучки."""
    t = text.lower()
    t = "".join(_TRANSLIT.get(ch, ch) for ch in t)
    t = t.replace("th", "t").replace("y", "i").replace("w", "v").replace("c", "k").replace("x", "ks")
    t = re.sub(r"[^a-z0-9 ]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def cer(ref: str, hyp: str) -> float:
    a, b = normalize_for_cer(ref), normalize_for_cer(hyp)
    if not a:
        return 0.0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i] + [0] * len(b)
        for j, cb in enumerate(b, 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb))
        prev = cur
    return prev[-1] / len(a)


def text_hash(scene: dict) -> str:
    """Хэш текста сцены — по нему валидатор видит устаревшую озвучку без доступа к записи автора."""
    payload = json.dumps([scene["narration"], scene.get("stress", {})], ensure_ascii=False)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def scene_hash(scene: dict, ref_digest: str) -> str:
    payload = json.dumps([SETTINGS_VERSION, ref_digest, scene["narration"], scene.get("stress", {})], ensure_ascii=False)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def ms_to_vtt(ms: int) -> str:
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def trim_silence(wav, sr, threshold=0.012, pad_ms=60):
    """Обрезает тишину и «хвосты» по краям фразы."""
    import torch
    x = wav.abs().max(dim=0).values if wav.dim() == 2 else wav.abs()
    win = max(1, sr // 100)
    n = x.shape[-1] // win
    if n == 0:
        return wav
    energy = x[: n * win].reshape(n, win).mean(dim=1)
    loud = torch.nonzero(energy > threshold).flatten()
    if loud.numel() == 0:
        return wav
    pad = int(sr * pad_ms / 1000)
    start = max(0, int(loud[0]) * win - pad)
    end = min(wav.shape[-1], (int(loud[-1]) + 1) * win + pad)
    return wav[..., start:end]


class Narrator:
    def __init__(self, ref_wav: str):
        import torch
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS
        from faster_whisper import WhisperModel

        torch.set_num_threads(os.cpu_count() or 2)
        self.torch = torch
        self.model = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
        self.sr = self.model.sr
        self.ref = ref_wav
        self.asr = WhisperModel("small", device="cpu", compute_type="int8")

    def transcribe(self, wav) -> str:
        import numpy as np
        import torchaudio.functional as F
        audio = F.resample(wav, self.sr, 16000).squeeze(0).numpy().astype(np.float32)
        segments, _ = self.asr.transcribe(audio, language="ru", beam_size=1, vad_filter=False)
        return " ".join(s.text.strip() for s in segments)

    def phrase(self, text: str, synth_text: str, seed: int):
        """Синтез с проверкой распознаванием; возвращает (wav, cer, attempts, heard)."""
        best = None
        for attempt in range(MAX_ATTEMPTS):
            self.torch.manual_seed(seed + attempt * 7919)
            wav = self.model.generate(synth_text, language_id="ru", audio_prompt_path=self.ref)
            wav = trim_silence(wav, self.sr)
            heard = self.transcribe(wav)
            score = cer(text, heard)
            if best is None or score < best[1]:
                best = (wav, score, attempt + 1, heard)
            if score <= CER_LIMIT:
                break
        return best


def encode_m4a(wav, sr, path: pathlib.Path, torch):
    import torchaudio as ta
    with tempfile.TemporaryDirectory() as tmp:
        raw = pathlib.Path(tmp) / "s.wav"
        ta.save(str(raw), wav, sr)
        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "error", "-i", str(raw),
            "-af", "loudnorm=I=-18:TP=-1.5:LRA=11", "-ar", "44100", "-ac", "1",
            "-c:a", "aac", "-b:a", "64k", "-movflags", "+faststart", str(path),
        ], check=True)


def probe_ms(path: pathlib.Path) -> int:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True, check=True).stdout
    return int(round(float(out.strip()) * 1000))


def narrate_lesson(lesson_dir: pathlib.Path, narrator_factory, ref_digest: str, voice: str, report: list):
    scenario = json.loads((lesson_dir / "scenario.json").read_text("utf-8"))
    audio_dir = lesson_dir / "audio"
    audio_dir.mkdir(exist_ok=True)
    meta_path = audio_dir / "narration.json"
    old = json.loads(meta_path.read_text("utf-8")) if meta_path.exists() else {"scenes": []}
    old_by_id = {s["id"]: s for s in old.get("scenes", [])}

    scenes_meta = []
    for idx, scene in enumerate(scenario["scenes"]):
        h = scene_hash(scene, ref_digest)
        file_name = f"{scene['id']}.m4a"
        prev = old_by_id.get(scene["id"])
        if prev and prev.get("hash") == h and (audio_dir / file_name).exists():
            scenes_meta.append(prev)
            report.append({"lesson": lesson_dir.name, "scene": scene["id"], "cached": True})
            continue
        narrator = narrator_factory()
        torch = narrator.torch
        phrases = split_phrases(scene["narration"])
        gap = torch.zeros(1, int(narrator.sr * SAMPLE_GAP_MS / 1000))
        chunks, cues, pos = [], [], 0
        t0 = time.monotonic()
        for k, ph in enumerate(phrases):
            wav, score, attempts, heard = narrator.phrase(ph, apply_stress(ph, scene.get("stress", {})),
                                                         seed=1000 * idx + k)
            dur = int(wav.shape[-1] * 1000 / narrator.sr)
            cues.append({"startMs": pos, "endMs": pos + dur, "text": ph})
            chunks += [wav, gap]
            pos += dur + SAMPLE_GAP_MS
            report.append({"lesson": lesson_dir.name, "scene": scene["id"], "phrase": ph, "cer": round(score, 3),
                           "attempts": attempts, "heard": heard})
            print(f"  [{scene['id']}] {k + 1}/{len(phrases)} cer={score:.2f} x{attempts}", flush=True)
        wav = torch.cat(chunks[:-1], dim=-1)
        encode_m4a(wav, narrator.sr, audio_dir / file_name, torch)
        real_ms = probe_ms(audio_dir / file_name)
        # Тайминги фраз масштабируются к фактической длительности файла (кодек слегка меняет длину).
        k = real_ms / max(1, pos - SAMPLE_GAP_MS)
        for c in cues:
            c["startMs"], c["endMs"] = int(c["startMs"] * k), int(c["endMs"] * k)
        scenes_meta.append({"id": scene["id"], "file": file_name, "durationMs": real_ms, "hash": h,
                            "textHash": text_hash(scene), "cues": cues})
        print(f"[{lesson_dir.name}/{scene['id']}] {real_ms / 1000:.1f} c за {time.monotonic() - t0:.0f} c", flush=True)

    # Удаляем аудио сцен, которых больше нет в сценарии.
    keep = {s["file"] for s in scenes_meta}
    for f in audio_dir.glob("*.m4a"):
        if f.name not in keep:
            f.unlink()

    meta = {"voice": voice, "engine": "chatterbox-multilingual", "watermark": "perth", "scenes": scenes_meta}
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n", "utf-8")

    lines, offset = ["WEBVTT", ""], 0
    for s in scenes_meta:
        for c in s["cues"]:
            lines += [f"{ms_to_vtt(offset + c['startMs'])} --> {ms_to_vtt(offset + c['endMs'])}", c["text"], ""]
        offset += s["durationMs"]
    (audio_dir / "subtitles.vtt").write_text("\n".join(lines), "utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ref")
    ap.add_argument("packs", nargs="?", default="content/packs")
    ap.add_argument("--voice", default="author")
    ap.add_argument("--report", default="narration-report.json")
    a = ap.parse_args()

    ref_digest = hashlib.sha256(pathlib.Path(a.ref).read_bytes()).hexdigest()[:16]
    holder = {}

    def factory():
        if "n" not in holder:  # модели грузятся, только если есть что синтезировать
            holder["n"] = Narrator(a.ref)
        return holder["n"]

    report = []
    for scen in sorted(pathlib.Path(a.packs).glob("*/lessons/*/scenario.json")):
        print(f"== {scen.parent}", flush=True)
        narrate_lesson(scen.parent, factory, ref_digest, a.voice, report)
    pathlib.Path(a.report).write_text(json.dumps(report, ensure_ascii=False, indent=1), "utf-8")
    bad = [r for r in report if r.get("cer", 0) > CER_LIMIT]
    print(f"Фраз: {sum(1 for r in report if 'cer' in r)}, выше порога CER: {len(bad)}")
    for r in bad:
        print(f"  ! {r['scene']}: cer={r['cer']} «{r['phrase']}» → «{r['heard']}»")
    # Плохо распознанные фразы не попадают в приложение: job падает, коммита нет, автор правит текст/ударения.
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
