"""Помощник для написания уроков: cue по подстроке фразы, запись файлов урока."""
import importlib.util, json, pathlib, textwrap
ROOT = pathlib.Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("narrate", ROOT / "content-pipeline/narrate.py")
narrate = importlib.util.module_from_spec(spec); spec.loader.exec_module(narrate)
PACK = ROOT / "content/packs/python-basics"


def scene(id, title, narration, actions, stress=None):
    narration = " ".join(narration.split())
    phrases = narrate.split_phrases(narration)
    out = []
    for a in actions:
        a = dict(a)
        at = a.pop("at", None)
        if at is not None:
            idx = [i for i, p in enumerate(phrases) if at in p]
            assert idx, f"[{id}] нет фразы с «{at}»: {phrases}"
            a["cue"] = idx[0]
        out.append(a)
    s = {"id": id, "title": title, "narration": narration, "actions": out}
    if stress:
        s["stress"] = stress
    return s


FILE = {"name": None}  # файл урока по умолчанию (main.sql, index.html…); None — main.py


def use_file(name):
    """Все следующие действия T/CLEAR/RUN/HL относятся к этому файлу."""
    FILE["name"] = name


def _f(d, file=None):
    f = file or FILE["name"]
    if f:
        d["file"] = f
    return d


def T(text, at=None, file=None): return _f({"type": "type", "text": text, **({"at": at} if at else {})}, file)
def CLEAR(at=None, file=None): return _f({"type": "clear", **({"at": at} if at else {})}, file)
def RUN(at=None, stdin=None, file=None):
    d = {"type": "run"}
    if at: d["at"] = at
    if stdin is not None: d["stdin"] = stdin
    return _f(d, file)
def OUT(text, at=None, err=False):
    d = {"type": "output", "text": text}
    if err: d["stream"] = "stderr"
    if at: d["at"] = at
    return d
def HL(lines, at=None, file=None): return _f({"type": "highlight", "lines": lines, **({"at": at} if at else {})}, file)
def NOTE(md, at=None): return {"type": "note", "md": md, **({"at": at} if at else {})}


def write_lesson(lid, title, goal, skills, prereq, scenes, notes, assignments, mistakes, min_pass=2,
                 pack="python-basics", runner="W"):
    d = ROOT / "content/packs" / pack / "lessons" / lid
    (d / "assignments").mkdir(parents=True, exist_ok=True)
    for f in (d / "assignments").glob("*.json"):
        f.unlink()
    files = []
    for a in assignments:
        name = f"assignments/{a['id']}.json"
        (d / name).write_text(json.dumps(a, ensure_ascii=False, indent=2) + "\n", "utf-8")
        files.append(name)
    lesson = {"id": lid, "title": title, "goal": goal, "skills": skills, "prerequisites": prereq,
              "runner": runner, "scenario": "scenario.json", "notes": "notes.md", "assignments": files,
              "passCriteria": {"minAssignmentsPassed": min_pass, "minScorePercent": 80},
              "commonMistakes": mistakes}
    (d / "lesson.json").write_text(json.dumps(lesson, ensure_ascii=False, indent=2) + "\n", "utf-8")
    (d / "scenario.json").write_text(json.dumps({"voice": "author", "scenes": scenes}, ensure_ascii=False, indent=2) + "\n", "utf-8")
    (d / "notes.md").write_text(textwrap.dedent(notes).strip() + "\n", "utf-8")
    words = sum(len(s["narration"].split()) for s in scenes)
    print(f"{lid}: {len(scenes)} сцен, {words} слов (~{words/140:.1f} мин), заданий {len(assignments)}")


def write_pack(pack_id, stage, title, description, language, lessons, skills, version="0.1.0"):
    d = ROOT / "content/packs" / pack_id
    d.mkdir(parents=True, exist_ok=True)
    data = {"id": pack_id, "version": version, "stage": stage, "title": title, "description": description,
            "language": language, "minAppVersion": 1, "lessons": lessons, "skills": skills}
    old = d / "pack.json"
    if old.exists() and "projects" in json.loads(old.read_text("utf-8")):
        data["projects"] = json.loads(old.read_text("utf-8"))["projects"]  # проекты пишет projects.py
    (d / "pack.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", "utf-8")


