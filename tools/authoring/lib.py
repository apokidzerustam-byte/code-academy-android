"""Надстройка над mk.py для быстрого и безошибочного написания уроков (этап 11).

Главное отличие от первых уроков: вывод анимации и ожидаемые ответы заданий НЕ набираются вручную —
они считаются запуском настоящего кода той же песочницей ca_runner, что и в валидаторе. Так анимация
физически не может показать вывод, которого код не даёт.

    from lib import *
    begin()                                   # новый урок: буфер main.py пуст
    S("id", "Заголовок", "озвучка…", t("код\\n", "фраза"), run("фраза"), nt("**md**", "фраза"))
    stdout_task(...), fn_task(...), predict_task(...)
    finish("alg-01", ...);  write_packs({...})
"""
import json, pathlib, sys, io, contextlib
from mk import *  # noqa: F401,F403
from mk import ROOT, scene, write_lesson, asg, hints  # noqa: F401

sys.path.insert(0, str(ROOT / "tools"))
import validate_content as vc  # noqa: E402

PACKS = {}
_BUF = {"code": "", "file": None}


def begin(file=None):
    """Начало урока: буфер кода сбрасывается; file — имя файла сцен (по умолчанию main.py)."""
    _BUF["code"] = ""
    _BUF["file"] = file
    use_file(file)


# --- шаги сцены ----------------------------------------------------------------------------------
def t(text, at=None): return ("t", text, at)
def clr(at=None): return ("c", at)
def run(at=None, stdin=None): return ("r", at, stdin)
def nt(md, at=None): return ("n", md, at)
def hl(lines, at=None): return ("h", lines, at)
def pause(ms, at=None): return ("p", ms, at)
def out(text, at=None, err=False): return ("o", text, at, err)  # ручной вывод (для не-Python)


def _error_line(stderr):
    lines = [ln for ln in stderr.strip().splitlines() if ln.strip()]
    return lines[-1] if lines else ""


def S(id, title, narration, *steps, stress=None):
    actions = []
    for st in steps:
        k = st[0]
        if k == "t":
            _BUF["code"] += st[1]
            actions.append(T(st[1], at=st[2]))
        elif k == "c":
            _BUF["code"] = ""
            actions.append(CLEAR(at=st[1]))
        elif k == "r":
            res = vc.run_code(_BUF["code"], st[2] or "")
            actions.append(RUN(at=st[1], stdin=st[2]))
            if res["status"] == "OK" and not res["stderr"].strip():
                text = res["stdout"]
                actions.append(OUT(text if text.strip() else "(программа ничего не вывела)\n", at=st[1]))
            else:
                line = _error_line(res["stderr"])
                assert line, (id, "код упал без сообщения", res)
                actions.append(OUT(line + "\n", at=st[1], err=True))
        elif k == "n":
            actions.append(NOTE(st[1], at=st[2]))
        elif k == "h":
            actions.append(HL(st[1], at=st[2]))
        elif k == "p":
            d = {"type": "pause", "ms": st[1]}
            if st[2]: d["at"] = st[2]
            actions.append(d)
        elif k == "o":
            actions.append(OUT(st[1], at=st[2], err=st[3]))
    sc = scene(id, title, narration, actions, stress)
    # Заметки не влияют на код — ставим их по порядку фраз, как бы они ни были перечислены в шагах.
    acts = [a for a in sc["actions"] if a["type"] != "note"]
    notes_ = [a for a in sc["actions"] if a["type"] == "note"]
    for n in notes_:
        eff, pos = -1, len(acts)
        for i, a in enumerate(acts):
            c = a.get("cue", eff)
            if c > n.get("cue", -1) and n.get("cue") is not None:
                pos = i
                break
            eff = c
        acts.insert(pos, n)
    sc["actions"] = acts
    prev = -1
    for a in sc["actions"]:
        c = a.get("cue")
        if c is not None:
            assert c >= prev, f"[{id}] действие {a.get('type')} привязано к фразе {c}, а предыдущее — к {prev}: поменяйте порядок шагов"
            prev = c
    return sc


# --- вычисление ожиданий -------------------------------------------------------------------------
def run_out(code, stdin=""):
    r = vc.run_code(code, stdin)
    assert r["status"] == "OK", ("эталон упал", r["stderr"][-400:], code[:200])
    return r["stdout"]


def _passes(code, tests):
    r = vc.check_code(code, tests)
    return bool(r.get("allPassed"))


def _text(v, default):
    return v if v is not None else default


def stdout_task(id, title, statement, solution, cases, wrong, hints_, explanation, *, type="write", starter="",
                goal=None, criteria=None, constraints=None, input_text=None, expected_text=None, match="strip"):
    """Задание «вывод программы». cases: [stdin | (stdin, hidden)]; ожидаемый вывод считается по эталону.
    Первый случай виден ученику, остальные скрыты (если не указано иначе)."""
    tc = []
    for i, c in enumerate(cases):
        stdin, hidden = (c if isinstance(c, tuple) else (c, i > 0))
        exp = run_out(solution, stdin)
        d = {"id": ("h" if hidden else "v") + str(i + 1), "stdin": stdin, "expected_stdout": exp}
        if hidden: d["hidden"] = True
        tc.append(d)
    tests = {"kind": "stdout", "match": match, "cases": tc}
    assert _passes(solution, tests), (id, "эталон не проходит свои тесты")
    for w, why in wrong:
        assert not _passes(w, tests), (id, "тесты не ловят неверное решение", why)
    if type in ("fix", "complete"):
        assert starter and not _passes(starter, tests), (id, "заготовка проходит или не задана")
    return asg(id, type, title, statement, _text(goal, title), _text(input_text, "Определяется условием."),
               _text(expected_text, "Вывод, указанный в условии."), constraints or [], hints_, tests, solution,
               explanation, criteria or ["Все проверки пройдены, включая скрытые."], wrong,
               starter=(starter if type != "predict" else None))


