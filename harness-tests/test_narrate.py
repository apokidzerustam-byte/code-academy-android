import importlib.util
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("narrate", ROOT / "content-pipeline" / "narrate.py")
narrate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(narrate)


def test_split_phrases_sentences_and_long():
    assert narrate.split_phrases("Привет! Как дела? Хорошо… Пока.") == ["Привет!", "Как дела?", "Хорошо…", "Пока."]
    long = "Слово, " * 60 + "конец."
    parts = narrate.split_phrases(long)
    assert all(len(p) <= narrate.MAX_PHRASE_CHARS for p in parts)
    assert " ".join(parts).replace("  ", " ") == long.strip()


def test_cer():
    assert narrate.cer("Привет, мир!", "привет мир") == 0
    assert narrate.cer("ёлка", "елка") == 0
    assert narrate.cer("функция print", "функция принт") == 0
    assert narrate.cer("Я учу Python", "я учу питон") < 0.2
    assert narrate.cer("Пишем слово print маленькими буквами", "пишем слово маленькими") > 0.1
    assert narrate.cer("абв", "") == 1


def test_stress_and_vtt():
    assert narrate.apply_stress("замок и замокнуть", {"замок": "за́мок"}) == "за́мок и замокнуть"
    assert narrate.ms_to_vtt(3_723_045) == "01:02:03.045"


def test_hashes_depend_on_text_and_voice():
    s = {"narration": "Текст", "actions": []}
    assert narrate.scene_hash(s, "a") != narrate.scene_hash(s, "b")
    assert narrate.text_hash(s) != narrate.text_hash({"narration": "Другой", "actions": []})
    assert narrate.text_hash(s) == narrate.text_hash({"narration": "Текст", "stress": {}, "actions": []})


def test_real_scenarios_split_reasonably():
    for p in (ROOT / "content" / "packs").glob("*/lessons/*/scenario.json"):
        for scene in json.loads(p.read_text("utf-8"))["scenes"]:
            phrases = narrate.split_phrases(scene["narration"])
            assert phrases and all(3 <= len(x) <= narrate.MAX_PHRASE_CHARS for x in phrases), scene["id"]
