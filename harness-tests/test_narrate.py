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


def test_spoken_form_and_dictionary_stress():
    pron = narrate.load_pronunciation()
    out = narrate.apply_stress(narrate.spoken_form("Python сообщает: SyntaxError — синтаксическая ошибка.", pron), pron["stress"])
    assert out == "Пайтон сообщает: Си́нтакс э́ррор — синтакси́ческая оши́бка."
    # Словарь поверх автоматических ударений; регистр сохраняется.
    auto = lambda t: t.replace("Программа", "Програ́мма").replace("ошибка", "ошибка́")
    assert narrate.apply_stress("Программа и ошибка", pron["stress"], auto) == "Програ́мма и оши́бка"
    # Каждое слово-ключ словаря произношения — одно слово без пробелов.
    assert all(" " not in k for k in pron["words"])
    # Знак ударения стоит только после гласной.
    for v in list(pron["stress"].values()) + list(pron["words"].values()):
        for i, ch in enumerate(v):
            if ch == narrate.ACUTE:
                assert v[i - 1].lower() in "аеёиоуыэюя", v


def test_latin_parts_inside_words():
    pron = narrate.load_pronunciation()
    assert narrate.spoken_form("f-строка и user_name", pron) == "эф-строка и ю́зер нэйм"
    # Слова без записи в словаре не меняются.
    assert narrate.spoken_form("Haskell", pron) == "Haskell"


def test_numbers_in_recognition_are_not_errors():
    assert narrate.number_words(21) == "двадцать один"
    assert narrate.number_words(5050) == "пять тысяч пятьдесят"
    assert narrate.number_words(1024) == "одна тысяча двадцать четыре"
    assert narrate.cer("Возьмём оценки: пять, четыре, три, пять, четыре.", "Возьмем оценки 5, 4, 3, 5, 4.") == 0
    assert narrate.cer("четыре целых две десятых", "4,2") == 0
    assert narrate.cer("Вводим два, семь и один.", "Вводим 2, 7 и 1.") == 0
    assert narrate.cer("пять тысяч пятьдесят", "5050") == 0


def test_percent_sign():
    assert narrate.cer("Запускаем: Скидка десять процентов.", "Запускаем скидка 10%.") == 0
