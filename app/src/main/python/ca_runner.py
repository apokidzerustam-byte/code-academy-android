"""Учебная песочница Code Academy: запуск кода ученика.

Уровень A (процесс :runner): ограничения на уровне Python —
audit hooks + защищённый __import__. Это защита от ошибок ученика,
а НЕ граница безопасности: целенаправленный обход возможен.
Уровень B (isolatedProcess): те же ограничения + запреты ядра Android
(отдельный UID, SELinux isolated_app: нет сети и файлов приложения).

Таймаут и принудительная остановка реализованы снаружи
(Kotlin убивает процесс), потому что Python-код нельзя надёжно
прервать изнутри.
"""

import builtins
import io
import json
import linecache
import os
import sys
import time
import traceback

AF_UNIX = 1

# Модули, недоступные коду ученика напрямую.
BLOCKED_MODULES = frozenset({
    "java", "com", "android",          # мост Chaquopy к Java/Android API
    "ctypes", "_ctypes",               # прямой доступ к памяти и libc
    "socket", "_socket", "ssl", "_ssl",
    "subprocess", "_posixsubprocess", "multiprocessing",
    "signal", "pty", "fcntl", "mmap", "resource",
    "js", "pyodide", "pyodide_js", "_pyodide",   # мост Pyodide к JavaScript
})

JAVA_BRIDGE = frozenset({"java", "com", "android"})

# Audit-события, запрещённые целиком.
BLOCKED_EVENT_PREFIXES = (
    "subprocess.", "os.system", "os.exec", "os.spawn", "os.posix_spawn",
    "os.fork", "os.forkpty", "os.kill", "os.killpg", "os.setuid",
    "ctypes.", "sys.addaudithook", "sys.setprofile", "sys.settrace",
    "socket.connect", "socket.bind", "socket.getaddrinfo", "socket.gethostbyname",
    "socket.gethostbyaddr", "socket.sendto", "socket.sendmsg", "socket.getnameinfo",
    "urllib.Request", "http.client.connect", "webbrowser.open",
)

# События с путём в первом аргументе: разрешены только внутри песочницы.
PATH_EVENTS = frozenset({
    "os.listdir", "os.scandir", "os.remove", "os.rmdir", "os.mkdir",
    "os.chdir", "os.chmod", "os.chown", "os.symlink", "os.link",
    "os.truncate", "os.utime", "shutil.rmtree", "shutil.copyfile",
    "shutil.copytree", "shutil.move", "os.rename", "glob.glob",
})

_ACTIVE = False
_SANDBOX = None
_READ_ROOTS = ()
_HOOK_INSTALLED = False
_real_import = builtins.__import__


class SandboxViolation(PermissionError):
    pass


def _real(path):
    try:
        return os.path.realpath(os.fspath(path))
    except Exception:
        return None


def _inside(path, root):
    if not path or not root:
        return False
    return path == root or path.startswith(root.rstrip(os.sep) + os.sep)


def _deny(what):
    raise SandboxViolation(f"Заблокировано учебной песочницей: {what}")


def _check_path(event, raw, write):
    if raw is None or isinstance(raw, int):
        return
    p = _real(raw)
    if _inside(p, _SANDBOX):
        return
    if not write and any(_inside(p, r) for r in _READ_ROOTS):
        return
    _deny(f"{event} {raw!r}")


