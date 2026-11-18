"""Файлы проекта: запись, многофайловый запуск, синхронизация созданных программой файлов."""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app", "src", "main", "python"))
import ca_runner  # noqa: E402


def test_multi_file_project_runs_and_syncs_back(tmp_path):
    root = str(tmp_path / "proj")
    files = {
        "main.py": "from utils.greet import hello\nprint(hello('Аня'))\nopen('out/log.txt','w').write('готово')\n",
        "utils/__init__.py": "",
        "utils/greet.py": "def hello(n):\n    return f'Привет, {n}!'\n",
        "out/.keep": "",
    }
    assert ca_runner.write_files(root, json.dumps(files)) == 4
    r = json.loads(ca_runner.run(open(os.path.join(root, "main.py")).read(), root))
    assert r["status"] == "OK", r["stderr"]
    assert r["stdout"] == "Привет, Аня!\n"
    back = json.loads(ca_runner.read_files(root))
    assert back["out/log.txt"] == "готово"
    assert "utils/greet.py" in back and not any("__pycache__" in k for k in back)


def test_write_replaces_old_files(tmp_path):
    root = str(tmp_path / "p")
    ca_runner.write_files(root, json.dumps({"a.py": "1", "b.py": "2"}))
    ca_runner.write_files(root, json.dumps({"a.py": "3"}))
    assert json.loads(ca_runner.read_files(root)) == {"a.py": "3"}


@pytest.mark.parametrize("bad", ["../evil.py", "/etc/passwd", "a/../../x", ""])
def test_unsafe_paths_rejected(tmp_path, bad):
    with pytest.raises(ValueError):
        ca_runner.write_files(str(tmp_path / "p"), json.dumps({bad: "x"}))


def test_limits(tmp_path):
    with pytest.raises(ValueError):
        ca_runner.write_files(str(tmp_path / "p"), json.dumps({"big.txt": "x" * (ca_runner.MAX_FILE_BYTES + 1)}))
    root = tmp_path / "q"
    root.mkdir()
    (root / "bin.dat").write_bytes(b"\xff\xfe\x00")
    (root / "huge.txt").write_text("y" * (ca_runner.MAX_FILE_BYTES + 1))
    (root / "ok.txt").write_text("ok")
    assert json.loads(ca_runner.read_files(str(root))) == {"ok.txt": "ok"}


def test_invalid_structure_keeps_old_files(tmp_path):
    root = str(tmp_path / "proj")
    ca_runner.write_files(root, json.dumps({"main.py": "print(1)"}))
    for bad in ({"main.py": "x", "main.py/inner.py": "y"}, {"a.py": "1", "./a.py": "2"}, {"/etc/x": "1"}):
        with pytest.raises(ValueError):
            ca_runner.write_files(root, json.dumps(bad))
        # Проверка до удаления: старый проект на месте.
        assert json.loads(ca_runner.read_files(root)) == {"main.py": "print(1)"}


def test_symlinks_not_followed(tmp_path):
    secret = tmp_path / "secret"
    secret.mkdir()
    (secret / "token.txt").write_text("SECRET")
    root = tmp_path / "proj"
    ca_runner.write_files(str(root), json.dumps({"main.py": "x"}))
    os.symlink(secret, root / "link")
    os.symlink(secret / "token.txt", root / "t.txt")
    assert json.loads(ca_runner.read_files(str(root))) == {"main.py": "x"}
    ca_runner.write_files(str(root), json.dumps({"main.py": "y"}))
    assert (secret / "token.txt").read_text() == "SECRET"  # rmtree не ушёл по ссылке
