"""Проверка многофайловых учебных проектов (kind=project)."""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app", "src", "main", "python"))
import ca_runner  # noqa: E402

MAIN = '''from money import total
items = []
while True:
    line = input()
    if line == "":
        break
    items.append(int(line))
print("Итого:", total(items))
with open("report.txt", "w", encoding="utf-8") as f:
    f.write(f"{len(items)} покупок\\n")
'''
MONEY = "def total(xs):\n    s = 0\n    for x in xs:\n        s += x\n    return s\n"

SPEC = {"kind": "project", "requiredFiles": ["money.py"], "cases": [
    {"id": "run", "file": "main.py", "stdin": "10\n5\n\n", "expected_stdout": "Итого: 15",
     "expected_files": {"report.txt": "2 покупок"}},
    {"id": "fn", "file": "money.py", "function": "total", "args": [[1, 2, 3]], "expected": 6},
    {"id": "empty", "hidden": True, "file": "money.py", "function": "total", "args": [[]], "expected": 0},
]}


def check(files, spec=SPEC, sandbox=None):
    return json.loads(ca_runner.check(json.dumps(files), json.dumps(spec), sandbox))


def test_reference_passes(tmp_path):
    r = check({"main.py": MAIN, "money.py": MONEY}, sandbox=str(tmp_path / "s"))
    assert r["allPassed"], r
    assert [c["file"] for c in r["cases"]] == ["main.py", "money.py", "money.py"]


def test_missing_required_file(tmp_path):
    r = check({"main.py": MAIN}, sandbox=str(tmp_path / "s"))
    assert "money.py" in r["loadError"]


def test_wrong_module_detected(tmp_path):
    r = check({"main.py": MAIN, "money.py": MONEY.replace("s += x", "s = x")}, sandbox=str(tmp_path / "s"))
    assert not r["allPassed"]
    assert not r["cases"][1]["passed"]


def test_expected_file_content(tmp_path):
    r = check({"main.py": MAIN.replace("покупок", "шт"), "money.py": MONEY}, sandbox=str(tmp_path / "s"))
    assert not r["cases"][0]["passed"]
    assert "report.txt" in r["cases"][0]["hint"]


def test_syntax_error_names_the_file(tmp_path):
    r = check({"main.py": MAIN, "money.py": "def total(xs)\n    return 0\n"}, sandbox=str(tmp_path / "s"))
    assert "money.py" in r["compileError"] or "money.py" in r.get("loadError", ""), r


def test_cases_are_isolated(tmp_path):
    """Файл, созданный первым тестом, не виден второму: файлы проекта записываются заново."""
    prog = 'import os\nprint(os.path.exists("x.txt"))\nopen("x.txt", "w").write("1")\n'
    spec = {"kind": "project", "cases": [{"id": "a", "stdin": "", "expected_stdout": "False"},
                                         {"id": "b", "stdin": "", "expected_stdout": "False"}]}
    r = check({"main.py": prog}, spec, sandbox=str(tmp_path / "s"))
    assert r["allPassed"], r


def test_fresh_module_between_checks(tmp_path):
    """Исправленный модуль виден при следующей проверке (нет кэша sys.modules)."""
    sb = str(tmp_path / "s")
    bad = check({"main.py": MAIN, "money.py": "def total(xs):\n    return -1\n"}, sandbox=sb)
    good = check({"main.py": MAIN, "money.py": MONEY}, sandbox=sb)
    assert not bad["allPassed"] and good["allPassed"], (bad, good)


def test_no_sandbox_dir_explained():
    r = check({"main.py": MAIN, "money.py": MONEY}, sandbox=None)
    assert "режим" in r["loadError"]


def test_path_traversal_rejected(tmp_path):
    r = check({"main.py": "print(1)", "../evil.py": "x"}, {"kind": "project", "cases": [{"stdin": "", "expected_stdout": "1"}]},
              sandbox=str(tmp_path / "s"))
    assert "loadError" in r
    assert not (tmp_path / "evil.py").exists()
