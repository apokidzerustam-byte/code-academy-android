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


def T(text, at=None): return {"type": "type", "text": text, **({"at": at} if at else {})}
def CLEAR(at=None): return {"type": "clear", **({"at": at} if at else {})}
def RUN(at=None, stdin=None):
    d = {"type": "run"}
    if at: d["at"] = at
    if stdin is not None: d["stdin"] = stdin
    return d
def OUT(text, at=None, err=False):
    d = {"type": "output", "text": text}
    if err: d["stream"] = "stderr"
    if at: d["at"] = at
    return d
def HL(lines, at=None): return {"type": "highlight", "lines": lines, **({"at": at} if at else {})}
def NOTE(md, at=None): return {"type": "note", "md": md, **({"at": at} if at else {})}


def write_lesson(lid, title, goal, skills, prereq, scenes, notes, assignments, mistakes, min_pass=2):
    d = PACK / "lessons" / lid
    (d / "assignments").mkdir(parents=True, exist_ok=True)
    for f in (d / "assignments").glob("*.json"):
        f.unlink()
    files = []
    for a in assignments:
        name = f"assignments/{a['id']}.json"
        (d / name).write_text(json.dumps(a, ensure_ascii=False, indent=2) + "\n", "utf-8")
        files.append(name)
    lesson = {"id": lid, "title": title, "goal": goal, "skills": skills, "prerequisites": prereq,
              "runner": "W", "scenario": "scenario.json", "notes": "notes.md", "assignments": files,
              "passCriteria": {"minAssignmentsPassed": min_pass, "minScorePercent": 80},
              "commonMistakes": mistakes}
    (d / "lesson.json").write_text(json.dumps(lesson, ensure_ascii=False, indent=2) + "\n", "utf-8")
    (d / "scenario.json").write_text(json.dumps({"voice": "author", "scenes": scenes}, ensure_ascii=False, indent=2) + "\n", "utf-8")
    (d / "notes.md").write_text(textwrap.dedent(notes).strip() + "\n", "utf-8")
    words = sum(len(s["narration"].split()) for s in scenes)
    print(f"{lid}: {len(scenes)} сцен, {words} слов (~{words/140:.1f} мин), заданий {len(assignments)}")


def hints(*h):
    assert len(h) == 5
    return list(h)
