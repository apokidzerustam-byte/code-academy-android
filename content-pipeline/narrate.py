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

PREVIOUS_REPORT: list = []
SETTINGS_VERSION = "2"  # меняется при изменении параметров синтеза → полная пересборка
CANDIDATES = 3  # вариантов каждой фразы; выбирается самый разборчивый по распознаванию
GEN_PARAMS = {"exaggeration": 0.45, "cfg_weight": 0.5, "temperature": 0.65}
ACUTE = "\u0301"
PRON_PATH = pathlib.Path(__file__).with_name("pronunciation.json")
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


def load_pronunciation() -> dict:
    data = json.loads(PRON_PATH.read_text("utf-8"))
    return {"words": {k.lower(): v for k, v in data.get("words", {}).items()},
            "stress": {k.lower(): v for k, v in data.get("stress", {}).items()}}


_WORD = re.compile(r"[A-Za-zА-Яа-яЁё\u0301-]+")


def spoken_form(text: str, pron: dict) -> str:
    """Как произносить: латиница и сокращения → русская запись (print → принт)."""
    def repl(m):
        w = m.group(0)
        r = pron["words"].get(w.lower())
        if r is None:
            return w
        return r[0].upper() + r[1:] if w[:1].isupper() and w.lower() != w.upper() and not w.isupper() else r
    # Латинские части отдельно: f в «f-строка», user и name в user_name; подчёркивание читается как пауза.
    return re.sub(r"[A-Za-z]+", repl, text).replace("_", " ")


def apply_stress(text: str, stress: dict, auto=None) -> str:
    """Ударения: автоматическая расстановка (если есть), затем словарь курса и сцены поверх неё.
    Слово сравнивается без знаков ударения и без учёта регистра."""
    if auto is not None:
        text = auto(text)
    lower = {k.lower(): v for k, v in stress.items()}

    def repl(m):
        w = m.group(0)
        key = w.replace(ACUTE, "").lower()
        if key in lower:
            fixed = lower[key]
            return fixed[0].upper() + fixed[1:] if w[:1].isupper() else fixed
        return w
    return _WORD.sub(repl, text)


def make_auto_stresser():
    """Автоматические ударения тем же инструментом, что ожидает Chatterbox (russian_text_stresser)."""
    try:
        from russian_text_stresser.text_stresser import RussianTextStresser
    except ImportError:
        return None
    ts = RussianTextStresser()
    return lambda t: ts.stress_text(t)


_TRANSLIT = dict(zip("абвгдеёжзийклмнопрстуфхцчшщъыьэюя",
                     ["a", "b", "v", "g", "d", "e", "e", "zh", "z", "i", "i", "k", "l", "m", "n", "o", "p", "r", "s",
                      "t", "u", "f", "h", "ts", "ch", "sh", "sch", "", "y", "", "e", "yu", "ya"]))


_ONES = ["ноль", "один", "два", "три", "четыре", "пять", "шесть", "семь", "восемь", "девять", "десять",
         "одиннадцать", "двенадцать", "тринадцать", "четырнадцать", "пятнадцать", "шестнадцать", "семнадцать",
         "восемнадцать", "девятнадцать"]
_TENS = ["", "", "двадцать", "тридцать", "сорок", "пятьдесят", "шестьдесят", "семьдесят", "восемьдесят", "девяносто"]
_HUNDREDS = ["", "сто", "двести", "триста", "четыреста", "пятьсот", "шестьсот", "семьсот", "восемьсот", "девятьсот"]


