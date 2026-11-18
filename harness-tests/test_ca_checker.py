"""Тесты автопроверки заданий (ca_runner.check)."""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app", "src", "main", "python"))
import ca_runner  # noqa: E402

GREET = {
    "kind": "stdout",
    "cases": [
        {"id": "v1", "stdin": "Аня\n", "expected_stdout": "Привет, Аня!\n"},
        {"id": "h1", "stdin": "Борис\n", "expected_stdout": "Привет, Борис!\n", "hidden": True, "hint": "Имя берётся из input()"},
    ],
}
ADD = {
    "kind": "function", "function": "add",
    "cases": [
        {"id": "v1", "args": [2, 3], "expected": 5},
        {"id": "h1", "args": [-1, 1], "expected": 0, "hidden": True, "hint": "Отрицательные числа"},
        {"id": "h2", "args": [0.1, 0.2], "expected": 0.3, "hidden": True, "hint": "Дробные числа"},
    ],
}
DIV = {
    "kind": "function", "function": "safe_div",
    "cases": [
        {"id": "v1", "args": [6, 3], "expected": 2.0},
        {"id": "e1", "args": [1, 0], "expected_error": "ZeroDivisionError", "hint": "Деление на ноль должно вызывать ошибку"},
    ],
}


def check(code, spec, box):
    return json.loads(ca_runner.check(code, json.dumps(spec), str(box)))


@pytest.fixture
def box(tmp_path):
    d = tmp_path / "p"
    d.mkdir()
    return d


def test_stdout_correct(box):
    r = check("name = input()\nprint(f'Привет, {name}!')", GREET, box)
    assert r["allPassed"] and r["passed"] == 2


def test_stdout_trailing_spaces_tolerated(box):
    r = check("print('Привет, ' + input() + '!   ')\n\n", GREET, box)
    assert r["allPassed"]


def test_hardcoded_answer_fails_hidden(box):
    r = check("input()\nprint('Привет, Аня!')", GREET, box)
    assert not r["allPassed"] and r["passed"] == 1
    hidden = [c for c in r["cases"] if c["hidden"]][0]
    assert hidden["passed"] is False and hidden["hint"] == "Имя берётся из input()"
    assert "expected" not in hidden and "input" not in hidden  # скрытые данные не раскрываются


def test_visible_failure_shows_expected_and_actual(box):
    r = check("print('Привет,', input())", GREET, box)
    v = r["cases"][0]
    assert v["passed"] is False and v["expected"] == "Привет, Аня!" and v["actual"] == "Привет, Аня"


def test_syntax_error_reported_once(box):
    r = check("print('x'", GREET, box)
    assert "SyntaxError" in r["compileError"] and r["allPassed"] is False


def test_function_correct_with_float_tolerance(box):
    r = check("def add(a, b):\n    return a + b", ADD, box)
    assert r["allPassed"], r


def test_function_wrong_and_missing(box):
    assert check("def add(a, b):\n    return a - b", ADD, box)["passed"] == 0
    r = check("def plus(a, b):\n    return a + b", ADD, box)
    assert "add()" in r["loadError"]


def test_function_expected_error(box):
    r = check("def safe_div(a, b):\n    return a / b", DIV, box)
    assert r["allPassed"], r
    r2 = check("def safe_div(a, b):\n    return a / b if b else 0", DIV, box)
    assert r2["passed"] == 1


def test_runtime_error_in_case_reported(box):
    r = check("def add(a, b):\n    return a + b + undefined_name", ADD, box)
    assert r["passed"] == 0 and "NameError" in r["cases"][0]["error"]
    assert r["cases"][1]["error"].startswith("NameError")  # скрытый тест — только последняя строка


def test_checker_respects_sandbox(box, tmp_path):
    secret = tmp_path / "secret.txt"
    secret.write_text("x")
    spec = {"kind": "function", "function": "f", "cases": [{"id": "v1", "args": [], "expected": "x"}]}
    r = check(f"def f():\n    return open({str(secret)!r}).read()", spec, box)
    assert r["passed"] == 0 and "песочниц" in r["cases"][0]["error"]


def test_module_level_output_does_not_break_function_tests(box):
    r = check("print('отладка')\ndef add(a, b):\n    return a + b", ADD, box)
    assert r["allPassed"]


PREDICT = {"kind": "answer", "expected_answer": "10 - 4\n6\nГотово\n"}


def test_answer_kind(box):
    spec = {"kind": "answer", "expected_answer": "2 + 3\n5\n"}
    assert check("2 + 3\n5", spec, box)["allPassed"]
    assert check("2 + 3\n5   \n\n", spec, box)["allPassed"]
    r = check("5\n5", spec, box)
    assert not r["allPassed"] and r["cases"][0]["hint"]


def test_answer_explains_typical_mistakes(box):
    # Реальный ответ ученика со скриншота.
    r = check('10-4\n6\n"Готово"', PREDICT, box)
    assert r["passed"] == 1 and r["total"] == 3 and not r["allPassed"]
    l1, l2, l3 = r["cases"]
    assert "пробелы" in l1["hint"] and l2["passed"] and "Кавычки" in l3["hint"]
    assert "expected" not in l1  # ответ не раскрывается


def test_answer_missing_extra_and_order(box):
    r = check("10 - 4\n6", PREDICT, box)
    assert "не хватает" in r["cases"][2]["hint"]
    r = check("10 - 4\n6\nГотово\nещё", PREDICT, box)
    assert "Лишняя" in r["cases"][3]["hint"]
    r = check("6\n10 - 4\nГотово", PREDICT, box)
    assert any("порядок" in c.get("hint", "") for c in r["cases"])
    r = check("", PREDICT, box)
    assert r["passed"] == 0 and r["total"] == 3


def test_huge_function_result_is_clipped(box):
    spec = {"kind": "function", "function": "f", "cases": [{"id": "v1", "args": [], "expected": [1, 2]}]}
    out = ca_runner.check("def f():\n    return list(range(10**6))", json.dumps(spec), str(box))
    assert len(out) < 10_000
    r = json.loads(out)
    assert r["passed"] == 0 and "обрезано" in r["cases"][0]["actual"]