def _hook(event, args):
    if not _ACTIVE:
        return
    if event == "socket.__new__":
        family = args[1] if len(args) > 1 else None
        if family != AF_UNIX:  # socketpair для asyncio разрешён, сеть — нет
            _deny("сетевой сокет")
        return
    if event.startswith(BLOCKED_EVENT_PREFIXES):
        _deny(event)
    if event == "open":
        path, mode, flags = (list(args) + [None, None, None])[:3]
        write = False
        if isinstance(mode, str):
            write = any(c in mode for c in "wax+")
        if isinstance(flags, int):
            write = write or bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
        _check_path("open", path, write)
        return
    if event in PATH_EVENTS:
        for a in args[:2]:
            if isinstance(a, (str, bytes, os.PathLike)):
                _check_path(event, a, write=event not in ("os.listdir", "os.scandir", "glob.glob"))
        return
    if event == "import":
        name = args[0] if args else ""
        # Только Java-мост: остальные модули stdlib импортирует сама (asyncio -> socket).
        if isinstance(name, str) and name.split(".")[0] in JAVA_BRIDGE:
            _deny(f"import {name}")


def _guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
    if level == 0 and name.split(".")[0] in BLOCKED_MODULES:
        raise ImportError(f"Модуль '{name}' недоступен в учебной песочнице")
    return _real_import(name, globals, locals, fromlist, level)


def _safe_builtins():
    b = dict(builtins.__dict__)
    b["__import__"] = _guarded_import
    return b


# Нативные модули stdlib, которые Chaquopy распаковывает в файлы приложения при ПЕРВОМ
# импорте. Под активным хуком эта запись была бы запрещена, поэтому импортируем их заранее.
# Порядок важен: «asyncio» раньше «_asyncio» — если C-модуль загрузить первым, asyncio.current_task()
# внутри задач возвращает None (Python 3.13), и anyio/FastAPI падают на task.set_name.
_PRELOAD = (
    "asyncio", "_asyncio", "select", "selectors", "_socket", "socket", "ssl",
    "math", "cmath", "_random", "random", "_datetime", "datetime", "_decimal", "decimal",
    "_bisect", "_heapq", "array", "_struct", "_contextvars", "_queue", "_json", "_csv",
    "_statistics", "statistics", "unicodedata", "_sqlite3", "sqlite3", "zlib", "_hashlib",
    "hashlib", "_sha2", "_md5", "binascii", "_pickle", "_zoneinfo", "_bz2", "_lzma",
    "pyexpat", "_elementtree", "_multibytecodec", "_uuid", "fractions", "itertools",
    # Учебный FastAPI (уровень A, Chaquopy): пакеты загружаются заранее, до включения песочницы.
    "typing_extensions", "pydantic", "starlette", "anyio", "anyio._backends._asyncio", "sniffio",
    "h11", "httpcore", "httpx", "fastapi", "fastapi.testclient", "fastapi.responses", "fastapi.encoders",
    "starlette.testclient", "starlette.routing", "fastapi.routing", "anyio.from_thread", "anyio.abc",
    "email.mime.text", "concurrent.futures.thread",
)


def _preload_native_modules():
    import importlib
    for name in _PRELOAD:
        try:
            importlib.import_module(name)
        except Exception:  # noqa: BLE001 — модуля может не быть на платформе
            pass


def _install_hook():
    global _HOOK_INSTALLED, _READ_ROOTS
    if _HOOK_INSTALLED:
        return
    _preload_native_modules()
    roots = set()
    for entry in sys.path:
        r = _real(entry) if entry else None
        if r:
            roots.add(r)
    for mod in (os, json, traceback):
        f = getattr(mod, "__file__", None)
        if f:
            roots.add(_real(os.path.dirname(f)))
    _READ_ROOTS = tuple(sorted(r for r in roots if r))
    sys.addaudithook(_hook)
    _HOOK_INSTALLED = True


class _CappedIO(io.TextIOBase):
    def __init__(self, limit):
        self._buf = []
        self._size = 0
        self._limit = limit
        self.truncated = False

    def writable(self):
        return True

    def write(self, s):
        if not isinstance(s, str):
            raise TypeError("write() argument must be str")
        room = self._limit - self._size
        if room <= 0:
            self.truncated = True
            return len(s)
        part = s[:room]
        if len(part) < len(s):
            self.truncated = True
        self._buf.append(part)
        self._size += len(part)
        return len(s)

    def getvalue(self):
        return "".join(self._buf)