def _below_1000(n: int, fem=False) -> list:
    out = []
    if n >= 100:
        out.append(_HUNDREDS[n // 100]); n %= 100
    if n >= 20:
        out.append(_TENS[n // 10]); n %= 10
        if n == 0:
            return out
    if n or not out:
        w = _ONES[n]
        if fem and n in (1, 2):
            w = "одна" if n == 1 else "две"
        out.append(w)
    return out


def number_words(n: int, fem=False) -> str:
    """Целое число словами (до миллиона) — распознавание пишет «5», а в сценарии «пять»."""
    if n < 0:
        return "минус " + number_words(-n, fem)
    if n >= 1_000_000:
        return str(n)
    th, rest = divmod(n, 1000)
    words = []
    if th:
        words += _below_1000(th, fem=True)
        last = th % 100
        words.append("тысяча" if last % 10 == 1 and last != 11 else
                     "тысячи" if last % 10 in (2, 3, 4) and last not in (12, 13, 14) else "тысяч")
    if rest or not words:
        words += _below_1000(rest, fem)
    return " ".join(words)


def _num_repl(m) -> str:
    whole, frac = m.group(1), m.group(2)
    if not frac:
        return number_words(int(whole))
    unit = {1: "десятых", 2: "сотых", 3: "тысячных"}.get(len(frac), "")
    return f"{number_words(int(whole), fem=True)} целых {number_words(int(frac), fem=True)} {unit}"


def normalize_for_cer(text: str) -> str:
    """Сравнение в общей латинской записи: распознавание пишет «принт» вместо print и «5» вместо «пять» — это не ошибка озвучки."""
    t = re.sub(r"(?<![\w.])(\d+)(?:[.,](\d{1,3}))?(?![\d])", _num_repl, text.lower())
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


def clean_reference(src: str, dst: str):
    """Чистая опорная запись: срез низкого гула, шумоподавление, ровная громкость, моно 24 кГц, до 15 с."""
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-t", "15",
                    "-af", "highpass=f=70,afftdn=nf=-25,loudnorm=I=-20:TP=-2", "-ac", "1", "-ar", "24000", dst],
                   check=True)


class Narrator:
    def __init__(self, ref_wav: str):
        import torch
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS
        from faster_whisper import WhisperModel
        import chatterbox.models.tokenizers.tokenizer as tk

        # Ударения расставляем сами (с правками словаря) — встроенную расстановку отключаем, чтобы не было двойной.
        tk.add_russian_stress = lambda t: t

        torch.set_num_threads(os.cpu_count() or 2)
        self.torch = torch
        self.model = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
        self.sr = self.model.sr
        self.ref = "/tmp/ref_clean.wav"
        clean_reference(ref_wav, self.ref)
        self.pron = load_pronunciation()
        self.auto_stress = make_auto_stresser()
        if self.auto_stress is None:
            raise SystemExit("Нет russian_text_stresser: без него ударения будут случайными")
        self.asr = WhisperModel("small", device="cpu", compute_type="int8")

    def prepare(self, phrase: str, scene_stress: dict) -> str:
        """Текст для синтеза: произношение слов + ударения (автоматические, словарь курса, правки сцены)."""
        stress = {**self.pron["stress"], **scene_stress}
        return apply_stress(spoken_form(phrase, self.pron), stress, self.auto_stress)

    def transcribe(self, wav):
        import numpy as np
        import torchaudio.functional as F
        audio = F.resample(wav, self.sr, 16000).squeeze(0).numpy().astype(np.float32)
        segments, _ = self.asr.transcribe(audio, language="ru", beam_size=1, vad_filter=False)
        segments = list(segments)
        text = " ".join(s.text.strip() for s in segments)
        # Средняя уверенность распознавания: чем ближе к 0, тем разборчивее речь.
        logprob = sum(s.avg_logprob for s in segments) / len(segments) if segments else -5.0
        return text, logprob

    def generate(self, text: str):
        try:
            return self.model.generate(text, language_id="ru", audio_prompt_path=self.ref, **GEN_PARAMS)
        except TypeError:  # старая версия без этих параметров
            return self.model.generate(text, language_id="ru", audio_prompt_path=self.ref)

    def phrase(self, text: str, synth_text: str, seed: int):
        """Несколько вариантов фразы; выбирается самый разборчивый (точность распознавания + уверенность).
        Возвращает (wav, cer, attempts, heard, logprob)."""
        best, best_score = None, None
        attempt = 0
        while attempt < CANDIDATES or (best[1] > CER_LIMIT and attempt < CANDIDATES + MAX_ATTEMPTS):
            self.torch.manual_seed(seed + attempt * 7919)
            wav = trim_silence(self.generate(synth_text), self.sr)
            heard, logprob = self.transcribe(wav)
            c = cer(text, heard)
            score = 2.0 * c - logprob
            attempt += 1
            if best is None or score < best_score:
                best, best_score = (wav, c, attempt, heard, logprob), score
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


def narrate_lesson(lesson_dir: pathlib.Path, narrator_factory, ref_digest: str, voice: str, report: list, preparer):
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
        # Текст для синтеза (произношение + ударения): правка словаря тоже пересобирает затронутые сцены.
        spoken = [preparer(ph, scene.get("stress", {})) for ph in split_phrases(scene["narration"])]
        same_spoken = prev is not None and prev.get("spoken", spoken) == spoken
        if prev and prev.get("hash") == h and same_spoken and (audio_dir / file_name).exists():
            scenes_meta.append(prev)
            # Сцена не менялась — в отчёте остаются результаты проверки её прошлой озвучки.
            old_rows = [r for r in PREVIOUS_REPORT if r.get("lesson") == lesson_dir.name and r.get("scene") == scene["id"] and "cer" in r]
            report.extend(old_rows or [{"lesson": lesson_dir.name, "scene": scene["id"], "cached": True}])
            continue
        narrator = narrator_factory()
        torch = narrator.torch
        phrases = split_phrases(scene["narration"])
        gap = torch.zeros(1, int(narrator.sr * SAMPLE_GAP_MS / 1000))
        chunks, cues, pos = [], [], 0
        t0 = time.monotonic()
        for k, ph in enumerate(phrases):
            synth = spoken[k]  # тот же текст, что сохраняется в narration.json
            wav, score, attempts, heard, logprob = narrator.phrase(ph, synth, seed=1000 * idx + k)
            dur = int(wav.shape[-1] * 1000 / narrator.sr)
            cues.append({"startMs": pos, "endMs": pos + dur, "text": ph})
            chunks += [wav, gap]
            pos += dur + SAMPLE_GAP_MS
            report.append({"lesson": lesson_dir.name, "scene": scene["id"], "phrase": ph, "spoken": synth,
                           "cer": round(score, 3), "logprob": round(logprob, 3), "attempts": attempts, "heard": heard})
            print(f"  [{scene['id']}] {k + 1}/{len(phrases)} cer={score:.2f} x{attempts}", flush=True)
        wav = torch.cat(chunks[:-1], dim=-1)
        encode_m4a(wav, narrator.sr, audio_dir / file_name, torch)
        real_ms = probe_ms(audio_dir / file_name)
        # Тайминги фраз масштабируются к фактической длительности файла (кодек слегка меняет длину).
        k = real_ms / max(1, pos - SAMPLE_GAP_MS)
        for c in cues:
            c["startMs"], c["endMs"] = int(c["startMs"] * k), int(c["endMs"] * k)
        scenes_meta.append({"id": scene["id"], "file": file_name, "durationMs": real_ms, "hash": h,
                            "textHash": text_hash(scene), "spoken": spoken, "cues": cues})
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
    ap.add_argument("--probe", action="store_true", help="только показать текст для синтеза с ударениями")
    ap.add_argument("--lesson", help="озвучить только этот урок (id папки), для параллельных запусков")
    a = ap.parse_args()

    if a.probe:
        pron, auto = load_pronunciation(), make_auto_stresser()
        print("Автоматические ударения:", "есть" if auto else "НЕТ (russian_text_stresser не установлен)")
        for scen in sorted(pathlib.Path(a.packs).glob("*/lessons/*/scenario.json")):
            for scene in json.loads(scen.read_text("utf-8"))["scenes"]:
                for ph in split_phrases(scene["narration"]):
                    stress = {**pron["stress"], **scene.get("stress", {})}
                    print(f"[{scene['id']}] {apply_stress(spoken_form(ph, pron), stress, auto)}")
        return 0

    ref_digest = hashlib.sha256(pathlib.Path(a.ref).read_bytes()).hexdigest()[:16]
    holder = {}

    def factory():
        if "n" not in holder:  # модели грузятся, только если есть что синтезировать
            holder["n"] = Narrator(a.ref)
        return holder["n"]

    global PREVIOUS_REPORT
    try:
        PREVIOUS_REPORT = json.loads(pathlib.Path(a.report).read_text("utf-8"))
    except (OSError, ValueError):
        PREVIOUS_REPORT = []
    pron, auto = load_pronunciation(), make_auto_stresser()
    if auto is None:
        raise SystemExit("Нет russian_text_stresser: без него ударения будут случайными")

    def preparer(phrase, scene_stress):
        return apply_stress(spoken_form(phrase, pron), {**pron["stress"], **scene_stress}, auto)

    report = []
    for scen in sorted(pathlib.Path(a.packs).glob("*/lessons/*/scenario.json")):
        if a.lesson and scen.parent.name != a.lesson:
            continue
        print(f"== {scen.parent}", flush=True)
        narrate_lesson(scen.parent, factory, ref_digest, a.voice, report, preparer)
    pathlib.Path(a.report).write_text(json.dumps(report, ensure_ascii=False, indent=1), "utf-8")
    bad = [r for r in report if r.get("cer", 0) > CER_LIMIT]
    print(f"Фраз: {sum(1 for r in report if 'cer' in r)}, выше порога CER: {len(bad)}")
    for r in bad:
        print(f"  ! {r['scene']}: cer={r['cer']} «{r['phrase']}» → «{r['heard']}»")
    # Фразы выше порога не роняют задачу (иначе теряется озвучка всего урока из-за одной фразы с числами):
    # они попадают в отчёт и в сводку запуска, автор правит текст или ударения, и пересобирается только эта сцена.
    if bad and os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write("### Фразы с ошибкой распознавания выше порога\n")
            for r in bad:
                f.write(f"- {r['lesson']}/{r['scene']}: CER {r['cer']} «{r['phrase']}» → «{r['heard']}»\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
