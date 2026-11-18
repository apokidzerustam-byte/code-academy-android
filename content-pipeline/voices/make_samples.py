"""Образцы озвучки уроков голосами Piper (только голоса с лицензией датасета CC0).

Запускается в CI (workflow voices.yml). Piper (GPL-3.0) используется только
в конвейере производства контента и в APK не попадает.
"""
import json
import pathlib
import subprocess
import sys
import time
import urllib.request
import wave

BASE = "https://huggingface.co/rhasspy/piper-voices/resolve/main/ru/ru_RU"
VOICES = {
    # имя: (папка, качество) — лицензия датасета: CC0 (OHF-Voice/voice-datasets)
    "denis": ("denis", "medium"),
    "dmitri": ("dmitri", "medium"),
}

TEXT = (
    "Привет! Это первый урок Code Academy. "
    "Сегодня мы напишем программу на Python, которая здоровается с пользователем. "
    "Функция print выводит текст на экран. Напишите print, откройте круглую скобку "
    "и в кавычках введите: Привет, мир. "
    "Нажмите кнопку «Запустить» — и в консоли появится результат. "
    "Если вы увидели ошибку SyntaxError, проверьте, закрыта ли скобка. "
    "Переменная x равна двенадцати, а список содержит три элемента: 3, 7 и 15."
)


def fetch(url, dest):
    if not dest.exists():
        urllib.request.urlretrieve(url, dest)
    return dest


def main(out_dir):
    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "sample_text.txt").write_text(TEXT, encoding="utf-8")
    from piper import PiperVoice

    report = {}
    for name, (folder, quality) in VOICES.items():
        stem = f"ru_RU-{folder}-{quality}"
        model = fetch(f"{BASE}/{folder}/{quality}/{stem}.onnx", out / f"{stem}.onnx")
        fetch(f"{BASE}/{folder}/{quality}/{stem}.onnx.json", out / f"{stem}.onnx.json")
        fetch(f"{BASE}/{folder}/{quality}/MODEL_CARD", out / f"{stem}.MODEL_CARD.txt")
        voice = PiperVoice.load(str(model))
        wav_path = out / f"sample_{name}.wav"
        t0 = time.monotonic()
        with wave.open(str(wav_path), "wb") as wf:
            voice.synthesize_wav(TEXT, wf)
        synth_s = time.monotonic() - t0
        mp3 = out / f"sample_{name}.mp3"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav_path), "-b:a", "96k", str(mp3)], check=True)
        with wave.open(str(wav_path)) as wf:
            dur = wf.getnframes() / wf.getframerate()
        report[name] = {"seconds": round(dur, 1), "synthSeconds": round(synth_s, 2), "mp3KB": mp3.stat().st_size // 1024}
        (out / f"{stem}.onnx").unlink()  # модель не нужна в артефакте
        wav_path.unlink()
    (out / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "voice-samples")
