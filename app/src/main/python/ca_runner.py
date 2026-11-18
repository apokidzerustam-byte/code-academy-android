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


def _install_hook():
    global _HOOK_INSTALLED, _READ_ROOTS
    if _HOOK_INSTALLED:
        return
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


def run(code, sandbox_dir=None, stdin_text="", max_output=65536):
    """Выполняет код ученика. Возвращает JSON-строку с результатом."""
    global _ACTIVE, _SANDBOX
    filename = "main.py"
    out, err = _CappedIO(max_output), _CappedIO(max_output)
    status = "OK"
    started = time.monotonic()
    old_streams = sys.stdout, sys.stderr, sys.stdin
    old_cwd = os.getcwd()
    sys.dont_write_bytecode = True
    try:
        if sandbox_dir:
            os.makedirs(sandbox_dir, exist_ok=True)
            os.chdir(sandbox_dir)
            _SANDBOX = _real(sandbox_dir)
            sys.path.insert(0, _SANDBOX)  # многофайловые проекты: import своих модулей
        else:
            _SANDBOX = None
        _install_hook()
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