def fn_task(id, title, statement, fname, solution, cases, wrong, hints_, explanation, *, type="function", starter="",
            goal=None, criteria=None, constraints=None, tolerance=None):
    """Задание «функция». cases: [args | (args, hidden) | dict(args=…, kwargs=…, expected_error=…)]; ожидание — по эталону."""
    ns = {}
    exec(compile(solution, "solution", "exec"), ns)
    fn = ns[fname]
    tc = []
    for i, c in enumerate(cases):
        if isinstance(c, dict):
            case = dict(c); hidden = case.pop("hidden", i > 1)
        else:
            args, hidden = (c if isinstance(c, tuple) and len(c) == 2 and isinstance(c[1], bool) else (c, i > 1))
            case = {"args": list(args)}
        case["id"] = ("h" if hidden else "v") + str(i + 1)
        if hidden: case["hidden"] = True
        if "expected_error" not in case:
            import copy
            val = fn(*copy.deepcopy(case.get("args", [])), **copy.deepcopy(case.get("kwargs", {})))
            json.dumps(val)
            case["expected"] = json.loads(json.dumps(val))
        tc.append(case)
    tests = {"kind": "function", "function": fname, "cases": tc}
    if tolerance: tests["tolerance"] = tolerance
    assert _passes(solution, tests), (id, "эталон не проходит свои тесты")
    for w, why in wrong:
        assert not _passes(w, tests), (id, "тесты не ловят неверное решение", why)
    if type in ("fix", "complete"):
        assert starter and not _passes(starter, tests), (id, "заготовка проходит или не задана")
    return asg(id, type, title, statement, _text(goal, title), "Аргументы функции из условия.",
               "Значение, которое возвращает функция.", constraints or [], hints_, tests, solution, explanation,
               criteria or ["Все проверки пройдены, включая скрытые."], wrong, starter=starter or None)


def predict_task(id, title, code, wrong, hints_, explanation, *, statement="Что выведет программа? Запишите вывод построчно, не запуская код.",
                 goal=None, type="predict", stdin=""):
    """Что выведет код. Ответ считается запуском; wrong — [(неверный ответ, почему)]."""
    expected = run_out(code, stdin)
    for w, why in wrong:
        assert w.strip() != expected.strip(), (id, "неверный ответ совпал с верным", why)
    return asg(id, type, title, statement, _text(goal, title), "Нет.", "Вывод программы.", ["Ответьте без запуска."],
               hints_, {"kind": "answer", "expected_answer": expected}, expected, explanation,
               ["Все строки вывода верны."], wrong, code=code)


# --- уроки и пакеты ------------------------------------------------------------------------------
def finish(lid, title, goal, skills, prereq, scenes, notes, tasks, mistakes, *, pack, runner="W", min_pass=None):
    """skills — словарь id → название (попадает в pack.json)."""
    p = PACKS.setdefault(pack, {"lessons": [], "skills": {}})
    if lid not in p["lessons"]:
        p["lessons"].append(lid)
    p["skills"].update(skills)
    write_lesson(lid, title, goal, list(skills), prereq, scenes, notes, tasks, mistakes,
                 min_pass=min_pass or max(2, len(tasks) - 1), pack=pack, runner=runner)
    _write_pack(pack)


PACK_META = {
    "python-core": dict(stage=3, title="Python: функции, коллекции, файлы, ООП", language="python", requires=["python-basics"],
        description="Функции, кортежи и множества, словари, исключения, файлы, JSON, модули, классы, асинхронность и HTTP — продолжение курса Python."),
    "algorithms": dict(stage=4, title="Алгоритмы и структуры данных", language="python", requires=["python-core"],
        description="Big O, поиск, сортировка, рекурсия, стек, очередь, хеш-таблицы, деревья, графы и оптимизация — на Python, с автопроверкой."),
}


def _write_pack(pid, version=None):
    m = PACK_META[pid]
    p = PACKS[pid]
    d = ROOT / "content/packs" / pid
    old = d / "pack.json"
    prev = json.loads(old.read_text("utf-8")) if old.exists() else {}
    lessons = list(prev.get("lessons", []))
    lessons += [x for x in p["lessons"] if x not in lessons]
    skills = dict(prev.get("skills", {})); skills.update(p["skills"])
    data = {"id": pid, "version": version or prev.get("version", "0.1.0"), "stage": m["stage"], "title": m["title"],
            "description": m["description"], "language": m.get("language", "python"), "minAppVersion": 1}
    if m.get("requires"): data["requiresPacks"] = m["requires"]
    data.update({"lessons": lessons, "skills": skills})
    if "projects" in prev: data["projects"] = prev["projects"]
    d.mkdir(parents=True, exist_ok=True)
    old.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", "utf-8")