_HARNESS = os.path.abspath(__file__)


def _user_traceback(exc, filename):
    tb = exc.__traceback__
    while tb is not None and tb.tb_frame.f_code.co_filename != filename:
        tb = tb.tb_next
    frames = [f for f in traceback.extract_tb(tb) if os.path.abspath(f.filename) != _HARNESS]
    head = ["Traceback (most recent call last):\n"] if frames else []
    return "".join(head + traceback.format_list(frames) + traceback.format_exception_only(type(exc), exc))


def _forget_user_modules(root):
    """Удаляет из sys.modules модули ученика, чтобы следующий запуск видел свежий код."""
    if not root:
        return
    for name, mod in list(sys.modules.items()):
        f = getattr(mod, "__file__", None)
        if f and _inside(_real(f), root):
            del sys.modules[name]


def run(code, sandbox_dir=None, stdin_text="", max_output=16384, filename="main.py"):
    """Выполняет код ученика. Возвращает JSON-строку с результатом. filename — имя файла в сообщениях об ошибках."""
    global _ACTIVE, _SANDBOX
    out, err = _CappedIO(max_output), _CappedIO(max_output)
    status = "OK"
    started = time.monotonic()
    old_streams = sys.stdout, sys.stderr, sys.stdin
    old_cwd = os.getcwd()
    sys.dont_write_bytecode = True
    try:
        _install_hook()
        if sandbox_dir:
            os.makedirs(sandbox_dir, exist_ok=True)
            os.chdir(sandbox_dir)
            _SANDBOX = _real(sandbox_dir)
            sys.path.insert(0, _SANDBOX)  # многофайловые проекты: import своих модулей
        else:
            _SANDBOX = None
        linecache.cache[filename] = (len(code), None, code.splitlines(True), filename)
        try:
            compiled = compile(code, filename, "exec")
        except SyntaxError as e:
            status = "SYNTAX_ERROR"
            err.write("".join(traceback.format_exception_only(type(e), e)))
            compiled = None
        if compiled is not None:
            g = {"__name__": "__main__", "__file__": filename, "__builtins__": _safe_builtins()}
            sys.stdout, sys.stderr, sys.stdin = out, err, io.StringIO(stdin_text or "")
            _ACTIVE = True
            try:
                exec(compiled, g)
            except SystemExit as e:
                _ACTIVE = False
                if e.code not in (None, 0):
                    status = "EXIT"
                    err.write(f"SystemExit: {e.code}\n")
            except BaseException as e:  # noqa: BLE001 — ошибки ученика возвращаем текстом
                _ACTIVE = False
                status = "ERROR"
                err.write(_user_traceback(e, filename))
            finally:
                _ACTIVE = False
    finally:
        _ACTIVE = False
        sys.stdout, sys.stderr, sys.stdin = old_streams
        try:
            os.chdir(old_cwd)
        except OSError:
            pass
        if _SANDBOX:
            _forget_user_modules(_SANDBOX)
            try:
                sys.path.remove(_SANDBOX)
            except ValueError:
                pass
        _SANDBOX = None
    return json.dumps({
        "status": status,
        "stdout": out.getvalue(),
        "stderr": err.getvalue(),
        "truncated": out.truncated or err.truncated,
        "durationMs": int((time.monotonic() - started) * 1000),
    }, ensure_ascii=False)


def info():
    return json.dumps({
        "python": sys.version.split()[0],
        "platform": sys.platform,
        "pid": os.getpid(),
        "uid": os.getuid() if hasattr(os, "getuid") else -1,
    })


