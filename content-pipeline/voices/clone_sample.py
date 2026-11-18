"""Озвучка урока клонированным голосом: Chatterbox Multilingual (MIT), язык ru.

Опорная запись: файл из аргумента (запись автора курса или опорный голос Piper).
Каждый файл Chatterbox содержит неслышимый водяной знак Perth (признак синтеза).
"""
import json
import pathlib
import sys
import time

TEXT = (
    "Привет! Это первый урок Code Academy. "
    "Сегодня мы напишем программу на Python, которая здоровается с пользователем. "
    "Функция print выводит текст на экран. Напишите print, откройте круглую скобку "
    "и в кавычках введите: Привет, мир. "
    "Нажмите кнопку «Запустить» — и в консоли появится результат. "
    "Если вы увидели ошибку SyntaxError, проверьте, закрыта ли скобка."
)


def main(ref_wav, out_mp3, name):
    import subprocess
    import torch
    import torchaudio as ta
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS

    import os
    torch.set_num_threads(os.cpu_count() or 2)
    t0 = time.monotonic()
    model = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
    load_s = time.monotonic() - t0

    # Модель лучше работает с фразами средней длины: синтезируем по предложениям.
    parts = [p.strip() for p in TEXT.replace("! ", "!|").replace(". ", ".|").split("|") if p.strip()]
    t1 = time.monotonic()
    wavs = [model.generate(p, language_id="ru", audio_prompt_path=ref_wav) for p in parts]
    synth_s = time.monotonic() - t1
    wav = torch.cat(wavs, dim=-1)
    tmp = pathlib.Path(out_mp3).with_suffix(".wav")
    ta.save(str(tmp), wav, model.sr)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(tmp), "-b:a", "96k", out_mp3], check=True)
    seconds = wav.shape[-1] / model.sr
    tmp.unlink()
    report = {name: {"seconds": round(seconds, 1), "synthSeconds": round(synth_s, 1),
                     "realtimeFactor": round(synth_s / seconds, 2), "modelLoadSeconds": round(load_s, 1),
                     "threads": torch.get_num_threads()}}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "clone")
