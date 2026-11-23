"""Учебная оболочка для проверки контента про терминал и Git (этап 11).

Приложение не запускает bash на телефоне: уроки по терминалу и Git показываются сценарием и проверяются
текстовыми ответами. Чтобы в этих уроках не было вымышленного вывода, валидатор выполняет команды сценариев
и заданий настоящим bash и git во временном каталоге и сравнивает результат с тем, что покажет приложение.

Среда фиксирована, чтобы вывод не зависел от машины:
  * домашний каталог — временный, в выводе он заменяется на /home/user;
  * git: пользователь Student, ветка по умолчанию main, без пейджера и цветов, фиксированные даты
    (поэтому хеши коммитов повторяются от запуска к запуску);
  * язык C, сеть недоступна (команды curl/wget/ssh/sudo и т. п. запрещены).

Файл — и модуль (ShellSandbox), и небольшая консольная утилита: python tools/shellrun.py 'git init'.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

FIXED_DATE = "2026-01-15T12:00:00+0000"
HOME_ALIAS = "/home/user"
TIMEOUT_S = 20

# Команды, которым в контролируемой учебной среде нечего делать (сеть, повышение прав, устройства).
FORBIDDEN = re.compile(r"(?<![\w.-])(sudo|su|curl|wget|ssh|scp|nc|ncat|telnet|ftp|dd|mkfs|mount|chroot|reboot|shutdown)(?![\w.-])"
                       r"|/dev/(?!null)|:\(\)\s*\{|rm\s+-[a-zA-Z]*r[a-zA-Z]*f?\s+(/|~|\$HOME)\s*($|;|&)")

GITCONFIG = """[user]
\tname = Student
\temail = student@example.com
[init]
\tdefaultBranch = main
[core]
\tpager = cat
\teditor = true
\tautocrlf = false
[color]
\tui = false
[commit]
\tgpgsign = false
[tag]
\tgpgsign = false
[pull]
\trebase = false
[advice]
\tdetachedHead = true
[safe]
\tdirectory = *
"""


class ShellError(Exception):
    pass


class ShellSandbox:
    """Один «сеанс терминала»: каталог и файлы сохраняются между вызовами run(), как в настоящей консоли."""

    def __init__(self):
        self.root = tempfile.mkdtemp(prefix="ca-shell-")
        self.home = os.path.join(self.root, "home")
        self.work = os.path.join(self.home, "project")
        os.makedirs(self.work)
        self.state = os.path.join(self.root, "cwd")
        with open(self.state, "w", encoding="utf-8") as f:
            f.write(self.work)
        with open(os.path.join(self.home, ".gitconfig"), "w", encoding="utf-8") as f:
            f.write(GITCONFIG)

    def close(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def _env(self):
        env = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": self.home, "LANG": "C", "LC_ALL": "C", "TERM": "dumb", "USER": "user", "LOGNAME": "user",
            "GIT_CONFIG_GLOBAL": os.path.join(self.home, ".gitconfig"), "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_AUTHOR_DATE": FIXED_DATE, "GIT_COMMITTER_DATE": FIXED_DATE,
            "GIT_PAGER": "cat", "GIT_EDITOR": "true", "GIT_TERMINAL_PROMPT": "0", "GIT_OPTIONAL_LOCKS": "0",
            "PS1": "$ ",
        }
        return env

    def run(self, script, timeout=TIMEOUT_S):
        """Выполняет сценарий; возвращает {"status": "OK"|"TIMEOUT"|"BLOCKED", "stdout": вывод (stdout+stderr вместе), "stderr": "", "code": int}.

        Вывод — в порядке появления, как в консоли. Код возврата последней команды не считается ошибкой:
        в уроках часто показывают, как git сообщает о проблеме.
        """
        bad = FORBIDDEN.search(script)
        if bad:
            return {"status": "BLOCKED", "stdout": "", "stderr": f"команда {bad.group(0)!r} запрещена в учебной среде", "code": 126}
        wrapped = (f'cd "$(cat \'{self.state}\')" 2>/dev/null || cd "$HOME"\n'
                   f"trap 'pwd > \"{self.state}\"' EXIT\n" + script)
        try:
            p = subprocess.run(["bash", "-c", wrapped], cwd=self.work, env=self._env(), stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
        except subprocess.TimeoutExpired as e:
            return {"status": "TIMEOUT", "stdout": self._clean((e.stdout or b"").decode("utf-8", "replace")),
                    "stderr": f"превышено время ({timeout} с)", "code": 124}
        out = self._clean(p.stdout.decode("utf-8", "replace"))
        return {"status": "OK", "stdout": out, "stderr": "", "code": p.returncode}

    def _clean(self, text):
        text = text.replace(self.home, HOME_ALIAS)
        text = text.replace(self.root, "/tmp/sandbox")
        return text


def run_script(script, setup=""):
    """Одноразовый запуск в чистой среде: сначала setup (вывод не нужен), потом script."""
    with ShellSandbox() as sb:
        if setup.strip():
            sb.run(setup)
        return sb.run(script)


def have_tools():
    return shutil.which("bash") is not None and shutil.which("git") is not None


if __name__ == "__main__":
    res = run_script(" ".join(sys.argv[1:]) if len(sys.argv) > 1 else sys.stdin.read())
    sys.stdout.write(res["stdout"])
    sys.exit(0 if res["status"] == "OK" else 1)
