"""Валидатор контент-пакетов Code Academy (раздел 16 ТЗ: «не выпускать задания без тестов»).

Проверяет:
  1. Соответствие JSON Schema (пакет, урок, сценарий, задания).
  2. Сценарий анимированного урока: код из «видео» реально запускается и выводит
     ровно то, что покажет анимация.
  3. Задания: эталон проходит все тесты; заготовка (fix/complete) и типовые
     неверные решения — НЕ проходят; для predict ответ совпадает с реальным выводом.
  4. Конспект: все блоки ```python выполняются без ошибок.
  5. Длительность озвучки: ≤ 10 минут (ТЗ), предупреждение вне 3–8 минут.

Использование: python tools/validate_content.py content/packs [--json report.json]
Код возврата 1 при ошибках.
"""
import argparse
import hashlib
import json
import pathlib
import re
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
RUNNER_DIR = ROOT / "app" / "src" / "main" / "python"
sys.path.insert(0, str(RUNNER_DIR))
import ca_runner  # noqa: E402
import jsonschema  # noqa: E402
import importlib.util as _ilu  # noqa: E402

_spec = _ilu.spec_from_file_location("narrate", pathlib.Path(__file__).resolve().parents[1] / "content-pipeline" / "narrate.py")
_narrate = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_narrate)
split_phrases = _narrate.split_phrases

SCHEMAS = {n: json.loads((ROOT / "content" / "schema" / f"{n}.schema.json").read_text(encoding="utf-8"))
           for n in ("pack", "lesson", "scenario", "assignment")}
WORDS_PER_MIN = 140  # замер: образцы озвучки ~150 слов/мин; берём с запасом
MAX_MIN, WARN_MIN_LOW, WARN_MIN_HIGH = 10.0, 3.0, 8.0


class Report:
    def __init__(self):
        self.errors, self.warnings, self.stats = [], [], {}

    def err(self, where, msg):
        self.errors.append(f"{where}: {msg}")

    def warn(self, where, msg):
        self.warnings.append(f"{where}: {msg}")


def load_json(path, schema, rep):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        rep.err(str(path), f"не читается: {e}")
        return None
    errs = sorted(jsonschema.Draft202012Validator(SCHEMAS[schema]).iter_errors(data), key=lambda e: list(e.path))
    for e in errs:
        rep.err(str(path), f"схема {schema}: {'/'.join(map(str, e.path)) or '<корень>'}: {e.message}")
    return data if not errs else None


def norm(text):
    return ca_runner._normalize(text or "", "strip")


RUN_TIMEOUT_S = 5
_CHILD = """
import json, sys, tempfile
sys.path.insert(0, sys.argv[1])
import ca_runner
req = json.loads(sys.stdin.read())
with tempfile.TemporaryDirectory() as d:
    if req["mode"] == "run":
        sys.__stdout__.write(ca_runner.run(req["code"], d, req["stdin"], 65536))
    else:
        sys.__stdout__.write(ca_runner.check(req["code"], json.dumps(req["tests"]), d, 65536))
"""


