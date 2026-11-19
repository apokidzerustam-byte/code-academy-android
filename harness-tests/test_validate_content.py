"""Валидатор должен ловить испорченный контент (мутационные тесты)."""
import json
import pathlib
import shutil
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import validate_content as vc  # noqa: E402

LESSON = "lessons/py-01-print"


@pytest.fixture
def pack(tmp_path):
    dst = tmp_path / "python-basics"
    shutil.copytree(ROOT / "content" / "packs" / "python-basics", dst)
    # Мутационные тесты — на первом уроке (весь пакет целиком проверяет CI-валидатор).
    pj = dst / "pack.json"
    data = json.loads(pj.read_text(encoding="utf-8"))
    data["lessons"] = [LESSON.split("/")[-1]]
    pj.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return dst


def errors(pack):
    rep = vc.Report()
    vc.validate_pack(pack, rep)
    return rep.errors


def edit_json(path, fn):
    data = json.loads(path.read_text(encoding="utf-8"))
    fn(data)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def test_original_is_valid(pack):
    assert errors(pack) == []


def test_scenario_output_mismatch_detected(pack):
    def f(s):
        s["scenes"][2]["actions"][1]["text"] = "Привет, мир\n"
    edit_json(pack / LESSON / "scenario.json", f)
    assert any("анимация покажет" in e for e in errors(pack))


def test_scenario_crashing_code_detected(pack):
    def f(s):
        s["scenes"][1]["actions"][1]["text"] = "print(\"Привет, мир!\"\n"
    edit_json(pack / LESSON / "scenario.json", f)
    assert any("код сцены упал" in e for e in errors(pack))


def test_broken_reference_solution_detected(pack):
    edit_json(pack / LESSON / "assignments/a1-hello.json", lambda a: a.update(solution="print('Привет, мир!')\n"))
    assert any("эталонное решение НЕ проходит" in e for e in errors(pack))


def test_weak_tests_detected(pack):
    def f(a):
        a["wrongSolutions"].append({"code": "print(\"Привет, мир!\")\nprint(\"Я учу Python\")  \n", "why": "те же строки с пробелом"})
    edit_json(pack / LESSON / "assignments/a1-hello.json", f)
    assert any("НЕ ловят типовую ошибку" in e for e in errors(pack))


def test_starter_that_already_passes_detected(pack):
    edit_json(pack / LESSON / "assignments/a2-fix-quote.json",
              lambda a: a.update(starterCode="print(\"Программирование — это интересно!\")\n"))
    assert any("заготовка уже проходит" in e for e in errors(pack))


def test_wrong_predict_answer_detected(pack):
    def f(a):
        a["tests"]["expected_answer"] = "10 - 4\n10 - 4\nГотово\n"
        a["solution"] = a["tests"]["expected_answer"]
    edit_json(pack / LESSON / "assignments/a3-predict.json", f)
    assert any("не совпадает с реальным выводом" in e for e in errors(pack))


def test_schema_violation_detected(pack):
    edit_json(pack / LESSON / "assignments/a1-hello.json", lambda a: a["hints"].pop())
    assert any("схема assignment" in e for e in errors(pack))


def test_broken_notes_code_detected(pack):
    p = pack / LESSON / "notes.md"
    p.write_text(p.read_text(encoding="utf-8") + "\n```python\nprint(\n```\n", encoding="utf-8")
    assert any("блок кода" in e for e in errors(pack))


def test_missing_file_detected(pack):
    (pack / LESSON / "notes.md").unlink()
    assert any("нет файла notes.md" in e for e in errors(pack))


def test_bad_cues_detected(pack):
    def f(s):
        s["scenes"][2]["actions"][0]["cue"] = 99          # нет такой фразы
        s["scenes"][5]["actions"][4]["cue"] = 0           # раньше предыдущей опорной точки
    edit_json(pack / LESSON / "scenario.json", f)
    errs = errors(pack)
    assert any("фраз в озвучке" in e for e in errs)
    assert any("раньше предыдущего" in e for e in errs)


def test_wrong_error_message_detected(pack):
    def f(s):
        s["scenes"][5]["actions"][3]["text"] = "NameError: name 'x' is not defined\n"
    edit_json(pack / LESSON / "scenario.json", f)
    assert any("в сообщении об ошибке нет" in e for e in errors(pack))


def test_stale_and_missing_audio(pack):
    audio = pack / LESSON / "audio"
    (audio / "run.m4a").unlink()
    edit_json(pack / LESSON / "scenario.json", lambda s: s["scenes"][0].__setitem__("narration", "Новый текст."))
    rep = vc.Report()
    vc.validate_pack(pack, rep)
    assert any("нет файла run.m4a" in e for e in rep.errors)
    assert any("изменился после озвучки" in w for w in rep.warnings)
