"""Тесты учебной песочницы ca_runner на обычном CPython 3.13.

Проверяют уровень A (ограничения Python). Ограничения ядра (уровень B)
проверяются только инструментальными тестами на эмуляторе.
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app", "src", "main", "python"))
import ca_runner  # noqa: E402


def run(code, sandbox=None, stdin=""):
    return json.loads(ca_runner.run(code, str(sandbox) if sandbox else None, stdin, 4096))


@pytest.fixture
def box(tmp_path):
    d = tmp_path / "sandbox"
    d.mkdir()
    return d


def test_print(box):
    r = run("print(2 + 2)", box)
    assert r["status"] == "OK" and r["stdout"] == "4\n" and r["stderr"] == ""


def test_syntax_error(box):
    r = run("print(", box)
    assert r["status"] == "SYNTAX_ERROR" and "SyntaxError" in r["stderr"]


def test_runtime_error_shows_user_line_only(box):
    r = run("x = 1\ny = x / 0\n", box)
    assert r["status"] == "ERROR"
    assert "ZeroDivisionError" in r["stderr"]
    assert 'File "main.py", line 2' in r["stderr"]
    assert "ca_runner" not in r["stderr"]


def test_stdin_input(box):
    r = run("name = input()\nprint('Привет,', name)", box, stdin="Аня\n")
    assert r["stdout"] == "Привет, Аня\n"


def test_input_without_stdin_is_eof(box):
    r = run("input()", box)
    assert r["status"] == "ERROR" and "EOFError" in r["stderr"]


def test_asyncio_works(box):
    r = run("import asyncio\nasync def f():\n    await asyncio.sleep(0)\n    return 7\nprint(asyncio.run(f()))", box)
    assert r["status"] == "OK", r["stderr"]
    assert r["stdout"] == "7\n"


def test_json_and_stdlib_imports(box):
    r = run("import json, collections, dataclasses, re\nprint(json.dumps({'a': 1}))", box)
    assert r["status"] == "OK", r["stderr"]


def test_write_and_read_inside_sandbox(box):
    r = run("open('notes.txt','w').write('ok')\nprint(open('notes.txt').read())", box)
    assert r["status"] == "OK", r["stderr"]
    assert r["stdout"] == "ok\n"
    assert (box / "notes.txt").read_text() == "ok"


def test_read_outside_sandbox_blocked(box, tmp_path):
    secret = tmp_path / "secret.db"
    secret.write_text("progress")
    r = run(f"print(open({str(secret)!r}).read())", box)
    assert r["status"] == "ERROR" and "песочниц" in r["stderr"]
    assert "progress" not in r["stdout"]


def test_path_traversal_blocked(box):
    r = run("print(open('../secret.db').read())", box)
    assert r["status"] == "ERROR" and "песочниц" in r["stderr"]


def test_write_outside_sandbox_blocked(box, tmp_path):
    target = tmp_path / "evil.txt"
    r = run(f"open({str(target)!r}, 'w').write('x')", box)
    assert r["status"] == "ERROR"
    assert not target.exists()


def test_listdir_outside_blocked(box):
    r = run("import os\nprint(os.listdir('/'))", box)
    assert r["status"] == "ERROR" and "песочниц" in r["stderr"]


def test_listdir_inside_allowed(box):
    r = run("import os\nopen('a.py','w').close()\nprint(os.listdir('.'))", box)
    assert r["stdout"] == "['a.py']\n"


@pytest.mark.parametrize("mod", ["socket", "subprocess", "ctypes", "java", "multiprocessing", "js", "pyodide"])
def test_dangerous_imports_blocked(box, mod):
    r = run(f"import {mod}", box)
    assert r["status"] == "ERROR" and "недоступен" in r["stderr"]


def test_importlib_bypass_still_blocked_by_audit(box):
    code = "import importlib\nsp = importlib.import_module('subprocess')\nsp.run(['ls'])"
    r = run(code, box)
    assert r["status"] == "ERROR" and "песочниц" in r["stderr"]


def test_os_system_blocked(box):
    r = run("import os\nos.system('echo hi')", box)
    assert r["status"] == "ERROR" and "песочниц" in r["stderr"]


def test_network_blocked(box):
    r = run("import urllib.request\nurllib.request.urlopen('http://example.com', timeout=2)", box)
    assert r["status"] == "ERROR" and "песочниц" in r["stderr"]


def test_output_is_capped(box):
    r = run("print('x' * 100000)", box)
    assert r["truncated"] is True and len(r["stdout"]) == 4096


def test_exit_codes(box):
    assert run("raise SystemExit(0)", box)["status"] == "OK"
    assert run("import sys\nsys.exit(3)", box)["status"] == "EXIT"


def test_no_bytecode_written(box):
    (box / "helper.py").write_text("X = 5\n")
    r = run("import helper\nprint(helper.X)", box)
    assert r["stdout"] == "5\n", r["stderr"]
    assert not (box / "__pycache__").exists()


def test_streams_and_cwd_restored(box):
    cwd = os.getcwd()
    run("print('hi')", box)
    assert sys.stdout is not None and os.getcwd() == cwd


def test_hook_inactive_outside_run(tmp_path):
    # После выполнения ограничения не мешают самому приложению.
    run("pass", tmp_path)
    p = tmp_path.parent / "outside.txt"
    p.write_text("ok")
    assert p.read_text() == "ok"


def test_user_module_reloaded_between_runs(box):
    (box / "cfg.py").write_text("V = 1\n")
    assert run("import cfg\nprint(cfg.V)", box)["stdout"] == "1\n"
    (box / "cfg.py").write_text("V = 2\n")
    assert run("import cfg\nprint(cfg.V)", box)["stdout"] == "2\n"


def test_sandbox_not_left_on_sys_path(box):
    run("pass", box)
    assert str(box) not in sys.path


def test_traceback_hides_harness_on_import_error(box):
    r = run("import nothing_here", box)
    assert "ModuleNotFoundError" in r["stderr"] and "ca_runner" not in r["stderr"]


def test_first_project_not_readable_from_other_project(tmp_path):
    a = tmp_path / "projA"; a.mkdir(); (a / "secret.txt").write_text("A")
    b = tmp_path / "projB"; b.mkdir()
    run("pass", a)
    r = run(f"print(open({str(a / 'secret.txt')!r}).read())", b)
    assert r["status"] == "ERROR" and r["stdout"] == ""


def test_common_native_modules_work_under_hook(box):
    r = run("import math, random, datetime, decimal, sqlite3, hashlib, statistics\nprint(math.isqrt(49))", box)
    assert r["status"] == "OK", r["stderr"]
    assert r["stdout"] == "7\n"