def _child(req):
    """Код ученика/контента — в отдельном процессе с таймаутом: бесконечный цикл не вешает валидатор."""
    import subprocess
    try:
        p = subprocess.run([sys.executable, "-c", _CHILD, str(RUNNER_DIR)], input=json.dumps(req), capture_output=True,
                           text=True, timeout=RUN_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        return None
    return json.loads(p.stdout)


def run_code(code, stdin=""):
    r = _child({"mode": "run", "code": code, "stdin": stdin})
    return r if r is not None else {"status": "TIMEOUT", "stdout": "", "stderr": f"превышено время ({RUN_TIMEOUT_S} с)"}


def check_code(code, tests):
    r = _child({"mode": "check", "code": code, "tests": tests})
    return r if r is not None else {"allPassed": False, "timeout": True}


def validate_scenario(path, scen, rep):
    files, last, words = {}, None, 0
    for scene in scen["scenes"]:
        where = f"{path}#{scene['id']}"
        words += len(re.findall(r"\w+", scene["narration"]))
        # Привязка к фразам озвучки: номер фразы существует и не идёт назад.
        n_phr = len(split_phrases(scene["narration"]))
        prev_cue = -1
        for i, a in enumerate(scene["actions"]):
            if "cue" in a:
                if a["cue"] >= n_phr:
                    rep.err(where, f"действие {i}: cue={a['cue']}, а фраз в озвучке {n_phr}")
                elif a["cue"] < prev_cue:
                    rep.err(where, f"действие {i}: cue={a['cue']} раньше предыдущего ({prev_cue})")
                prev_cue = max(prev_cue, a["cue"])
        for i, a in enumerate(scene["actions"]):
            f = a.get("file", "main.py")
            t = a["type"]
            if t == "clear":
                files[f] = ""
            elif t == "type":
                files[f] = files.get(f, "") + a["text"]
            elif t == "run":
                last = run_code(files.get("main.py", ""), a.get("stdin", ""))
            elif t == "output" and a.get("stream") == "stderr":
                if last is None:
                    rep.err(where, f"действие {i}: output без предшествующего run")
                elif last["status"] == "OK":
                    rep.err(where, f"действие {i}: анимация показывает ошибку, а код выполнился без ошибок")
                else:
                    missing = [ln.strip() for ln in a["text"].splitlines() if ln.strip() and ln.strip() not in last["stderr"]]
                    if missing:
                        rep.err(where, f"действие {i}: в сообщении об ошибке нет {missing!r}; фактически: {last['stderr'].strip()[-300:]!r}")
                last = None
            elif t == "output":
                if last is None:
                    rep.err(where, f"действие {i}: output без предшествующего run")
                elif last["status"] != "OK":
                    rep.err(where, f"действие {i}: код сцены упал ({last['status']}): {last['stderr'].strip()[-200:]}")
                elif norm(last["stdout"]) != norm(a["text"]):
                    rep.err(where, f"действие {i}: анимация покажет {a['text']!r}, а код выводит {last['stdout']!r}")
                last = None
            elif t == "highlight":
                n = len(files.get(f, "").splitlines())
                bad = [ln for ln in a["lines"] if ln > n]
                if bad:
                    rep.err(where, f"действие {i}: подсветка строк {bad}, а в файле {n} строк")
    minutes = words / WORDS_PER_MIN
    validate_audio(path.parent, scen, rep)
    return words, minutes


def validate_audio(ldir, scen, rep):
    """Озвучка (если уже сделана): совпадение сцен, наличие файлов, разумные тайминги, актуальность текста."""
    meta_path = ldir / "audio" / "narration.json"
    if not meta_path.exists():
        rep.warn(str(ldir), "озвучки ещё нет (появится после workflow «Narrate lessons»)")
        return
    meta = json.loads(meta_path.read_text("utf-8"))
    by_id = {s["id"]: s for s in meta.get("scenes", [])}
    for scene in scen["scenes"]:
        where = f"{meta_path}#{scene['id']}"
        m = by_id.get(scene["id"])
        if not m:
            rep.err(where, "нет озвучки сцены")
            continue
        if not (ldir / "audio" / m["file"]).exists():
            rep.err(where, f"нет файла {m['file']}")
        if m["durationMs"] <= 0 or not m["cues"]:
            rep.err(where, "пустая озвучка")
        prev_end = 0
        for c in m["cues"]:
            if not (prev_end <= c["startMs"] <= c["endMs"] <= m["durationMs"] + 50):
                rep.err(where, f"неверный тайминг фразы {c}")
            prev_end = c["endMs"]
        payload = json.dumps([scene["narration"], scene.get("stress", {})], ensure_ascii=False)
        if m.get("textHash") != hashlib.sha256(payload.encode()).hexdigest()[:16]:
            rep.warn(where, "текст сцены изменился после озвучки — озвучка будет пересобрана")
    extra = set(by_id) - {s["id"] for s in scen["scenes"]}
    if extra:
        rep.err(str(meta_path), f"озвучка лишних сцен: {sorted(extra)}")


def validate_assignment(path, a, rep):
    where = str(path)
    tests = a["tests"]
    if tests["kind"] == "answer":
        actual = run_code(a["code"])
        if actual["status"] != "OK":
            rep.err(where, f"код для предсказания падает: {actual['stderr'][-200:]}")
        elif norm(actual["stdout"]) != norm(tests["expected_answer"]):
            rep.err(where, f"expected_answer {tests['expected_answer']!r} не совпадает с реальным выводом {actual['stdout']!r}")
        if norm(a["solution"]) != norm(tests["expected_answer"]):
            rep.err(where, "solution не совпадает с expected_answer")
        for w in a.get("wrongSolutions", []):
            if norm(w.get("answer", w["code"])) == norm(tests["expected_answer"]):
                rep.err(where, f"неверный ответ «{w['why']}» засчитывается как верный")
        return
    cases = tests["cases"]
    visible = [c for c in cases if not c.get("hidden")]
    hidden = [c for c in cases if c.get("hidden")]
    if not visible:
        rep.err(where, "нет видимых тестов")
    if tests["kind"] == "function" and not hidden:
        rep.err(where, "у задания с функцией нет скрытых тестов")
    if tests["kind"] == "stdout" and any(c.get("stdin") for c in cases) and not hidden:
        rep.err(where, "задание с вводом без скрытых тестов: «зашитый» ответ пройдёт")
    r = check_code(a["solution"], tests)
    if not r.get("allPassed"):
        rep.err(where, f"эталонное решение НЕ проходит тесты: {json.dumps(r, ensure_ascii=False)[:400]}")
    if a["type"] in ("fix", "complete") and check_code(a["starterCode"], tests).get("allPassed"):
        rep.err(where, "заготовка уже проходит все тесты — задание бессмысленно")
    for w in a.get("wrongSolutions", []):
        if check_code(w["code"], tests).get("allPassed"):
            rep.err(where, f"тесты НЕ ловят типовую ошибку «{w['why']}»")
    if not a.get("wrongSolutions"):
        rep.err(where, "нет wrongSolutions — непроверено, что тесты ловят типовые ошибки")
    elif len(a["wrongSolutions"]) < 2:
        rep.warn(where, "меньше двух типовых неверных решений")


def validate_notes(path, rep):
    text = path.read_text(encoding="utf-8")
    if len(text.strip()) < 100:
        rep.err(str(path), "конспект слишком короткий")
    for i, block in enumerate(re.findall(r"```python\n(.*?)```", text, re.S)):
        r = run_code(block)
        if r["status"] != "OK":
            rep.err(str(path), f"блок кода {i + 1} не выполняется: {r['stderr'].strip()[-200:]}")


def validate_pack(pack_dir, rep):
    pack = load_json(pack_dir / "pack.json", "pack", rep)
    if not pack:
        return
    pstats = rep.stats.setdefault(pack["id"], {"lessons": {}})
    seen_assign = set()
    for lid in pack["lessons"]:
        ldir = pack_dir / "lessons" / lid
        lesson = load_json(ldir / "lesson.json", "lesson", rep)
        if not lesson:
            continue
        if lesson["id"] != lid:
            rep.err(str(ldir), f"id урока {lesson['id']!r} не совпадает с папкой {lid!r}")
        titles = pack.get("skills", {})
        for sk in lesson["skills"]:
            if sk not in titles:
                rep.err(str(ldir), f"навык {sk!r} без названия в pack.json → skills (нужно для карты знаний)")
        for ref in [lesson["scenario"], lesson["notes"], *lesson["assignments"]]:
            if not (ldir / ref).exists():
                rep.err(str(ldir), f"нет файла {ref}")
        st = {"assignments": len(lesson["assignments"])}
        if (ldir / lesson["scenario"]).exists():
            scen = load_json(ldir / lesson["scenario"], "scenario", rep)
            if scen:
                words, minutes = validate_scenario(ldir / lesson["scenario"], scen, rep)
                st.update(words=words, minutes=round(minutes, 1), scenes=len(scen["scenes"]))
                if minutes > MAX_MIN:
                    rep.err(str(ldir), f"озвучка ~{minutes:.1f} мин > {MAX_MIN} мин: разбейте урок")
                elif not WARN_MIN_LOW <= minutes <= WARN_MIN_HIGH:
                    rep.warn(str(ldir), f"озвучка ~{minutes:.1f} мин (ориентир ТЗ 6–8)")
        if (ldir / lesson["notes"]).exists():
            validate_notes(ldir / lesson["notes"], rep)
        if lesson["passCriteria"]["minAssignmentsPassed"] > len(lesson["assignments"]):
            rep.err(str(ldir), "minAssignmentsPassed больше числа заданий")
        for ref in lesson["assignments"]:
            p = ldir / ref
            if not p.exists():
                continue
            a = load_json(p, "assignment", rep)
            if a:
                key = (lid, a["id"])
                if key in seen_assign:
                    rep.err(str(p), f"повтор id задания {a['id']}")
                seen_assign.add(key)
                validate_assignment(p, a, rep)
        pstats["lessons"][lid] = st


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("packs", type=pathlib.Path)
    ap.add_argument("--json", type=pathlib.Path)
    args = ap.parse_args()
    rep = Report()
    packs = sorted(p.parent for p in args.packs.glob("*/pack.json"))
    if not packs:
        rep.err(str(args.packs), "не найдено ни одного pack.json")
    for p in packs:
        validate_pack(p, rep)
    for w in rep.warnings:
        print("ПРЕДУПРЕЖДЕНИЕ", w)
    for e in rep.errors:
        print("ОШИБКА", e)
    print(json.dumps(rep.stats, ensure_ascii=False, indent=2))
    print(f"Итог: пакетов {len(packs)}, ошибок {len(rep.errors)}, предупреждений {len(rep.warnings)}")
    if args.json:
        args.json.write_text(json.dumps({"errors": rep.errors, "warnings": rep.warnings, "stats": rep.stats},
                                        ensure_ascii=False, indent=2), encoding="utf-8")
    return 1 if rep.errors else 0


if __name__ == "__main__":
    sys.exit(main())