def kernel_probe(path):
    """Только для тестов: проверка ограничений ЯДРА в обход Python-хуков
    (хуки неактивны вне run()). Показывает, что запрещает сам Android."""
    import socket
    res = {}
    try:
        fd = os.open(path, os.O_RDONLY)
        os.close(fd)
        res["file"] = "READABLE"
    except OSError as e:
        res["file"] = f"DENIED {e.errno} {e.strerror}"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        try:
            s.connect(("1.1.1.1", 80))
            res["net"] = "CONNECTED"
        finally:
            s.close()
    except OSError as e:
        res["net"] = f"DENIED {e.errno} {e.strerror}"
    return json.dumps(res)


# ---------------------------------------------------------------------------
# Автопроверка заданий (AssignmentEngine / TestEngine).
# Проверяется ПОВЕДЕНИЕ кода на разных входных данных, а не текст решения.
# ---------------------------------------------------------------------------

def _normalize(text, mode):
    if mode == "exact":
        return text
    lines = [ln.rstrip() for ln in text.replace("\r\n", "\n").split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    if mode == "lines_unordered":
        return sorted(lines)
    return "\n".join(lines)  # "strip" по умолчанию: без хвостовых пробелов и пустых строк


def _values_equal(expected, actual, tol):
    if isinstance(expected, float) or isinstance(actual, float):
        try:
            return abs(float(expected) - float(actual)) <= tol
        except (TypeError, ValueError):
            return False
    if isinstance(expected, (list, tuple)) and isinstance(actual, (list, tuple)):
        return len(expected) == len(actual) and all(_values_equal(e, a, tol) for e, a in zip(expected, actual))
    if isinstance(expected, dict) and isinstance(actual, dict):
        return expected.keys() == actual.keys() and all(_values_equal(expected[k], actual[k], tol) for k in expected)
    return expected == actual


_MAX_VALUE_CHARS = 2000


def _clip(v):
    """Ограничивает размер значения в отчёте (огромный результат функции не должен ломать передачу)."""
    try:
        text = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
    except (TypeError, ValueError):
        text = repr(v)
    if len(text) <= _MAX_VALUE_CHARS:
        return v
    return text[:_MAX_VALUE_CHARS] + f"… (обрезано, всего {len(text)} символов)"


def _case_report(case, passed, expected=None, actual=None, error=None):
    hidden = bool(case.get("hidden"))
    rep = {"id": case.get("id"), "hidden": hidden, "passed": passed}
    if not passed:
        rep["hint"] = case.get("hint", "")
        if error:
            # Для скрытых тестов показываем только тип ошибки, без деталей входных данных.
            rep["error"] = error.strip().splitlines()[-1] if hidden else error
    if not hidden:
        rep["input"] = _clip(case.get("stdin", case.get("args")))
        rep["expected"] = _clip(expected)
        rep["actual"] = _clip(actual)
    return rep


def _check_stdout(code, spec, sandbox_dir, max_output, filename="main.py"):
    mode = spec.get("match", "strip")
    reports = []
    for case in spec["cases"]:
        r = json.loads(run(code, sandbox_dir, case.get("stdin", ""), max_output, filename))
        exp = _normalize(case["expected_stdout"], mode)
        act = _normalize(r["stdout"], mode)
        if r["status"] == "SYNTAX_ERROR":
            return {"compileError": r["stderr"]}
        ok = r["status"] == "OK" and exp == act
        err = r["stderr"] if r["status"] != "OK" else None
        disp = (lambda v: "\n".join(v) if isinstance(v, list) else v)
        reports.append(_case_report(case, ok, disp(exp), disp(act), err))
    return {"cases": reports}


def _check_function(code, spec, sandbox_dir, max_output, filename="main.py"):
    global _ACTIVE, _SANDBOX
    fname = spec["function"]
    tol = float(spec.get("tolerance", 1e-9))
    out, err = _CappedIO(max_output), _CappedIO(max_output)
    old_streams = sys.stdout, sys.stderr, sys.stdin
    old_cwd = os.getcwd()
    sys.dont_write_bytecode = True
    reports = []
    try:
        _install_hook()
        if sandbox_dir:
            os.makedirs(sandbox_dir, exist_ok=True)
            os.chdir(sandbox_dir)
            _SANDBOX = _real(sandbox_dir)
            sys.path.insert(0, _SANDBOX)
        linecache.cache[filename] = (len(code), None, code.splitlines(True), filename)
        try:
            compiled = compile(code, filename, "exec")
        except SyntaxError as e:
            return {"compileError": "".join(traceback.format_exception_only(type(e), e))}
        g = {"__name__": "__check__", "__file__": filename, "__builtins__": _safe_builtins()}
        sys.stdout, sys.stderr, sys.stdin = out, err, io.StringIO("")
        _ACTIVE = True
        try:
            exec(compiled, g)
        except BaseException as e:  # noqa: BLE001
            _ACTIVE = False
            return {"loadError": _user_traceback(e, filename)}
        fn = g.get(fname)
        if not callable(fn):
            _ACTIVE = False
            return {"loadError": f"Функция {fname}() не найдена. Проверьте имя и что она объявлена через def."}
        for case in spec["cases"]:
            args = case.get("args", [])
            kwargs = case.get("kwargs", {})
            try:
                _ACTIVE = True
                actual = fn(*args, **kwargs)
                _ACTIVE = False
                if "expected_error" in case:
                    reports.append(_case_report(case, False, case["expected_error"], repr(actual)))
                else:
                    ok = _values_equal(case["expected"], actual, tol)
                    reports.append(_case_report(case, ok, case["expected"], actual if _jsonable(actual) else repr(actual)))
            except BaseException as e:  # noqa: BLE001
                _ACTIVE = False
                if "expected_error" in case and type(e).__name__ == case["expected_error"]:
                    reports.append(_case_report(case, True, case["expected_error"], type(e).__name__))
                else:
                    reports.append(_case_report(case, False, case.get("expected", case.get("expected_error")), None,
                                                _user_traceback(e, filename)))
    finally:
        _ACTIVE = False
        sys.stdout, sys.stderr, sys.stdin = old_streams
        try:
            os.chdir(old_cwd)
        except OSError:
            pass
        if _SANDBOX:
            _forget_user_modules(_SANDBOX)
            try:
                sys.path.remove(_SANDBOX)
            except ValueError:
                pass
        _SANDBOX = None
    return {"cases": reports}


def _jsonable(v):
    try:
        json.dumps(v)
        return True
    except (TypeError, ValueError):
        return False


def _line_hint(mine, right):
    """Почему строка ответа неверна: типичные ошибки новичка (Error-Based Learning)."""
    if mine is None:
        return "Этой строки не хватает: программа выводит больше строк."
    if right is None:
        return "Лишняя строка: программа выводит меньше строк."
    strip_q = mine.strip().strip("\"'«»")
    if strip_q == right.strip() and mine.strip() != right.strip():
        return "Кавычки на экран не выводятся: они только показывают Python, где текст."
    if "".join(mine.split()) == "".join(right.split()):
        return "Текст в кавычках выводится символ в символ — проверьте пробелы."
    if mine.strip().lower() == right.strip().lower():
        return "Проверьте большие и маленькие буквы."
    return "Проследите, что делает эта строка программы: выводит текст как есть или сначала вычисляет."


def _read_text(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except (OSError, UnicodeDecodeError):
        return None


def _check_project(files_json, spec, sandbox_dir, max_output):
    """Проверка многофайлового проекта. Каждый тест указывает файл ("file", по умолчанию main.py) и одно из:
    - stdin / expected_stdout (+ expected_files: какие файлы программа должна создать и с каким текстом);
    - function / args / expected (функция из этого файла).
    Перед каждым тестом файлы проекта записываются заново: тесты не влияют друг на друга."""
    try:
        files = json.loads(files_json)
        if not isinstance(files, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in files.items()):
            raise ValueError
    except ValueError:
        return {"loadError": "Не удалось прочитать файлы проекта"}
    if not sandbox_dir:
        return {"loadError": "Проекты проверяются в режимах W или A (в изолированном режиме B нет папки проекта)."}
    for req in spec.get("requiredFiles", []):
        if req not in files:
            return {"loadError": f"В проекте нет файла {req}. Создайте его кнопкой «+ файл»."}
    mode = spec.get("match", "strip")
    tol = spec.get("tolerance", 1e-9)
    reports = []
    for case in spec["cases"]:
        fname = case.get("file", spec.get("entry", "main.py"))
        if fname not in files:
            return {"loadError": f"В проекте нет файла {fname}. Создайте его кнопкой «+ файл»."}
        try:
            write_files(sandbox_dir, json.dumps(files))
        except ValueError as e:
            return {"loadError": str(e)}
        code = files[fname]
        if "function" in case:
            r = _check_function(code, {"function": case["function"], "tolerance": tol, "cases": [case]},
                                sandbox_dir, max_output, fname)
        else:
            r = _check_stdout(code, {"match": mode, "cases": [case]}, sandbox_dir, max_output, fname)
        if "compileError" in r or "loadError" in r:
            return r
        rep = r["cases"][0]
        if rep["passed"] and case.get("expected_files"):
            for path, want in case["expected_files"].items():
                got = _read_text(os.path.join(sandbox_dir, _safe_rel(path)))
                if got is None or _normalize(got, mode) != _normalize(want, mode):
                    rep = _case_report(case, False, want, got,
                                       None if got is not None else f"Файл {path} не создан")
                    rep["hint"] = case.get("hint") or (f"Проверьте содержимое файла {path}" if got is not None
                                                       else f"Программа должна создать файл {path}")
                    if not rep["hidden"]:
                        rep["input"] = _clip(case.get("stdin"))
                    break
        rep["file"] = fname
        reports.append(rep)
    return {"cases": reports}


def _check_answer(answer, spec):
    mine = _normalize(answer, "strip").split("\n") if answer.strip() else []
    right = _normalize(spec["expected_answer"], "strip").split("\n")
    cases = []
    for i in range(max(len(mine), len(right))):
        m = mine[i] if i < len(mine) else None
        r = right[i] if i < len(right) else None
        ok = m is not None and r is not None and m.rstrip() == r.rstrip()
        c = {"id": f"line{i + 1}", "line": i + 1, "hidden": False, "passed": ok, "actual": m}
        if not ok:
            c["hint"] = _line_hint(m, r)
        cases.append(c)
    if sorted(mine) == sorted(right) and mine != right:
        cases.append({"id": "order", "hidden": False, "passed": False, "actual": None,
                      "hint": "Все строки верные, но порядок другой: команды выполняются сверху вниз."})
    return {"kind": "answer", "cases": cases}


def _fastapi_case(client, case):
    method = case.get("method", "GET").upper()
    kwargs = {}
    for key in ("json", "params", "headers"):
        if key in case:
            kwargs[key] = case[key]
    resp = client.request(method, case["path"], **kwargs)
    try:
        body = resp.json()
    except ValueError:
        body = resp.text
    return resp.status_code, body


def _check_fastapi(code, spec, sandbox_dir, max_output):
    """Учебный API на FastAPI: запросы через TestClient (без сети), сравнение кода ответа и JSON."""
    global _ACTIVE, _SANDBOX
    try:
        from fastapi.testclient import TestClient
    except ImportError:
        return {"loadError": "FastAPI недоступен в этом режиме выполнения. Выберите в настройках режим A или «Авто»."}
    filename = "main.py"
    out, err = _CappedIO(max_output), _CappedIO(max_output)
    old_streams = sys.stdout, sys.stderr, sys.stdin
    old_cwd = os.getcwd()
    sys.dont_write_bytecode = True
    reports = []
    app_name = spec.get("app", "app")
    try:
        _install_hook()
        if sandbox_dir:
            os.makedirs(sandbox_dir, exist_ok=True)
            os.chdir(sandbox_dir)
            _SANDBOX = _real(sandbox_dir)
            sys.path.insert(0, _SANDBOX)
        linecache.cache[filename] = (len(code), None, code.splitlines(True), filename)
        try:
            compiled = compile(code, filename, "exec")
        except SyntaxError as e:
            return {"compileError": "".join(traceback.format_exception_only(type(e), e))}
        g = {"__name__": "__check__", "__file__": filename, "__builtins__": _safe_builtins()}
        sys.stdout, sys.stderr, sys.stdin = out, err, io.StringIO("")
        _ACTIVE = True
        try:
            exec(compiled, g)
        except BaseException as e:  # noqa: BLE001
            _ACTIVE = False
            return {"loadError": _user_traceback(e, filename)}
        _ACTIVE = False
        app = g.get(app_name)
        if app is None or not callable(app):
            return {"loadError": f"Приложение {app_name} не найдено. Создайте его: {app_name} = FastAPI()"}
        tol = float(spec.get("tolerance", 1e-9))
        # Без «with»: события запуска (lifespan) не нужны, а клиент создаётся до включения песочницы.
        client = TestClient(app)
        if True:
            for case in spec["cases"]:
                shown = {"method": case.get("method", "GET").upper(), "path": case["path"]}
                if "json" in case:
                    shown["json"] = case["json"]
                if "params" in case:
                    shown["params"] = case["params"]
                expected = {"status": case.get("expected_status", 200)}
                if "expected_json" in case:
                    expected["json"] = case["expected_json"]
                try:
                    _ACTIVE = True
                    status, body = _fastapi_case(client, case)
                    _ACTIVE = False
                except BaseException as e:  # noqa: BLE001 — ошибка в обработчике ученика
                    _ACTIVE = False
                    rep = _case_report(case, False, expected, None, _user_traceback(e, filename))
                    if not rep["hidden"]:
                        rep["input"] = shown
                    reports.append(rep)
                    continue
                actual = {"status": status}
                if "expected_json" in case:
                    actual["json"] = body
                ok = status == expected["status"] and ("expected_json" not in case or _values_equal(case["expected_json"], body, tol))
                if "expected_json_contains" in case:
                    sub = case["expected_json_contains"]
                    ok = ok and isinstance(body, dict) and all(k in body and _values_equal(v, body[k], tol) for k, v in sub.items())
                    expected["json_contains"] = sub
                    actual["json"] = body
                rep = _case_report(case, ok, expected, actual)
                if not rep["hidden"]:
                    rep["input"] = shown
                if not ok and not rep.get("hint"):
                    if status != expected["status"]:
                        rep["hint"] = f"Код ответа {status}, а нужен {expected['status']}"
                    else:
                        rep["hint"] = "Код ответа верный, но данные в ответе другие"
                reports.append(rep)
    finally:
        _ACTIVE = False
        sys.stdout, sys.stderr, sys.stdin = old_streams
        try:
            os.chdir(old_cwd)
        except OSError:
            pass
        if _SANDBOX:
            _forget_user_modules(_SANDBOX)
            try:
                sys.path.remove(_SANDBOX)
            except ValueError:
                pass
        _SANDBOX = None
    return {"cases": reports}


def check(code, tests_json, sandbox_dir=None, max_output=4096):
    """Проверка решения. tests_json: {"kind": "stdout"|"function", ...}. Возвращает JSON-отчёт."""
    spec = json.loads(tests_json)
    started = time.monotonic()
    if spec["kind"] == "stdout":
        res = _check_stdout(code, spec, sandbox_dir, max_output)
    elif spec["kind"] == "function":
        res = _check_function(code, spec, sandbox_dir, max_output)
    elif spec["kind"] == "fastapi":
        res = _check_fastapi(code, spec, sandbox_dir, max_output)
    elif spec["kind"] == "project":
        # Учебный проект: code — JSON {путь: текст} всех файлов проекта.
        res = _check_project(code, spec, sandbox_dir, max_output)
    elif spec["kind"] == "answer":
        # «Предскажи результат»: code — ответ ученика текстом, код не выполняется.
        res = _check_answer(code, spec)
        spec = dict(spec, cases=res["cases"])
    else:
        raise ValueError(f"Неизвестный вид тестов: {spec['kind']}")
    cases = res.get("cases", [])
    res["passed"] = sum(1 for c in cases if c["passed"])
    res["total"] = len(spec["cases"])
    res["allPassed"] = bool(cases) and res["passed"] == res["total"]
    res["durationMs"] = int((time.monotonic() - started) * 1000)
    return json.dumps(res, ensure_ascii=False, default=repr)


# ---------------------------------------------------------------------------
# Файлы проекта (IDE): запись перед запуском и чтение после.
# ---------------------------------------------------------------------------

MAX_FILE_BYTES = 256 * 1024
MAX_PROJECT_BYTES = 2 * 1024 * 1024
MAX_FILES = 200


def _safe_rel(path):
    """Относительный путь внутри проекта; '..', абсолютные пути и скрытые служебные файлы запрещены."""
    p = path.replace("\\", "/")
    if p.startswith("/") or (len(p) > 1 and p[1] == ":"):
        raise ValueError(f"Абсолютный путь запрещён: {path!r}")
    p = p.strip("/")
    parts = [x for x in p.split("/") if x not in ("", ".")]
    if not parts or any(x == ".." for x in parts):
        raise ValueError(f"Недопустимый путь: {path!r}")
    return "/".join(parts)


def write_files(root, files_json):
    """Заменяет содержимое папки проекта переданными файлами {путь: текст}."""
    import shutil
    files = json.loads(files_json)
    if len(files) > MAX_FILES:
        raise ValueError("Слишком много файлов в проекте")
    # Всё проверяем до удаления старых файлов.
    prepared, total = [], 0
    for path, text in files.items():
        rel = _safe_rel(path)
        data = text.encode("utf-8")
        total += len(data)
        if len(data) > MAX_FILE_BYTES or total > MAX_PROJECT_BYTES:
            raise ValueError(f"Файл {rel} или проект слишком большой")
        prepared.append((rel, data))
    rels = [r for r, _ in prepared]
    if len(set(rels)) != len(rels):
        raise ValueError("Один и тот же файл указан дважды")
    rel_set = set(rels)
    for r in rels:
        parts = r.split("/")
        for i in range(1, len(parts)):
            d = "/".join(parts[:i])
            if d in rel_set:
                raise ValueError(f"«{d}» — это файл, внутри него не может быть «{r}»")
    if os.path.islink(root):
        os.unlink(root)
    elif os.path.isdir(root):
        shutil.rmtree(root)  # rmtree не переходит по символическим ссылкам
    os.makedirs(root, exist_ok=True)
    for rel, data in prepared:
        full = os.path.join(root, rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "wb") as f:
            f.write(data)
    return len(files)


def read_files(root):
    """Текстовые файлы проекта после запуска {путь: текст}; двоичные и слишком большие пропускаются."""
    out, total = {}, 0
    if not os.path.isdir(root):
        return json.dumps(out)
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d != "__pycache__")
        for name in sorted(filenames):
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root).replace(os.sep, "/")
            if os.path.islink(full):
                continue  # ссылка может вести за пределы проекта
            try:
                size = os.path.getsize(full)
                if size > MAX_FILE_BYTES or total + size > MAX_PROJECT_BYTES or len(out) >= MAX_FILES:
                    continue
                with open(full, "rb") as f:
                    text = f.read().decode("utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            total += size
            out[rel] = text
    return json.dumps(out, ensure_ascii=False)