def asg(id, type, title, statement, goal, input, expected, constraints, hints_, tests, solution, explanation, criteria,
        wrong, starter=None, code=None):
    """Задание в формате схемы; wrong — [(код или ответ, почему)]."""
    a = {"id": id, "type": type, "title": title, "statement": statement, "goal": goal, "input": input,
         "expectedResult": expected, "constraints": constraints}
    if starter is not None:
        a["starterCode"] = starter
    if code is not None:
        a["code"] = code
    a.update({"hints": hints_, "tests": tests, "solution": solution, "explanation": explanation, "criteria": criteria})
    if type in ("predict", "review"):
        a["wrongSolutions"] = [{"code": w, "answer": w, "why": why} for w, why in wrong]
    else:
        a["wrongSolutions"] = [{"code": w, "why": why} for w, why in wrong]
    return a


def hints(*h):
    assert len(h) == 5
    return list(h)


def sql_out(code, setup=""):
    """Вывод SQL так, как его покажет приложение (то же ядро форматирования)."""
    import subprocess
    p = subprocess.run(["node", "--experimental-sqlite", "--no-warnings", str(ROOT / "tools/authoring/sqlout.mjs")],
                       input=json.dumps({"code": code, "setup": setup}), capture_output=True, text=True, check=True)
    return json.loads(p.stdout)


def sql_check(code, spec):
    import subprocess
    p = subprocess.run(["node", "--experimental-sqlite", "--no-warnings", str(ROOT / "tools/authoring/sqlout.mjs")],
                       input=json.dumps({"code": code, "check": spec}), capture_output=True, text=True, check=True)
    return json.loads(p.stdout)


# --- Веб-раннер (HTML/CSS/JS, Kotlin): тот же host page, что в приложении, в настольном Chrome -------
def _web_assets():
    import os
    env = os.environ.get("WEBRUNNER_ASSETS")
    built = ROOT / "app/src/main/assets/webrunner"
    p = pathlib.Path(env) if env else (built if (built / "host.js").exists() else pathlib.Path("/tmp/ca-assets/webrunner"))
    assert (p / "host.js").exists(), f"веб-раннер не собран: {p}"
    return p


def web_jobs(jobs):
    import subprocess, tempfile
    for i, j in enumerate(jobs):
        j.setdefault("id", f"j{i}")
    with tempfile.TemporaryDirectory() as d:
        jp, op = pathlib.Path(d, "j.json"), pathlib.Path(d, "o.json")
        jp.write_text(json.dumps(jobs, ensure_ascii=False), "utf-8")
        subprocess.run(["node", str(ROOT / "web-runner/tools/run-jobs.mjs"), str(jp), str(op), str(_web_assets().parent)],
                       check=True, capture_output=True, text=True)
        res = json.loads(op.read_text("utf-8"))
    assert not res.get("__network"), res["__network"]
    return [res[j["id"]] for j in jobs]


def web_out(lang, code, stdin=""):
    """Вывод запуска так, как его покажет приложение: {stdout, stderr, status}."""
    return web_jobs([{"lang": lang, "mode": "run", "code": code, "stdin": stdin}])[0]["result"]


def web_check(lang, code, spec):
    return web_jobs([{"lang": lang, "mode": "check", "code": code, "tests": spec}])[0]["check"]


def page_text(code, expr="document.body.innerText"):
    """Что видно на странице (текст), по настоящему рендеру."""
    r = web_check("html", code, {"kind": "web", "lang": "html", "cases": [{"id": "t", "expr": expr, "expected": None}]})
    return r["cases"][0]["actual"]


def web_verify(lang, a):
    """Эталон проходит, заготовка и типовые ошибки — нет (тем же раннером, что в приложении)."""
    t = a["tests"]
    if t.get("kind") == "answer":
        return
    jobs = [{"lang": lang, "mode": "check", "code": a["solution"], "tests": t}]
    jobs += [{"lang": lang, "mode": "check", "code": w["code"], "tests": t} for w in a["wrongSolutions"]]
    if a.get("starterCode"):
        jobs.append({"lang": lang, "mode": "check", "code": a["starterCode"], "tests": t})
    res = [r.get("check") or r for r in web_jobs(jobs)]
    assert res[0].get("allPassed"), (a["id"], "эталон не проходит", json.dumps(res[0], ensure_ascii=False)[:1500])
    for w, r in zip(a["wrongSolutions"], res[1:]):
        assert not r.get("allPassed"), (a["id"], "неверное решение проходит", w["code"])
    if a.get("starterCode"):
        assert not res[-1].get("allPassed"), (a["id"], "заготовка проходит")
